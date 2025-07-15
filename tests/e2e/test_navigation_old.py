"""
ナビゲーションのE2Eテスト
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestNavigation:
    """ナビゲーション関連のテスト"""
    
    @pytest.mark.smoke
    def test_main_page_loads(self, page: Page, screenshot_path):
        """TC001: メインページの表示確認"""
        # ページタイトルの確認
        expect(page).to_have_title("TradingAgents WebUI", timeout=10000)
        
        # ヘッダーの確認
        header = page.locator("text=TradingAgents WebUI").first
        expect(header).to_be_visible()
        
        # サイドバーの確認
        sidebar = page.locator("[data-testid='stSidebar']")
        expect(sidebar).to_be_visible()
        
        # ダッシュボードコンテンツの確認
        dashboard_title = page.locator("text=ダッシュボード").first
        expect(dashboard_title).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("dashboard_initial"), full_page=True)
    
    @pytest.mark.smoke
    def test_sidebar_navigation(self, page: Page, screenshot_path):
        """TC002: サイドバーナビゲーション"""
        navigation_items = [
            ("分析設定", "settings"),
            ("分析実行", "execution"),
            ("結果表示", "results"),
        ]
        
        for item_text, item_id in navigation_items:
            # サイドバーアイテムをクリック
            sidebar_item = page.locator(f"text={item_text}").first
            
            # アイテムが見えるまで待機
            sidebar_item.wait_for(state="visible", timeout=5000)
            sidebar_item.click()
            
            # ページ遷移を待機
            time.sleep(2)
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"navigation_{item_id}"),
                full_page=True
            )
            
            # ページ内容の確認（各ページに特有の要素を確認）
            if item_id == "settings":
                # 設定ページの要素確認
                api_section = page.locator("text=API").first
                expect(api_section).to_be_visible()
    
    def test_responsive_sidebar(self, page: Page, screenshot_path):
        """サイドバーのレスポンシブ動作確認"""
        # デスクトップサイズ
        page.set_viewport_size({"width": 1920, "height": 1080})
        sidebar = page.locator("[data-testid='stSidebar']")
        expect(sidebar).to_be_visible()
        page.screenshot(path=screenshot_path("sidebar_desktop"))
        
        # タブレットサイズ
        page.set_viewport_size({"width": 768, "height": 1024})
        time.sleep(1)
        page.screenshot(path=screenshot_path("sidebar_tablet"))
        
        # モバイルサイズ
        page.set_viewport_size({"width": 375, "height": 812})
        time.sleep(1)
        page.screenshot(path=screenshot_path("sidebar_mobile"))
    
    def test_cross_browser_compatibility(self, browser, webui_server):
        """クロスブラウザ互換性テスト"""
        browser_name = browser.browser_type.name
        
        context = browser.new_context()
        page = context.new_page()
        page.goto("http://localhost:8501")
        
        # 基本的な要素の確認
        expect(page.locator("text=TradingAgents WebUI").first).to_be_visible()
        
        page.close()
        context.close()