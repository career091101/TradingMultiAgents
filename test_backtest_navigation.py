#!/usr/bin/env python3
"""
バックテストナビゲーションテスト
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

def test_navigation():
    driver = None
    try:
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
            logger.info("✓ ログイン成功")
            time.sleep(5)
        except:
            logger.info("既にログイン済み")
        
        # JavaScriptでバックテストボタンをクリック
        logger.info("バックテストボタンを探しています...")
        
        # 方法1: JavaScriptで直接クリック
        js_click = """
        // すべてのボタンを取得
        const buttons = Array.from(document.querySelectorAll('button'));
        console.log('Total buttons:', buttons.length);
        
        // バックテストボタンを探す
        const backtestBtn = buttons.find(btn => {
            const text = btn.textContent || '';
            console.log('Button text:', text);
            return text.includes('バックテスト') && !text.includes('実行');
        });
        
        if (backtestBtn) {
            console.log('Found backtest button:', backtestBtn.textContent);
            backtestBtn.scrollIntoView();
            backtestBtn.click();
            return 'クリック成功';
        }
        
        // セカンドトライ - data-testidやaria-labelも確認
        const altBtn = document.querySelector('[data-testid*="backtest"], [aria-label*="バックテスト"]');
        if (altBtn) {
            altBtn.click();
            return 'クリック成功（代替方法）';
        }
        
        return 'ボタンが見つかりません';
        """
        
        result = driver.execute_script(js_click)
        logger.info(f"JavaScript実行結果: {result}")
        
        # 少し待機
        time.sleep(3)
        
        # ページが変わったか確認
        current_url = driver.current_url
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "バックテスト" in page_text and ("設定" in page_text or "実行" in page_text):
            logger.info("✓ バックテストページへの遷移成功！")
            driver.save_screenshot("backtest_page_success.png")
            
            # 実行タブを探す
            logger.info("\n実行タブを探しています...")
            
            # バックテスト実行タブをクリック
            exec_js = """
            // タブを探す
            const tabs = document.querySelectorAll('[role="tab"], button');
            const execTab = Array.from(tabs).find(tab => {
                const text = tab.textContent || '';
                return text.includes('実行') && !text.includes('分析実行');
            });
            
            if (execTab) {
                execTab.click();
                return '実行タブクリック成功';
            }
            
            // 代替方法: pタグのテキストから親要素を探す
            const pTags = document.querySelectorAll('p');
            const execP = Array.from(pTags).find(p => p.textContent === 'バックテスト実行');
            if (execP && execP.parentElement) {
                execP.parentElement.click();
                return '実行タブクリック成功（代替）';
            }
            
            return '実行タブが見つかりません';
            """
            
            exec_result = driver.execute_script(exec_js)
            logger.info(f"実行タブクリック結果: {exec_result}")
            
            time.sleep(2)
            
            # 実行ボタンを探す
            logger.info("\n実行ボタンを探しています...")
            
            # ページを下にスクロール
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # 実行ボタンをクリック
            exec_button_js = """
            const buttons = Array.from(document.querySelectorAll('button'));
            const execBtn = buttons.find(btn => {
                const text = btn.textContent || '';
                return text.includes('マルチエージェントバックテストを開始') || 
                       (text.includes('開始') && text.includes('バックテスト'));
            });
            
            if (execBtn) {
                execBtn.scrollIntoView({block: 'center'});
                execBtn.click();
                return '実行ボタンクリック成功: ' + execBtn.textContent;
            }
            
            return '実行ボタンが見つかりません';
            """
            
            exec_btn_result = driver.execute_script(exec_button_js)
            logger.info(f"実行ボタンクリック結果: {exec_btn_result}")
            
            if "成功" in exec_btn_result:
                time.sleep(5)
                driver.save_screenshot("backtest_execution_started.png")
                logger.info("✓ バックテスト実行を開始しました！")
            
        else:
            logger.error("バックテストページへの遷移に失敗しました")
            driver.save_screenshot("navigation_failed.png")
            
            # デバッグ情報
            logger.info(f"現在のURL: {current_url}")
            logger.info(f"ページテキスト（最初の200文字）: {page_text[:200]}")
        
    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            driver.save_screenshot("error_screenshot.png")
    
    finally:
        if driver:
            driver.quit()
            logger.info("ブラウザを閉じました")

if __name__ == "__main__":
    test_navigation()