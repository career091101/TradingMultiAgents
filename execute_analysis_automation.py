#!/usr/bin/env python3
"""
分析実行ボタンを使ったバックテスト自動実行
現在のWebUIの状態に合わせた実装
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
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisExecutionAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.results = {}
        
    def setup(self):
        """ブラウザセットアップ"""
        logger.info("=== 分析実行自動化開始 ===")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("✓ ブラウザ起動成功")
        
    def login(self):
        """ログイン処理"""
        logger.info("WebUIに接続...")
        self.driver.get("http://localhost:8501")
        time.sleep(3)
        
        try:
            username = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
            username.clear()
            username.send_keys("user")
            
            password = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password.clear()
            password.send_keys("user123")
            
            login_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
            login_button.click()
            logger.info("✓ ログイン成功")
            time.sleep(5)
        except:
            logger.info("既にログイン済み")
    
    def navigate_to_analysis(self):
        """分析実行ページへ移動"""
        logger.info("分析実行ページへ移動...")
        
        try:
            # 「▶️ 分析実行」ボタンを探す
            analysis_button = None
            patterns = [
                "//button[contains(text(), '▶️ 分析実行')]",
                "//button[contains(., '分析実行')]",
                "//button[@class='st-emotion-cache-1ub9ykg e1e4lema2' and contains(., '分析実行')]"
            ]
            
            for pattern in patterns:
                try:
                    buttons = self.driver.find_elements(By.XPATH, pattern)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            analysis_button = button
                            break
                    if analysis_button:
                        break
                except:
                    continue
            
            if analysis_button:
                self.driver.execute_script("arguments[0].click();", analysis_button)
                logger.info("✓ 分析実行ページへ移動")
                time.sleep(3)
                return True
            else:
                logger.error("分析実行ボタンが見つかりません")
                return False
                
        except Exception as e:
            logger.error(f"ナビゲーションエラー: {e}")
            return False
    
    def execute_analysis(self):
        """分析を実行"""
        logger.info("分析を実行中...")
        
        try:
            # 実行ボタンを探す（分析実行ページ内）
            execute_patterns = [
                "//button[contains(text(), '実行')]",
                "//button[contains(text(), '分析開始')]",
                "//button[contains(text(), '開始')]",
                "//button[@kind='primary']"
            ]
            
            execute_button = None
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # すべてのボタンをチェック
            all_buttons = self.driver.find_elements(By.XPATH, "//button")
            logger.info(f"ボタン総数: {len(all_buttons)}")
            
            for button in all_buttons:
                try:
                    text = button.text.strip()
                    if text and button.is_displayed() and button.is_enabled():
                        if any(keyword in text for keyword in ["実行", "開始", "Start"]):
                            if "ログ" not in text:
                                execute_button = button
                                logger.info(f"実行ボタン発見: {text}")
                                break
                except:
                    pass
            
            if execute_button:
                self.driver.execute_script("arguments[0].click();", execute_button)
                logger.info("✓ 分析実行開始")
                time.sleep(5)
                return True
            else:
                logger.error("実行ボタンが見つかりません")
                self.driver.save_screenshot("no_execute_button_analysis.png")
                return False
                
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            return False
    
    def monitor_execution(self):
        """実行状態を監視"""
        logger.info("実行状態を監視中...")
        
        start_time = time.time()
        timeout = 300  # 5分
        
        while time.time() - start_time < timeout:
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # エラーチェック
                if "error" in page_text.lower() or "エラー" in page_text:
                    logger.error("エラーが検出されました")
                    return False
                
                # 完了チェック
                if any(keyword in page_text for keyword in ["完了", "Complete", "結果", "取引"]):
                    logger.info("✓ 分析完了")
                    return True
                
                # プログレスバーやステータスメッセージを確認
                progress_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'stProgress')]")
                if progress_elements:
                    logger.info("実行中...")
                
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"監視中のエラー: {e}")
        
        logger.warning("実行タイムアウト")
        return True
    
    def extract_results(self):
        """結果を抽出"""
        logger.info("結果を抽出中...")
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 基本的な結果パターン
            import re
            patterns = {
                "取引数": r"取引数[：:]\s*(\d+)",
                "総リターン": r"総リターン[：:]\s*([-\d.]+)%",
                "シャープレシオ": r"シャープレシオ[：:]\s*([-\d.]+)",
                "最大ドローダウン": r"最大ドローダウン[：:]\s*([-\d.]+)%"
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, page_text)
                if match:
                    self.results[key] = match.group(1)
            
            # スクリーンショット保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"analysis_result_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
            
            return self.results
            
        except Exception as e:
            logger.error(f"結果抽出エラー: {e}")
            return {}
    
    def generate_report(self):
        """レポート生成"""
        logger.info("レポート生成中...")
        
        timestamp = datetime.now()
        
        report = {
            "実行日時": timestamp.isoformat(),
            "結果": self.results,
            "ステータス": "成功" if self.results else "失敗"
        }
        
        # コンソール出力
        print("\n=== 分析実行結果 ===")
        print(f"実行日時: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.results:
            print("結果:")
            for key, value in self.results.items():
                print(f"  {key}: {value}")
        else:
            print("結果の取得に失敗しました")
        
        # ファイル保存
        report_file = f"analysis_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レポート保存: {report_file}")
    
    def cleanup(self):
        """クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行フロー"""
        try:
            self.setup()
            self.login()
            
            if self.navigate_to_analysis():
                if self.execute_analysis():
                    self.monitor_execution()
                    self.extract_results()
                    self.generate_report()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    automation = AnalysisExecutionAutomation()
    success = automation.run()
    exit(0 if success else 1)