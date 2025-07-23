"""
E2E tests for WebUI authentication
"""

import pytest
from playwright.sync_api import Page, expect
import time
import os


class TestWebUIAuthentication:
    """Test WebUI authentication flow"""
    
    @pytest.fixture(scope="function")
    def webui_url(self):
        """Get WebUI URL from environment or use default"""
        return os.getenv("WEBUI_URL", "http://localhost:8501")
    
    def test_login_required(self, page: Page, webui_url: str):
        """Test that login is required to access the app"""
        # Navigate to the app
        page.goto(webui_url)
        
        # Should see login page
        expect(page.locator("text=Trading Agents WebUI - Login")).to_be_visible()
        expect(page.locator("text=Please login to continue")).to_be_visible()
        
        # Should have username and password fields
        expect(page.locator("input[aria-label='Username']")).to_be_visible()
        expect(page.locator("input[aria-label='Password']")).to_be_visible()
        
        # Should have login button
        expect(page.locator("button:has-text('Login')")).to_be_visible()
    
    def test_login_with_valid_credentials(self, page: Page, webui_url: str):
        """Test login with valid credentials"""
        # Navigate to the app
        page.goto(webui_url)
        
        # Fill in credentials
        page.fill("input[aria-label='Username']", "user")
        page.fill("input[aria-label='Password']", "user123")
        
        # Click login
        page.click("button:has-text('Login')")
        
        # Wait for navigation
        page.wait_for_timeout(2000)
        
        # Should be logged in and see main UI
        expect(page.locator("text=TradingAgents WebUI")).to_be_visible()
        expect(page.locator("text=User: user")).to_be_visible()
        expect(page.locator("text=Role: user")).to_be_visible()
        
        # Should have logout button
        expect(page.locator("button:has-text('Logout')")).to_be_visible()
    
    def test_login_with_invalid_credentials(self, page: Page, webui_url: str):
        """Test login with invalid credentials"""
        # Navigate to the app
        page.goto(webui_url)
        
        # Fill in wrong credentials
        page.fill("input[aria-label='Username']", "wronguser")
        page.fill("input[aria-label='Password']", "wrongpass")
        
        # Click login
        page.click("button:has-text('Login')")
        
        # Should see error message
        expect(page.locator("text=Invalid username or password")).to_be_visible()
        
        # Should still be on login page
        expect(page.locator("text=Please login to continue")).to_be_visible()
    
    def test_admin_login_sees_env_vars(self, page: Page, webui_url: str):
        """Test that admin can see environment variables"""
        # Navigate to the app
        page.goto(webui_url)
        
        # Login as admin
        page.fill("input[aria-label='Username']", "admin")
        page.fill("input[aria-label='Password']", "admin123")
        page.click("button:has-text('Login')")
        
        # Wait for navigation
        page.wait_for_timeout(2000)
        
        # Should see admin role
        expect(page.locator("text=Role: admin")).to_be_visible()
        
        # Admin should see environment settings
        expect(page.locator("text=環境設定")).to_be_visible()
    
    def test_logout(self, page: Page, webui_url: str):
        """Test logout functionality"""
        # Navigate and login
        page.goto(webui_url)
        page.fill("input[aria-label='Username']", "user")
        page.fill("input[aria-label='Password']", "user123")
        page.click("button:has-text('Login')")
        
        # Wait for login
        page.wait_for_timeout(2000)
        
        # Click logout
        page.click("button:has-text('Logout')")
        
        # Should be back on login page
        expect(page.locator("text=Please login to continue")).to_be_visible()
        
        # Should not see user info anymore
        expect(page.locator("text=User: user")).not_to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])