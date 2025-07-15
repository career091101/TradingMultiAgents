# Phase 4 E2E Test Implementation Plan

## 実装計画概要

Phase 4のE2Eテスト実装を効率的に進めるための詳細な実装計画です。既存のPlaywrightベースのテストフレームワークを拡張し、より高度なシナリオテストを実現します。

## 1. テストフレームワーク拡張

### 1.1 Page Object Model (POM) の実装

```python
# tests/e2e/pages/base_page.py
class BasePage:
    def __init__(self, page):
        self.page = page
        self.timeout = 30000
    
    async def wait_for_element(self, selector, state="visible"):
        await self.page.wait_for_selector(selector, state=state, timeout=self.timeout)
    
    async def safe_click(self, selector):
        await self.wait_for_element(selector)
        await self.page.click(selector)

# tests/e2e/pages/settings_page.py
class SettingsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.ticker_input = '[data-testid="ticker_input"]'
        self.analyst_checkboxes = '[data-testid^="analyst_"]'
        self.save_button = '[data-testid="save_settings"]'
    
    async def set_ticker(self, ticker):
        await self.page.fill(self.ticker_input, ticker)
    
    async def select_preset(self, preset_name):
        await self.safe_click(f'[data-testid="preset_{preset_name}"]')

# tests/e2e/pages/execution_page.py
class ExecutionPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.start_button = '[data-testid="start_analysis"]'
        self.progress_bar = '[data-testid="progress_bar"]'
        self.stop_button = '[data-testid="stop_analysis"]'
    
    async def start_analysis(self):
        await self.safe_click(self.start_button)
    
    async def wait_for_completion(self):
        await self.page.wait_for_selector(
            '[data-testid="analysis_complete"]',
            timeout=600000  # 10分
        )

# tests/e2e/pages/results_page.py
class ResultsPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.pdf_button = '[data-testid="generate_pdf"]'
        self.result_tabs = '[data-testid^="result_tab_"]'
    
    async def generate_pdf(self):
        await self.safe_click(self.pdf_button)
        # PDFダウンロードを待機
        download = await self.page.wait_for_event('download')
        return download
```

### 1.2 テストフィクスチャの拡張

```python
# tests/e2e/fixtures/test_fixtures.py
import pytest
from playwright.async_api import async_playwright
import asyncio
import json

@pytest.fixture(scope="session")
async def browser_context():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # デバッグ時は可視化
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ja-JP',
            timezone_id='Asia/Tokyo'
        )
        yield context
        await browser.close()

@pytest.fixture
async def authenticated_page(browser_context):
    page = await browser_context.new_page()
    
    # APIキーを事前設定
    await page.goto("http://localhost:8501")
    await page.evaluate('''
        localStorage.setItem('tradingagents_settings', JSON.stringify({
            api_keys: {
                finnhub: 'test_finnhub_key',
                openai: 'test_openai_key'
            }
        }))
    ''')
    
    yield page
    await page.close()

@pytest.fixture
def mock_api_responses():
    return {
        'analysis_success': {
            'status': 'completed',
            'data': {'recommendation': 'BUY', 'confidence': 0.85}
        },
        'rate_limit_error': {
            'error': 'API rate limit exceeded',
            'retry_after': 60
        }
    }
```

### 1.3 カスタムアサーション

```python
# tests/e2e/utils/custom_assertions.py
class CustomAssertions:
    @staticmethod
    async def assert_element_visible(page, selector, timeout=5000):
        try:
            await page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except:
            raise AssertionError(f"Element {selector} is not visible")
    
    @staticmethod
    async def assert_text_contains(page, selector, expected_text):
        element = await page.wait_for_selector(selector)
        actual_text = await element.inner_text()
        assert expected_text in actual_text, \
            f"Expected '{expected_text}' in '{actual_text}'"
    
    @staticmethod
    async def assert_progress_completes(page, timeout=300000):
        await page.wait_for_selector(
            '[data-testid="progress_bar"][aria-valuenow="100"]',
            timeout=timeout
        )
```

## 2. シナリオテストの実装例

### 2.1 完全分析フローテスト

```python
# tests/e2e/scenarios/test_full_analysis_flow.py
import pytest
from pages.settings_page import SettingsPage
from pages.execution_page import ExecutionPage
from pages.results_page import ResultsPage
from utils.custom_assertions import CustomAssertions

class TestFullAnalysisFlow:
    @pytest.mark.asyncio
    async def test_first_time_user_complete_flow(self, browser_context):
        # 新規コンテキストでクリーンな状態を確保
        page = await browser_context.new_page()
        await page.goto("http://localhost:8501")
        
        # Step 1: 初回起動確認
        assert_helper = CustomAssertions()
        await assert_helper.assert_element_visible(
            page, '[data-testid="env_warning"]'
        )
        
        # Step 2: 設定ページへ移動
        await page.click('[data-testid="nav_settings"]')
        settings_page = SettingsPage(page)
        
        # Step 3: APIキー設定
        await page.fill('[data-testid="finnhub_api_key"]', 'test_key_123')
        await page.fill('[data-testid="openai_api_key"]', 'test_key_456')
        await settings_page.save_button.click()
        
        # Step 4: 環境チェック成功確認
        await assert_helper.assert_text_contains(
            page, '[data-testid="env_status"]', '✅'
        )
        
        # Step 5: クイックアクション実行
        await page.click('[data-testid="nav_dashboard"]')
        await page.click('[data-testid="quick_spy"]')
        
        # Step 6: 実行ページへの自動遷移確認
        await page.wait_for_url("**/execution")
        execution_page = ExecutionPage(page)
        
        # Step 7: 分析開始
        await execution_page.start_analysis()
        await assert_helper.assert_element_visible(
            page, '[data-testid="progress_container"]'
        )
        
        # Step 8: 完了待機（モックの場合は高速）
        await execution_page.wait_for_completion()
        
        # Step 9: 結果ページへの自動遷移確認
        await page.wait_for_url("**/results")
        results_page = ResultsPage(page)
        
        # Step 10: PDF生成
        download = await results_page.generate_pdf()
        assert download.suggested_filename.endswith('.pdf')
        
        await page.close()
```

### 2.2 エラーリカバリーテスト

```python
# tests/e2e/scenarios/test_error_recovery.py
class TestErrorRecovery:
    @pytest.mark.asyncio
    async def test_api_rate_limit_recovery(self, authenticated_page, mock_api_responses):
        page = authenticated_page
        
        # APIモックを設定（レート制限エラーを返す）
        await page.route('**/api/analyze', lambda route: route.fulfill(
            status=429,
            json=mock_api_responses['rate_limit_error']
        ))
        
        # 分析実行
        await page.goto("http://localhost:8501/execution")
        await page.click('[data-testid="start_analysis"]')
        
        # エラーメッセージ確認
        error_msg = await page.wait_for_selector('[data-testid="error_message"]')
        assert "rate limit" in await error_msg.inner_text()
        
        # リトライボタン確認
        retry_button = await page.wait_for_selector('[data-testid="retry_analysis"]')
        
        # APIモックを成功に変更
        await page.unroute('**/api/analyze')
        await page.route('**/api/analyze', lambda route: route.fulfill(
            json=mock_api_responses['analysis_success']
        ))
        
        # リトライ実行
        await retry_button.click()
        
        # 成功確認
        await page.wait_for_selector('[data-testid="analysis_complete"]')
```

### 2.3 データ永続性テスト

```python
# tests/e2e/integration/test_data_persistence.py
class TestDataPersistence:
    @pytest.mark.asyncio
    async def test_settings_persistence_across_reload(self, browser_context):
        page = await browser_context.new_page()
        await page.goto("http://localhost:8501/settings")
        
        # カスタム設定を作成
        test_settings = {
            'ticker': 'TSLA',
            'analysts': ['technical', 'sentiment'],
            'depth': 4,
            'timeout': 300
        }
        
        # 設定を入力
        await page.fill('[data-testid="ticker_input"]', test_settings['ticker'])
        await page.set_input_value('[data-testid="depth_slider"]', str(test_settings['depth']))
        
        # 保存
        await page.click('[data-testid="save_settings"]')
        await page.wait_for_timeout(1000)  # 保存完了待機
        
        # ページリロード
        await page.reload()
        
        # 設定が復元されていることを確認
        ticker_value = await page.input_value('[data-testid="ticker_input"]')
        assert ticker_value == test_settings['ticker']
        
        depth_value = await page.get_attribute('[data-testid="depth_slider"]', 'value')
        assert int(depth_value) == test_settings['depth']
```

## 3. 実装スケジュール

### Week 1 (Days 1-7)
- **Day 1-2**: Page Object Model基盤構築
  - BasePage, SettingsPage, ExecutionPage, ResultsPage実装
  - カスタムアサーションライブラリ作成
  
- **Day 3-4**: 基本シナリオテスト実装
  - E2E-P4-001: 初回ユーザーフロー
  - E2E-P4-002: プリセット活用
  
- **Day 5-6**: マルチセッションテスト
  - E2E-P4-004: 複数銘柄分析
  - E2E-P4-005: 並行実行
  
- **Day 7**: 中間レビューと調整

### Week 2 (Days 8-14)
- **Day 8-9**: エラーハンドリングテスト
  - E2E-P4-007: API制限エラー
  - E2E-P4-008: ネットワーク障害
  
- **Day 10-11**: データ永続性テスト
  - E2E-P4-010: 設定永続化
  - E2E-P4-011: 履歴管理
  
- **Day 12-13**: パフォーマンステスト
  - E2E-P4-013: 長期間データ
  - E2E-P4-014: 大量ログ
  
- **Day 14**: 統合テストとドキュメント化

## 4. CI/CD統合

```yaml
# .github/workflows/e2e-phase4-tests.yml
name: Phase 4 E2E Tests

on:
  pull_request:
    paths:
      - 'webui/**'
      - 'tests/e2e/**'
  schedule:
    - cron: '0 2 * * *'  # 毎日午前2時

jobs:
  e2e-scenarios:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-category: [scenarios, integration, performance]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright
          playwright install chromium --with-deps
      
      - name: Start WebUI
        run: |
          python run_webui.py &
          sleep 10
      
      - name: Run E2E Tests
        run: |
          pytest tests/e2e/${{ matrix.test-category }} \
            -v \
            --html=reports/${{ matrix.test-category }}_report.html \
            --screenshot=on \
            --video=on-first-retry
      
      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-results-${{ matrix.test-category }}
          path: |
            reports/
            screenshots/
            videos/
```

## 5. テストデータ管理

```python
# tests/e2e/fixtures/test_data.py
class TestDataManager:
    @staticmethod
    def get_test_tickers():
        return ['SPY', 'AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    @staticmethod
    def get_test_date_ranges():
        return [
            {'start': '2024-01-01', 'end': '2024-12-31'},
            {'start': '2023-01-01', 'end': '2023-12-31'},
            {'start': '2020-01-01', 'end': '2024-12-31'}  # 5年間
        ]
    
    @staticmethod
    def get_mock_analysis_result():
        return {
            'summary': 'Test analysis summary',
            'recommendation': 'BUY',
            'confidence': 0.85,
            'reports': {
                'technical': 'Technical analysis report...',
                'fundamental': 'Fundamental analysis report...'
            }
        }
```

## 6. 実装のベストプラクティス

1. **非同期処理の活用**
   - Playwrightの非同期APIを最大限活用
   - 並列実行可能なテストは並列化

2. **待機戦略**
   - 固定待機時間は避ける
   - 要素の出現/状態変化を待つ
   - カスタムwait条件の実装

3. **エラーハンドリング**
   - スクリーンショット自動保存
   - 詳細なエラーログ
   - リトライメカニズム

4. **テストの独立性**
   - 各テストは独立して実行可能
   - テスト間の依存関係を排除
   - クリーンアップの徹底

5. **パフォーマンス考慮**
   - 不要な待機の削減
   - 効率的なセレクタ使用
   - リソースの適切な解放