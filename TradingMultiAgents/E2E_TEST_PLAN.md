# TradingAgents WebUI E2Eテスト計画書

## 1. 概要

### 目的
TradingAgents WebUIの全機能を自動的にテストし、ユーザー体験の品質を保証する。

### 対象範囲
- 全ページのナビゲーション
- フォーム入力と送信
- データ表示の正確性
- レスポンシブデザイン
- エラーハンドリング
- パフォーマンス

### テストフレームワーク
**Playwright** を選定（理由：Streamlitとの互換性、スクリーンショット機能、複数ブラウザ対応）

## 2. テスト環境

### 必要なツール
```bash
# インストール
pip install playwright pytest pytest-playwright pytest-html pytest-xdist
playwright install chromium firefox webkit

# オプション（ビジュアルテスト用）
pip install pytest-screenshot pixelmatch-py
```

### ブラウザマトリックス
- Chrome/Chromium (メイン)
- Firefox
- Safari/WebKit
- モバイルエミュレーション（iPhone、Android）

### 解像度マトリックス
- Desktop: 1920x1080, 1366x768
- Tablet: 768x1024
- Mobile: 375x812, 390x844

## 3. テストシナリオ

### 3.1 基本ナビゲーション
```
TC001: メインページの表示
- WebUIを起動
- http://localhost:8501 にアクセス
- ページタイトルの確認
- ダッシュボードの表示確認
- スクリーンショット取得

TC002: サイドバーナビゲーション
- 各メニュー項目のクリック
- ページ遷移の確認
- URLの変更確認
- 戻るボタンの動作確認
```

### 3.2 ダッシュボードページ
```
TC003: 統計情報の表示
- 総分析数の表示確認
- 完了分析数の確認
- 実行中分析の確認
- 成功率の計算確認

TC004: 人気銘柄分析
- 銘柄リストの表示
- 分析時間の表示
- クリックアクション
```

### 3.3 設定ページ
```
TC005: API設定
- API Key入力フィールドの表示
- マスキング機能の確認
- 保存ボタンの動作
- 設定の永続化確認

TC006: モデル選択
- ドロップダウンの動作
- 選択肢の確認
- デフォルト値の確認
```

### 3.4 分析実行ページ
```
TC007: 銘柄分析の実行
- 銘柄シンボル入力
- バリデーション確認
- 分析実行ボタン
- プログレス表示
- 結果の表示

TC008: エラーハンドリング
- 無効な銘柄の入力
- API制限エラー
- ネットワークエラー
```

### 3.5 結果表示ページ
```
TC009: 分析結果の表示
- チャートの描画
- データテーブル
- エクスポート機能
- フィルタリング

TC010: PDFレポート生成
- レポート生成ボタン
- ダウンロード確認
- 内容の検証
```

### 3.6 レスポンシブデザイン
```
TC011: モバイル表示
- サイドバーの折りたたみ
- タッチ操作
- スクロール動作
- 画面回転

TC012: タブレット表示
- レイアウト調整
- グリッド表示
- ナビゲーション
```

### 3.7 パフォーマンステスト
```
TC013: ページロード時間
- 各ページの読み込み時間測定
- リソースの最適化確認
- キャッシュの動作

TC014: 大量データ処理
- 100件以上の結果表示
- スクロール性能
- メモリ使用量
```

## 4. テスト実装構造

```
tests/
├── e2e/
│   ├── conftest.py           # Pytest設定とフィクスチャ
│   ├── test_navigation.py    # ナビゲーションテスト
│   ├── test_dashboard.py     # ダッシュボードテスト
│   ├── test_settings.py      # 設定ページテスト
│   ├── test_execution.py     # 分析実行テスト
│   ├── test_results.py       # 結果表示テスト
│   ├── test_responsive.py    # レスポンシブテスト
│   └── test_performance.py   # パフォーマンステスト
├── fixtures/
│   ├── test_data.json        # テストデータ
│   └── mock_responses.json   # モックレスポンス
├── screenshots/              # スクリーンショット保存
│   └── baseline/            # ベースライン画像
└── reports/                  # テストレポート
```

## 5. テストスクリプトサンプル

### conftest.py
```python
import pytest
from playwright.sync_api import Page, Browser
import json
from datetime import datetime

@pytest.fixture(scope="session")
def browser_context(browser: Browser):
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="ja-JP",
        timezone_id="Asia/Tokyo"
    )
    yield context
    context.close()

@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    page.goto("http://localhost:8501")
    yield page
    page.close()

@pytest.fixture
def screenshot_dir(request):
    test_name = request.node.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"screenshots/{test_name}_{timestamp}"
```

### test_navigation.py
```python
import pytest
from playwright.sync_api import Page, expect

class TestNavigation:
    def test_main_page_loads(self, page: Page, screenshot_dir):
        # ページタイトルの確認
        expect(page).to_have_title("TradingAgents WebUI")
        
        # ダッシュボードの表示確認
        expect(page.locator("text=ダッシュボード")).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=f"{screenshot_dir}/main_page.png", full_page=True)
        
    def test_sidebar_navigation(self, page: Page, screenshot_dir):
        pages = [
            ("分析設定", "settings"),
            ("分析実行", "execution"),
            ("結果表示", "results"),
        ]
        
        for page_name, page_id in pages:
            # サイドバーのリンクをクリック
            page.click(f"text={page_name}")
            
            # ページ遷移の確認
            page.wait_for_load_state("networkidle")
            
            # スクリーンショット
            page.screenshot(path=f"{screenshot_dir}/{page_id}.png", full_page=True)
            
            # 要素の存在確認
            assert page.is_visible(f"[data-testid='{page_id}-content']")
```

## 6. CI/CD統合

### GitHub Actions設定
```yaml
name: E2E Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 毎日実行

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest pytest-playwright
          playwright install ${{ matrix.browser }}
      
      - name: Start WebUI
        run: |
          python run_webui.py &
          sleep 10
      
      - name: Run E2E tests
        run: |
          pytest tests/e2e/ \
            --browser=${{ matrix.browser }} \
            --screenshot=on \
            --html=reports/e2e-report.html \
            --self-contained-html
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots-${{ matrix.browser }}
          path: tests/screenshots/
      
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-report-${{ matrix.browser }}
          path: reports/e2e-report.html
```

## 7. ビジュアルリグレッションテスト

### 実装例
```python
import pytest
from pixelmatch import pixelmatch
from PIL import Image
import numpy as np

def test_visual_regression(page: Page):
    # 現在のスクリーンショット
    page.screenshot(path="current.png")
    
    # ベースライン画像と比較
    baseline = Image.open("baseline/main_page.png")
    current = Image.open("current.png")
    
    # 差分計算
    diff = Image.new("RGBA", baseline.size)
    mismatch = pixelmatch(
        np.array(baseline),
        np.array(current),
        np.array(diff),
        threshold=0.1
    )
    
    # 差分が5%以下なら合格
    assert mismatch / (baseline.width * baseline.height) < 0.05
```

## 8. 実行スケジュール

### 開発フェーズ
- プルリクエスト時: 基本テストのみ
- マージ時: 全テストスイート
- 夜間: フルリグレッションテスト

### リリースフェーズ
- リリース前: 全ブラウザ・全解像度テスト
- リリース後: スモークテスト

## 9. レポートとモニタリング

### テストレポート
- HTML形式のレポート生成
- スクリーンショット付き
- 実行時間の記録
- 失敗率の追跡

### アラート設定
- テスト失敗時のSlack通知
- パフォーマンス低下の警告
- ビジュアルリグレッションの検出

## 10. メンテナンス

### 月次タスク
- [ ] ベースライン画像の更新
- [ ] テストデータの見直し
- [ ] 新機能のテスト追加
- [ ] 古いテストの削除

### 四半期タスク
- [ ] ブラウザバージョンの更新
- [ ] パフォーマンスベンチマークの見直し
- [ ] テストカバレッジの分析

---

作成日: 2025年7月15日
最終更新: 2025年7月15日