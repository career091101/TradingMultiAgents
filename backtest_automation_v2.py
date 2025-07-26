#!/usr/bin/env python3
"""
WebUIバックテスト自動実行 - 改良版
ポップアップ処理とバックテスト実行を適切に処理
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestAutomationV2:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup(self):
        """ブラウザセットアップ"""
        logger.info("=== バックテスト自動実行開始 ===")
        logger.info("1. 環境準備: Chromeブラウザ起動")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-notifications')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("✓ ブラウザ起動成功")
        
    def login(self):
        """ログイン処理"""
        logger.info("2. WebUI接続とログイン")
        self.driver.get("http://localhost:8501")
        time.sleep(3)
        
        try:
            # ユーザー名入力
            username = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
            )
            username.clear()
            username.send_keys("user")
            
            # パスワード入力
            password = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password.clear()
            password.send_keys("user123")
            
            # ログインボタンクリック
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
                logger.info("✓ ログイン成功")
            else:
                raise Exception("ログインボタンが見つかりません")
            
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            raise
    
    def close_popup(self):
        """ポップアップを閉じる"""
        try:
            # Deploy popupの×ボタンを探す
            close_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Close' or contains(@class, 'close')]")
            for button in close_buttons:
                if button.is_displayed():
                    button.click()
                    logger.info("✓ ポップアップを閉じました")
                    time.sleep(1)
                    return
                    
            # 代替: ESCキーを送信
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"ポップアップクローズ失敗（続行）: {e}")
    
    def navigate_to_backtest(self):
        """バックテストページへ移動"""
        logger.info("3. バックテストページへの遷移")
        
        # ポップアップを閉じる
        self.close_popup()
        
        try:
            # サイドバーの「バックテスト」ボタンを探す
            backtest_button = None
            
            # パターン1: サイドバーのボタン
            try:
                backtest_button = self.driver.find_element(By.XPATH, "//button[contains(., 'バックテスト')]")
            except NoSuchElementException:
                pass
            
            # パターン2: リンク形式
            if not backtest_button:
                try:
                    backtest_button = self.driver.find_element(By.XPATH, "//a[contains(., 'バックテスト')]")
                except NoSuchElementException:
                    pass
            
            if backtest_button:
                # スクロールして表示
                self.driver.execute_script("arguments[0].scrollIntoView(true);", backtest_button)
                time.sleep(1)
                backtest_button.click()
                logger.info("✓ バックテストページへ移動")
                time.sleep(3)
            else:
                logger.warning("バックテストボタンが見つからない - 既に表示されている可能性")
                
        except Exception as e:
            logger.error(f"ナビゲーションエラー: {e}")
            raise
    
    def find_and_click_backtest2(self):
        """バックテスト2タブを探してクリック"""
        logger.info("4. バックテスト2タブへの移動")
        
        try:
            # ページ内のタブやボタンを探す
            tab_patterns = [
                "//button[contains(text(), 'バックテスト2')]",
                "//div[contains(@class, 'tab') and contains(., 'バックテスト2')]",
                "//span[contains(text(), 'バックテスト2')]",
                "//h3[contains(text(), 'バックテスト2')]"
            ]
            
            for pattern in tab_patterns:
                try:
                    element = self.driver.find_element(By.XPATH, pattern)
                    if element.is_displayed():
                        element.click()
                        logger.info("✓ バックテスト2タブをクリック")
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
            
            # バックテスト2が見つからない場合、現在のページを確認
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "バックテスト2" in page_text:
                logger.info("バックテスト2は既に表示されています")
                return True
            else:
                logger.warning("バックテスト2タブが見つかりません")
                return False
                
        except Exception as e:
            logger.error(f"タブ切り替えエラー: {e}")
            return False
    
    def execute_backtest(self):
        """バックテスト実行"""
        logger.info("5. バックテスト実行")
        
        try:
            # 実行ボタンを探す
            execute_patterns = [
                "//button[contains(text(), 'バックテスト実行')]",
                "//button[contains(text(), '実行') and not(contains(text(), 'ログ'))]",
                "//button[contains(text(), 'Run Backtest')]",
                "//button[contains(@class, 'primary') and contains(., '実行')]"
            ]
            
            execute_button = None
            for pattern in execute_patterns:
                try:
                    buttons = self.driver.find_elements(By.XPATH, pattern)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            execute_button = button
                            break
                    if execute_button:
                        break
                except:
                    continue
            
            if not execute_button:
                # 全てのボタンをチェック
                all_buttons = self.driver.find_elements(By.XPATH, "//button")
                for button in all_buttons:
                    text = button.text.strip()
                    if text and ("実行" in text or "Run" in text) and button.is_enabled():
                        logger.info(f"候補ボタン発見: {text}")
                        execute_button = button
                        break
            
            if execute_button:
                # スクロールして表示
                self.driver.execute_script("arguments[0].scrollIntoView(true);", execute_button)
                time.sleep(1)
                
                # JavaScriptでクリック（通常クリックが失敗する場合の対策）
                self.driver.execute_script("arguments[0].click();", execute_button)
                logger.info("✓ 実行ボタンをクリック")
                
                # 実行開始を待つ
                time.sleep(5)
                
                # 実行状態を監視
                return self.monitor_execution()
            else:
                logger.error("実行ボタンが見つかりません")
                self.driver.save_screenshot("no_execute_button.png")
                return False
                
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            self.driver.save_screenshot("execution_error.png")
            return False
    
    def monitor_execution(self):
        """実行状態を監視"""
        logger.info("実行状態を監視中...")
        
        start_time = time.time()
        timeout = 300  # 5分
        check_interval = 5
        
        while time.time() - start_time < timeout:
            try:
                # エラーチェック
                error_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert-danger')]")
                if error_elements:
                    for elem in error_elements:
                        if elem.is_displayed():
                            logger.error(f"エラー検出: {elem.text}")
                            return False
                
                # 完了チェック
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                completion_keywords = ["完了", "Complete", "Finished", "結果", "Results", "取引数", "Total Trades"]
                
                if any(keyword in page_text for keyword in completion_keywords):
                    logger.info("✓ バックテスト完了")
                    return True
                
                # プログレス表示
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0:
                    logger.info(f"実行中... ({elapsed}秒経過)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.warning(f"監視中のエラー: {e}")
        
        logger.warning("実行タイムアウト - 結果を確認します")
        return True
    
    def analyze_results(self):
        """結果分析"""
        logger.info("6. ログ確認・問題判定")
        
        problems = []
        warnings = []
        results = {}
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # エラーチェック
            if "error" in page_text.lower() or "エラー" in page_text:
                error_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error')]")
                for div in error_divs:
                    if div.is_displayed():
                        problems.append(f"エラー: {div.text[:200]}")
            
            # 結果データの抽出
            import re
            result_patterns = {
                "取引数": r"取引数[：:]\s*(\d+)",
                "総リターン": r"総リターン[：:]\s*([-\d.]+)%",
                "シャープレシオ": r"シャープレシオ[：:]\s*([-\d.]+)",
                "最大ドローダウン": r"最大ドローダウン[：:]\s*([-\d.]+)%"
            }
            
            for key, pattern in result_patterns.items():
                match = re.search(pattern, page_text)
                if match:
                    results[key] = match.group(1)
            
            # 警告チェック
            if "取引数" in results and int(results["取引数"]) == 0:
                warnings.append("取引が0件です")
            
            # スクリーンショット保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"backtest_result_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
            
            return problems, warnings, results
            
        except Exception as e:
            logger.error(f"結果分析エラー: {e}")
            problems.append(f"分析エラー: {str(e)}")
            return problems, warnings, results
    
    def generate_report(self, problems, warnings, results):
        """レポート生成"""
        logger.info("7. 結果処理とレポート出力")
        
        timestamp = datetime.now()
        
        report = {
            "実行日時": timestamp.isoformat(),
            "ステータス": "エラー" if problems else ("警告" if warnings else "成功"),
            "問題": problems,
            "警告": warnings,
            "結果": results
        }
        
        # コンソール出力
        logger.info("\n=== 実行結果サマリー ===")
        if report["ステータス"] == "成功":
            logger.info("✅ 正常完了")
            if results:
                logger.info("結果:")
                for key, value in results.items():
                    logger.info(f"  {key}: {value}")
        elif report["ステータス"] == "警告":
            logger.warning("⚠️ 警告ありで完了")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.error("❌ エラーが発生しました")
            for problem in problems:
                logger.error(f"  - {problem}")
        
        # 根本原因分析
        if problems:
            logger.error("\n根本原因分析:")
            problem_text = " ".join(problems).lower()
            
            if "api" in problem_text or "key" in problem_text:
                logger.error("- APIキー関連の問題の可能性")
                logger.error("  対処法: 環境変数とAPIキー設定を確認")
            elif "connection" in problem_text or "timeout" in problem_text:
                logger.error("- 接続/タイムアウトの問題")
                logger.error("  対処法: ネットワーク接続とデータプロバイダーのステータスを確認")
            elif "data" in problem_text:
                logger.error("- データ関連の問題")
                logger.error("  対処法: 銘柄コードと期間設定を確認")
        
        # ファイル保存
        report_file = f"backtest_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"\nレポート保存: {report_file}")
        
        return report
    
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
            self.navigate_to_backtest()
            
            # バックテスト2があるか確認
            if self.find_and_click_backtest2():
                if self.execute_backtest():
                    problems, warnings, results = self.analyze_results()
                    self.generate_report(problems, warnings, results)
                    return len(problems) == 0
            else:
                # バックテスト2がない場合は通常のバックテストを実行
                logger.info("バックテスト2が見つからないため、通常のバックテストを試行")
                if self.execute_backtest():
                    problems, warnings, results = self.analyze_results()
                    self.generate_report(problems, warnings, results)
                    return len(problems) == 0
            
            return False
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            
            # エラーレポート生成
            self.generate_report(
                [f"予期しないエラー: {str(e)}"],
                [],
                {}
            )
            return False
        finally:
            self.cleanup()

def main():
    automation = BacktestAutomationV2()
    success = automation.run()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())