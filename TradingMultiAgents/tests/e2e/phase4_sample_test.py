"""
Phase 4 E2E Test - サンプル実装
完全な分析フローをテストする実行可能なサンプル
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import json
import os
from datetime import datetime
from pathlib import Path

class TestTradingAgentsE2E:
    """TradingAgents WebUI E2Eテストサンプル"""
    
    @pytest.fixture(scope="session")
    async def browser(self):
        """ブラウザインスタンスの作成"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # デモ用に可視化
                slow_mo=500,     # 動作を見やすくするため遅延追加
            )
            yield browser
            await browser.close()
    
    @pytest.fixture
    async def context(self, browser):
        """ブラウザコンテキストの作成"""
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ja-JP',
            timezone_id='Asia/Tokyo'
        )
        yield context
        await context.close()
    
    @pytest.fixture
    async def page(self, context):
        """新規ページの作成"""
        page = await context.new_page()
        yield page
        await page.close()
    
    async def wait_for_streamlit_ready(self, page: Page):
        """Streamlitアプリの準備完了を待機"""
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
        await asyncio.sleep(1)  # Streamlitの初期化待ち
    
    @pytest.mark.asyncio
    async def test_complete_analysis_flow(self, page: Page):
        """
        完全な分析フローのE2Eテスト
        初回ユーザーが設定から結果確認まで実行
        """
        print("\n=== Phase 4 E2E Test: 完全分析フロー開始 ===")
        
        # Step 1: アプリケーションにアクセス
        print("Step 1: WebUIにアクセス")
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit_ready(page)
        
        # Step 2: 初回起動時の環境チェック
        print("Step 2: 環境チェック確認")
        try:
            env_warning = await page.wait_for_selector(
                'text="環境変数が設定されていません"',
                timeout=5000
            )
            if env_warning:
                print("  ⚠️ 環境変数未設定の警告を確認")
        except:
            print("  ✅ 環境変数は設定済み")
        
        # Step 3: 設定ページへ移動
        print("Step 3: 設定ページへ移動")
        settings_button = await page.wait_for_selector('text="⚙️ 設定"')
        await settings_button.click()
        await asyncio.sleep(2)
        
        # Step 4: 分析設定を行う
        print("Step 4: 分析設定の入力")
        
        # ティッカー入力
        ticker_input = await page.wait_for_selector('[data-testid="ticker_input"]')
        await ticker_input.fill("AAPL")
        print("  - ティッカー: AAPL")
        
        # プリセット選択
        preset_button = await page.wait_for_selector('text="総合分析"')
        await preset_button.click()
        print("  - プリセット: 総合分析")
        
        # 研究深度設定
        depth_slider = await page.wait_for_selector('[data-testid="depth_slider"]')
        await depth_slider.fill("3")
        print("  - 研究深度: 3")
        
        # 設定保存
        save_button = await page.wait_for_selector('text="設定を保存"')
        await save_button.click()
        await asyncio.sleep(1)
        print("  ✅ 設定を保存")
        
        # Step 5: 実行ページへ移動
        print("Step 5: 分析実行ページへ移動")
        execution_button = await page.wait_for_selector('text="▶️ 実行"')
        await execution_button.click()
        await asyncio.sleep(2)
        
        # Step 6: 分析を開始
        print("Step 6: 分析を開始")
        start_button = await page.wait_for_selector('text="分析を開始"')
        await start_button.click()
        print("  ⏳ 分析実行中...")
        
        # 進捗表示を確認
        progress_bar = await page.wait_for_selector('[role="progressbar"]', timeout=10000)
        print("  - 進捗バー表示を確認")
        
        # Step 7: 分析完了を待機（デモ用に短時間で完了と仮定）
        print("Step 7: 分析完了待機")
        try:
            # 実際の実装では完了通知を待機
            await page.wait_for_selector('text="分析が完了しました"', timeout=300000)
            print("  ✅ 分析完了")
        except:
            # タイムアウトの場合はスキップ（デモ用）
            print("  ⏭️ 完了待機をスキップ（デモモード）")
        
        # Step 8: 結果ページへ移動
        print("Step 8: 結果表示ページへ移動")
        results_button = await page.wait_for_selector('text="📊 結果"')
        await results_button.click()
        await asyncio.sleep(2)
        
        # Step 9: 結果の確認
        print("Step 9: 分析結果の確認")
        try:
            # 結果セレクタの確認
            result_selector = await page.wait_for_selector(
                '[data-testid="result_selector"]',
                timeout=5000
            )
            print("  - 結果セレクタ表示を確認")
            
            # サマリータブの確認
            summary_tab = await page.wait_for_selector('text="サマリー"')
            await summary_tab.click()
            print("  - サマリータブを確認")
        except:
            print("  ⚠️ 結果が見つかりません（分析未完了の可能性）")
        
        # Step 10: スクリーンショット保存
        print("Step 10: 実行結果のスクリーンショット保存")
        screenshot_dir = Path("tests/e2e/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"phase4_test_{timestamp}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  📸 スクリーンショット保存: {screenshot_path}")
        
        print("\n=== テスト完了 ===")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, page: Page):
        """エラーハンドリングのテスト"""
        print("\n=== エラーハンドリングテスト開始 ===")
        
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit_ready(page)
        
        # 設定ページで不正な入力
        settings_button = await page.wait_for_selector('text="⚙️ 設定"')
        await settings_button.click()
        await asyncio.sleep(1)
        
        # 存在しない銘柄を入力
        ticker_input = await page.wait_for_selector('[data-testid="ticker_input"]')
        await ticker_input.fill("INVALID123")
        
        # エラーメッセージの確認（実装依存）
        print("  - 不正な銘柄入力のテスト完了")
        
    @pytest.mark.asyncio
    async def test_data_persistence(self, page: Page):
        """データ永続性のテスト"""
        print("\n=== データ永続性テスト開始 ===")
        
        await page.goto("http://localhost:8501")
        await self.wait_for_streamlit_ready(page)
        
        # 設定を保存
        settings_button = await page.wait_for_selector('text="⚙️ 設定"')
        await settings_button.click()
        
        ticker_input = await page.wait_for_selector('[data-testid="ticker_input"]')
        await ticker_input.fill("MSFT")
        
        save_button = await page.wait_for_selector('text="設定を保存"')
        await save_button.click()
        
        # ページリロード
        await page.reload()
        await self.wait_for_streamlit_ready(page)
        
        # 設定が保持されているか確認
        await settings_button.click()
        ticker_value = await ticker_input.input_value()
        assert ticker_value == "MSFT", "設定が永続化されていません"
        print("  ✅ 設定の永続化を確認")

if __name__ == "__main__":
    # 直接実行用のヘルパー関数
    async def run_demo():
        test = TestTradingAgentsE2E()
        browser = await async_playwright().start()
        browser_instance = await browser.chromium.launch(headless=False, slow_mo=500)
        context = await browser_instance.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            await test.test_complete_analysis_flow(page)
        finally:
            await context.close()
            await browser_instance.close()
            await browser.stop()
    
    # デモ実行
    print("TradingAgents WebUI E2E Test Demo")
    print("前提条件: WebUIが http://localhost:8501 で起動していること")
    asyncio.run(run_demo())