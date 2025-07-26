#!/usr/bin/env python3
"""
WebUIの現在の状態をデバッグするスクリプト
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chromeドライバーのセットアップ
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # WebUIに接続
    logger.info("WebUIに接続中...")
    driver.get("http://localhost:8501")
    time.sleep(5)
    
    # スクリーンショット保存
    driver.save_screenshot("webui_current_state.png")
    logger.info("スクリーンショット保存: webui_current_state.png")
    
    # ページタイトル確認
    logger.info(f"ページタイトル: {driver.title}")
    
    # 現在のURLを確認
    logger.info(f"現在のURL: {driver.current_url}")
    
    # ページ内のボタンを全て探す
    buttons = driver.find_elements("tag name", "button")
    logger.info(f"ボタン数: {len(buttons)}")
    for i, button in enumerate(buttons):
        try:
            text = button.text.strip()
            if text:
                logger.info(f"ボタン{i}: {text}")
        except:
            pass
    
    # タブやリンクを探す
    links = driver.find_elements("tag name", "a")
    logger.info(f"\nリンク数: {len(links)}")
    for i, link in enumerate(links):
        try:
            text = link.text.strip()
            if text:
                logger.info(f"リンク{i}: {text}")
        except:
            pass
    
    # 入力フィールドを探す  
    inputs = driver.find_elements("tag name", "input")
    logger.info(f"\n入力フィールド数: {len(inputs)}")
    
    # ページの一部テキストを取得
    body_text = driver.find_element("tag name", "body").text[:500]
    logger.info(f"\nページテキスト（最初の500文字）:\n{body_text}")
    
finally:
    driver.quit()
    logger.info("デバッグ完了")