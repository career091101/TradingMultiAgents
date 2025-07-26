#!/usr/bin/env python3
"""
Simple browser launcher using Playwright
"""

from playwright.sync_api import sync_playwright
import time
import sys

def launch_chromium_browser(keep_alive=True, url='https://www.google.com'):
    """Launch Chromium browser
    
    Args:
        keep_alive: If True, keeps browser open until Ctrl+C. If False, returns immediately.
        url: Initial URL to navigate to
    """
    with sync_playwright() as p:
        # Launch browser with GUI
        browser = p.chromium.launch(
            headless=False,  # Show the browser window
            args=['--start-maximized']
        )
        
        # Create a new page
        page = browser.new_page()
        
        # Navigate to specified URL
        page.goto(url)
        
        print(f"Browser launched successfully!")
        print(f"Navigated to: {url}")
        
        if keep_alive:
            print("Press Ctrl+C to close the browser...")
            try:
                # Keep the browser open
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing browser...")
                browser.close()
        else:
            print("Browser is running in detached mode.")
            # Return browser and page objects for further use
            return browser, page

def launch_detached():
    """Launch browser and return immediately"""
    # Using subprocess to run in background
    import subprocess
    subprocess.Popen([sys.executable, __file__, "--keep-alive"])
    print("Browser launched in background!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--keep-alive":
        launch_chromium_browser(keep_alive=True)
    else:
        launch_detached()