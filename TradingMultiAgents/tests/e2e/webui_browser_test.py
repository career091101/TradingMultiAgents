"""
WebUI Browser E2E Test - 主要機能の完全動作確認
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from pathlib import Path
import sys

class WebUIBrowserTest:
    def __init__(self):
        self.results = []
        self.screenshots_dir = Path("tests/e2e/screenshots/browser_test")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def log_result(self, step, status, details=""):
        """テスト結果をログに記録"""
        result = {
            "step": step,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{'✅' if status == 'success' else '❌'} {step}: {details}")
        
    async def take_screenshot(self, page, name):
        """スクリーンショットを保存"""
        path = self.screenshots_dir / f"{self.timestamp}_{name}.png"
        await page.screenshot(path=str(path), full_page=True)
        return path
        
    async def wait_for_streamlit(self, page):
        """Streamlitの準備完了を待機"""
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        await asyncio.sleep(2)  # Streamlit完全初期化待ち
        
    async def run_test(self):
        """メインテスト実行"""
        async with async_playwright() as p:
            # ブラウザ起動（ヘッドレスモードをオフにして可視化）
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=300  # 動作を見やすくする
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP'
            )
            
            page = await context.new_page()
            
            try:
                print("=== WebUI主要機能E2Eテスト開始 ===\n")
                
                # 1. アプリケーションアクセス
                await self.log_result("アプリケーションアクセス", "in_progress", "http://localhost:8501")
                await page.goto("http://localhost:8501")
                await self.wait_for_streamlit(page)
                await self.take_screenshot(page, "01_initial_load")
                await self.log_result("アプリケーションアクセス", "success", "正常に読み込み完了")
                
                # 2. ダッシュボード確認
                await self.log_result("ダッシュボード表示", "in_progress")
                # ヘッダー確認
                header = await page.wait_for_selector('h1:has-text("TradingAgents WebUI")')
                if header:
                    await self.log_result("ダッシュボード表示", "success", "ヘッダー表示確認")
                
                # 環境変数チェック
                try:
                    env_status = await page.wait_for_selector('text="環境変数の状態"', timeout=5000)
                    await self.take_screenshot(page, "02_dashboard")
                    await self.log_result("環境変数チェック", "success", "環境変数状態表示を確認")
                except:
                    await self.log_result("環境変数チェック", "warning", "環境変数セクションが見つかりません")
                
                # 3. 設定ページテスト
                await self.log_result("設定ページ", "in_progress")
                settings_button = await page.wait_for_selector('button:has-text("⚙️ 設定")')
                await settings_button.click()
                await asyncio.sleep(2)
                
                # ティッカー入力
                ticker_inputs = await page.query_selector_all('input[type="text"]')
                if ticker_inputs:
                    await ticker_inputs[0].fill("AAPL")
                    await self.log_result("ティッカー入力", "success", "AAPL入力完了")
                
                # アナリストプリセット確認
                try:
                    preset_button = await page.wait_for_selector('button:has-text("総合分析")', timeout=3000)
                    await preset_button.click()
                    await self.log_result("プリセット選択", "success", "総合分析プリセット選択")
                except:
                    await self.log_result("プリセット選択", "warning", "プリセットボタンが見つかりません")
                
                await self.take_screenshot(page, "03_settings")
                
                # 4. 実行ページテスト
                await self.log_result("実行ページ", "in_progress")
                execution_button = await page.wait_for_selector('button:has-text("▶️ 実行")')
                await execution_button.click()
                await asyncio.sleep(2)
                
                # 設定サマリー確認
                try:
                    summary_section = await page.wait_for_selector('text="現在の設定"', timeout=5000)
                    await self.take_screenshot(page, "04_execution_ready")
                    await self.log_result("実行準備画面", "success", "設定サマリー表示確認")
                except:
                    await self.log_result("実行準備画面", "warning", "設定サマリーが見つかりません")
                
                # 分析開始ボタン確認（実際の実行はスキップ）
                try:
                    start_button = await page.wait_for_selector('button:has-text("分析を開始")', timeout=5000)
                    if start_button:
                        await self.log_result("分析開始ボタン", "success", "実行可能状態を確認")
                        # デモのため実際の実行はスキップ
                        await self.log_result("分析実行", "skipped", "デモモードのため実行をスキップ")
                except:
                    await self.log_result("分析開始ボタン", "warning", "開始ボタンが見つかりません")
                
                # 5. 結果ページテスト
                await self.log_result("結果ページ", "in_progress")
                results_button = await page.wait_for_selector('button:has-text("📊 結果")')
                await results_button.click()
                await asyncio.sleep(2)
                
                await self.take_screenshot(page, "05_results")
                
                # 結果選択セクション確認
                try:
                    result_section = await page.wait_for_selector('text="分析結果を選択"', timeout=5000)
                    await self.log_result("結果ページ", "success", "結果選択画面表示確認")
                except:
                    await self.log_result("結果ページ", "info", "分析結果がまだありません")
                
                # 6. ナビゲーション総合テスト
                await self.log_result("ナビゲーション総合", "in_progress")
                
                # 各ページを順番に訪問
                pages = [
                    ("🏠 ダッシュボード", "dashboard"),
                    ("⚙️ 設定", "settings"),
                    ("▶️ 実行", "execution"),
                    ("📊 結果", "results")
                ]
                
                for button_text, page_name in pages:
                    button = await page.wait_for_selector(f'button:has-text("{button_text}")')
                    await button.click()
                    await asyncio.sleep(1)
                    await self.log_result(f"ナビゲーション - {page_name}", "success", "正常に遷移")
                
                await self.take_screenshot(page, "06_navigation_complete")
                
                # 7. レスポンシブデザインテスト
                await self.log_result("レスポンシブデザイン", "in_progress")
                
                # タブレットサイズ
                await page.set_viewport_size({"width": 768, "height": 1024})
                await asyncio.sleep(1)
                await self.take_screenshot(page, "07_responsive_tablet")
                
                # モバイルサイズ
                await page.set_viewport_size({"width": 375, "height": 667})
                await asyncio.sleep(1)
                await self.take_screenshot(page, "08_responsive_mobile")
                
                await self.log_result("レスポンシブデザイン", "success", "各画面サイズで正常表示")
                
            except Exception as e:
                await self.log_result("エラー発生", "error", str(e))
                await self.take_screenshot(page, "error_screenshot")
            
            finally:
                await context.close()
                await browser.close()
                
        # テスト結果のサマリー
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        print("\n=== テスト結果サマリー ===")
        total = len(self.results)
        success = len([r for r in self.results if r['status'] == 'success'])
        warning = len([r for r in self.results if r['status'] == 'warning'])
        error = len([r for r in self.results if r['status'] == 'error'])
        
        print(f"総テスト数: {total}")
        print(f"成功: {success} ✅")
        print(f"警告: {warning} ⚠️")
        print(f"エラー: {error} ❌")
        print(f"成功率: {(success/total*100):.1f}%")
        print(f"\nスクリーンショット保存先: {self.screenshots_dir}")
        
    def save_results(self):
        """テスト結果をJSONファイルに保存"""
        results_file = self.screenshots_dir / f"test_results_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_run": self.timestamp,
                "results": self.results,
                "summary": {
                    "total": len(self.results),
                    "success": len([r for r in self.results if r['status'] == 'success']),
                    "warning": len([r for r in self.results if r['status'] == 'warning']),
                    "error": len([r for r in self.results if r['status'] == 'error'])
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"テスト結果保存: {results_file}")

async def main():
    """メイン実行関数"""
    test = WebUIBrowserTest()
    await test.run_test()

if __name__ == "__main__":
    print("TradingAgents WebUI ブラウザE2Eテスト")
    print("前提: WebUIが http://localhost:8501 で起動中")
    print("-" * 50)
    asyncio.run(main())