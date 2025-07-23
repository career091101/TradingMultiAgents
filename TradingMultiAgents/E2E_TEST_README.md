# TradingAgents WebUI E2Eテストガイド

## 概要
このドキュメントは、TradingAgents WebUIのEnd-to-End（E2E）テストの実行方法を説明します。

## セットアップ

### 1. 依存関係のインストール
```bash
# 基本的な依存関係
pip install -r requirements.txt

# E2Eテスト用の追加パッケージ
pip install playwright pytest pytest-playwright pytest-html pytest-xdist

# Playwrightブラウザのインストール
playwright install chromium firefox webkit
```

### 2. 環境変数の設定
```bash
export FINNHUB_API_KEY="your_finnhub_api_key"
export OPENAI_API_KEY="your_openai_api_key"
```

## テストの実行

### 基本的な実行
```bash
# すべてのE2Eテストを実行
python tests/e2e/run_e2e_tests.py

# スモークテストのみ実行（高速）
python tests/e2e/run_e2e_tests.py --smoke

# 特定のブラウザで実行
python tests/e2e/run_e2e_tests.py --browser firefox

# ヘッドフルモードで実行（ブラウザを表示）
python tests/e2e/run_e2e_tests.py --headless

# 並列実行（4プロセス）
python tests/e2e/run_e2e_tests.py --parallel 4
```

### Pytestコマンドでの実行
```bash
# 基本実行
pytest tests/e2e/

# 詳細出力
pytest tests/e2e/ -v

# 特定のテストファイル
pytest tests/e2e/test_navigation.py

# 特定のテストケース
pytest tests/e2e/test_navigation.py::TestNavigation::test_main_page_loads

# マーカーを使用
pytest tests/e2e/ -m smoke
pytest tests/e2e/ -m "not slow"
```

## テスト構造

```
tests/
├── e2e/
│   ├── conftest.py           # Pytest設定とフィクスチャ
│   ├── test_navigation.py    # ナビゲーションテスト
│   ├── test_dashboard.py     # ダッシュボードテスト
│   ├── test_settings.py      # 設定ページテスト（未実装）
│   ├── test_execution.py     # 分析実行テスト（未実装）
│   ├── test_results.py       # 結果表示テスト（未実装）
│   └── run_e2e_tests.py      # テスト実行スクリプト
├── fixtures/
│   └── test_data.json        # テストデータ
├── screenshots/              # スクリーンショット
│   ├── baseline/            # ベースライン画像
│   └── failures/            # 失敗時のスクリーンショット
└── reports/                  # HTMLレポート
```

## テストレポート

### HTMLレポート
テスト実行後、`tests/reports/`ディレクトリにHTMLレポートが生成されます。
```bash
# レポートを開く（macOS）
open tests/reports/e2e_report_*.html

# レポートを開く（Linux）
xdg-open tests/reports/e2e_report_*.html
```

### スクリーンショット
- 各テストケースでスクリーンショットが自動的に保存されます
- 失敗時は`tests/screenshots/failures/`に保存されます
- ベースライン画像は`tests/screenshots/baseline/`に保存されます

## CI/CD統合

### GitHub Actions
`.github/workflows/e2e-tests.yml`が設定されています：

- **プルリクエスト時**: スモークテストを実行
- **mainブランチへのプッシュ時**: フルテストを実行
- **毎日定期実行**: 午前0時（UTC）にフルテストを実行
- **手動実行**: GitHub UIから手動でトリガー可能

### 必要なSecretsの設定
GitHubリポジトリの設定で以下のSecretsを追加してください：
- `FINNHUB_API_KEY`
- `OPENAI_API_KEY`

## トラブルシューティング

### よくある問題

#### 1. WebUIが起動しない
```bash
# ポートが使用中の場合
lsof -i :8501
kill -9 <PID>

# 手動で起動してテスト
python run_webui.py
```

#### 2. Playwrightのエラー
```bash
# ブラウザを再インストール
playwright install --force

# 依存関係を確認
playwright install-deps
```

#### 3. タイムアウトエラー
```python
# conftest.pyでタイムアウトを調整
page.wait_for_load_state("networkidle", timeout=30000)
```

## ベストプラクティス

### 1. テストの独立性
- 各テストは独立して実行可能にする
- テスト間の依存関係を避ける
- セットアップとティアダウンを適切に行う

### 2. 待機戦略
```python
# 明示的な待機を使用
page.wait_for_selector("text=ダッシュボード", state="visible")

# ネットワーク待機
page.wait_for_load_state("networkidle")

# タイムアウトは避ける
# page.wait_for_timeout(5000)  # 避ける
```

### 3. セレクタの選択
```python
# 推奨: テストIDを使用
page.locator("[data-testid='submit-button']")

# 次善: テキストベース
page.locator("text=送信")

# 避ける: クラス名やCSS
page.locator(".btn-primary")  # 変更される可能性
```

### 4. スクリーンショット
```python
# 意味のある名前を使用
page.screenshot(path=screenshot_path("dashboard_after_login"))

# フルページスクリーンショット
page.screenshot(path=screenshot_path("full_page"), full_page=True)
```

## 拡張方法

### 新しいテストケースの追加
1. `tests/e2e/`に新しいテストファイルを作成
2. `Test`で始まるクラスを定義
3. `test_`で始まるメソッドを追加
4. 必要なフィクスチャを使用

### 新しいページのテスト
```python
# tests/e2e/test_newpage.py
import pytest
from playwright.sync_api import Page, expect

class TestNewPage:
    @pytest.mark.smoke
    def test_new_feature(self, page: Page, screenshot_path):
        # ページに移動
        page.click("text=新機能")
        
        # 要素の確認
        expect(page.locator("[data-testid='new-feature']")).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("new_feature"))
```

## メンテナンス

### 定期的なタスク
- [ ] 週次: スクリーンショットの確認
- [ ] 月次: テストカバレッジの確認
- [ ] 四半期: Playwrightとブラウザのアップデート
- [ ] 年次: テストシナリオの見直し

---

最終更新: 2025年7月15日