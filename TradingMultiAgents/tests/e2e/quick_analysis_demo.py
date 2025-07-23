#!/usr/bin/env python3
"""
クイック分析デモ - 短時間で画面遷移を確認
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

async def quick_demo():
    """短時間で分析開始までの流れを確認"""
    
    test_dir = Path("tests/e2e/quick_demo_results")
    test_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=== TradingAgents クイック分析デモ ===")
    print("分析開始後、1分間だけ待機して画面状態を確認します")
    print("-" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000  # ゆっくり動作
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # 1. WebUIアクセス
            print("\n1. WebUIアクセス...")
            await page.goto("http://localhost:8501")
            await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 設定
            print("2. 設定入力...")
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
                text = await button.inner_text()
                if "総合分析" in text:
                    await button.click()
                    break
            
            # 深度1
            sliders = await page.query_selector_all('input[type="range"]')
            if sliders:
                await sliders[0].fill("1")
            
            await page.screenshot(path=str(test_dir / f"{timestamp}_settings.png"))
            
            # 3. 実行画面へ
            print("3. 実行画面へ移動...")
            exec_btn = await page.wait_for_selector('button:has-text("実行")')
            await exec_btn.click()
            await asyncio.sleep(2)
            
            # 4. 分析開始
            print("4. 分析開始...")
            buttons = await page.query_selector_all('button')
            analysis_started = False
            for button in buttons:
                text = await button.inner_text()
                if "分析" in text and ("実行" in text or "開始" in text):
                    print(f"   実行ボタン: '{text}'")
                    await button.click()
                    analysis_started = True
                    break
            
            if analysis_started:
                await page.screenshot(path=str(test_dir / f"{timestamp}_started.png"))
                
                # 5. 1分間待機して画面状態を確認
                print("\n5. 分析実行中の画面を確認（1分間）...")
                
                for i in range(6):  # 10秒×6回=1分
                    await asyncio.sleep(10)
                    
                    # 画面の状態を確認
                    print(f"\n[{i*10+10}秒経過]")
                    
                    # エラーチェック
                    alerts = await page.query_selector_all('[role="alert"]')
                    if alerts:
                        for alert in alerts:
                            alert_text = await alert.inner_text()
                            print(f"   アラート: {alert_text}")
                    
                    # 進捗要素を探す
                    progress_found = False
                    
                    # プログレスバー
                    progress_bars = await page.query_selector_all('[role="progressbar"]')
                    if progress_bars:
                        print("   ✅ プログレスバー発見")
                        progress_found = True
                    
                    # Streamlitのスピナー
                    spinners = await page.query_selector_all('[data-testid="stSpinner"]')
                    if spinners:
                        print("   ✅ スピナー発見")
                        progress_found = True
                    
                    # メッセージ表示を確認
                    divs = await page.query_selector_all('div')
                    for div in divs[:30]:
                        text = await div.inner_text()
                        if "実行中" in text or "処理中" in text or "分析中" in text:
                            print(f"   メッセージ: {text[:50]}...")
                            break
                    
                    if not progress_found and i == 0:
                        print("   ⚠️ 進捗表示要素が見つかりません")
                    
                    # スクリーンショット
                    await page.screenshot(
                        path=str(test_dir / f"{timestamp}_progress_{i*10+10}s.png")
                    )
                
                print("\n6. 最終状態確認...")
                
                # 結果ページへの自動遷移を確認
                current_url = page.url
                print(f"   現在のURL: {current_url}")
                
                # 手動で結果ページへ
                results_btn = await page.wait_for_selector('button:has-text("結果")')
                await results_btn.click()
                await asyncio.sleep(2)
                
                await page.screenshot(path=str(test_dir / f"{timestamp}_results_check.png"))
                
            else:
                print("   ❌ 実行ボタンが見つかりません")
                
        except Exception as e:
            print(f"\n❌ エラー: {str(e)}")
            await page.screenshot(path=str(test_dir / f"{timestamp}_error.png"))
            
        finally:
            print("\n7. ブラウザを10秒後に閉じます...")
            await asyncio.sleep(10)
            await context.close()
            await browser.close()
    
    print("\n" + "="*60)
    print("デモ完了")
    print(f"スクリーンショット: {test_dir}")
    print("="*60)

if __name__ == "__main__":
    # 環境変数確認
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("FINNHUB_API_KEY"):
        print("⚠️ 環境変数が設定されていません")
        print("デモモードで実行します（実際の分析は行われない可能性があります）")
    
    asyncio.run(quick_demo())