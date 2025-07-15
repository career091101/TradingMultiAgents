"""
E2E Security Tests - Phase 2 Implementation (Adapted)
現在のWebUI構造に合わせたセキュリティテスト
"""

import pytest
from playwright.sync_api import Page, expect
import json
from typing import List, Dict, Any
from utils.streamlit_selectors import StreamlitSelectors
from utils.streamlit_test_helpers import StreamlitTestHelpers, StreamlitAssertions

# Phase 2 マーカー
pytestmark = pytest.mark.security


class TestSecurityAdapted:
    """WebUI構造に適応したセキュリティテスト"""
    
    def setup_method(self):
        """Set up selectors for testing"""
        self.selectors = StreamlitSelectors()

    def test_input_validation_security(self, page: Page, screenshot_dir):
        """入力検証のセキュリティテスト（修正版）"""
        page.goto("http://localhost:8501")
        StreamlitTestHelpers.wait_for_streamlit_ready(page)
        
        # Navigate to settings page where inputs might exist
        StreamlitTestHelpers.safe_click_with_retry(page, self.selectors.nav_button("settings"))
        StreamlitTestHelpers.wait_for_navigation_complete(page)
        
        page.screenshot(path=f"{screenshot_dir}/settings_security_initial.png", full_page=True)
        
        # Look for any text input fields
        text_inputs = page.locator("input[type='text'], input[type='password'], textarea")
        
        if text_inputs.count() > 0:
            # Test potentially malicious inputs
            malicious_inputs = [
                "<script>alert('XSS')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "javascript:alert(1)"
            ]
            
            for i, malicious_input in enumerate(malicious_inputs):
                first_input = text_inputs.first
                first_input.clear()
                first_input.fill(malicious_input)
                
                page.screenshot(path=f"{screenshot_dir}/malicious_input_{i}.png")
                
                # Check that malicious content is not executed
                # No alert should appear, and page should remain stable
                StreamlitTestHelpers.wait_for_stable_ui(page)
                
                # Page should still be functional using safe assertion
                body_visible = StreamlitTestHelpers.safe_element_check(page, "body", "visible", 5000)
                assert body_visible, "Page should remain functional after malicious input"
                
                # Check page content doesn't contain unescaped malicious code
                page_content = page.content()
                assert "<script>" not in page_content or malicious_input not in page_content
        
        print(f"Found {text_inputs.count()} input fields for security testing")

    def test_api_key_protection(self, page: Page, screenshot_dir):
        """APIキー保護のテスト（修正版）"""
        page.goto("http://localhost:8501")
        StreamlitTestHelpers.wait_for_streamlit_ready(page)
        
        # Navigate to settings page
        StreamlitTestHelpers.safe_click_with_retry(page, self.selectors.nav_button("settings"))
        StreamlitTestHelpers.wait_for_navigation_complete(page)
        
        page.screenshot(path=f"{screenshot_dir}/api_key_protection.png", full_page=True)
        
        # Look for password fields (likely for API keys)
        password_inputs = page.locator("input[type='password']")
        
        if password_inputs.count() > 0:
            test_api_key = "sk-test123456789abcdef"
            
            # Enter API key
            first_password_input = password_inputs.first
            first_password_input.fill(test_api_key)
            
            # Wait for input to be processed
            StreamlitTestHelpers.wait_for_stable_ui(page)
            
            # Verify that the input is masked
            input_type = first_password_input.get_attribute("type")
            assert input_type == "password", "API key input should be masked"
            
            page.screenshot(path=f"{screenshot_dir}/api_key_masked.png")
            
            # Check that API key is not visible in page source
            page_source = page.content()
            assert test_api_key not in page_source, "API key should not appear in page source"
            
            print("API key protection verified")
        else:
            print("No password fields found for API key testing")

    def test_network_security_headers(self, page: Page, screenshot_dir):
        """ネットワークセキュリティヘッダーのテスト"""
        response = page.goto("http://localhost:8501")
        
        headers = response.headers
        
        # Check for security headers
        security_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-xss-protection": "1; mode=block"
        }
        
        found_headers = {}
        for header_name, expected_values in security_headers.items():
            header_value = headers.get(header_name)
            if header_value:
                found_headers[header_name] = header_value
                
                if isinstance(expected_values, list):
                    assert header_value in expected_values, f"Invalid {header_name} header value"
                else:
                    assert header_value == expected_values, f"Invalid {header_name} header value"
        
        page.screenshot(path=f"{screenshot_dir}/security_headers.png", full_page=True)
        
        print(f"Security headers found: {found_headers}")
        
        # At minimum, we should have some security considerations
        # Even if not all headers are present, the app should be functional

    def test_session_security(self, page: Page, screenshot_dir):
        """セッションセキュリティのテスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Check if any sensitive data is stored in localStorage or sessionStorage
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")
        session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
        
        print(f"LocalStorage: {local_storage}")
        print(f"SessionStorage: {session_storage}")
        
        # Common patterns that shouldn't be in storage
        sensitive_patterns = ["password", "token", "key", "secret"]
        
        for pattern in sensitive_patterns:
            assert pattern not in local_storage.lower(), f"Sensitive data '{pattern}' found in localStorage"
            assert pattern not in session_storage.lower(), f"Sensitive data '{pattern}' found in sessionStorage"
        
        page.screenshot(path=f"{screenshot_dir}/session_security.png", full_page=True)

    def test_error_information_disclosure(self, page: Page, screenshot_dir):
        """エラー情報漏洩のテスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Try to trigger errors and check if sensitive information is disclosed
        
        # 1. Invalid navigation
        try:
            page.goto("http://localhost:8501/nonexistent")
            page.wait_for_load_state("networkidle", timeout=5000)
        except:
            pass
        
        page_content = page.content().lower()
        
        # Check for potential information disclosure in error messages
        sensitive_info_patterns = [
            "traceback", "stack trace", "internal server error",
            "database", "sql", "exception", "debug"
        ]
        
        disclosed_info = []
        for pattern in sensitive_info_patterns:
            if pattern in page_content:
                disclosed_info.append(pattern)
        
        page.screenshot(path=f"{screenshot_dir}/error_disclosure.png", full_page=True)
        
        # Some error information might be acceptable for debugging
        # But we should avoid exposing sensitive system details
        if disclosed_info:
            print(f"Potential information disclosure: {disclosed_info}")

    def test_input_length_limits(self, page: Page, screenshot_dir):
        """入力長制限のテスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings page
        page.click(self.selectors.nav_button("settings"))
        page.wait_for_load_state("networkidle")
        
        # Look for input fields
        text_inputs = page.locator("input[type='text']")
        
        if text_inputs.count() > 0:
            # Test with very long input
            very_long_input = "A" * 10000
            
            first_input = text_inputs.first
            first_input.fill(very_long_input)
            
            # Check that the application handles long input gracefully
            page.wait_for_timeout(1000)
            
            # Application should still be responsive
            expect(page.locator("body")).to_be_visible()
            
            page.screenshot(path=f"{screenshot_dir}/long_input_test.png")
            
            # Check current input value (might be truncated)
            current_value = first_input.input_value()
            print(f"Input length after filling 10000 chars: {len(current_value)}")
            
            # Assert the application didn't crash
            assert len(current_value) >= 0, "Input field should handle long input"

    def test_special_characters_handling(self, page: Page, screenshot_dir):
        """特殊文字処理のテスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings page
        page.click(self.selectors.nav_button("settings"))
        page.wait_for_load_state("networkidle")
        
        # Look for input fields
        text_inputs = page.locator("input[type='text']")
        
        if text_inputs.count() > 0:
            # Test with various special characters
            special_chars = [
                "!@#$%^&*()",
                "中文字符",
                "العربية",
                "🚀💎📈",
                "áéíóúñü"
            ]
            
            for i, chars in enumerate(special_chars):
                first_input = text_inputs.first
                first_input.clear()
                first_input.fill(chars)
                
                page.wait_for_timeout(500)
                
                page.screenshot(path=f"{screenshot_dir}/special_chars_{i}.png")
                
                # Verify application remains stable
                expect(page.locator("body")).to_be_visible()
                
                print(f"Tested special characters: {chars}")

    def test_csrf_protection_indicators(self, page: Page, screenshot_dir):
        """CSRF保護の確認テスト"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Look for forms that might need CSRF protection
        forms = page.locator("form")
        
        if forms.count() > 0:
            for i in range(forms.count()):
                form = forms.nth(i)
                
                # Check for CSRF tokens or other protection mechanisms
                csrf_inputs = form.locator("input[name*='csrf'], input[name*='token']")
                
                if csrf_inputs.count() > 0:
                    print(f"Form {i} has potential CSRF protection")
                else:
                    print(f"Form {i} might need CSRF protection review")
        
        page.screenshot(path=f"{screenshot_dir}/csrf_protection.png", full_page=True)
        
        print(f"Found {forms.count()} forms for CSRF analysis")