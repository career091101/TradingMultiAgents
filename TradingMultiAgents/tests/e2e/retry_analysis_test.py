#!/usr/bin/env python3
"""
分析フローE2Eテスト再実行版
ディスク容量確認とエラーハンドリング改善
"""
import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

class RetryAnalysisTest:
    def __init__(self):
        self.test_dir = Path("tests/e2e/retry_test_results")
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
        
        icons = {
            "start": "🚀", "progress": "⏳", "complete": "✅",
            "error": "❌", "info": "ℹ️", "warning": "⚠️"
        }
        icon = icons.get(event_type, "")
        print(f"{icon} [{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    async def check_disk_space(self):
        """ディスク容量チェック"""
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        used_percent = (stat.used / stat.total) * 100
        
        await self.log_event("info", 
            f"ディスク容量: {free_gb:.1f}GB空き / {total_gb:.0f}GB総容量 (使用率: {used_percent:.0f}%)")
        
        if free_gb < 1:
            await self.log_event("error", "ディスク容量不足！最低1GB必要です")
            return False
        return True
        
    async def run_test(self):
        """メインテスト実行"""
        print("=== TradingAgents 分析フローE2Eテスト（再実行版） ===")
        print("深度1での分析実行テスト")
        print("-" * 60)
        
        # ディスク容量チェック
        if not await self.check_disk_space():
            return {"status": "failed", "error": "Insufficient disk space"}
        
        test_result = {
            "test_id": f"retry_{self.timestamp}",
            "start_time": datetime.now().isoformat(),
            "ticker": "SPY",
            "depth": 1,
            "status": "running"
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=300
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. WebUIアクセス
                await self.log_event("start", "WebUIアクセス")
                await page.goto("http://localhost:8501")
                await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
                await asyncio.sleep(3)
                
                # 2. 設定
                await self.log_event("info", "設定ページで分析設定")
                settings_btn = await page.wait_for_selector('button:has-text("設定")')
                await settings_btn.click()
                await asyncio.sleep(2)
                
                # SPY設定
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    await text_inputs[0].fill("SPY")
                    await self.log_event("info", "ティッカー: SPY")
                
                # 総合分析
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "総合分析" in text:
                        await button.click()
                        await self.log_event("info", "プリセット: 総合分析")
                        break
                
                # 深度1
                sliders = await page.query_selector_all('input[type="range"]')
                if sliders:
                    await sliders[0].fill("1")
                    await self.log_event("info", "研究深度: 1")
                
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_settings.png"))
                
                # 3. 実行
                await self.log_event("info", "実行ページへ移動")
                exec_btn = await page.wait_for_selector('button:has-text("実行")')
                await exec_btn.click()
                await asyncio.sleep(2)
                
                # 分析開始
                await self.log_event("start", "分析実行開始")
                start_buttons = await page.query_selector_all('button')
                for button in start_buttons:
                    text = await button.inner_text()
                    if "分析" in text and ("実行" in text or "開始" in text):
                        await button.click()
                        analysis_start = time.time()
                        test_result["analysis_start"] = datetime.now().isoformat()
                        break
                
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_started.png"))
                
                # 4. 進捗モニタリング（短時間版）
                await self.log_event("info", "進捗モニタリング（最大3分）")
                max_wait = 180  # 3分
                check_interval = 10
                elapsed = 0
                completed = False
                
                while elapsed < max_wait:
                    # エラーチェック
                    alerts = await page.query_selector_all('[role="alert"]')
                    for alert in alerts:
                        alert_text = await alert.inner_text()
                        if "error" in alert_text.lower() or "errno" in alert_text.lower():
                            await self.log_event("error", f"エラー検出: {alert_text}")
                            test_result["error"] = alert_text
                            raise Exception(f"分析エラー: {alert_text}")
                    
                    # 進捗確認
                    progress_bars = await page.query_selector_all('[role="progressbar"]')
                    if progress_bars:
                        await self.log_event("progress", "進捗バー検出")
                        completed = True
                        break
                    
                    # スピナー確認
                    spinners = await page.query_selector_all('[data-testid="stSpinner"]')
                    if spinners:
                        await self.log_event("progress", "処理中スピナー検出")
                    
                    # 完了メッセージ確認
                    divs = await page.query_selector_all('div')
                    for div in divs[:50]:
                        text = await div.inner_text()
                        if "完了" in text and "分析" in text:
                            await self.log_event("complete", "分析完了メッセージ検出")
                            completed = True
                            break
                    
                    if completed:
                        break
                    
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
                    
                    if elapsed % 30 == 0:
                        await self.log_event("info", f"{elapsed}秒経過...")
                        await page.screenshot(
                            path=str(self.test_dir / f"{self.timestamp}_progress_{elapsed}s.png")
                        )
                
                # 5. 結果確認
                if completed or elapsed >= max_wait:
                    await self.log_event("info", "結果ページへ移動")
                    results_btn = await page.wait_for_selector('button:has-text("結果")')
                    await results_btn.click()
                    await asyncio.sleep(3)
                    
                    # 結果確認
                    result_found = False
                    elements = await page.query_selector_all('div')
                    for elem in elements[:100]:
                        text = await elem.inner_text()
                        if "SPY" in text:
                            result_found = True
                            break
                    
                    if result_found:
                        await self.log_event("complete", "分析結果確認")
                        test_result["status"] = "success"
                    else:
                        await self.log_event("warning", "結果が見つかりません")
                        test_result["status"] = "no_results"
                    
                    await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_results.png"))
                else:
                    test_result["status"] = "timeout"
                    
            except Exception as e:
                await self.log_event("error", f"エラー: {str(e)}")
                test_result["status"] = "error"
                test_result["error_details"] = str(e)
                await page.screenshot(path=str(self.test_dir / f"{self.timestamp}_error.png"))
                
            finally:
                test_result["end_time"] = datetime.now().isoformat()
                if test_result.get("analysis_start"):
                    test_result["duration"] = time.time() - analysis_start
                
                await asyncio.sleep(3)
                await context.close()
                await browser.close()
        
        # 結果保存
        results_file = self.test_dir / f"test_result_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_result": test_result,
                "event_log": self.results
            }, f, ensure_ascii=False, indent=2)
        
        # サマリー
        print("\n" + "="*60)
        print("テスト完了")
        print("="*60)
        print(f"ステータス: {test_result['status']}")
        if test_result.get('duration'):
            print(f"実行時間: {test_result['duration']:.0f}秒")
        print(f"結果: {results_file}")
        
        return test_result

async def main():
    # 環境変数確認
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("FINNHUB_API_KEY"):
        print("⚠️ 環境変数が設定されていません")
        print(".envファイルを確認してください")
        
    # WebUI確認
    import requests
    try:
        requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認\n")
    except:
        print("❌ WebUIが起動していません")
        return
    
    # テスト実行
    test = RetryAnalysisTest()
    await test.run_test()

if __name__ == "__main__":
    asyncio.run(main())