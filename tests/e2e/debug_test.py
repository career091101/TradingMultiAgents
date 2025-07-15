"""Debug test to check WebUI content"""
import pytest
from playwright.sync_api import Page
import time


def test_debug_webui(page: Page, screenshot_path):
    """Debug test to check what's actually on the page"""
    # Take screenshot immediately after page loads
    page.screenshot(path=screenshot_path("debug_initial"))
    
    # Wait a bit for any dynamic content
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    
    # Take another screenshot
    page.screenshot(path=screenshot_path("debug_after_wait"), full_page=True)
    
    # Print page content for debugging
    print("\n=== PAGE CONTENT ===")
    print(page.content()[:2000])  # First 2000 chars
    
    # Check for common elements
    elements_to_check = [
        ('h1', 'H1 elements'),
        ('h2', 'H2 elements'),
        ('button', 'Buttons'),
        ('[data-testid="stSidebar"]', 'Sidebar'),
        ('[data-testid="stButton"]', 'Streamlit buttons'),
        ('[data-testid="stMetric"]', 'Metrics'),
        ('[data-testid="stMarkdown"]', 'Markdown elements'),
    ]
    
    for selector, name in elements_to_check:
        elements = page.locator(selector).all()
        if elements:
            print(f"\n{name} found: {len(elements)}")
            for i, elem in enumerate(elements[:3]):  # First 3
                try:
                    text = elem.text_content()
                    print(f"  {i+1}: {text[:100] if text else 'No text'}")
                except:
                    print(f"  {i+1}: Unable to get text")
    
    # Check for text content
    text_to_check = ["ダッシュボード", "分析設定", "TradingAgents", "Dashboard", "Settings"]
    for text in text_to_check:
        if text in page.content():
            print(f"\nFound text: '{text}'")
    
    # Pause to allow manual inspection if needed
    time.sleep(2)