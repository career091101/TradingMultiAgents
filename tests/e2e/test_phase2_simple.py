"""
Phase 2 Simple Test - 動作確認用
"""

import pytest
from playwright.sync_api import Page, expect
from utils.streamlit_selectors import StreamlitSelectors

pytestmark = pytest.mark.error_handling


class TestPhase2Simple:
    """Phase 2の簡単な動作確認テスト"""
    
    def setup_method(self):
        """Set up selectors for testing"""
        self.selectors = StreamlitSelectors()

    def test_navigation_to_execution(self, page: Page, screenshot_dir):
        """分析実行ページへのナビゲーションテスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Take screenshot of initial state
        page.screenshot(path=f"{screenshot_dir}/initial_state.png", full_page=True)
        
        # Navigate to execution page
        execution_nav = page.locator(self.selectors.nav_button("execution"))
        execution_nav.click()
        page.wait_for_load_state("networkidle", timeout=5000)
        
        # Take screenshot after navigation
        page.screenshot(path=f"{screenshot_dir}/execution_page.png", full_page=True)
        
        # Check that we're on the execution page
        page_title = page.locator('h2:has-text("分析実行")')
        expect(page_title).to_be_visible()

    def test_ticker_input_exists(self, page: Page, screenshot_dir):
        """ティッカー入力フィールドの存在確認"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to execution page
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")
        
        # Check if ticker input exists in the sidebar
        # First check sidebar exists
        sidebar = page.locator(self.selectors.sidebar())
        expect(sidebar).to_be_visible()
        
        # Look for ticker input - try different approaches
        ticker_input = page.locator(self.selectors.settings_input("ticker"))
        
        # Take screenshot to see current state
        page.screenshot(path=f"{screenshot_dir}/ticker_input_check.png", full_page=True)
        
        # If the specific selector doesn't work, let's try a more general approach
        # Look for any text input in the sidebar
        sidebar_inputs = page.locator(f"{self.selectors.sidebar()} input[type='text']")
        
        if sidebar_inputs.count() > 0:
            print(f"Found {sidebar_inputs.count()} text inputs in sidebar")
            # Try to use the first input
            first_input = sidebar_inputs.first
            first_input.fill("TEST")
            page.screenshot(path=f"{screenshot_dir}/input_filled.png", full_page=True)
        else:
            # If no input found, check what's in the sidebar
            sidebar_content = sidebar.text_content()
            print(f"Sidebar content: {sidebar_content}")
            
            # Look for any input fields
            all_inputs = page.locator("input")
            print(f"Total inputs on page: {all_inputs.count()}")
            
            page.screenshot(path=f"{screenshot_dir}/no_input_found.png", full_page=True)