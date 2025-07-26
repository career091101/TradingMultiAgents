#!/usr/bin/env python3
"""
Browser launcher using Selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def launch_chrome_selenium():
    """Launch Chrome browser using Selenium"""
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    try:
        # Try to launch Chrome
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.google.com")
        
        print("Chrome browser launched successfully with Selenium!")
        print("Press Ctrl+C to close the browser...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")
            driver.quit()
            
    except Exception as e:
        print(f"Error launching Chrome with Selenium: {e}")
        print("\nTrying with Safari driver instead...")
        
        try:
            # On macOS, Safari driver is often available
            driver = webdriver.Safari()
            driver.get("https://www.google.com")
            
            print("Safari browser launched successfully!")
            print("Press Ctrl+C to close the browser...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing browser...")
                driver.quit()
                
        except Exception as safari_error:
            print(f"Error launching Safari: {safari_error}")
            print("\nPlease install Chrome driver or enable Safari developer mode.")

if __name__ == "__main__":
    launch_chrome_selenium()