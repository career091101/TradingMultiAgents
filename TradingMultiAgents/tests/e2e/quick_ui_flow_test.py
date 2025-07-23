#!/usr/bin/env python3
"""
UIフロー確認テスト（分析実行なし）
設定→実行画面→結果画面の遷移のみ確認
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from pathlib import Path

async def test_ui_flow():
    """UIフローのみをテスト（実際の分析は実行しない）"""
    
    test_dir = Path("tests/e2e/ui_flow_test_results")
    test_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=== WebUI UIフローテスト ===")
    print("※ 実際の分析は実行せず、画面遷移のみ確認\n")
    
    results = {
        "timestamp": timestamp,
        "steps": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # ヘッドレスモードで高速実行
            args=['--disable-gpu']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # 1. アプリケーションアクセス
            print("1. WebUIアクセス中...")
            await page.goto("http://localhost:8501")
            await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
            await asyncio.sleep(2)
            
            results["steps"].append({
                "step": "WebUIアクセス",
                "status": "success",
                "time": datetime.now().isoformat()
            })
            print("   ✅ 成功\n")
            
            # 2. 設定ページ
            print("2. 設定ページへ移動...")
            settings_found = False
            buttons = await page.query_selector_all('button')
            for button in buttons:
                text = await button.inner_text()
                if "設定" in text:
                    await button.click()
                    settings_found = True
                    break
            
            if settings_found:
                await asyncio.sleep(2)
                
                # 設定入力
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    await text_inputs[0].fill("SPY")
                    print("   - ティッカー: SPY")
                
                # 研究深度を最小に設定
                sliders = await page.query_selector_all('input[type="range"]')
                if sliders:
                    await sliders[0].fill("1")
                    print("   - 研究深度: 1（最小）")
                
                await page.screenshot(path=str(test_dir / f"{timestamp}_settings.png"))
                
                results["steps"].append({
                    "step": "設定入力",
                    "status": "success",
                    "ticker": "SPY",
                    "depth": 1,
                    "time": datetime.now().isoformat()
                })
                print("   ✅ 成功\n")
            
            # 3. 実行ページ
            print("3. 実行ページへ移動...")
            exec_found = False
            buttons = await page.query_selector_all('button')
            for button in buttons:
                text = await button.inner_text()
                if "実行" in text:
                    await button.click()
                    exec_found = True
                    break
            
            if exec_found:
                await asyncio.sleep(2)
                
                # 実行ボタンの存在確認
                exec_button_found = False
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "分析" in text and ("実行" in text or "開始" in text):
                        exec_button_found = True
                        print(f"   - 実行ボタン確認: '{text}'")
                        break
                
                await page.screenshot(path=str(test_dir / f"{timestamp}_execution.png"))
                
                results["steps"].append({
                    "step": "実行ページ",
                    "status": "success",
                    "exec_button_found": exec_button_found,
                    "time": datetime.now().isoformat()
                })
                print("   ✅ 成功\n")
            
            # 4. 結果ページ
            print("4. 結果ページへ移動...")
            results_found = False
            buttons = await page.query_selector_all('button')
            for button in buttons:
                text = await button.inner_text()
                if "結果" in text:
                    await button.click()
                    results_found = True
                    break
            
            if results_found:
                await asyncio.sleep(2)
                await page.screenshot(path=str(test_dir / f"{timestamp}_results.png"))
                
                results["steps"].append({
                    "step": "結果ページ",
                    "status": "success",
                    "time": datetime.now().isoformat()
                })
                print("   ✅ 成功\n")
            
            # 全体の成功判定
            all_success = all(step["status"] == "success" for step in results["steps"])
            results["overall_status"] = "success" if all_success else "partial"
            
        except Exception as e:
            print(f"\n❌ エラー: {str(e)}")
            results["error"] = str(e)
            results["overall_status"] = "failed"
            
        finally:
            await context.close()
            await browser.close()
    
    # 結果保存
    results_file = test_dir / f"ui_flow_test_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # サマリー表示
    print("\n" + "="*50)
    print("UIフローテスト完了")
    print("="*50)
    print(f"総ステップ数: {len(results['steps'])}")
    print(f"成功: {sum(1 for s in results['steps'] if s['status'] == 'success')}")
    print(f"全体ステータス: {results.get('overall_status', 'unknown')}")
    print(f"\n結果保存先: {results_file}")
    print(f"スクリーンショット: {test_dir}")
    
    return results

if __name__ == "__main__":
    # WebUI起動確認
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認\n")
    except:
        print("❌ WebUIが起動していません")
        print("'python run_webui.py' でWebUIを起動してください")
        exit(1)
    
    # テスト実行
    asyncio.run(test_ui_flow())