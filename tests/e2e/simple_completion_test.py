#!/usr/bin/env python3
"""
シンプルな完了確認E2Eテスト
実行画面の状態変化を監視して完了を確認
"""
import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class SimpleCompletionTest:
    def __init__(self):
        self.test_dir = Path("tests/e2e/simple_completion_results")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def run_test(self):
        """シンプルな完了確認テスト"""
        print("=== シンプル完了確認E2Eテスト ===")
        print("実行画面の状態変化を監視")
        print("-" * 60)
        
        results = {
            "test_id": f"simple_{self.timestamp}",
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "screenshots": []
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=300,
                args=['--window-size=1600,1200']
            )
            
            context = await browser.new_context(
                viewport={'width': 1536, 'height': 1024}
            )
            
            page = await context.new_page()
            
            try:
                # 1. セットアップと分析開始
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WebUIアクセス")
                await page.goto("http://localhost:8501")
                await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
                await asyncio.sleep(3)
                
                # 設定
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 設定入力")
                settings_btn = await page.wait_for_selector('button:has-text("設定")')
                await settings_btn.click()
                await asyncio.sleep(2)
                
                # SPY設定
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    await text_inputs[0].fill("SPY")
                
                # 総合分析
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    if "総合分析" in await button.inner_text():
                        await button.click()
                        break
                
                # 深度1
                sliders = await page.query_selector_all('input[type="range"]')
                if sliders:
                    await sliders[0].fill("1")
                
                # 実行ページへ
                exec_btn = await page.wait_for_selector('button:has-text("実行")')
                await exec_btn.click()
                await asyncio.sleep(2)
                
                # 分析開始
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 分析開始")
                start_buttons = await page.query_selector_all('button')
                for button in start_buttons:
                    text = await button.inner_text()
                    if "分析" in text and ("実行" in text or "開始" in text):
                        await button.click()
                        start_time = time.time()
                        results["analysis_start"] = datetime.now().isoformat()
                        break
                
                await asyncio.sleep(5)
                
                # 2. 実行画面の監視（最大10分）
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 実行画面監視開始")
                
                check_count = 0
                max_checks = 60  # 10秒×60回=10分
                completed = False
                
                while check_count < max_checks:
                    check_count += 1
                    current_time = datetime.now().strftime('%H:%M:%S')
                    
                    # 画面の全テキストを取得
                    page_text = await page.inner_text('body')
                    
                    # 完了を示すキーワードチェック
                    completion_keywords = [
                        "分析が完了しました",
                        "Analysis completed",
                        "完了",
                        "処理が終了しました",
                        "結果が生成されました"
                    ]
                    
                    for keyword in completion_keywords:
                        if keyword in page_text:
                            print(f"[{current_time}] ✅ 完了キーワード検出: {keyword}")
                            completed = True
                            break
                    
                    # 進捗情報を探す
                    if "%" in page_text:
                        lines = page_text.split('\n')
                        for line in lines:
                            if "%" in line and len(line) < 100:
                                print(f"[{current_time}] 📊 {line.strip()}")
                    
                    # エラーチェック
                    if "error" in page_text.lower() or "エラー" in page_text:
                        print(f"[{current_time}] ❌ エラー検出")
                        results["error"] = "Error detected in page"
                        break
                    
                    # スクリーンショット（30秒ごと）
                    if check_count % 3 == 0:
                        screenshot_path = str(self.test_dir / f"{self.timestamp}_check_{check_count}.png")
                        await page.screenshot(path=screenshot_path, full_page=True)
                        results["screenshots"].append(screenshot_path)
                        print(f"[{current_time}] 📸 スクリーンショット保存")
                    
                    if completed:
                        break
                    
                    # 結果ページへの自動遷移チェック
                    current_url = page.url
                    if "results" in current_url or "結果" in current_url:
                        print(f"[{current_time}] 📊 結果ページへ自動遷移")
                        completed = True
                        break
                    
                    await asyncio.sleep(10)
                
                # 3. 結果確認
                if completed:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 分析完了確認")
                    results["status"] = "completed"
                    results["duration"] = time.time() - start_time
                    
                    # 結果ページへ移動（まだ移動していない場合）
                    if "results" not in page.url:
                        results_btn = await page.wait_for_selector('button:has-text("結果")')
                        await results_btn.click()
                        await asyncio.sleep(3)
                    
                    # 最終スクリーンショット
                    final_screenshot = str(self.test_dir / f"{self.timestamp}_final.png")
                    await page.screenshot(path=final_screenshot, full_page=True)
                    results["screenshots"].append(final_screenshot)
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ テスト成功")
                else:
                    results["status"] = "timeout"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️ タイムアウト")
                    
            except Exception as e:
                results["status"] = "error"
                results["error_details"] = str(e)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ エラー: {str(e)}")
                
            finally:
                results["end_time"] = datetime.now().isoformat()
                await asyncio.sleep(5)
                await context.close()
                await browser.close()
        
        # 結果保存
        results_file = self.test_dir / f"test_result_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # サマリー
        print("\n" + "="*60)
        print("テスト結果")
        print("="*60)
        print(f"ステータス: {results['status']}")
        if results.get('duration'):
            print(f"実行時間: {results['duration']:.0f}秒")
        print(f"スクリーンショット数: {len(results['screenshots'])}")
        print(f"結果: {results_file}")
        
        return results

async def main():
    # WebUI確認
    import requests
    try:
        requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認\n")
    except:
        print("❌ WebUIが起動していません")
        return
    
    test = SimpleCompletionTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())