#!/usr/bin/env python3
"""
ブラウザ設定の共通モジュール
Macの画面サイズに合わせた設定を提供
"""

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import platform
import subprocess
import re

def get_mac_display_resolution():
    """Macのディスプレイ解像度を取得"""
    try:
        # system_profilerコマンドでディスプレイ情報を取得
        result = subprocess.run(
            ['system_profiler', 'SPDisplaysDataType'],
            capture_output=True,
            text=True
        )
        
        # 解像度を抽出
        match = re.search(r'Resolution:\s*(\d+)\s*x\s*(\d+)', result.stdout)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return width, height
    except:
        pass
    
    # デフォルト値を返す
    return 2560, 1600

def get_chrome_options(headless=False):
    """Chrome起動オプションを取得"""
    chrome_options = Options()
    
    # 基本設定
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # Macの画面解像度を取得
    width, height = get_mac_display_resolution()
    
    # ウィンドウサイズを設定
    chrome_options.add_argument(f'--window-size={width},{height}')
    chrome_options.add_argument('--start-maximized')
    
    # ヘッドレスモード（オプション）
    if headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
    
    # その他の最適化
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    return chrome_options

def create_driver(headless=False):
    """設定済みのChromeドライバーを作成"""
    chrome_options = get_chrome_options(headless)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # プラットフォームがMacの場合、ウィンドウサイズを再設定
    if platform.system() == 'Darwin':
        width, height = get_mac_display_resolution()
        driver.set_window_size(width, height)
        driver.set_window_position(0, 0)
    
    return driver

def log_browser_info(driver):
    """ブラウザ情報をログ出力"""
    size = driver.get_window_size()
    position = driver.get_window_position()
    
    print(f"ブラウザ情報:")
    print(f"  ウィンドウサイズ: {size['width']}x{size['height']}")
    print(f"  ウィンドウ位置: ({position['x']}, {position['y']})")
    print(f"  User-Agent: {driver.execute_script('return navigator.userAgent')}")

if __name__ == "__main__":
    # テスト実行
    print("Mac画面解像度を取得中...")
    width, height = get_mac_display_resolution()
    print(f"検出された解像度: {width}x{height}")
    
    print("\nテストドライバーを作成中...")
    driver = create_driver()
    log_browser_info(driver)
    
    # テストページを開く
    driver.get("https://www.google.com")
    input("Enterキーを押すとブラウザを閉じます...")
    driver.quit()