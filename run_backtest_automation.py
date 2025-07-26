#!/usr/bin/env python3
"""
WebUIバックテスト自動実行の簡易版
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
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBacktestAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup(self):
        """ブラウザセットアップ"""
        logger.info("1. ブラウザ起動")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        
    def login(self):
        """ログイン処理"""
        logger.info("2. WebUIにアクセス")
        self.driver.get("http://localhost:8501")
        time.sleep(3)
        
        # ログイン処理
        try:
            # ユーザー名入力
            username = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
            )
            username.clear()
            username.send_keys("user")
            logger.info("✓ ユーザー名入力")
            
            # パスワード入力
            password = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password.clear()
            password.send_keys("user123")
            logger.info("✓ パスワード入力")
            
            # ログインボタンクリック
            # Streamlitのボタンは特殊なので、複数の方法を試す
            login_selectors = [
                "//button[contains(., 'Login')]",
                "//button[text()='Login']",
                "//div[contains(@class, 'stButton')]//button",
                "//button[@kind='primary']"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.XPATH, selector)
                    if login_button and login_button.is_displayed():
                        break
                except:
                    continue
            
            if login_button:
                login_button.click()
                logger.info("✓ ログインボタンクリック")
            else:
                logger.error("ログインボタンが見つかりません")
            
            time.sleep(5)
            
            # ログイン成功確認
            self.driver.save_screenshot("after_login.png")
            logger.info("ログイン後のスクリーンショット保存: after_login.png")
            
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            self.driver.save_screenshot("login_error.png")
            raise
    
    def navigate_to_backtest(self):
        """バックテストページへ移動"""
        logger.info("3. バックテストページへ移動")
        
        try:
            # 現在のページ内容を確認
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"現在のページ内容（最初の200文字）: {page_text[:200]}")
            
            # サイドバーのボタンを探す（Streamlitのハンバーガーメニュー）
            menu_buttons = self.driver.find_elements(By.XPATH, "//button[@kind='header' or contains(@class, 'css')]")
            if menu_buttons:
                logger.info(f"メニューボタン数: {len(menu_buttons)}")
                menu_buttons[0].click()
                time.sleep(2)
                logger.info("✓ メニューボタンクリック")
            
            # バックテスト2を探す
            backtest_elements = [
                "//span[contains(text(), 'バックテスト2')]",
                "//div[contains(text(), 'バックテスト2')]",
                "//a[contains(text(), 'バックテスト2')]",
                "//li[contains(text(), 'バックテスト2')]",
                "//button[contains(text(), 'バックテスト2')]"
            ]
            
            found = False
            for xpath in backtest_elements:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    logger.info(f"バックテスト2要素を発見: {xpath}")
                    elements[0].click()
                    found = True
                    break
            
            if not found:
                logger.warning("バックテスト2が見つからない - 既に表示されている可能性")
            
            time.sleep(3)
            self.driver.save_screenshot("backtest_page.png")
            logger.info("バックテストページのスクリーンショット保存")
            
        except Exception as e:
            logger.error(f"ナビゲーションエラー: {e}")
            self.driver.save_screenshot("navigation_error.png")
            raise
    
    def execute_backtest(self):
        """バックテスト実行"""
        logger.info("4. バックテスト実行")
        
        try:
            # 実行タブを探す
            tabs = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'tab')]")
            logger.info(f"タブ数: {len(tabs)}")
            
            for tab in tabs:
                if "実行" in tab.text or "Execute" in tab.text:
                    tab.click()
                    logger.info("✓ 実行タブクリック")
                    time.sleep(2)
                    break
            
            # 実行ボタンを探す
            buttons = self.driver.find_elements(By.XPATH, "//button")
            logger.info(f"ボタン総数: {len(buttons)}")
            
            execution_button = None
            for button in buttons:
                button_text = button.text.strip()
                if button_text:
                    logger.info(f"ボタン: {button_text}")
                    if "実行" in button_text or "Execute" in button_text or "Run" in button_text:
                        if button.is_enabled():
                            execution_button = button
                            logger.info(f"✓ 実行ボタン発見: {button_text}")
            
            if execution_button:
                execution_button.click()
                logger.info("✓ 実行ボタンクリック")
                
                # 実行開始を待つ
                time.sleep(5)
                
                # 実行中のスクリーンショット
                self.driver.save_screenshot("execution_started.png")
                logger.info("実行開始のスクリーンショット保存")
                
                # 完了を待つ（最大5分）
                logger.info("実行完了を待機中...")
                for i in range(60):  # 5秒 x 60 = 5分
                    time.sleep(5)
                    
                    # エラーチェック
                    errors = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error')]")
                    if errors:
                        logger.error("エラーが発生しました")
                        self.driver.save_screenshot("execution_error.png")
                        break
                    
                    # 完了チェック
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if "完了" in page_text or "Complete" in page_text or "結果" in page_text:
                        logger.info("✓ バックテスト完了")
                        break
                    
                    if i % 12 == 0:  # 1分ごとに状態表示
                        logger.info(f"実行中... ({i*5}秒経過)")
                
                # 最終スクリーンショット
                self.driver.save_screenshot(f"final_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                logger.info("最終結果のスクリーンショット保存")
                
            else:
                logger.error("実行ボタンが見つかりません")
                self.driver.save_screenshot("no_execute_button.png")
                
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            self.driver.save_screenshot("execution_exception.png")
            raise
    
    def analyze_results(self):
        """結果分析"""
        logger.info("5. 結果分析")
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 問題判定
            problems = []
            warnings = []
            
            if "error" in page_text.lower() or "エラー" in page_text:
                problems.append("エラーが検出されました")
            
            if "取引数: 0" in page_text or "Total Trades: 0" in page_text:
                warnings.append("取引が0件です")
            
            # レポート出力
            logger.info("=== 実行結果 ===")
            if problems:
                logger.error("問題あり:")
                for p in problems:
                    logger.error(f"  - {p}")
            elif warnings:
                logger.warning("警告あり:")
                for w in warnings:
                    logger.warning(f"  - {w}")
            else:
                logger.info("✅ 正常完了")
            
            # 結果の一部を表示
            logger.info("\n結果の一部:")
            lines = page_text.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ["取引", "リターン", "シャープ", "Trade", "Return", "Sharpe"]):
                    logger.info(f"  {line.strip()}")
                    
        except Exception as e:
            logger.error(f"結果分析エラー: {e}")
    
    def cleanup(self):
        """クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行"""
        try:
            self.setup()
            self.login()
            self.navigate_to_backtest()
            self.execute_backtest()
            self.analyze_results()
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

if __name__ == "__main__":
    automation = SimpleBacktestAutomation()
    automation.run()