#!/usr/bin/env python3
"""
分析完了度100%確認E2Eテスト
分析開始から進捗バーが100%になるまでを確認
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

class AnalysisCompletionTest:
    def __init__(self):
        self.test_dir = Path("tests/e2e/completion_test_results")
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
            "error": "❌", "info": "ℹ️", "warning": "⚠️",
            "percent": "📊"
        }
        icon = icons.get(event_type, "")
        print(f"{icon} [{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    async def check_disk_space(self):
        """ディスク容量チェック"""
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        
        if free_gb < 1:
            await self.log_event("error", "ディスク容量不足！最低1GB必要です")
            return False
        
        await self.log_event("info", f"ディスク容量: {free_gb:.1f}GB空き")
        return True
        
    async def run_completion_test(self):
        """完了度100%確認テスト実行"""
        print("=== 分析完了度100%確認E2Eテスト ===")
        print("分析開始から進捗バーが100%になるまでを監視")
        print("-" * 60)
        
        # ディスク容量チェック
        if not await self.check_disk_space():
            return {"status": "failed", "error": "Insufficient disk space"}
        
        test_result = {
            "test_id": f"completion_{self.timestamp}",
            "start_time": datetime.now().isoformat(),
            "ticker": "SPY",
            "depth": 1,
            "status": "running",
            "progress_history": []
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=200,
                args=[
                    '--window-size=1600,1200',
                    '--window-position=100,50'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1536, 'height': 1024},
                device_scale_factor=1.0,
                locale='ja-JP'
            )
            
            page = await context.new_page()
            
            try:
                # 1. WebUIアクセスと設定
                await self.log_event("start", "WebUIアクセス開始")
                await page.goto("http://localhost:8501")
                await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
                await asyncio.sleep(3)
                
                # 設定ページ
                await self.log_event("info", "設定ページへ移動")
                settings_btn = await page.wait_for_selector('button:has-text("設定")')
                await settings_btn.click()
                await asyncio.sleep(2)
                
                # SPY、総合分析、深度1を設定
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    await text_inputs[0].fill("SPY")
                
                buttons = await page.query_selector_all('button')
                for button in buttons:
                    text = await button.inner_text()
                    if "総合分析" in text:
                        await button.click()
                        break
                
                sliders = await page.query_selector_all('input[type="range"]')
                if sliders:
                    await sliders[0].fill("1")
                
                await self.log_event("info", "設定完了: SPY, 総合分析, 深度1")
                
                # 2. 実行ページへ移動して分析開始
                exec_btn = await page.wait_for_selector('button:has-text("実行")')
                await exec_btn.click()
                await asyncio.sleep(2)
                
                await self.log_event("start", "分析実行開始")
                start_buttons = await page.query_selector_all('button')
                for button in start_buttons:
                    text = await button.inner_text()
                    if "分析" in text and ("実行" in text or "開始" in text):
                        await button.click()
                        analysis_start_time = time.time()
                        test_result["analysis_start_time"] = datetime.now().isoformat()
                        break
                
                await asyncio.sleep(5)  # 実行開始後の初期化待ち
                
                # 3. 進捗モニタリング（100%になるまで）
                await self.log_event("info", "進捗モニタリング開始")
                
                max_wait_time = 900  # 最大15分
                check_interval = 5   # 5秒間隔でチェック
                elapsed = 0
                last_progress = -1
                progress_100_count = 0
                
                while elapsed < max_wait_time:
                    # 進捗バーを探す
                    progress_value = 0
                    progress_found = False
                    
                    # Streamlitのプログレスバー
                    progress_bars = await page.query_selector_all('[role="progressbar"]')
                    if progress_bars:
                        for bar in progress_bars:
                            try:
                                # aria-valuenow属性から進捗値を取得
                                value_str = await bar.get_attribute("aria-valuenow")
                                if value_str:
                                    progress_value = float(value_str)
                                    progress_found = True
                                    break
                            except:
                                pass
                    
                    # 進捗テキストを探す（代替手段）
                    if not progress_found:
                        progress_texts = await page.query_selector_all('div')
                        for elem in progress_texts[:100]:
                            text = await elem.inner_text()
                            if "%" in text and ("進捗" in text or "Progress" in text):
                                # テキストから数値を抽出
                                import re
                                match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                                if match:
                                    progress_value = float(match.group(1))
                                    progress_found = True
                                    break
                    
                    # 進捗が更新された場合のみログ出力
                    if progress_found and progress_value != last_progress:
                        await self.log_event("percent", f"進捗: {progress_value:.1f}%")
                        
                        # 進捗履歴に記録
                        test_result["progress_history"].append({
                            "time": elapsed,
                            "progress": progress_value,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # スクリーンショット（10%刻み）
                        if int(progress_value / 10) != int(last_progress / 10):
                            await page.screenshot(
                                path=str(self.test_dir / f"{self.timestamp}_progress_{int(progress_value)}pct.png"),
                                full_page=True
                            )
                        
                        last_progress = progress_value
                        
                        # 100%到達確認
                        if progress_value >= 100:
                            progress_100_count += 1
                            await self.log_event("complete", f"進捗100%到達！（{progress_100_count}回目）")
                            
                            # 100%を3回確認したら完了とする（安定性のため）
                            if progress_100_count >= 3:
                                test_result["completion_time"] = datetime.now().isoformat()
                                test_result["total_duration"] = time.time() - analysis_start_time
                                break
                    
                    # エラーチェック
                    alerts = await page.query_selector_all('[role="alert"]')
                    for alert in alerts:
                        alert_text = await alert.inner_text()
                        if "error" in alert_text.lower():
                            await self.log_event("error", f"エラー検出: {alert_text}")
                            test_result["error"] = alert_text
                            raise Exception(f"分析エラー: {alert_text}")
                    
                    # 完了メッセージの確認
                    completion_messages = [
                        "分析が完了しました",
                        "Analysis completed",
                        "完了",
                        "100%"
                    ]
                    
                    divs = await page.query_selector_all('div')
                    for div in divs[:50]:
                        text = await div.inner_text()
                        for msg in completion_messages:
                            if msg in text:
                                await self.log_event("info", f"完了メッセージ検出: {text[:50]}")
                                break
                    
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
                    
                    # 定期的なステータス表示
                    if elapsed % 30 == 0:
                        await self.log_event("info", f"経過時間: {elapsed}秒 ({elapsed/60:.1f}分)")
                
                # 4. 完了確認と結果ページへの移動
                if progress_100_count > 0:
                    await self.log_event("info", "結果ページへ移動")
                    
                    # 自動遷移を待つか、手動で移動
                    await asyncio.sleep(5)
                    
                    results_btn = await page.wait_for_selector('button:has-text("結果")')
                    await results_btn.click()
                    await asyncio.sleep(3)
                    
                    # 結果ページのスクリーンショット
                    await page.screenshot(
                        path=str(self.test_dir / f"{self.timestamp}_results_100pct.png"),
                        full_page=True
                    )
                    
                    # サマリー確認
                    summary_found = False
                    elements = await page.query_selector_all('div')
                    for elem in elements[:100]:
                        text = await elem.inner_text()
                        if "SPY" in text and ("サマリー" in text or "Summary" in text):
                            summary_found = True
                            await self.log_event("complete", "分析サマリー確認")
                            break
                    
                    if summary_found:
                        test_result["status"] = "success"
                        test_result["summary_confirmed"] = True
                    else:
                        test_result["status"] = "success_no_summary"
                        test_result["summary_confirmed"] = False
                else:
                    test_result["status"] = "timeout"
                    await self.log_event("warning", "タイムアウト: 100%に到達しませんでした")
                    
            except Exception as e:
                await self.log_event("error", f"テストエラー: {str(e)}")
                test_result["status"] = "error"
                test_result["error_details"] = str(e)
                await page.screenshot(
                    path=str(self.test_dir / f"{self.timestamp}_error.png"),
                    full_page=True
                )
                
            finally:
                test_result["end_time"] = datetime.now().isoformat()
                
                # 最終的な進捗確認
                if test_result.get("progress_history"):
                    final_progress = test_result["progress_history"][-1]["progress"]
                    await self.log_event("info", f"最終進捗: {final_progress}%")
                
                await asyncio.sleep(5)
                await context.close()
                await browser.close()
        
        # 結果保存
        results_file = self.test_dir / f"completion_test_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_result": test_result,
                "event_log": self.results
            }, f, ensure_ascii=False, indent=2)
        
        # サマリー表示
        print("\n" + "="*60)
        print("完了度テスト結果")
        print("="*60)
        print(f"ステータス: {test_result['status']}")
        
        if test_result.get("total_duration"):
            duration = test_result["total_duration"]
            print(f"分析時間: {duration:.0f}秒 ({duration/60:.1f}分)")
        
        if test_result.get("progress_history"):
            print(f"進捗記録数: {len(test_result['progress_history'])}回")
            final = test_result["progress_history"][-1]["progress"]
            print(f"最終進捗: {final}%")
        
        print(f"\n結果ファイル: {results_file}")
        print(f"スクリーンショット: {self.test_dir}")
        
        return test_result

async def main():
    # 環境変数確認
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("FINNHUB_API_KEY"):
        print("⚠️ 環境変数が設定されていません")
        
    # WebUI確認
    import requests
    try:
        requests.get("http://localhost:8501", timeout=5)
        print("✅ WebUI起動確認\n")
    except:
        print("❌ WebUIが起動していません")
        return
    
    # テスト実行
    test = AnalysisCompletionTest()
    await test.run_completion_test()

if __name__ == "__main__":
    asyncio.run(main())