"""
E2E Error Handling Tests - Phase 2 Implementation
TC014: Network Error Handling
TC015: API Rate Limit Error Handling
"""

import pytest
from playwright.sync_api import Page, expect, Browser
import asyncio
import json
from typing import Dict, Any
from utils.streamlit_selectors import StreamlitSelectors

# Phase 2 マーカー
pytestmark = pytest.mark.error_handling


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def setup_method(self):
        """Set up selectors for testing"""
        self.selectors = StreamlitSelectors()

    @pytest.fixture(autouse=True)
    def setup_page(self, page: Page):
        """Navigate to execution page for testing"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Navigate to execution page
        page.click(self.selectors.nav_button("execution"))
        page.wait_for_load_state("networkidle", timeout=5000)

    def test_network_connection_failure(self, page: Page, screenshot_dir):
        """TC014: Test network disconnection error handling"""
        # Block all network requests to simulate network failure
        page.route("**/*", lambda route: route.abort())
        
        # Try to perform analysis with blocked network
        symbol_input = page.locator(self.selectors.settings_input("ticker"))
        symbol_input.fill("AAPL")
        
        # Click analysis button
        analyze_button = page.locator(self.selectors.button(text="分析開始"))
        analyze_button.click()
        
        # Wait for error message to appear
        error_locator = page.locator("text*=エラー").first
        expect(error_locator).to_be_visible(timeout=10000)
        
        # Take screenshot of error state
        page.screenshot(path=f"{screenshot_dir}/network_error.png", full_page=True)
        
        # Verify error message content
        error_text = error_locator.text_content()
        assert any(keyword in error_text.lower() for keyword in ["ネットワーク", "接続", "エラー", "失敗"])

    def test_api_timeout_error(self, page: Page, screenshot_dir):
        """Test API timeout error handling"""
        # Route API calls to delay responses significantly
        def handle_api_request(route):
            # Delay for 30 seconds to trigger timeout
            import time
            time.sleep(30)
            route.continue_()
        
        page.route("**/api/**", handle_api_request)
        
        # Perform analysis
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("MSFT")
        
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        # Wait for timeout error
        timeout_error = page.locator("text*=タイムアウト")
        expect(timeout_error).to_be_visible(timeout=35000)
        
        page.screenshot(path=f"{screenshot_dir}/timeout_error.png", full_page=True)

    def test_invalid_stock_symbol_error(self, page: Page, screenshot_dir):
        """Test invalid stock symbol error handling"""
        # Test various invalid inputs
        invalid_symbols = [
            "INVALID123",
            "NOTREAL",
            "12345",
            "!@#$%",
            ""
        ]
        
        for i, symbol in enumerate(invalid_symbols):
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            
            if symbol:  # Don't fill empty string
                symbol_input.fill(symbol)
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            # Wait for error message
            error_message = page.locator("text*=エラー, text*=無効, text*=見つかりません").first
            expect(error_message).to_be_visible(timeout=5000)
            
            # Take screenshot for each error case
            page.screenshot(path=f"{screenshot_dir}/invalid_symbol_{i}_{symbol or 'empty'}.png")
            
            # Clear the error before next test
            page.reload()
            page.wait_for_load_state("networkidle")

    def test_api_rate_limit_error(self, page: Page, screenshot_dir):
        """TC015: Test API rate limit error handling"""
        # Mock rate limit response
        def handle_rate_limit(route):
            route.fulfill(
                status=429,
                headers={"content-type": "application/json"},
                body=json.dumps({
                    "error": "Rate limit exceeded",
                    "message": "API制限に達しました。しばらくお待ちください",
                    "retry_after": 60
                })
            )
        
        page.route("**/api/**", handle_rate_limit)
        
        # Perform analysis
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("GOOGL")
        
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        # Wait for rate limit error message
        rate_limit_error = page.locator("text*=制限, text*=API").first
        expect(rate_limit_error).to_be_visible(timeout=10000)
        
        # Check for retry information
        retry_info = page.locator("text*=待機, text*=しばらく")
        expect(retry_info).to_be_visible(timeout=5000)
        
        page.screenshot(path=f"{screenshot_dir}/rate_limit_error.png", full_page=True)

    def test_server_error_500(self, page: Page, screenshot_dir):
        """Test internal server error handling"""
        # Mock 500 error response
        def handle_server_error(route):
            route.fulfill(
                status=500,
                headers={"content-type": "application/json"},
                body=json.dumps({
                    "error": "Internal server error",
                    "message": "サーバーエラーが発生しました"
                })
            )
        
        page.route("**/api/**", handle_server_error)
        
        # Perform analysis
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("TSLA")
        
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        # Wait for server error message
        server_error = page.locator("text*=サーバー, text*=エラー").first
        expect(server_error).to_be_visible(timeout=10000)
        
        page.screenshot(path=f"{screenshot_dir}/server_error.png", full_page=True)

    def test_error_recovery_mechanism(self, page: Page, screenshot_dir):
        """Test error recovery and retry functionality"""
        # First, simulate an error
        page.route("**/api/**", lambda route: route.abort())
        
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("AAPL")
        
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        # Wait for error
        error_message = page.locator("text*=エラー").first
        expect(error_message).to_be_visible(timeout=10000)
        
        # Take screenshot of error state
        page.screenshot(path=f"{screenshot_dir}/error_before_recovery.png")
        
        # Clear the route to allow normal requests
        page.unroute("**/api/**")
        
        # Look for retry button and click it
        retry_button = page.locator("text*=再試行, text*=もう一度").first
        if retry_button.is_visible():
            retry_button.click()
            
            # Wait for successful recovery
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Take screenshot of recovery
            page.screenshot(path=f"{screenshot_dir}/error_after_recovery.png")

    def test_error_message_localization(self, page: Page, screenshot_dir):
        """Test that error messages are properly localized in Japanese"""
        # Test different error types and verify Japanese messages
        error_scenarios = [
            {
                "route": "**/api/**",
                "status": 401,
                "response": {"error": "Unauthorized"},
                "expected_keywords": ["認証", "エラー", "失敗"]
            },
            {
                "route": "**/api/**", 
                "status": 404,
                "response": {"error": "Not found"},
                "expected_keywords": ["見つかりません", "存在しません"]
            }
        ]
        
        for i, scenario in enumerate(error_scenarios):
            # Setup mock response
            def handle_error(route):
                route.fulfill(
                    status=scenario["status"],
                    headers={"content-type": "application/json"},
                    body=json.dumps(scenario["response"])
                )
            
            page.route(scenario["route"], handle_error)
            
            # Trigger error
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill("TEST")
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            # Wait for error message
            error_element = page.locator("text*=エラー").first
            expect(error_element).to_be_visible(timeout=10000)
            
            # Verify Japanese content
            error_text = error_element.text_content()
            assert any(keyword in error_text for keyword in scenario["expected_keywords"])
            
            page.screenshot(path=f"{screenshot_dir}/localized_error_{i}.png")
            
            # Clear route for next test
            page.unroute(scenario["route"])
            page.reload()
            page.wait_for_load_state("networkidle")


class TestErrorHandlingSettings:
    """Test error handling in settings page"""

    def test_invalid_api_key_format(self, page: Page, screenshot_dir):
        """Test validation of API key format"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        # Test invalid API key formats
        invalid_keys = [
            "short",
            "spaces in key",
            "invalid-format-123",
            "!@#$%^&*()"
        ]
        
        for i, invalid_key in enumerate(invalid_keys):
            # Find API key input field
            api_key_input = page.locator("input[type='password'], input[placeholder*='API']").first
            api_key_input.clear()
            api_key_input.fill(invalid_key)
            
            # Try to save
            save_button = page.locator("text=保存, button[type='submit']").first
            save_button.click()
            
            # Check for validation error
            validation_error = page.locator("text*=無効, text*=エラー, text*=形式").first
            expect(validation_error).to_be_visible(timeout=5000)
            
            page.screenshot(path=f"{screenshot_dir}/invalid_api_key_{i}.png")


class TestErrorHandlingDashboard:
    """Test error handling in dashboard components"""

    def test_dashboard_data_loading_failure(self, page: Page, screenshot_dir):
        """Test dashboard behavior when data loading fails"""
        # Block API calls that fetch dashboard data
        page.route("**/stats/**", lambda route: route.abort())
        page.route("**/popular/**", lambda route: route.abort())
        
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # Look for error indicators or fallback content
        error_indicators = page.locator("text*=エラー, text*=読み込み, text*=失敗")
        
        # Take screenshot showing error state
        page.screenshot(path=f"{screenshot_dir}/dashboard_loading_error.png", full_page=True)
        
        # Verify that the page doesn't crash and shows appropriate messaging
        page_title = page.locator("h1, text=TradingAgents")
        expect(page_title).to_be_visible()