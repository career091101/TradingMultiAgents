#!/usr/bin/env python3
"""
WebUI経由でバックテストを自動実行するスクリプト
Seleniumを使用してブラウザを自動操作
"""

import time
import os
import sys
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webui_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebUIAutomation:
    def __init__(self, url="http://localhost:8501"):
        self.url = url
        self.driver = None
        self.wait = None
        self.max_retries = 3
        
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        logger.info("1. 環境準備: Chromeドライバーのセットアップ")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("✓ Chromeドライバー起動成功")
            return True
        except Exception as e:
            logger.error(f"✗ Chromeドライバー起動失敗: {e}")
            return False
    
    def connect_webui(self):
        """WebUIに接続"""
        logger.info("2. WebUI接続")
        
        try:
            self.driver.get(self.url)
            time.sleep(3)  # ページ読み込み待機
            
            # Streamlitアプリの読み込み確認
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logger.info(f"✓ WebUI接続成功: {self.url}")
            
            # ログイン画面の確認
            try:
                login_form = self.driver.find_element(By.XPATH, "//input[@type='password']")
                logger.info("ログイン画面を検出")
                
                # デフォルトパスワードでログイン
                login_form.send_keys("admin")
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
                login_button.click()
                time.sleep(2)
                logger.info("✓ ログイン完了")
            except NoSuchElementException:
                logger.info("ログイン不要（既にログイン済み）")
                
            return True
            
        except TimeoutException:
            logger.error("✗ WebUI接続タイムアウト")
            return False
        except Exception as e:
            logger.error(f"✗ WebUI接続エラー: {e}")
            return False
    
    def navigate_to_backtest(self):
        """バックテストページへ遷移"""
        logger.info("3. バックテストページへの遷移")
        
        try:
            # サイドバーまたはタブから「バックテスト2」を探す
            backtest_links = [
                "//a[contains(text(), 'バックテスト2')]",
                "//button[contains(text(), 'バックテスト2')]",
                "//div[contains(text(), 'バックテスト2')]",
                "//span[contains(text(), 'バックテスト2')]"
            ]
            
            element_found = False
            for xpath in backtest_links:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    element.click()
                    element_found = True
                    logger.info("✓ バックテスト2タブをクリック")
                    break
                except NoSuchElementException:
                    continue
            
            if not element_found:
                logger.warning("バックテスト2タブが見つからない - 既に表示されている可能性")
            
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"✗ ナビゲーションエラー: {e}")
            return False
    
    def execute_backtest(self):
        """バックテストを実行"""
        logger.info("4. バックテスト実行タブへの移動")
        logger.info("5. バックテスト実行")
        
        try:
            # 実行ボタンを探す
            execute_buttons = [
                "//button[contains(text(), 'バックテスト実行')]",
                "//button[contains(text(), '実行')]",
                "//button[contains(text(), 'Run Backtest')]",
                "//button[contains(@class, 'stButton')]"
            ]
            
            button_found = False
            for xpath in execute_buttons:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    if buttons:
                        # 最後のボタンをクリック（通常は実行ボタン）
                        buttons[-1].click()
                        button_found = True
                        logger.info("✓ 実行ボタンをクリック")
                        break
                except Exception:
                    continue
            
            if not button_found:
                logger.error("✗ 実行ボタンが見つかりません")
                return False
            
            # 実行開始の確認
            time.sleep(3)
            
            # プログレスバーまたはステータスメッセージを確認
            progress_indicators = [
                "//div[contains(@class, 'stProgress')]",
                "//div[contains(text(), '実行中')]",
                "//div[contains(text(), 'Running')]",
                "//div[contains(text(), '初期化中')]"
            ]
            
            execution_started = False
            for xpath in progress_indicators:
                try:
                    self.driver.find_element(By.XPATH, xpath)
                    execution_started = True
                    logger.info("✓ バックテスト実行開始を確認")
                    break
                except NoSuchElementException:
                    continue
            
            if not execution_started:
                logger.warning("実行状態の確認ができませんでしたが、処理を継続します")
            
            # 実行完了まで監視（最大10分）
            logger.info("実行完了を待機中...")
            timeout = 600  # 10分
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # エラーメッセージの確認
                try:
                    error_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'stAlert') and contains(@class, 'error')]")
                    logger.error(f"✗ エラーが発生: {error_element.text}")
                    return False
                except NoSuchElementException:
                    pass
                
                # 完了メッセージの確認
                completion_indicators = [
                    "//div[contains(text(), '完了')]",
                    "//div[contains(text(), 'Complete')]",
                    "//div[contains(text(), 'Finished')]",
                    "//div[contains(text(), '結果')]"
                ]
                
                for xpath in completion_indicators:
                    try:
                        self.driver.find_element(By.XPATH, xpath)
                        logger.info("✓ バックテスト完了")
                        return True
                    except NoSuchElementException:
                        continue
                
                time.sleep(5)
            
            logger.warning("タイムアウト: 実行が完了しませんでした")
            return True  # タイムアウトでも継続
            
        except Exception as e:
            logger.error(f"✗ 実行エラー: {e}")
            return False
    
    def check_logs_and_results(self):
        """ログ確認と結果判定"""
        logger.info("6. ログ確認・問題判定")
        
        problems = []
        warnings = []
        
        try:
            # ページのテキスト全体を取得
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # エラーログセクションを探す
            error_sections = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'stExpander')]")
            
            for section in error_sections:
                section_text = section.text
                if "エラー" in section_text or "Error" in section_text:
                    # エクスパンダーを開く
                    try:
                        expander_button = section.find_element(By.XPATH, ".//button")
                        expander_button.click()
                        time.sleep(1)
                    except:
                        pass
                    
                    # エラー内容を取得
                    error_content = section.text
                    if "ERROR" in error_content:
                        problems.append(f"エラーログ検出: {error_content[:200]}...")
            
            # 結果データの確認
            result_indicators = ["取引数", "リターン", "シャープレシオ", "Trades", "Return", "Sharpe"]
            result_found = False
            
            for indicator in result_indicators:
                if indicator in page_text:
                    result_found = True
                    break
            
            if not result_found:
                warnings.append("結果データが見つかりません")
            
            # 取引数の確認
            if "取引数: 0" in page_text or "Trades: 0" in page_text:
                warnings.append("取引が0件です")
            
            # スクリーンショット保存
            screenshot_path = f"backtest_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
            
        except Exception as e:
            logger.error(f"ログ確認エラー: {e}")
            problems.append(f"ログ確認エラー: {str(e)}")
        
        return problems, warnings
    
    def generate_report(self, problems, warnings):
        """結果レポートを生成"""
        logger.info("7. 結果処理")
        
        report = {
            "execution_time": datetime.now().isoformat(),
            "url": self.url,
            "status": "error" if problems else ("warning" if warnings else "success"),
            "problems": problems,
            "warnings": warnings,
            "screenshot": f"backtest_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        }
        
        if not problems:
            if warnings:
                logger.warning("=== 警告ありで完了 ===")
                for warning in warnings:
                    logger.warning(f"- {warning}")
            else:
                logger.info("=== 正常完了 ===")
        else:
            logger.error("=== エラーが発生しました ===")
            for problem in problems:
                logger.error(f"- {problem}")
            
            logger.error("\n根本原因分析:")
            if any("API" in p for p in problems):
                logger.error("- APIキーまたは認証の問題")
                logger.error("推奨: 環境変数とWebUI設定を確認")
            elif any("接続" in p or "Connection" in p for p in problems):
                logger.error("- ネットワーク接続の問題")
                logger.error("推奨: WebUIが起動しているか確認")
            else:
                logger.error("- アプリケーションエラー")
                logger.error("推奨: ログファイルを詳細に確認")
        
        # レポート保存
        report_file = f"webui_automation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レポート保存: {report_file}")
        return report
    
    def cleanup(self):
        """クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行フロー"""
        logger.info("=== WebUI自動実行開始 ===")
        
        try:
            # 1. 環境準備
            if not self.setup_driver():
                return False
            
            # 2. WebUI接続
            if not self.connect_webui():
                return False
            
            # 3. バックテストページへ遷移
            if not self.navigate_to_backtest():
                return False
            
            # 4-5. バックテスト実行
            if not self.execute_backtest():
                return False
            
            # 6. ログ確認
            problems, warnings = self.check_logs_and_results()
            
            # 7. 結果処理
            self.generate_report(problems, warnings)
            
            return len(problems) == 0
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    automation = WebUIAutomation()
    success = automation.run()
    sys.exit(0 if success else 1)