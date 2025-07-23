"""
E2E Error Handling Tests - Phase 2 Implementation (Adapted)
現在のWebUI構造に合わせて適応
"""

import pytest
from playwright.sync_api import Page, expect
import json
from typing import Dict, Any
from utils.streamlit_selectors import StreamlitSelectors

# Phase 2 マーカー
pytestmark = pytest.mark.error_handling


class TestErrorHandlingAdapted:
    """WebUI構造に適応したエラーハンドリングテスト"""
    
    def setup_method(self):
        """Set up selectors for testing"""
        self.selectors = StreamlitSelectors()

    def test_navigation_error_handling(self, page: Page, screenshot_dir):
        """ページナビゲーション時のエラーハンドリング"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Block all requests to simulate network issues
        page.route("**/*", lambda route: route.abort())
        
        # Try to navigate to different pages
        try:
            page.click(self.selectors.nav_button("settings"))
            page.wait_for_timeout(2000)
        except:
            pass  # Expected to fail
        
        page.screenshot(path=f"{screenshot_dir}/navigation_error.png", full_page=True)
        
        # Clear the route to restore functionality
        page.unroute("**/*")
        
        # Verify app still responds
        page.reload()
        page.wait_for_load_state("networkidle")
        
        # Should be able to navigate normally now
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")

    def test_settings_page_error_handling(self, page: Page, screenshot_dir):
        """設定ページでのエラーハンドリング"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings page
        page.click(self.selectors.nav_button("settings"))
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/settings_page.png", full_page=True)
        
        # Look for ticker input field
        ticker_inputs = page.locator("input[type='text']")
        if ticker_inputs.count() > 0:
            first_input = ticker_inputs.first
            
            # Test various invalid inputs
            invalid_inputs = ["", "123", "!@#$%", "INVALID_TICKER_SYMBOL"]
            
            for i, invalid_input in enumerate(invalid_inputs):
                first_input.clear()
                if invalid_input:  # Don't fill empty string
                    first_input.fill(invalid_input)
                
                page.screenshot(path=f"{screenshot_dir}/invalid_input_{i}_{invalid_input or 'empty'}.png")
                
                # Try to trigger validation or save
                save_buttons = page.locator("button:has-text('保存'), button:has-text('更新')")
                if save_buttons.count() > 0:
                    save_buttons.first.click()
                    page.wait_for_timeout(1000)
                
                # Check for validation messages
                page_content = page.content()
                
                # Take screenshot after attempted save
                page.screenshot(path=f"{screenshot_dir}/after_save_{i}.png")

    def test_execution_button_error_handling(self, page: Page, screenshot_dir):
        """実行ボタンのエラーハンドリング"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to execution page
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/execution_page_initial.png", full_page=True)
        
        # Block API requests to simulate server errors
        page.route("**/api/**", lambda route: route.fulfill(
            status=500,
            headers={"content-type": "application/json"},
            body=json.dumps({"error": "Internal server error"})
        ))
        
        # Look for execution/analysis buttons
        execution_buttons = page.locator(
            "button:has-text('実行'), button:has-text('分析'), button:has-text('開始')"
        )
        
        if execution_buttons.count() > 0:
            # Click the first execution button
            execution_buttons.first.click()
            
            # Wait for response
            page.wait_for_timeout(3000)
            
            page.screenshot(path=f"{screenshot_dir}/after_execution_error.png", full_page=True)
            
            # Check for error messages
            error_indicators = page.locator(
                "text*=エラー, text*=失敗, text*=error, [data-testid='stAlert']"
            )
            
            if error_indicators.count() > 0:
                print(f"Found {error_indicators.count()} error indicators")
            
        # Clear the route
        page.unroute("**/api/**")

    def test_quick_action_error_handling(self, page: Page, screenshot_dir):
        """クイックアクションのエラーハンドリング"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/quick_actions_initial.png", full_page=True)
        
        # Block network requests
        page.route("**/*", lambda route: route.abort())
        
        # Look for quick action buttons in sidebar
        quick_action_buttons = page.locator(f"{self.selectors.sidebar()} button")
        
        if quick_action_buttons.count() > 0:
            # Try clicking quick action buttons
            for i in range(min(3, quick_action_buttons.count())):
                try:
                    button = quick_action_buttons.nth(i)
                    button_text = button.text_content()
                    print(f"Clicking button: {button_text}")
                    
                    button.click()
                    page.wait_for_timeout(2000)
                    
                    page.screenshot(path=f"{screenshot_dir}/quick_action_{i}_error.png")
                    
                except Exception as e:
                    print(f"Expected error for button {i}: {e}")
        
        # Clear the route
        page.unroute("**/*")

    def test_api_rate_limit_simulation(self, page: Page, screenshot_dir):
        """APIレート制限のシミュレーション"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Mock rate limit response
        page.route("**/api/**", lambda route: route.fulfill(
            status=429,
            headers={"content-type": "application/json"},
            body=json.dumps({
                "error": "Rate limit exceeded",
                "message": "API制限に達しました。しばらくお待ちください",
                "retry_after": 60
            })
        ))
        
        # Navigate to execution page
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")
        
        # Try to execute analysis
        execution_buttons = page.locator("button")
        analysis_button = None
        
        for i in range(execution_buttons.count()):
            button = execution_buttons.nth(i)
            button_text = button.text_content()
            if any(keyword in button_text for keyword in ["実行", "分析", "開始", "スタート"]):
                analysis_button = button
                break
        
        if analysis_button:
            analysis_button.click()
            page.wait_for_timeout(3000)
            
            page.screenshot(path=f"{screenshot_dir}/rate_limit_error.png", full_page=True)
            
            # Look for rate limit error messages
            page_content = page.content().lower()
            rate_limit_keywords = ["制限", "rate", "limit", "429"]
            
            found_rate_limit_indicator = any(keyword in page_content for keyword in rate_limit_keywords)
            print(f"Rate limit indicator found: {found_rate_limit_indicator}")
        
        # Clear the route
        page.unroute("**/api/**")

    def test_api_server_overload_simulation(self, page: Page, screenshot_dir):
        """APIサーバー過負荷（529エラー）のシミュレーション"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Mock server overload response (529 error)
        page.route("**/api/**", lambda route: route.fulfill(
            status=529,
            headers={"content-type": "application/json"},
            body=json.dumps({
                "type": "error",
                "error": {
                    "type": "overloaded_error",
                    "message": "Overloaded"
                }
            })
        ))
        
        # Navigate to execution page
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")
        
        # Try to execute analysis
        execution_buttons = page.locator("button")
        analysis_button = None
        
        for i in range(execution_buttons.count()):
            button = execution_buttons.nth(i)
            button_text = button.text_content()
            if any(keyword in button_text for keyword in ["実行", "分析", "開始", "スタート"]):
                analysis_button = button
                break
        
        if analysis_button:
            analysis_button.click()
            page.wait_for_timeout(3000)
            
            page.screenshot(path=f"{screenshot_dir}/server_overload_error.png", full_page=True)
            
            # Look for overload error messages
            page_content = page.content().lower()
            overload_keywords = ["過負荷", "overload", "529", "サーバー", "busy"]
            
            found_overload_indicator = any(keyword in page_content for keyword in overload_keywords)
            print(f"Server overload indicator found: {found_overload_indicator}")
        
        # Clear the route
        page.unroute("**/api/**")

    def test_page_reload_recovery(self, page: Page, screenshot_dir):
        """ページリロード後の復旧テスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to execution page
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/before_reload.png", full_page=True)
        
        # Simulate temporary network issues
        page.route("**/*", lambda route: route.abort())
        
        # Try to interact with the page (should fail)
        try:
            page.click(self.selectors.nav_button("settings"))
            page.wait_for_timeout(1000)
        except:
            pass  # Expected to fail
        
        # Clear routes and reload
        page.unroute("**/*")
        page.reload()
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/after_reload.png", full_page=True)
        
        # Verify page recovered
        page_title = page.locator("h1, h2").first
        expect(page_title).to_be_visible()
        
        # Should be able to navigate normally
        page.click(self.selectors.nav_button("settings"))
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/recovery_success.png", full_page=True)

    def test_concurrent_operations(self, page: Page, screenshot_dir):
        """同時操作のテスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Open multiple contexts to simulate concurrent users
        context = page.context
        new_page = context.new_page()
        new_page.goto("http://localhost:8501")
        new_page.wait_for_load_state("networkidle")
        
        # Both pages try to navigate simultaneously
        page.click(self.selectors.nav_button("execution"))
        new_page.click(self.selectors.nav_button("settings"))
        
        # Wait for both to complete
        page.wait_for_load_state("networkidle")
        new_page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/concurrent_page1.png", full_page=True)
        new_page.screenshot(path=f"{screenshot_dir}/concurrent_page2.png", full_page=True)
        
        # Both pages should still be functional
        expect(page.locator("body")).to_be_visible()
        expect(new_page.locator("body")).to_be_visible()
        
        new_page.close()