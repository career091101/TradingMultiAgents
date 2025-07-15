#!/usr/bin/env python3
"""
デモ用分析フローテスト
実際のAPI呼び出しを行わないモックモードで動作確認
"""
import asyncio
from datetime import datetime
from pathlib import Path
import json
from playwright.async_api import async_playwright

class DemoAnalysisTest:
    def __init__(self):
        self.test_dir = Path("tests/e2e/demo_results")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def run_demo(self):
        """デモテストを実行（UIナビゲーションのみ）"""
        print("=== TradingAgents WebUI デモテスト ===")
        print("※ 実際の分析は実行せず、UIフローのみ確認します")
        print("-" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000  # デモ用にゆっくり動作
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. アプリケーションアクセス
                print("\n1. WebUIにアクセス...")
                await page.goto("http://localhost:8501")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
                await asyncio.sleep(2)
                print("✅ アクセス成功")
                
                # 2. 設定ページへ移動
                print("\n2. 設定ページへ移動...")
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "設定" in text:
                        await button.click()
                        break
                await asyncio.sleep(2)
                print("✅ 設定ページ表示")
                
                # 3. 設定入力
                print("\n3. 分析設定を入力...")
                
                # ティッカー入力
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    await text_inputs[0].fill("SPY")
                    print("  - ティッカー: SPY")
                
                # 総合分析プリセット
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "総合分析" in text:
                        await button.click()
                        print("  - プリセット: 総合分析")
                        break
                
                # 研究深度（デモは1に設定）
                sliders = await page.query_selector_all('input[type="range"]')
                if sliders:
                    await sliders[0].fill("1")
                    print("  - 研究深度: 1")
                
                await asyncio.sleep(2)
                
                # スクリーンショット
                await page.screenshot(
                    path=str(self.test_dir / f"demo_{self.timestamp}_settings.png")
                )
                print("✅ 設定完了")
                
                # 4. 実行ページへ移動
                print("\n4. 実行ページへ移動...")
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "実行" in text:
                        await button.click()
                        break
                await asyncio.sleep(2)
                
                # 実行画面のスクリーンショット
                await page.screenshot(
                    path=str(self.test_dir / f"demo_{self.timestamp}_execution.png")
                )
                print("✅ 実行ページ表示")
                
                # 5. 実行ボタンの確認（実際には押さない）
                print("\n5. 実行ボタンを確認...")
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "分析" in text and ("実行" in text or "開始" in text):
                        print(f"✅ 実行ボタン発見: '{text}'")
                        print("  （デモモードのため実行はスキップ）")
                        break
                
                # 6. 結果ページへ移動
                print("\n6. 結果ページへ移動...")
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "結果" in text:
                        await button.click()
                        break
                await asyncio.sleep(2)
                
                # 結果画面のスクリーンショット
                await page.screenshot(
                    path=str(self.test_dir / f"demo_{self.timestamp}_results.png")
                )
                print("✅ 結果ページ表示")
                
                # 7. ナビゲーション完了
                print("\n7. UIフロー確認完了")
                print("✅ 全ページへのナビゲーション成功")
                
            except Exception as e:
                print(f"\n❌ エラー発生: {str(e)}")
                await page.screenshot(
                    path=str(self.test_dir / f"demo_{self.timestamp}_error.png")
                )
            
            finally:
                # ブラウザを開いたまま少し待機
                print("\n10秒後にブラウザを閉じます...")
                await asyncio.sleep(10)
                await context.close()
                await browser.close()
        
        # 結果サマリー
        print("\n" + "="*60)
        print("デモテスト完了")
        print("="*60)
        print(f"スクリーンショット保存先: {self.test_dir}")
        print("\n実際の分析実行テストを行う場合は、以下を実行してください:")
        print("  ./tests/e2e/run_analysis_flow_test.sh quick")

async def main():
    demo = DemoAnalysisTest()
    await demo.run_demo()

if __name__ == "__main__":
    print("TradingAgents WebUI デモテスト")
    print("前提: WebUIが http://localhost:8501 で起動中")
    print("-" * 60)
    
    # WebUI起動確認
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認")
    except:
        print("❌ WebUIが起動していません")
        exit(1)
    
    asyncio.run(main())