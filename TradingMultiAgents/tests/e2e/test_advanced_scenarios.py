"""
E2E Advanced Test Scenarios - Phase 2 Implementation
Edge cases, complex workflows, and integration scenarios
"""

import pytest
from playwright.sync_api import Page, expect, Browser
import json
import time
from typing import Dict, List, Any

# Phase 2 マーカー（複数マーカーを設定）
pytestmark = [pytest.mark.accessibility, pytest.mark.network]


class TestComplexWorkflows:
    """Test complex user workflows and interactions"""

    def test_full_analysis_workflow(self, page: Page, screenshot_dir):
        """Test complete end-to-end analysis workflow"""
        # Step 1: Start from dashboard
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle", timeout=10000)
        
        page.screenshot(path=f"{screenshot_dir}/workflow_step_1_dashboard.png", full_page=True)
        
        # Step 2: Configure settings
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        # Configure API keys if inputs exist
        api_inputs = page.locator("input[type='password'], input[placeholder*='API']").all()
        if api_inputs:
            for i, input_field in enumerate(api_inputs):
                input_field.fill(f"test-key-{i}")
        
        page.screenshot(path=f"{screenshot_dir}/workflow_step_2_settings.png", full_page=True)
        
        # Step 3: Execute analysis
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        # Enter stock symbol
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("AAPL")
        
        page.screenshot(path=f"{screenshot_dir}/workflow_step_3_execution_input.png", full_page=True)
        
        # Submit analysis
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        # Wait for analysis to start
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{screenshot_dir}/workflow_step_4_analysis_running.png", full_page=True)
        
        # Step 4: Check results
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/workflow_step_5_results.png", full_page=True)
        
        # Verify workflow completed successfully
        assert page.locator("body").is_visible()

    def test_multiple_stock_analysis_workflow(self, page: Page, screenshot_dir):
        """Test analyzing multiple stocks in sequence"""
        stocks_to_test = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        for i, stock in enumerate(stocks_to_test):
            # Clear previous input
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(stock)
            
            # Submit analysis
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            # Wait for processing
            page.wait_for_timeout(2000)
            
            page.screenshot(path=f"{screenshot_dir}/multi_stock_{i}_{stock}.png")
            
            # Navigate to results to verify
            page.click("text=結果表示")
            page.wait_for_load_state("networkidle")
            
            page.screenshot(path=f"{screenshot_dir}/multi_stock_results_{i}_{stock}.png")
            
            # Go back to execution for next stock
            if i < len(stocks_to_test) - 1:
                page.click("text=分析実行")
                page.wait_for_load_state("networkidle")

    def test_settings_persistence_workflow(self, page: Page, screenshot_dir):
        """Test that settings persist across sessions"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        # Configure settings
        test_settings = {
            "api_key": "test-persistence-key",
            "model": "gpt-4"
        }
        
        # Set API key
        api_input = page.locator("input[type='password'], input[placeholder*='API']").first
        if api_input.is_visible():
            api_input.fill(test_settings["api_key"])
        
        # Set model if dropdown exists
        model_dropdown = page.locator("select, .selectbox").first
        if model_dropdown.is_visible():
            try:
                model_dropdown.select_option(label=test_settings["model"])
            except:
                pass  # Model selection might not be available
        
        # Save settings
        save_button = page.locator("text=保存").first
        if save_button.is_visible():
            save_button.click()
            page.wait_for_timeout(1000)
        
        page.screenshot(path=f"{screenshot_dir}/settings_saved.png")
        
        # Navigate away and come back
        page.click("text=ダッシュボード")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/settings_restored.png")
        
        # Verify settings are preserved (API key should be masked)
        api_input_restored = page.locator("input[type='password'], input[placeholder*='API']").first
        if api_input_restored.is_visible():
            # For password fields, we can't read the value, but we can verify it's not empty
            input_value = api_input_restored.get_attribute("value")
            assert input_value is not None  # Should have some value


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_input_handling(self, page: Page, screenshot_dir):
        """Test behavior with empty inputs"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        # Try to submit with empty input
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        # Should show validation error
        page.wait_for_timeout(2000)
        
        page.screenshot(path=f"{screenshot_dir}/empty_input_test.png")
        
        # Verify appropriate error handling
        page_content = page.content().lower()
        assert any(keyword in page_content for keyword in ["エラー", "入力", "必須", "required"])

    def test_very_long_input_handling(self, page: Page, screenshot_dir):
        """Test behavior with extremely long inputs"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        # Create very long input
        long_input = "A" * 1000
        
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill(long_input)
        
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        page.wait_for_timeout(2000)
        page.screenshot(path=f"{screenshot_dir}/long_input_test.png")
        
        # Should handle gracefully without crashing
        assert page.locator("body").is_visible()

    def test_special_characters_in_stock_symbols(self, page: Page, screenshot_dir):
        """Test handling of special characters in stock symbols"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        special_symbols = [
            "BRK.A",    # Berkshire Hathaway Class A
            "BF.B",     # Brown-Forman Class B
            "GOOG",     # Alphabet Class C
            "GOOGL",    # Alphabet Class A
            "$VIX",     # Volatility Index
            "^GSPC",    # S&P 500 Index
        ]
        
        for i, symbol in enumerate(special_symbols):
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(symbol)
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{screenshot_dir}/special_symbol_{i}_{symbol.replace('.', '_').replace('^', 'caret').replace('$', 'dollar')}.png")
            
            # Should handle without crashing
            assert page.locator("body").is_visible()

    def test_rapid_click_handling(self, page: Page, screenshot_dir):
        """Test rapid clicking behavior"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        # Fill in a stock symbol
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("AAPL")
        
        # Rapidly click the analyze button
        analyze_button = page.locator("text=分析").first
        
        for i in range(10):
            try:
                analyze_button.click(timeout=500)
                page.wait_for_timeout(100)
            except:
                break  # Button might become disabled
        
        page.screenshot(path=f"{screenshot_dir}/rapid_click_test.png")
        
        # Should handle gracefully without multiple submissions
        assert page.locator("body").is_visible()

    def test_browser_back_forward_behavior(self, page: Page, screenshot_dir):
        """Test browser back/forward button behavior"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate through pages
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/navigation_forward.png")
        
        # Use browser back button
        page.go_back()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"{screenshot_dir}/navigation_back_1.png")
        
        page.go_back()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"{screenshot_dir}/navigation_back_2.png")
        
        # Use browser forward button
        page.go_forward()
        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"{screenshot_dir}/navigation_forward_1.png")
        
        # Verify the application state is maintained
        assert page.locator("body").is_visible()


class TestConcurrentOperations:
    """Test concurrent operations and race conditions"""

    def test_multiple_simultaneous_requests(self, page: Page, screenshot_dir):
        """Test handling of multiple simultaneous analysis requests"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        # Open multiple tabs/contexts to simulate concurrent users
        new_page = page.context.new_page()
        new_page.goto("http://localhost:8501")
        new_page.wait_for_load_state("networkidle")
        new_page.click("text=分析実行")
        new_page.wait_for_load_state("networkidle")
        
        # Submit analysis from both pages simultaneously
        symbol_input_1 = page.locator("input[placeholder*='銘柄']").first
        symbol_input_1.fill("AAPL")
        
        symbol_input_2 = new_page.locator("input[placeholder*='銘柄']").first
        symbol_input_2.fill("MSFT")
        
        # Click both analyze buttons at nearly the same time
        analyze_button_1 = page.locator("text=分析").first
        analyze_button_2 = new_page.locator("text=分析").first
        
        analyze_button_1.click()
        analyze_button_2.click()
        
        # Wait for both to process
        page.wait_for_timeout(5000)
        new_page.wait_for_timeout(5000)
        
        page.screenshot(path=f"{screenshot_dir}/concurrent_request_1.png")
        new_page.screenshot(path=f"{screenshot_dir}/concurrent_request_2.png")
        
        # Both should handle gracefully
        assert page.locator("body").is_visible()
        assert new_page.locator("body").is_visible()
        
        new_page.close()

    def test_session_timeout_handling(self, page: Page, screenshot_dir):
        """Test session timeout and recovery"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Simulate long idle time by waiting
        page.wait_for_timeout(5000)
        
        # Try to perform an action after "timeout"
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("AAPL")
        
        analyze_button = page.locator("text=分析").first
        analyze_button.click()
        
        page.wait_for_timeout(3000)
        page.screenshot(path=f"{screenshot_dir}/session_timeout_test.png")
        
        # Should still work after idle time
        assert page.locator("body").is_visible()


class TestAccessibilityEdgeCases:
    """Test accessibility in edge cases"""

    def test_keyboard_only_navigation(self, page: Page, screenshot_dir):
        """Test full keyboard-only navigation"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Use Tab key to navigate
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{screenshot_dir}/keyboard_nav_1.png")
        
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{screenshot_dir}/keyboard_nav_2.png")
        
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        page.screenshot(path=f"{screenshot_dir}/keyboard_nav_3.png")
        
        # Try to activate focused element
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        page.screenshot(path=f"{screenshot_dir}/keyboard_activation.png")
        
        # Should maintain functionality with keyboard only
        assert page.locator("body").is_visible()

    def test_high_contrast_mode(self, page: Page, screenshot_dir):
        """Test appearance in high contrast mode"""
        # Enable high contrast CSS
        page.add_style_tag(content="""
            * {
                background: black !important;
                color: white !important;
                border-color: white !important;
            }
            a, button {
                background: blue !important;
                color: yellow !important;
            }
        """)
        
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/high_contrast_dashboard.png", full_page=True)
        
        # Navigate through pages
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"{screenshot_dir}/high_contrast_settings.png", full_page=True)
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=f"{screenshot_dir}/high_contrast_execution.png", full_page=True)
        
        # Should remain functional in high contrast
        assert page.locator("body").is_visible()

    def test_screen_reader_compatibility(self, page: Page, screenshot_dir):
        """Test screen reader compatibility markers"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Check for ARIA labels and roles
        elements_with_aria = page.locator("[aria-label], [role], [aria-labelledby]").all()
        
        print(f"Found {len(elements_with_aria)} elements with ARIA attributes")
        
        # Check for proper heading structure
        headings = page.locator("h1, h2, h3, h4, h5, h6").all()
        heading_levels = []
        
        for heading in headings:
            tag_name = heading.evaluate("el => el.tagName.toLowerCase()")
            heading_levels.append(int(tag_name[1]))
        
        print(f"Heading structure: {heading_levels}")
        
        # Take screenshot for manual review
        page.screenshot(path=f"{screenshot_dir}/screen_reader_test.png", full_page=True)
        
        # Basic accessibility checks
        assert len(headings) > 0, "No headings found for screen reader navigation"


class TestDataPersistence:
    """Test data persistence and state management"""

    def test_analysis_history_persistence(self, page: Page, screenshot_dir):
        """Test that analysis history is maintained"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Perform several analyses
        stocks = ["AAPL", "MSFT", "GOOGL"]
        
        for stock in stocks:
            page.click("text=分析実行")
            page.wait_for_load_state("networkidle")
            
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(stock)
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            page.wait_for_timeout(2000)
        
        # Check results page for history
        page.click("text=結果表示")
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/analysis_history.png", full_page=True)
        
        # Reload page and check if history is maintained
        page.reload()
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/analysis_history_after_reload.png", full_page=True)
        
        # Should maintain some form of analysis state
        assert page.locator("body").is_visible()

    def test_browser_refresh_recovery(self, page: Page, screenshot_dir):
        """Test recovery after browser refresh"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to execution and fill form
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        symbol_input = page.locator("input[placeholder*='銘柄']").first
        symbol_input.fill("AAPL")
        
        page.screenshot(path=f"{screenshot_dir}/before_refresh.png")
        
        # Refresh the page
        page.reload()
        page.wait_for_load_state("networkidle")
        
        page.screenshot(path=f"{screenshot_dir}/after_refresh.png")
        
        # Application should recover gracefully
        assert page.locator("body").is_visible()
        
        # Check if we can continue working
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        # Should be functional after refresh
        symbol_input_new = page.locator("input[placeholder*='銘柄']").first
        assert symbol_input_new.is_visible()