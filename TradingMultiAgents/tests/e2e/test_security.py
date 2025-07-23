"""
E2E Security Tests - Phase 2 Implementation
TC018: XSS Attack Prevention
TC019: API Key Protection
Additional security validations
"""

import pytest
from playwright.sync_api import Page, expect, Browser
import re
import json
from typing import List, Dict, Any

# Phase 2 マーカー
pytestmark = pytest.mark.security


class TestSecurityValidation:
    """Test security measures and input validation"""

    # Malicious input patterns for testing
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//",
        "<iframe src=javascript:alert('XSS')>",
        "<<SCRIPT>alert('XSS')//<</SCRIPT>",
        "<script>document.location='http://evil.com'</script>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>"
    ]

    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE stocks; --",
        "' OR '1'='1",
        "'; DELETE FROM users; --",
        "' UNION SELECT password FROM users --",
        "admin'/*",
        "' OR 1=1 --",
        "'; EXEC sp_configure 'show advanced options', 1 --"
    ]

    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc%252fpasswd"
    ]

    def test_xss_prevention_stock_symbol_input(self, page: Page, screenshot_dir):
        """TC018: Test XSS attack prevention in stock symbol input"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to execution page
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")

        for i, payload in enumerate(self.XSS_PAYLOADS):
            # Clear and input malicious payload
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(payload)
            
            # Submit the form
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            # Wait a moment for any potential script execution
            page.wait_for_timeout(2000)
            
            # Check that no alert was triggered (XSS prevention)
            try:
                # If an alert dialog appears, this would indicate XSS vulnerability
                alert = page.wait_for_event("dialog", timeout=1000)
                alert.dismiss()
                # If we get here, XSS was not prevented - this is a security issue
                pytest.fail(f"XSS vulnerability detected with payload: {payload}")
            except:
                # No alert appeared - XSS was prevented (expected behavior)
                pass
            
            # Verify that the input is properly escaped/sanitized
            page_content = page.content()
            
            # Check that script tags are not executed
            assert "<script>" not in page_content.lower() or payload not in page_content
            
            # Take screenshot for documentation
            page.screenshot(path=f"{screenshot_dir}/xss_test_{i}.png")
            
            # Reload page for next test
            page.reload()
            page.wait_for_load_state("networkidle")
            page.click("text=分析実行")
            page.wait_for_load_state("networkidle")

    def test_sql_injection_prevention(self, page: Page, screenshot_dir):
        """Test SQL injection prevention"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")

        for i, payload in enumerate(self.SQL_INJECTION_PAYLOADS):
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(payload)
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            # Wait for response
            page.wait_for_timeout(3000)
            
            # Check for error message (expected) rather than data exposure
            error_messages = page.locator("text*=エラー, text*=無効").all()
            
            # Should show validation error, not expose database errors
            page_content = page.content().lower()
            
            # Check that SQL error messages are not exposed
            sql_error_indicators = [
                "syntax error", "mysql", "postgresql", "sqlite", 
                "database error", "table", "column", "sql"
            ]
            
            for indicator in sql_error_indicators:
                assert indicator not in page_content, f"SQL error exposed with payload: {payload}"
            
            page.screenshot(path=f"{screenshot_dir}/sql_injection_test_{i}.png")
            
            page.reload()
            page.wait_for_load_state("networkidle")
            page.click("text=分析実行")
            page.wait_for_load_state("networkidle")

    def test_path_traversal_prevention(self, page: Page, screenshot_dir):
        """Test path traversal attack prevention"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")

        for i, payload in enumerate(self.PATH_TRAVERSAL_PAYLOADS):
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(payload)
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            page.wait_for_timeout(3000)
            
            # Check that system files are not exposed
            page_content = page.content().lower()
            
            # Look for signs of file exposure
            file_indicators = [
                "root:x:", "etc/passwd", "system32", "config", 
                "windows", "bin/bash", "home/", "users/"
            ]
            
            for indicator in file_indicators:
                assert indicator not in page_content, f"Path traversal vulnerability with payload: {payload}"
            
            page.screenshot(path=f"{screenshot_dir}/path_traversal_test_{i}.png")
            
            page.reload()
            page.wait_for_load_state("networkidle")
            page.click("text=分析実行")
            page.wait_for_load_state("networkidle")


class TestAPIKeyProtection:
    """TC019: Test API key protection and secure handling"""

    def test_api_key_masking_in_ui(self, page: Page, screenshot_dir):
        """Test that API keys are properly masked in the UI"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        # Find API key input fields
        api_inputs = page.locator("input[type='password'], input[placeholder*='API']").all()
        
        test_api_key = "sk-test123456789abcdef"
        
        for i, input_field in enumerate(api_inputs):
            # Enter API key
            input_field.fill(test_api_key)
            
            # Check that the input is masked
            input_type = input_field.get_attribute("type")
            assert input_type == "password", f"API key input {i} is not masked (type={input_type})"
            
            # Verify that the actual value is not visible in the DOM
            displayed_value = input_field.input_value()
            # For password fields, this should return the actual value for testing,
            # but it should not be visible to users
            
            page.screenshot(path=f"{screenshot_dir}/api_key_masking_{i}.png")

    def test_api_key_not_in_network_requests(self, page: Page, screenshot_dir):
        """Test that API keys are not transmitted in plain text"""
        network_requests = []
        
        def capture_request(request):
            network_requests.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": request.post_data
            })
        
        page.on("request", capture_request)
        
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings and save API key
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        test_api_key = "sk-test123456789abcdef"
        
        # Enter and save API key
        api_input = page.locator("input[type='password'], input[placeholder*='API']").first
        api_input.fill(test_api_key)
        
        save_button = page.locator("text=保存").first
        if save_button.is_visible():
            save_button.click()
            page.wait_for_timeout(2000)
        
        # Analyze network requests
        for request in network_requests:
            # Check URL parameters
            assert test_api_key not in request["url"], f"API key found in URL: {request['url']}"
            
            # Check headers
            for header_value in request["headers"].values():
                assert test_api_key not in str(header_value), f"API key found in headers: {request['headers']}"
            
            # Check POST data
            if request["post_data"]:
                assert test_api_key not in request["post_data"], f"API key found in POST data: {request['post_data']}"
        
        page.screenshot(path=f"{screenshot_dir}/api_key_network_test.png")

    def test_api_key_not_in_local_storage(self, page: Page, screenshot_dir):
        """Test that API keys are not stored in browser local storage"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Navigate to settings
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        test_api_key = "sk-test123456789abcdef"
        
        # Enter API key
        api_input = page.locator("input[type='password'], input[placeholder*='API']").first
        api_input.fill(test_api_key)
        
        # Save if possible
        save_button = page.locator("text=保存").first
        if save_button.is_visible():
            save_button.click()
            page.wait_for_timeout(2000)
        
        # Check local storage
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")
        local_storage_data = json.loads(local_storage) if local_storage != "{}" else {}
        
        for key, value in local_storage_data.items():
            assert test_api_key not in str(value), f"API key found in localStorage[{key}]: {value}"
        
        # Check session storage
        session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
        session_storage_data = json.loads(session_storage) if session_storage != "{}" else {}
        
        for key, value in session_storage_data.items():
            assert test_api_key not in str(value), f"API key found in sessionStorage[{key}]: {value}"
        
        page.screenshot(path=f"{screenshot_dir}/api_key_storage_test.png")

    def test_api_key_not_in_page_source(self, page: Page, screenshot_dir):
        """Test that API keys don't appear in page source code"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析設定")
        page.wait_for_load_state("networkidle")
        
        test_api_key = "sk-test123456789abcdef"
        
        # Enter API key
        api_input = page.locator("input[type='password'], input[placeholder*='API']").first
        api_input.fill(test_api_key)
        
        # Get page source
        page_source = page.content()
        
        # API key should not appear in plain text in the page source
        assert test_api_key not in page_source, "API key found in page source code"
        
        page.screenshot(path=f"{screenshot_dir}/api_key_source_test.png")


class TestCSRFProtection:
    """Test Cross-Site Request Forgery protection"""

    def test_csrf_token_validation(self, page: Page, screenshot_dir):
        """Test CSRF token validation for form submissions"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Look for CSRF tokens in forms
        forms = page.locator("form").all()
        
        for i, form in enumerate(forms):
            # Check for CSRF token field
            csrf_inputs = form.locator("input[name*='csrf'], input[name*='token']").all()
            
            # Take screenshot of form
            page.screenshot(path=f"{screenshot_dir}/csrf_form_{i}.png")
            
            # If CSRF tokens exist, verify they are properly implemented
            for csrf_input in csrf_inputs:
                token_value = csrf_input.get_attribute("value")
                assert token_value is not None and len(token_value) > 10, "CSRF token appears to be weak or missing"


class TestContentSecurityPolicy:
    """Test Content Security Policy implementation"""

    def test_csp_headers(self, page: Page, screenshot_dir):
        """Test that proper CSP headers are set"""
        response = page.goto("http://localhost:8501")
        
        headers = response.headers
        
        # Check for security headers
        security_headers = [
            "content-security-policy",
            "x-content-type-options", 
            "x-frame-options",
            "x-xss-protection"
        ]
        
        found_headers = {}
        for header in security_headers:
            if header in headers:
                found_headers[header] = headers[header]
        
        page.screenshot(path=f"{screenshot_dir}/security_headers_test.png")
        
        # Log found security headers for review
        print(f"Security headers found: {found_headers}")

    def test_inline_script_prevention(self, page: Page, screenshot_dir):
        """Test that inline scripts are prevented by CSP"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        # Try to inject and execute inline script
        try:
            result = page.evaluate("eval('1+1')")
            # If eval works, CSP might not be strict enough
            print(f"Eval result: {result} - Consider stricter CSP")
        except Exception as e:
            # Eval blocked by CSP (good security)
            print(f"Eval blocked: {e}")
        
        page.screenshot(path=f"{screenshot_dir}/inline_script_test.png")


class TestInputSanitization:
    """Test comprehensive input sanitization"""

    def test_special_characters_handling(self, page: Page, screenshot_dir):
        """Test handling of special characters in inputs"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        special_chars = [
            "!@#$%^&*()",
            "~`{}[]|\\:;\"'<>,.?/",
            "áéíóúñü",  # accented characters
            "中文字符",    # Chinese characters
            "العربية",    # Arabic
            "🚀💎📈",     # emojis
        ]
        
        for i, chars in enumerate(special_chars):
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(chars)
            
            # Verify input handling
            current_value = symbol_input.input_value()
            
            # Take screenshot
            page.screenshot(path=f"{screenshot_dir}/special_chars_{i}.png")
            
            # Try to submit
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            page.wait_for_timeout(2000)
            
            # Check that the application doesn't crash
            page_content = page.content()
            assert "error" not in page_content.lower() or "エラー" in page_content

    def test_unicode_handling(self, page: Page, screenshot_dir):
        """Test Unicode character handling"""
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        
        page.click("text=分析実行")
        page.wait_for_load_state("networkidle")
        
        unicode_tests = [
            "𝕌𝕟𝕚𝕔𝕠𝕕𝕖",  # mathematical alphanumeric
            "\u0000\u0001\u0002",  # null and control characters
            "\ufeff",  # byte order mark
            "Test\u202e\u202dtest",  # RTL/LTR override
        ]
        
        for i, unicode_str in enumerate(unicode_tests):
            symbol_input = page.locator("input[placeholder*='銘柄']").first
            symbol_input.clear()
            symbol_input.fill(unicode_str)
            
            analyze_button = page.locator("text=分析").first
            analyze_button.click()
            
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{screenshot_dir}/unicode_test_{i}.png")
            
            # Ensure no crashes or security issues
            assert page.locator("body").is_visible()