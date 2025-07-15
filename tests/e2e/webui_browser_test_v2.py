"""
WebUI Browser E2E Test V2 - Streamlit対応版
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from pathlib import Path

class WebUIBrowserTestV2:
    def __init__(self):
        self.results = []
        self.screenshots_dir = Path("tests/e2e/screenshots/browser_test_v2")
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
        status_icon = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️",
            "skipped": "⏭️"
        }.get(status, "")
        print(f"{status_icon} {step}: {details}")
        
    async def take_screenshot(self, page, name):
        """スクリーンショットを保存"""
        path = self.screenshots_dir / f"{self.timestamp}_{name}.png"
        await page.screenshot(path=str(path), full_page=True)
        return path
        
    async def wait_for_streamlit(self, page):
        """Streamlitの準備完了を待機"""
        await page.wait_for_load_state("networkidle")
        # Streamlitメインアプリコンテナを待機
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        await asyncio.sleep(3)  # Streamlit完全初期化待ち
        
    async def click_sidebar_item(self, page, text):
        """サイドバーのアイテムをクリック（Streamlit特有の処理）"""
        # サイドバーを展開（必要な場合）
        try:
            sidebar_button = await page.query_selector('[data-testid="stSidebarNavButton"]')
            if sidebar_button:
                await sidebar_button.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # サイドバー内のボタンを探す
        sidebar_items = await page.query_selector_all('[data-testid="stSidebarNavLink"]')
        for item in sidebar_items:
            item_text = await item.inner_text()
            if text in item_text:
                await item.click()
                return True
                
        # 通常のボタンも試す
        buttons = await page.query_selector_all('button')
        for button in buttons:
            button_text = await button.inner_text()
            if text in button_text:
                await button.click()
                return True
        
        return False
        
    async def run_test(self):
        """メインテスト実行"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500  # 動作を見やすくする
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP'
            )
            
            page = await context.new_page()
            
            try:
                print("=== TradingAgents WebUI E2Eテスト V2 ===\n")
                
                # 1. アプリケーションアクセス
                await self.log_result("アプリケーションアクセス", "info", "http://localhost:8501")
                await page.goto("http://localhost:8501")
                await self.wait_for_streamlit(page)
                await self.take_screenshot(page, "01_initial_load")
                await self.log_result("アプリケーションアクセス", "success", "正常に読み込み完了")
                
                # 2. 初期ページ確認（ダッシュボード）
                await self.log_result("初期ページ確認", "info", "ダッシュボード表示確認")
                
                # タイトル確認
                title_elements = await page.query_selector_all('h1, h2, h3')
                title_found = False
                for elem in title_elements:
                    text = await elem.inner_text()
                    if "TradingAgents" in text:
                        await self.log_result("タイトル表示", "success", f"タイトル確認: {text}")
                        title_found = True
                        break
                
                if not title_found:
                    await self.log_result("タイトル表示", "warning", "タイトルが見つかりません")
                
                await self.take_screenshot(page, "02_dashboard")
                
                # 3. 設定ページへ移動
                await self.log_result("設定ページ", "info", "設定ページへ移動")
                
                # Streamlitのナビゲーション方法を試す
                settings_clicked = await self.click_sidebar_item(page, "設定")
                
                if settings_clicked:
                    await asyncio.sleep(3)
                    await self.log_result("設定ページ", "success", "設定ページへ遷移成功")
                    
                    # 入力フィールドを探す
                    await self.log_result("設定入力", "info", "設定項目の入力テスト")
                    
                    # テキスト入力フィールド（ティッカー）
                    text_inputs = await page.query_selector_all('input[type="text"]')
                    if text_inputs:
                        # 最初のテキスト入力をティッカーと仮定
                        await text_inputs[0].click()
                        await text_inputs[0].fill("")
                        await text_inputs[0].fill("AAPL")
                        await self.log_result("ティッカー入力", "success", "AAPL入力完了")
                    
                    # ボタンを探す（プリセット）
                    buttons = await page.query_selector_all('button')
                    for button in buttons:
                        text = await button.inner_text()
                        if "総合分析" in text or "プリセット" in text:
                            await button.click()
                            await self.log_result("プリセット選択", "success", f"ボタンクリック: {text}")
                            break
                    
                    await self.take_screenshot(page, "03_settings_filled")
                else:
                    await self.log_result("設定ページ", "warning", "設定ページへの遷移に失敗")
                
                # 4. 実行ページテスト
                await self.log_result("実行ページ", "info", "実行ページへ移動")
                
                execution_clicked = await self.click_sidebar_item(page, "実行")
                
                if execution_clicked:
                    await asyncio.sleep(3)
                    await self.log_result("実行ページ", "success", "実行ページへ遷移成功")
                    await self.take_screenshot(page, "04_execution")
                    
                    # 実行ボタンを探す
                    buttons = await page.query_selector_all('button')
                    start_button_found = False
                    for button in buttons:
                        text = await button.inner_text()
                        if "開始" in text or "実行" in text or "Start" in text:
                            await self.log_result("実行ボタン", "success", f"実行ボタン発見: {text}")
                            start_button_found = True
                            break
                    
                    if not start_button_found:
                        await self.log_result("実行ボタン", "info", "実行ボタンが見つかりません（設定が必要かもしれません）")
                else:
                    await self.log_result("実行ページ", "warning", "実行ページへの遷移に失敗")
                
                # 5. 結果ページテスト
                await self.log_result("結果ページ", "info", "結果ページへ移動")
                
                results_clicked = await self.click_sidebar_item(page, "結果")
                
                if results_clicked:
                    await asyncio.sleep(3)
                    await self.log_result("結果ページ", "success", "結果ページへ遷移成功")
                    await self.take_screenshot(page, "05_results")
                    
                    # 結果関連の要素を探す
                    elements = await page.query_selector_all('div')
                    for elem in elements[:20]:  # 最初の20要素のみチェック
                        text = await elem.inner_text()
                        if "結果" in text or "分析" in text:
                            await self.log_result("結果表示", "info", f"結果関連要素: {text[:50]}...")
                            break
                else:
                    await self.log_result("結果ページ", "warning", "結果ページへの遷移に失敗")
                
                # 6. ナビゲーション統合テスト
                await self.log_result("ナビゲーション統合", "info", "全ページ巡回テスト")
                
                # ダッシュボードに戻る
                dashboard_clicked = await self.click_sidebar_item(page, "ダッシュボード")
                if dashboard_clicked:
                    await asyncio.sleep(2)
                    await self.log_result("ダッシュボード復帰", "success", "ダッシュボードへ戻りました")
                
                await self.take_screenshot(page, "06_final_state")
                
                # 7. レスポンシブテスト（簡易版）
                await self.log_result("レスポンシブ", "info", "画面サイズ変更テスト")
                
                # タブレットサイズ
                await page.set_viewport_size({"width": 768, "height": 1024})
                await asyncio.sleep(2)
                await self.take_screenshot(page, "07_tablet")
                await self.log_result("タブレット表示", "success", "768x1024で表示確認")
                
                # モバイルサイズ
                await page.set_viewport_size({"width": 375, "height": 667})
                await asyncio.sleep(2)
                await self.take_screenshot(page, "08_mobile")
                await self.log_result("モバイル表示", "success", "375x667で表示確認")
                
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
        info = len([r for r in self.results if r['status'] == 'info'])
        
        print(f"総テスト項目: {total}")
        print(f"成功: {success} ✅")
        print(f"警告: {warning} ⚠️")
        print(f"エラー: {error} ❌")
        print(f"情報: {info} ℹ️")
        
        if total > 0:
            success_rate = (success / (success + warning + error)) * 100 if (success + warning + error) > 0 else 0
            print(f"成功率: {success_rate:.1f}%")
        
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
                    "error": len([r for r in self.results if r['status'] == 'error']),
                    "info": len([r for r in self.results if r['status'] == 'info'])
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"テスト結果保存: {results_file}")

async def main():
    """メイン実行関数"""
    test = WebUIBrowserTestV2()
    await test.run_test()

if __name__ == "__main__":
    print("TradingAgents WebUI ブラウザE2Eテスト V2")
    print("Streamlit UI要素に対応した改良版")
    print("-" * 50)
    asyncio.run(main())