#!/usr/bin/env python3
"""
バックテストページの構造を詳細に調査
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

def explore_backtest_page():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)
    
    try:
        # ログイン
        logger.info("WebUIに接続...")
        driver.get("http://localhost:8501")
        time.sleep(3)
        
        # ログイン処理
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
        
        # バックテストボタンをクリック
        logger.info("\nバックテストボタンを探しています...")
        
        # すべてのボタンをチェック
        buttons = driver.find_elements(By.XPATH, "//button")
        backtest_button = None
        
        for button in buttons:
            try:
                text = button.text.strip()
                if "バックテスト" in text and button.is_displayed():
                    logger.info(f"バックテストボタン発見: {text}")
                    backtest_button = button
                    break
            except:
                pass
        
        if backtest_button:
            # JavaScriptでクリック
            driver.execute_script("arguments[0].scrollIntoView(true);", backtest_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", backtest_button)
            logger.info("バックテストボタンをクリックしました")
            time.sleep(5)
            
            # バックテストページの内容を調査
            logger.info("\n=== バックテストページの内容 ===")
            
            # ページテキスト
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"\nページテキスト（最初の1000文字）:\n{page_text[:1000]}")
            
            # タブ構造を調査
            logger.info("\n=== タブ構造 ===")
            tabs = driver.find_elements(By.XPATH, "//*[contains(@role, 'tab') or contains(@class, 'tab')]")
            logger.info(f"タブ数: {len(tabs)}")
            for i, tab in enumerate(tabs):
                try:
                    logger.info(f"タブ{i}: {tab.text}")
                except:
                    pass
            
            # セクションを調査
            logger.info("\n=== セクション/ヘッダー ===")
            headers = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4")
            for header in headers[:10]:
                try:
                    text = header.text.strip()
                    if text:
                        logger.info(f"ヘッダー: {text}")
                except:
                    pass
            
            # フォーム要素を調査
            logger.info("\n=== フォーム要素 ===")
            inputs = driver.find_elements(By.XPATH, "//input | //select | //textarea")
            logger.info(f"入力要素数: {len(inputs)}")
            
            # バックテスト関連のボタンを探す
            logger.info("\n=== バックテスト実行ボタンを探しています ===")
            all_buttons = driver.find_elements(By.XPATH, "//button")
            
            for i, button in enumerate(all_buttons):
                try:
                    text = button.text.strip()
                    if text and button.is_displayed():
                        # 実行に関連するキーワード
                        if any(keyword in text for keyword in ["実行", "開始", "Run", "Start", "Execute", "バックテスト"]):
                            logger.info(f"関連ボタン{i}: {text}")
                            logger.info(f"  表示: {button.is_displayed()}")
                            logger.info(f"  有効: {button.is_enabled()}")
                            logger.info(f"  クラス: {button.get_attribute('class')}")
                            
                            # このボタンをハイライト
                            driver.execute_script("arguments[0].style.border='3px solid red'", button)
                except:
                    pass
            
            # Streamlitの特殊な要素
            logger.info("\n=== Streamlit要素 ===")
            st_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'stButton') or contains(@data-testid, 'stButton')]")
            logger.info(f"Streamlitボタン数: {len(st_elements)}")
            
            # エクスパンダーやコラプス要素
            expanders = driver.find_elements(By.XPATH, "//*[contains(@class, 'streamlit-expanderHeader')]")
            logger.info(f"エクスパンダー数: {len(expanders)}")
            
            # スクリーンショット
            driver.save_screenshot("backtest_page_structure.png")
            logger.info("\nスクリーンショット保存: backtest_page_structure.png")
            
        else:
            logger.error("バックテストボタンが見つかりません")
            
            # 代替手段: URLに直接アクセス
            logger.info("\n代替手段: URLパラメータを試しています...")
            driver.get("http://localhost:8501/?page=backtest")
            time.sleep(3)
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"URLアクセス後のページ内容（最初の500文字）:\n{page_text[:500]}")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        time.sleep(5)
        driver.quit()
        logger.info("\n調査完了")

if __name__ == "__main__":
    explore_backtest_page()