#!/usr/bin/env python3
"""
完全分析フローE2Eテスト
実際のAPI呼び出しを含む深度1のテスト
"""
import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
import json
from playwright.async_api import async_playwright, Page
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

class FullAnalysisFlowTest:
    def __init__(self):
        self.test_dir = Path("tests/e2e/full_analysis_results")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []
        
    async def log_event(self, event_type: str, message: str, details: dict = None):
        """イベントログ記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "details": details or {}
        }
        self.results.append(log_entry)
        
        # アイコン定義
        icons = {
            "start": "🚀", "progress": "⏳", "complete": "✅",
            "error": "❌", "info": "ℹ️", "warning": "⚠️"
        }
        icon = icons.get(event_type, "")
        print(f"{icon} [{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    async def wait_for_streamlit(self, page: Page):
        """Streamlit準備待機"""
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        await asyncio.sleep(3)
        
    async def run_full_flow_test(self):
        """完全な分析フローテストを実行"""
        print("=== TradingAgents WebUI 完全分析フローE2Eテスト ===")
        print("テスト内容: 深度1での実際の分析実行")
        print("予想時間: 約10-15分")
        print("-" * 60)
        
        test_result = {
            "test_id": f"full_flow_{self.timestamp}",
            "start_time": datetime.now().isoformat(),
            "ticker": "SPY",
            "depth": 1,
            "status": "running"
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 実行状況を確認できるよう可視化
                slow_mo=500
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP'
            )
            
            page = await context.new_page()
            
            try:
                # 1. アプリケーションアクセス
                await self.log_event("start", "WebUIアクセス開始")
                await page.goto("http://localhost:8501")
                await self.wait_for_streamlit(page)
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_01_initial.png"))
                await self.log_event("info", "WebUIアクセス成功")
                
                # 2. 設定ページで分析設定
                await self.log_event("info", "設定ページへ移動")
                settings_button = await page.wait_for_selector('button:has-text("設定")')
                await settings_button.click()
                await asyncio.sleep(2)
                
                # ティッカー設定
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    await text_inputs[0].fill("SPY")
                    await self.log_event("info", "ティッカー設定: SPY")
                
                # 総合分析プリセット
                preset_buttons = await page.query_selector_all('button')
                for button in preset_buttons:
                    text = await button.inner_text()
                    if "総合分析" in text:
                        await button.click()
                        await self.log_event("info", "総合分析プリセット選択")
                        break
                
                # 研究深度設定（深度1）
                sliders = await page.query_selector_all('input[type="range"]')
                if sliders:
                    await sliders[0].fill("1")
                    await self.log_event("info", "研究深度設定: 1")
                
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_02_settings.png"))
                
                # 3. 実行ページへ移動して分析開始
                await self.log_event("info", "実行ページへ移動")
                exec_button = await page.wait_for_selector('button:has-text("実行")')
                await exec_button.click()
                await asyncio.sleep(2)
                
                # 分析実行ボタンをクリック
                await self.log_event("start", "分析実行開始")
                start_buttons = await page.query_selector_all('button')
                for button in start_buttons:
                    text = await button.inner_text()
                    if "分析" in text and ("実行" in text or "開始" in text):
                        await button.click()
                        analysis_start_time = time.time()
                        test_result["analysis_start_time"] = datetime.now().isoformat()
                        break
                
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_03_execution_started.png"))
                
                # 4. 進捗モニタリング
                await self.log_event("info", "進捗モニタリング開始")
                max_wait_time = 15 * 60  # 最大15分
                check_interval = 10  # 10秒間隔
                elapsed_time = 0
                last_progress = 0
                
                while elapsed_time < max_wait_time:
                    # 進捗確認
                    progress_elements = await page.query_selector_all('[role="progressbar"]')
                    current_progress = 0
                    
                    if progress_elements:
                        for elem in progress_elements:
                            try:
                                value = await elem.get_attribute("aria-valuenow")
                                if value:
                                    current_progress = float(value)
                                    break
                            except:
                                pass
                    
                    # 進捗更新時のみログ出力
                    if current_progress != last_progress:
                        await self.log_event("progress", 
                            f"進捗: {current_progress:.0f}% (経過: {elapsed_time//60:.0f}分{elapsed_time%60:.0f}秒)")
                        last_progress = current_progress
                    
                    # 完了確認
                    if current_progress >= 100:
                        await self.log_event("complete", "分析完了！")
                        test_result["analysis_duration"] = time.time() - analysis_start_time
                        break
                    
                    # エラーチェック
                    error_alerts = await page.query_selector_all('[role="alert"]')
                    for alert in error_alerts:
                        alert_text = await alert.inner_text()
                        if "error" in alert_text.lower():
                            await self.log_event("error", f"エラー検出: {alert_text}")
                            test_result["error"] = alert_text
                            raise Exception(f"分析エラー: {alert_text}")
                    
                    # 完了メッセージチェック
                    completion_msgs = await page.query_selector_all('div')
                    for msg in completion_msgs[:50]:  # 最初の50要素のみチェック
                        text = await msg.inner_text()
                        if "完了" in text and "分析" in text:
                            await self.log_event("complete", "分析完了メッセージ確認")
                            current_progress = 100
                            break
                    
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                
                # タイムアウトチェック
                if elapsed_time >= max_wait_time:
                    await self.log_event("error", "タイムアウト")
                    test_result["status"] = "timeout"
                else:
                    await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_04_analysis_complete.png"))
                    
                    # 5. 結果ページへ移動
                    await self.log_event("info", "結果ページへ移動")
                    
                    # 自動遷移を待つか、手動で移動
                    await asyncio.sleep(3)
                    
                    # 結果ボタンをクリック
                    results_button = await page.wait_for_selector('button:has-text("結果")')
                    await results_button.click()
                    await asyncio.sleep(3)
                    
                    # 6. 結果検証
                    await self.log_event("info", "結果検証開始")
                    
                    # 結果が表示されているか確認
                    result_found = False
                    elements = await page.query_selector_all('div')
                    for elem in elements[:100]:
                        text = await elem.inner_text()
                        if "SPY" in text and ("結果" in text or "レポート" in text):
                            result_found = True
                            break
                    
                    if result_found:
                        await self.log_event("complete", "分析結果確認")
                        
                        # タブ確認
                        tabs = await page.query_selector_all('[role="tab"]')
                        available_reports = []
                        for tab in tabs:
                            tab_text = await tab.inner_text()
                            available_reports.append(tab_text)
                            
                        await self.log_event("info", f"利用可能なレポート: {len(available_reports)}個")
                        test_result["available_reports"] = available_reports
                        
                        # サマリータブをクリック
                        for tab in tabs:
                            text = await tab.inner_text()
                            if "サマリー" in text:
                                await tab.click()
                                await asyncio.sleep(2)
                                break
                        
                        await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_05_results_summary.png"))
                        test_result["status"] = "success"
                    else:
                        await self.log_event("warning", "結果が見つかりません")
                        test_result["status"] = "no_results"
                        
            except Exception as e:
                await self.log_event("error", f"テストエラー: {str(e)}")
                test_result["status"] = "error"
                test_result["error_details"] = str(e)
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_error.png"))
                
            finally:
                test_result["end_time"] = datetime.now().isoformat()
                
                # ブラウザを少し開いたままにする
                await self.log_event("info", "5秒後にブラウザを閉じます...")
                await asyncio.sleep(5)
                
                await context.close()
                await browser.close()
        
        # 結果保存
        results_file = self.test_dir / f"test_result_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_result": test_result,
                "event_log": self.results
            }, f, ensure_ascii=False, indent=2)
        
        # サマリー表示
        print("\n" + "="*60)
        print("テスト完了")
        print("="*60)
        print(f"ステータス: {test_result['status']}")
        if test_result.get('analysis_duration'):
            duration = test_result['analysis_duration']
            print(f"分析時間: {duration//60:.0f}分{duration%60:.0f}秒")
        print(f"結果保存: {results_file}")
        print(f"スクリーンショット: {self.test_dir}")
        
        return test_result

async def main():
    # 環境変数確認
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("FINNHUB_API_KEY"):
        print("❌ 環境変数が設定されていません")
        print(".envファイルを確認してください")
        return
        
    # WebUI起動確認
    import requests
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認")
    except:
        print("❌ WebUIが起動していません")
        return
    
    # テスト実行
    test = FullAnalysisFlowTest()
    await test.run_full_flow_test()

if __name__ == "__main__":
    asyncio.run(main())