#!/usr/bin/env python3
"""
ナビゲーションデバッグツール
サイドバーのボタンを詳しく調査
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_config import create_driver
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_navigation():
    driver = None
    try:
        # ブラウザ起動
        driver = create_driver()
        wait = WebDriverWait(driver, 30)
        
        # WebUIに接続
        driver.get("http://localhost:8501")
        time.sleep(3)
        
        # ログイン
        try:
            username = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
            )
            username.send_keys("user")
            
            password = driver.find_element(By.XPATH, "//input[@type='password']")
            password.send_keys("user123")
            
            login_button = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
            login_button.click()
            logger.info("ログイン成功")
            time.sleep(5)
        except:
            logger.info("既にログイン済み")
        
        # スクリーンショット
        driver.save_screenshot("debug_after_login.png")
        
        # サイドバーのすべてのボタンを探す
        logger.info("\n=== サイドバーのボタンを調査 ===")
        
        # すべてのボタンを取得
        all_buttons = driver.find_elements(By.XPATH, "//button")
        logger.info(f"ページ内のボタン総数: {len(all_buttons)}")
        
        # サイドバー内のボタンを特定
        sidebar_buttons = []
        for i, button in enumerate(all_buttons):
            try:
                # ボタンの情報を取得
                text = button.text.strip()
                key = button.get_attribute("key") or ""
                classes = button.get_attribute("class") or ""
                is_displayed = button.is_displayed()
                is_enabled = button.is_enabled()
                
                # サイドバーのボタンかチェック（nav_で始まるkey）
                if "nav_" in key or "バックテスト" in text:
                    button_info = {
                        "index": i,
                        "text": text,
                        "key": key,
                        "classes": classes[:100],  # 最初の100文字
                        "displayed": is_displayed,
                        "enabled": is_enabled
                    }
                    sidebar_buttons.append(button_info)
                    
                    logger.info(f"\nボタン {i}:")
                    logger.info(f"  テキスト: '{text}'")
                    logger.info(f"  key属性: {key}")
                    logger.info(f"  表示: {is_displayed}, 有効: {is_enabled}")
                    
            except Exception as e:
                pass
        
        # バックテストボタンを探す
        logger.info("\n=== バックテストボタンの検索 ===")
        
        backtest_patterns = [
            "//button[contains(text(), 'バックテスト')]",
            "//button[contains(., 'バックテスト')]",
            "//button[@key='nav_backtest2']",
            "//button[contains(@data-testid, 'backtest')]",
            "//*[contains(text(), 'バックテスト')]/ancestor::button"
        ]
        
        for pattern in backtest_patterns:
            try:
                elements = driver.find_elements(By.XPATH, pattern)
                if elements:
                    logger.info(f"\nパターン '{pattern}' で {len(elements)} 個のボタンが見つかりました:")
                    for elem in elements:
                        logger.info(f"  - テキスト: '{elem.text.strip()}'")
                        logger.info(f"  - 表示: {elem.is_displayed()}")
            except Exception as e:
                logger.error(f"パターン '{pattern}' でエラー: {e}")
        
        # JavaScript で直接ボタンを探す
        logger.info("\n=== JavaScriptでボタンを検索 ===")
        
        js_script = """
        const buttons = Array.from(document.querySelectorAll('button'));
        const backtestButtons = buttons.filter(btn => 
            btn.textContent.includes('バックテスト') || 
            btn.getAttribute('key') === 'nav_backtest2'
        );
        return backtestButtons.map(btn => ({
            text: btn.textContent.trim(),
            key: btn.getAttribute('key'),
            visible: btn.offsetParent !== null,
            rect: btn.getBoundingClientRect()
        }));
        """
        
        js_results = driver.execute_script(js_script)
        logger.info(f"JavaScript で見つかったボタン: {len(js_results)}")
        for result in js_results:
            logger.info(f"  - {result}")
        
        # ページのHTMLを部分的に出力（デバッグ用）
        page_source = driver.page_source
        if "バックテスト" in page_source:
            logger.info("\n'バックテスト'という文字列はページ内に存在します")
            
            # バックテスト周辺のHTMLを抽出
            import re
            matches = re.finditer(r'.{50}バックテスト.{50}', page_source)
            for match in matches:
                logger.info(f"  周辺HTML: ...{match.group()}...")
        
        # 最終スクリーンショット
        driver.save_screenshot("debug_navigation_final.png")
        
        # バックテストボタンをクリックしてみる
        logger.info("\n=== バックテストボタンのクリックを試行 ===")
        
        # JavaScriptで直接クリック
        click_script = """
        const buttons = Array.from(document.querySelectorAll('button'));
        const backtestBtn = buttons.find(btn => 
            btn.textContent.includes('バックテスト') && 
            !btn.textContent.includes('実行')
        );
        if (backtestBtn) {
            backtestBtn.click();
            return 'クリック成功: ' + backtestBtn.textContent;
        }
        return 'バックテストボタンが見つかりません';
        """
        
        click_result = driver.execute_script(click_script)
        logger.info(f"クリック結果: {click_result}")
        
        time.sleep(3)
        driver.save_screenshot("debug_after_click.png")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            input("\nEnterキーを押すとブラウザを閉じます...")
            driver.quit()

if __name__ == "__main__":
    debug_navigation()