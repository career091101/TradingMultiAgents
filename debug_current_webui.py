#!/usr/bin/env python3
"""
WebUIの現在の状態を詳細にデバッグ
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_webui():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # ログイン処理
        logger.info("WebUIに接続...")
        driver.get("http://localhost:8501")
        time.sleep(3)
        
        # ログイン
        try:
            username = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
            username.clear()
            username.send_keys("user")
            
            password = driver.find_element(By.XPATH, "//input[@type='password']")
            password.clear()
            password.send_keys("user123")
            
            login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
            login_button.click()
            logger.info("ログイン成功")
            time.sleep(5)
        except:
            logger.info("既にログイン済み")
        
        # 現在のページ状態を詳細に調査
        logger.info("\n=== ページ分析 ===")
        
        # タイトル
        logger.info(f"ページタイトル: {driver.title}")
        
        # URL
        logger.info(f"現在のURL: {driver.current_url}")
        
        # ページテキスト（最初の500文字）
        body_text = driver.find_element(By.TAG_NAME, "body").text
        logger.info(f"\nページテキスト（最初の500文字）:\n{body_text[:500]}")
        
        # すべてのボタンを詳細に調査
        logger.info("\n=== ボタン詳細 ===")
        buttons = driver.find_elements(By.XPATH, "//button")
        logger.info(f"ボタン総数: {len(buttons)}")
        
        for i, button in enumerate(buttons):
            try:
                text = button.text.strip()
                is_visible = button.is_displayed()
                is_enabled = button.is_enabled()
                classes = button.get_attribute("class")
                
                if text or is_visible:
                    logger.info(f"\nボタン{i}:")
                    logger.info(f"  テキスト: {text}")
                    logger.info(f"  表示: {is_visible}")
                    logger.info(f"  有効: {is_enabled}")
                    logger.info(f"  クラス: {classes}")
                    
                    # バックテストや実行に関連するボタンを特定
                    if any(keyword in text.lower() for keyword in ["バックテスト", "実行", "分析", "run", "execute", "backtest"]):
                        logger.info(f"  ⭐ 関連ボタンの可能性あり")
                        
                        # スクリーンショットを保存
                        driver.execute_script("arguments[0].style.border='3px solid red'", button)
                        time.sleep(0.5)
                        driver.save_screenshot(f"button_{i}_{text.replace(' ', '_')}.png")
            except:
                pass
        
        # リンクも調査
        logger.info("\n=== リンク詳細 ===")
        links = driver.find_elements(By.XPATH, "//a")
        logger.info(f"リンク総数: {len(links)}")
        
        for i, link in enumerate(links[:10]):  # 最初の10個
            try:
                text = link.text.strip()
                href = link.get_attribute("href")
                if text:
                    logger.info(f"リンク{i}: {text} -> {href}")
            except:
                pass
        
        # サイドバーの要素を調査
        logger.info("\n=== サイドバー要素 ===")
        sidebar_elements = driver.find_elements(By.XPATH, "//section[@data-testid='stSidebar']//*[contains(@class, 'element')]")
        logger.info(f"サイドバー要素数: {len(sidebar_elements)}")
        
        # タブを調査
        logger.info("\n=== タブ要素 ===")
        tabs = driver.find_elements(By.XPATH, "//*[contains(@class, 'tab')]")
        logger.info(f"タブ数: {len(tabs)}")
        for i, tab in enumerate(tabs[:5]):
            try:
                logger.info(f"タブ{i}: {tab.text}")
            except:
                pass
        
        # 最終スクリーンショット
        driver.save_screenshot("webui_full_debug.png")
        logger.info("\n最終スクリーンショット保存: webui_full_debug.png")
        
        # ポップアップの確認
        popups = driver.find_elements(By.XPATH, "//div[contains(@class, 'modal') or contains(@class, 'popup')]")
        if popups:
            logger.info(f"\nポップアップ検出: {len(popups)}個")
            for popup in popups:
                if popup.is_displayed():
                    logger.info("表示中のポップアップあり")
                    
                    # ×ボタンを探す
                    close_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='Close' or contains(@class, 'close')]")
                    if close_buttons:
                        logger.info("クローズボタンを発見")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        time.sleep(3)
        driver.quit()
        logger.info("\nデバッグ完了")

if __name__ == "__main__":
    debug_webui()