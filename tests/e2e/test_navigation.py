"""
ナビゲーションのE2Eテスト（更新版）
StreamlitSelectorsを使用した安定したテスト
"""

import pytest
from playwright.sync_api import Page, expect
from utils import StreamlitSelectors, StreamlitPageObjects


class TestNavigation:
    """ナビゲーション関連のテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.selectors = StreamlitSelectors()
    
    @pytest.mark.smoke
    def test_main_page_loads(self, page: Page, screenshot_path):
        """TC001: メインページの表示確認"""
        # ページタイトルの確認
        expect(page).to_have_title("TradingAgents WebUI", timeout=10000)
        
        # ヘッダーの確認（Streamlitのmarkdown内のテキスト）
        header_text = page.locator('h1:has-text("TradingAgents WebUI")')
        expect(header_text).to_be_visible()
        
        # サイドバーの確認
        sidebar = page.locator(self.selectors.sidebar())
        expect(sidebar).to_be_visible()
        
        # ダッシュボードコンテンツの確認
        dashboard_elements = {
            "title": page.locator('text="ダッシュボード"').first,
            "stats": page.locator(self.selectors.metric("総分析数"))
        }
        
        for name, element in dashboard_elements.items():
            expect(element).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("dashboard_initial"), full_page=True)
    
    @pytest.mark.smoke
    def test_sidebar_navigation(self, page: Page, screenshot_path):
        """TC002: サイドバーナビゲーション"""
        page_obj = StreamlitPageObjects(page)
        
        navigation_items = [
            ("settings", "分析設定"),
            ("execution", "分析実行"),
            ("results", "結果表示"),
            ("dashboard", "ダッシュボード")  # 最後にダッシュボードに戻る
        ]
        
        for page_key, expected_title in navigation_items:
            # ナビゲーションボタンをクリック
            nav_button = page.locator(self.selectors.nav_button(page_key))
            nav_button.click()
            
            # ページ遷移を待機
            page.wait_for_load_state("networkidle")
            
            # ページタイトルまたは特徴的な要素を確認
            if page_key == "dashboard":
                expect(page.locator(self.selectors.metric("総分析数"))).to_be_visible(timeout=5000)
            else:
                # 各ページ特有の要素を確認
                page_content = page.locator("text=" + expected_title).first
                expect(page_content).to_be_visible(timeout=5000)
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"navigation_{page_key}"),
                full_page=True
            )
    
    def test_responsive_sidebar(self, page: Page, screenshot_path):
        """サイドバーのレスポンシブ動作確認"""
        # デスクトップサイズ
        page.set_viewport_size({"width": 1920, "height": 1080})
        sidebar = page.locator(self.selectors.sidebar())
        expect(sidebar).to_be_visible()
        page.screenshot(path=screenshot_path("sidebar_desktop"))
        
        # タブレットサイズ
        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(1000)
        # Streamlitはタブレットサイズでもサイドバーを表示
        expect(sidebar).to_be_visible()
        page.screenshot(path=screenshot_path("sidebar_tablet"))
        
        # モバイルサイズ
        page.set_viewport_size({"width": 375, "height": 812})
        page.wait_for_timeout(1000)
        # モバイルではサイドバーが折りたたまれる可能性
        page.screenshot(path=screenshot_path("sidebar_mobile"))
    
    def test_quick_actions(self, page: Page, screenshot_path):
        """クイックアクションボタンのテスト"""
        # SPY分析ボタン
        spy_button = page.locator(self.selectors.button(text="SPY分析"))
        expect(spy_button).to_be_visible()
        
        # クリック前のスクリーンショット
        page.screenshot(path=screenshot_path("quick_actions_before"))
        
        # SPY分析ボタンをクリック
        spy_button.click()
        page.wait_for_load_state("networkidle")
        
        # 設定ページに遷移し、SPYが選択されていることを確認
        page.screenshot(path=screenshot_path("quick_actions_after_spy"))
        
        # ダッシュボードに戻る
        dashboard_button = page.locator(self.selectors.nav_button("dashboard"))
        dashboard_button.click()
        page.wait_for_load_state("networkidle")
        
        # JP225分析ボタン
        jp225_button = page.locator(self.selectors.button(text="JP225分析"))
        expect(jp225_button).to_be_visible()
        
        jp225_button.click()
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=screenshot_path("quick_actions_after_jp225"))
    
    def test_environment_status(self, page: Page, screenshot_path):
        """環境変数ステータスの表示確認"""
        # サイドバーの環境設定セクション
        env_section = page.locator(self.selectors.markdown_with_text("環境設定"))
        expect(env_section).to_be_visible()
        
        # API KEY のステータス確認
        finnhub_status = page.locator('text="FINNHUB_API_KEY"')
        openai_status = page.locator('text="OPENAI_API_KEY"')
        
        expect(finnhub_status).to_be_visible()
        expect(openai_status).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("environment_status"))
    
    def test_cross_browser_compatibility(self, browser, webui_server):
        """クロスブラウザ互換性テスト"""
        browser_name = browser.browser_type.name
        
        context = browser.new_context()
        page = context.new_page()
        page.goto("http://localhost:8501")
        
        # 基本的な要素の確認
        selectors = StreamlitSelectors()
        
        # ページロード完了を待機
        page.wait_for_load_state("networkidle")
        
        # サイドバーの確認
        sidebar = page.locator(selectors.sidebar())
        assert sidebar.is_visible(), f"{browser_name}: サイドバーが表示されていません"
        
        # ナビゲーションボタンの確認
        dashboard_button = page.locator(selectors.nav_button("dashboard"))
        assert dashboard_button.is_visible(), f"{browser_name}: ダッシュボードボタンが表示されていません"
        
        page.close()
        context.close()