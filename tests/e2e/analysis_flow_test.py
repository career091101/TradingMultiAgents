"""
TradingAgents WebUI 完全分析フローE2Eテスト
研究深度1-5での分析実行から結果確認までの完全なフローをテスト
"""
import asyncio
import time
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright, Page

class AnalysisFlowE2ETest:
    def __init__(self):
        self.test_dir = Path("tests/e2e/analysis_flow_results")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = []
        
        # 深度別設定
        self.depth_configs = {
            1: {"name": "クイック分析", "timeout": 15*60, "expected_time": 11*60},
            3: {"name": "標準分析", "timeout": 35*60, "expected_time": 29*60},
            5: {"name": "詳細分析", "timeout": 60*60, "expected_time": 47*60}
        }
        
    async def log_event(self, event_type: str, message: str, details: Dict = None):
        """イベントログ記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "details": details or {}
        }
        self.results.append(log_entry)
        
        # コンソール出力
        icon = {
            "start": "🚀",
            "progress": "⏳",
            "complete": "✅",
            "error": "❌",
            "info": "ℹ️",
            "warning": "⚠️"
        }.get(event_type, "")
        
        print(f"{icon} [{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    async def wait_for_streamlit(self, page: Page):
        """Streamlit準備完了待機"""
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        await asyncio.sleep(3)
        
    async def navigate_to_page(self, page: Page, page_name: str) -> bool:
        """ページナビゲーション"""
        buttons = await page.query_selector_all('button')
        for button in buttons:
            text = await button.inner_text()
            if page_name in text:
                await button.click()
                await asyncio.sleep(2)
                return True
        return False
        
    async def configure_analysis(self, page: Page, ticker: str, depth: int) -> bool:
        """分析設定を行う"""
        await self.log_event("info", f"分析設定開始: {ticker}, 深度{depth}")
        
        # 設定ページへ移動
        if not await self.navigate_to_page(page, "設定"):
            await self.log_event("error", "設定ページへの移動失敗")
            return False
            
        # ティッカー入力
        text_inputs = await page.query_selector_all('input[type="text"]')
        if text_inputs:
            await text_inputs[0].fill("")
            await text_inputs[0].fill(ticker)
            await self.log_event("info", f"ティッカー設定: {ticker}")
            
        # 総合分析プリセット選択
        buttons = await page.query_selector_all('button')
        for button in buttons:
            text = await button.inner_text()
            if "総合分析" in text:
                await button.click()
                await self.log_event("info", "総合分析プリセット選択")
                break
                
        # 研究深度設定（スライダー）
        sliders = await page.query_selector_all('input[type="range"]')
        for slider in sliders:
            await slider.fill(str(depth))
            await self.log_event("info", f"研究深度設定: {depth}")
            break
            
        await asyncio.sleep(1)
        return True
        
    async def start_analysis(self, page: Page) -> Tuple[bool, float]:
        """分析を開始し、開始時刻を返す"""
        # 実行ページへ移動
        if not await self.navigate_to_page(page, "実行"):
            await self.log_event("error", "実行ページへの移動失敗")
            return False, 0
            
        # 実行ボタンを探す
        buttons = await page.query_selector_all('button')
        for button in buttons:
            text = await button.inner_text()
            if "分析" in text and ("実行" in text or "開始" in text):
                await button.click()
                start_time = time.time()
                await self.log_event("start", "分析実行開始", {"start_time": start_time})
                return True, start_time
                
        await self.log_event("error", "実行ボタンが見つかりません")
        return False, 0
        
    async def monitor_progress(self, page: Page, depth: int, start_time: float) -> Dict:
        """進捗を監視し、完了を待つ"""
        config = self.depth_configs[depth]
        timeout = config["timeout"]
        expected_time = config["expected_time"]
        
        progress_data = {
            "start_time": start_time,
            "end_time": None,
            "duration": None,
            "progress_history": [],
            "final_status": "running",
            "agents_completed": []
        }
        
        last_progress = 0
        stall_count = 0
        check_interval = 10  # 10秒間隔でチェック
        
        await self.log_event("info", f"進捗監視開始 (タイムアウト: {timeout//60}分)")
        
        while (time.time() - start_time) < timeout:
            elapsed = time.time() - start_time
            
            # 進捗要素を探す
            progress_elements = await page.query_selector_all('[role="progressbar"]')
            current_progress = 0
            
            if progress_elements:
                for elem in progress_elements:
                    try:
                        # Streamlitのプログレスバーの値を取得
                        value = await elem.get_attribute("aria-valuenow")
                        if value:
                            current_progress = float(value)
                            break
                    except:
                        pass
                        
            # 進捗履歴記録
            progress_data["progress_history"].append({
                "time": elapsed,
                "progress": current_progress
            })
            
            # 進捗表示
            if current_progress != last_progress:
                await self.log_event("progress", 
                    f"進捗: {current_progress:.0f}% (経過: {elapsed//60:.0f}分)")
                stall_count = 0
            else:
                stall_count += 1
                
            # 完了チェック
            if current_progress >= 100:
                progress_data["end_time"] = time.time()
                progress_data["duration"] = progress_data["end_time"] - start_time
                progress_data["final_status"] = "completed"
                await self.log_event("complete", 
                    f"分析完了 (所要時間: {progress_data['duration']//60:.0f}分)")
                break
                
            # 停滞チェック（5分間進捗なし）
            if stall_count > 30:
                await self.log_event("warning", "進捗が停滞しています")
                await page.screenshot(
                    path=str(self.test_dir / f"stalled_{self.timestamp}_depth{depth}.png")
                )
                
            # エラーチェック
            error_elements = await page.query_selector_all('div[role="alert"]')
            if error_elements:
                for elem in error_elements:
                    error_text = await elem.inner_text()
                    if "error" in error_text.lower():
                        progress_data["final_status"] = "error"
                        await self.log_event("error", f"エラー検出: {error_text}")
                        return progress_data
                        
            last_progress = current_progress
            await asyncio.sleep(check_interval)
            
        # タイムアウト
        if progress_data["final_status"] == "running":
            progress_data["final_status"] = "timeout"
            await self.log_event("error", f"タイムアウト ({timeout//60}分)")
            
        return progress_data
        
    async def verify_results(self, page: Page, ticker: str, depth: int) -> Dict:
        """結果を検証"""
        await self.log_event("info", "結果検証開始")
        
        verification = {
            "page_accessible": False,
            "results_found": False,
            "reports_available": [],
            "summary_content": None,
            "errors": []
        }
        
        # 結果ページへ移動
        if await self.navigate_to_page(page, "結果"):
            verification["page_accessible"] = True
            await asyncio.sleep(3)
            
            # 結果が表示されているかチェック
            elements = await page.query_selector_all('div')
            for elem in elements[:50]:  # 最初の50要素をチェック
                text = await elem.inner_text()
                if ticker in text and ("完了" in text or "結果" in text):
                    verification["results_found"] = True
                    break
                    
            # タブを確認（各レポート）
            tabs = await page.query_selector_all('[role="tab"]')
            for tab in tabs:
                tab_text = await tab.inner_text()
                verification["reports_available"].append(tab_text)
                
            # サマリータブをクリック
            for tab in tabs:
                text = await tab.inner_text()
                if "サマリー" in text:
                    await tab.click()
                    await asyncio.sleep(2)
                    
                    # サマリー内容を取得
                    content_elements = await page.query_selector_all('[role="tabpanel"]')
                    if content_elements:
                        verification["summary_content"] = await content_elements[0].inner_text()
                    break
                    
            # スクリーンショット保存
            await page.screenshot(
                path=str(self.test_dir / f"results_{self.timestamp}_depth{depth}.png"),
                full_page=True
            )
            
        await self.log_event("info", f"結果検証完了: {verification['results_found']}")
        return verification
        
    async def run_depth_test(self, depth: int, ticker: str = "SPY"):
        """特定の深度でテストを実行"""
        config = self.depth_configs[depth]
        test_name = f"深度{depth} - {config['name']}"
        
        print(f"\n{'='*60}")
        print(f"テスト開始: {test_name}")
        print(f"予想時間: {config['expected_time']//60}分")
        print(f"{'='*60}\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # デバッグのため可視化
                slow_mo=200
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP'
            )
            
            page = await context.new_page()
            
            test_result = {
                "depth": depth,
                "ticker": ticker,
                "test_name": test_name,
                "start_time": datetime.now().isoformat(),
                "status": "failed",
                "duration": None,
                "progress_data": None,
                "verification": None,
                "errors": []
            }
            
            try:
                # 1. アプリケーションアクセス
                await page.goto("http://localhost:8501")
                await self.wait_for_streamlit(page)
                
                # 2. 分析設定
                if not await self.configure_analysis(page, ticker, depth):
                    raise Exception("分析設定失敗")
                    
                # 3. 分析実行
                success, start_time = await self.start_analysis(page)
                if not success:
                    raise Exception("分析開始失敗")
                    
                # 4. 進捗監視
                progress_data = await self.monitor_progress(page, depth, start_time)
                test_result["progress_data"] = progress_data
                test_result["duration"] = progress_data.get("duration")
                
                # 5. 結果検証
                if progress_data["final_status"] == "completed":
                    verification = await self.verify_results(page, ticker, depth)
                    test_result["verification"] = verification
                    
                    if verification["results_found"]:
                        test_result["status"] = "success"
                        
            except Exception as e:
                await self.log_event("error", f"テストエラー: {str(e)}")
                test_result["errors"].append(str(e))
                await page.screenshot(
                    path=str(self.test_dir / f"error_{self.timestamp}_depth{depth}.png")
                )
                
            finally:
                test_result["end_time"] = datetime.now().isoformat()
                await context.close()
                await browser.close()
                
        return test_result
        
    async def run_all_tests(self, depths: list = None):
        """全深度でテストを実行"""
        if depths is None:
            depths = [1, 3, 5]
            
        all_results = {
            "test_run": self.timestamp,
            "start_time": datetime.now().isoformat(),
            "depth_results": {},
            "summary": {}
        }
        
        for depth in depths:
            await self.log_event("info", f"\n{'='*20} 深度{depth}テスト開始 {'='*20}")
            result = await self.run_depth_test(depth)
            all_results["depth_results"][depth] = result
            
            # 次のテストまで少し待機（API制限対策）
            if depth != depths[-1]:
                await self.log_event("info", "次のテストまで60秒待機...")
                await asyncio.sleep(60)
                
        # サマリー作成
        all_results["end_time"] = datetime.now().isoformat()
        all_results["summary"] = self._create_summary(all_results["depth_results"])
        
        # 結果保存
        results_file = self.test_dir / f"test_results_{self.timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
            
        print(f"\n\nテスト結果保存: {results_file}")
        self._print_summary(all_results["summary"])
        
        return all_results
        
    def _create_summary(self, depth_results: Dict) -> Dict:
        """テスト結果のサマリー作成"""
        summary = {
            "total_tests": len(depth_results),
            "successful": sum(1 for r in depth_results.values() if r["status"] == "success"),
            "failed": sum(1 for r in depth_results.values() if r["status"] != "success"),
            "depth_performance": {}
        }
        
        for depth, result in depth_results.items():
            expected = self.depth_configs[depth]["expected_time"]
            actual = result.get("duration", 0)
            
            summary["depth_performance"][depth] = {
                "status": result["status"],
                "expected_time": expected,
                "actual_time": actual,
                "difference": actual - expected if actual else None,
                "within_tolerance": abs(actual - expected) <= expected * 0.2 if actual else False
            }
            
        return summary
        
    def _print_summary(self, summary: Dict):
        """サマリーを見やすく出力"""
        print("\n" + "="*60)
        print("テスト実行サマリー")
        print("="*60)
        print(f"総テスト数: {summary['total_tests']}")
        print(f"成功: {summary['successful']} ✅")
        print(f"失敗: {summary['failed']} ❌")
        print("\n深度別パフォーマンス:")
        
        for depth, perf in summary["depth_performance"].items():
            status_icon = "✅" if perf["status"] == "success" else "❌"
            print(f"\n深度{depth}: {status_icon}")
            if perf["actual_time"]:
                print(f"  予想: {perf['expected_time']//60}分")
                print(f"  実際: {perf['actual_time']//60}分")
                print(f"  差異: {perf['difference']//60:+.0f}分")
                print(f"  許容範囲内: {'Yes' if perf['within_tolerance'] else 'No'}")

async def main():
    """メイン実行関数"""
    test = AnalysisFlowE2ETest()
    
    # テスト対象の深度を選択
    print("実行する研究深度を選択してください:")
    print("1. 深度1のみ（クイック: 約15分）")
    print("2. 深度1,3（標準: 約50分）")
    print("3. 全深度1,3,5（完全: 約2時間）")
    
    choice = input("\n選択 (1-3): ").strip()
    
    depths_map = {
        "1": [1],
        "2": [1, 3],
        "3": [1, 3, 5]
    }
    
    depths = depths_map.get(choice, [1])
    
    print(f"\n選択された深度: {depths}")
    confirm = input("実行しますか？ (y/n): ").strip().lower()
    
    if confirm == 'y':
        await test.run_all_tests(depths)
    else:
        print("テストをキャンセルしました")

if __name__ == "__main__":
    print("TradingAgents WebUI 完全分析フローE2Eテスト")
    print("前提条件:")
    print("- WebUIが起動中 (http://localhost:8501)")
    print("- APIキーが設定済み")
    print("-" * 60)
    
    asyncio.run(main())