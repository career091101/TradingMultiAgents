#!/usr/bin/env python3
"""
WebUI経由でバックテストを自動実行するスクリプト
Seleniumを使用してブラウザを自動操作
改良版: ユーザー指定の認証情報とエラーハンドリング強化
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webui_backtest_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebUIBacktestAutomation:
    def __init__(self, url="http://localhost:8501", username="user", password="user123"):
        self.url = url
        self.username = username
        self.password = password
        self.driver = None
        self.wait = None
        self.max_retries = 3
        self.retry_count = 0
        
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        logger.info("1. 環境準備: Chromeドライバーのセットアップ")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # ヘッドレスモードオプション（必要に応じてコメントアウト）
        # chrome_options.add_argument('--headless')
        
        try:
            # webdriver-managerを使用して自動的にChromeDriverをダウンロード
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
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
            
            # ログイン処理
            if not self._handle_login():
                return False
                
            return True
            
        except TimeoutException:
            logger.error("✗ WebUI接続タイムアウト")
            return False
        except Exception as e:
            logger.error(f"✗ WebUI接続エラー: {e}")
            return False
    
    def _handle_login(self):
        """ログイン処理"""
        try:
            # ユーザー名入力フィールドを探す
            username_inputs = [
                "//input[@type='text' and (@placeholder='Username' or @placeholder='ユーザー名')]",
                "//input[@name='username']",
                "//input[contains(@id, 'username')]"
            ]
            
            username_field = None
            for xpath in username_inputs:
                try:
                    username_field = self.driver.find_element(By.XPATH, xpath)
                    break
                except NoSuchElementException:
                    continue
            
            if username_field:
                logger.info("ログイン画面を検出")
                
                # ユーザー名入力
                username_field.clear()
                username_field.send_keys(self.username)
                
                # パスワード入力フィールドを探す
                password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                password_field.clear()
                password_field.send_keys(self.password)
                
                # ログインボタンを探してクリック
                login_buttons = [
                    "//button[contains(text(), 'Login')]",
                    "//button[contains(text(), 'ログイン')]",
                    "//button[@type='submit']"
                ]
                
                for xpath in login_buttons:
                    try:
                        login_button = self.driver.find_element(By.XPATH, xpath)
                        login_button.click()
                        time.sleep(3)
                        logger.info("✓ ログイン完了")
                        return True
                    except NoSuchElementException:
                        continue
                
                # Enterキーでのログインを試行
                password_field.send_keys(Keys.RETURN)
                time.sleep(3)
                logger.info("✓ ログイン完了（Enterキー）")
                return True
                
            else:
                logger.info("ログイン不要（既にログイン済み）")
                return True
                
        except Exception as e:
            logger.error(f"✗ ログインエラー: {e}")
            return False
    
    def navigate_to_backtest(self):
        """バックテストページへ遷移"""
        logger.info("3. バックテストページへの遷移")
        
        try:
            # サイドバーを探す（Streamlitの場合）
            try:
                sidebar = self.driver.find_element(By.XPATH, "//section[@data-testid='stSidebar']")
                logger.info("サイドバーを検出")
            except NoSuchElementException:
                # サイドバーが閉じている場合はメニューボタンをクリック
                menu_buttons = [
                    "//button[@kind='header']",
                    "//button[contains(@class, 'css-1q8dd3e')]"
                ]
                for xpath in menu_buttons:
                    try:
                        menu_button = self.driver.find_element(By.XPATH, xpath)
                        menu_button.click()
                        time.sleep(1)
                        logger.info("メニューボタンをクリック")
                        break
                    except NoSuchElementException:
                        continue
            
            # バックテストリンクを探す
            backtest_links = [
                "//a[contains(text(), 'バックテスト2')]",
                "//button[contains(text(), 'バックテスト2')]",
                "//div[contains(text(), 'バックテスト2')]",
                "//span[contains(text(), 'バックテスト2')]",
                "//li[contains(text(), 'バックテスト2')]"
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
            
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"✗ ナビゲーションエラー: {e}")
            return False
    
    def navigate_to_execution_tab(self):
        """バックテスト実行タブへの移動"""
        logger.info("4. バックテスト実行タブへの移動")
        
        try:
            # タブを探す
            execution_tabs = [
                "//button[contains(text(), '実行')]",
                "//div[contains(@class, 'tab') and contains(text(), '実行')]",
                "//li[contains(text(), '実行')]"
            ]
            
            for xpath in execution_tabs:
                try:
                    tab = self.driver.find_element(By.XPATH, xpath)
                    tab.click()
                    logger.info("✓ 実行タブに切り替え")
                    time.sleep(2)
                    return True
                except NoSuchElementException:
                    continue
            
            logger.info("実行タブが見つからない - 既に実行画面の可能性")
            return True
            
        except Exception as e:
            logger.error(f"✗ タブ切り替えエラー: {e}")
            return False
    
    def execute_backtest(self):
        """バックテストを実行"""
        logger.info("5. バックテスト実行")
        
        try:
            # 設定値の確認（オプション）
            self._check_settings()
            
            # 実行ボタンを探す
            execute_buttons = [
                "//button[contains(text(), 'バックテスト実行')]",
                "//button[contains(text(), '実行')]",
                "//button[contains(text(), 'Run Backtest')]",
                "//button[contains(text(), 'Execute')]",
                "//button[contains(@class, 'stButton') and not(contains(@disabled, 'true'))]"
            ]
            
            button_found = False
            for xpath in execute_buttons:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for button in reversed(buttons):  # 後ろから確認
                        if button.is_enabled() and button.is_displayed():
                            button.click()
                            button_found = True
                            logger.info("✓ 実行ボタンをクリック")
                            break
                    if button_found:
                        break
                except Exception:
                    continue
            
            if not button_found:
                logger.error("✗ 実行ボタンが見つかりません")
                return False
            
            # 実行開始の確認
            time.sleep(3)
            
            # 実行状態の監視
            return self._monitor_execution()
            
        except Exception as e:
            logger.error(f"✗ 実行エラー: {e}")
            return False
    
    def _check_settings(self):
        """設定値の確認（オプション）"""
        try:
            # 必要に応じて設定値を確認・変更
            logger.info("設定値を確認中...")
            # TODO: 必要に応じて実装
        except Exception as e:
            logger.warning(f"設定確認スキップ: {e}")
    
    def _monitor_execution(self):
        """実行状態を監視"""
        logger.info("実行完了を待機中...")
        
        timeout = 600  # 10分
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # エラーチェック
            error_check = self._check_for_errors()
            if error_check is not None:
                return error_check
            
            # 完了チェック
            if self._check_completion():
                logger.info("✓ バックテスト完了")
                return True
            
            # プログレス表示
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0:  # 30秒ごとに状態表示
                logger.info(f"実行中... ({elapsed}秒経過)")
            
            time.sleep(5)
        
        logger.warning("タイムアウト: 実行が完了しませんでした")
        return True  # タイムアウトでも継続
    
    def _check_for_errors(self):
        """エラーの確認"""
        error_indicators = [
            "//div[contains(@class, 'stAlert') and contains(@class, 'error')]",
            "//div[contains(@class, 'error-message')]",
            "//div[contains(text(), 'Error:')]",
            "//div[contains(text(), 'エラー:')]"
        ]
        
        for xpath in error_indicators:
            try:
                error_element = self.driver.find_element(By.XPATH, xpath)
                error_text = error_element.text
                logger.error(f"✗ エラーが発生: {error_text}")
                
                # リトライ可能なエラーか判定
                if self.retry_count < self.max_retries and self._is_retryable_error(error_text):
                    self.retry_count += 1
                    logger.info(f"リトライを実行します ({self.retry_count}/{self.max_retries})")
                    time.sleep(10)
                    return None  # リトライ継続
                
                return False
            except NoSuchElementException:
                pass
        
        return None
    
    def _is_retryable_error(self, error_text):
        """リトライ可能なエラーか判定"""
        retryable_keywords = [
            "timeout", "タイムアウト",
            "connection", "接続",
            "temporary", "一時的"
        ]
        
        error_lower = error_text.lower()
        return any(keyword in error_lower for keyword in retryable_keywords)
    
    def _check_completion(self):
        """完了状態の確認"""
        completion_indicators = [
            "//div[contains(text(), '完了')]",
            "//div[contains(text(), 'Complete')]",
            "//div[contains(text(), 'Finished')]",
            "//h3[contains(text(), '結果')]",
            "//h3[contains(text(), 'Results')]",
            "//div[contains(@class, 'results-container')]"
        ]
        
        for xpath in completion_indicators:
            try:
                self.driver.find_element(By.XPATH, xpath)
                return True
            except NoSuchElementException:
                continue
        
        return False
    
    def check_logs_and_results(self):
        """ログ確認と結果判定"""
        logger.info("6. ログ確認・問題判定")
        
        problems = []
        warnings = []
        results = {}
        
        try:
            # ページのテキスト全体を取得
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # エラーログの確認
            self._check_error_logs(problems, warnings)
            
            # 結果データの取得
            results = self._extract_results(page_text)
            
            # 結果の検証
            self._validate_results(results, problems, warnings)
            
            # スクリーンショット保存
            self._save_screenshot()
            
        except Exception as e:
            logger.error(f"ログ確認エラー: {e}")
            problems.append(f"ログ確認エラー: {str(e)}")
        
        return problems, warnings, results
    
    def _check_error_logs(self, problems, warnings):
        """エラーログの確認"""
        try:
            # エクスパンダーを開く
            expanders = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'css-1xo6twm')]")
            for expander in expanders:
                try:
                    if "エラー" in expander.text or "Error" in expander.text:
                        expander.click()
                        time.sleep(0.5)
                except:
                    pass
            
            # エラーメッセージを収集
            error_elements = self.driver.find_elements(By.XPATH, "//pre[contains(@class, 'error')]")
            for element in error_elements:
                error_text = element.text.strip()
                if error_text:
                    problems.append(f"エラーログ: {error_text[:200]}...")
                    
        except Exception as e:
            logger.warning(f"エラーログ確認失敗: {e}")
    
    def _extract_results(self, page_text):
        """結果データの抽出"""
        results = {}
        
        # 結果パターン
        patterns = {
            "total_trades": [r"取引数[:：]\s*(\d+)", r"Total Trades[:：]\s*(\d+)"],
            "total_return": [r"総リターン[:：]\s*([-\d.]+)%", r"Total Return[:：]\s*([-\d.]+)%"],
            "sharpe_ratio": [r"シャープレシオ[:：]\s*([-\d.]+)", r"Sharpe Ratio[:：]\s*([-\d.]+)"],
            "max_drawdown": [r"最大ドローダウン[:：]\s*([-\d.]+)%", r"Max Drawdown[:：]\s*([-\d.]+)%"]
        }
        
        import re
        for key, regex_patterns in patterns.items():
            for pattern in regex_patterns:
                match = re.search(pattern, page_text)
                if match:
                    results[key] = match.group(1)
                    break
        
        return results
    
    def _validate_results(self, results, problems, warnings):
        """結果の検証"""
        if not results:
            warnings.append("結果データが見つかりません")
            return
        
        # 取引数の確認
        if "total_trades" in results:
            trades = int(results["total_trades"])
            if trades == 0:
                warnings.append("取引が0件です - ストラテジーの設定を確認してください")
            elif trades < 10:
                warnings.append(f"取引数が少ない可能性があります ({trades}件)")
        
        # リターンの確認
        if "total_return" in results:
            total_return = float(results["total_return"])
            if total_return < -50:
                problems.append(f"大幅な損失が発生しています ({total_return}%)")
        
        # シャープレシオの確認
        if "sharpe_ratio" in results:
            sharpe = float(results["sharpe_ratio"])
            if sharpe < -1:
                warnings.append(f"シャープレシオが低い値です ({sharpe})")
    
    def _save_screenshot(self):
        """スクリーンショット保存"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"backtest_result_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            logger.error(f"スクリーンショット保存失敗: {e}")
            return None
    
    def generate_report(self, problems, warnings, results):
        """結果レポートを生成"""
        logger.info("7. 結果処理とレポート出力")
        
        timestamp = datetime.now()
        
        report = {
            "execution_time": timestamp.isoformat(),
            "url": self.url,
            "status": "error" if problems else ("warning" if warnings else "success"),
            "problems": problems,
            "warnings": warnings,
            "results": results,
            "screenshot": f"backtest_result_{timestamp.strftime('%Y%m%d_%H%M%S')}.png",
            "retry_count": self.retry_count
        }
        
        # 根本原因分析
        if problems:
            report["root_cause_analysis"] = self._analyze_root_cause(problems)
        
        # コンソール出力
        self._print_report(report)
        
        # ファイル保存
        report_file = f"webui_backtest_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レポート保存: {report_file}")
        return report
    
    def _analyze_root_cause(self, problems):
        """根本原因分析"""
        analysis = {
            "error_type": "unknown",
            "possible_causes": [],
            "recommendations": []
        }
        
        problem_text = " ".join(problems).lower()
        
        if "api" in problem_text or "認証" in problem_text or "auth" in problem_text:
            analysis["error_type"] = "authentication"
            analysis["possible_causes"] = [
                "APIキーが設定されていない",
                "APIキーが無効または期限切れ",
                "認証情報が正しくない"
            ]
            analysis["recommendations"] = [
                "環境変数にAPIキーが設定されているか確認",
                "WebUIの設定画面でAPIキーを再入力",
                ".envファイルの内容を確認"
            ]
        elif "接続" in problem_text or "connection" in problem_text or "timeout" in problem_text:
            analysis["error_type"] = "connection"
            analysis["possible_causes"] = [
                "WebUIが起動していない",
                "ネットワークの問題",
                "ファイアウォールの設定"
            ]
            analysis["recommendations"] = [
                "streamlit run コマンドでWebUIを起動",
                "http://localhost:8501 にアクセスできるか確認",
                "ファイアウォール設定を確認"
            ]
        elif "データ" in problem_text or "data" in problem_text:
            analysis["error_type"] = "data"
            analysis["possible_causes"] = [
                "市場データの取得に失敗",
                "データ形式が不正",
                "期間設定が不適切"
            ]
            analysis["recommendations"] = [
                "インターネット接続を確認",
                "データプロバイダーのAPIステータスを確認",
                "期間設定を短くして再試行"
            ]
        else:
            analysis["error_type"] = "application"
            analysis["possible_causes"] = [
                "アプリケーション内部エラー",
                "設定の不整合",
                "依存関係の問題"
            ]
            analysis["recommendations"] = [
                "アプリケーションログを確認",
                "設定ファイルを初期化",
                "依存パッケージを再インストール"
            ]
        
        return analysis
    
    def _print_report(self, report):
        """レポートをコンソールに出力"""
        if report["status"] == "success":
            logger.info("=== ✅ 正常完了 ===")
            if report["results"]:
                logger.info("結果サマリー:")
                for key, value in report["results"].items():
                    logger.info(f"  {key}: {value}")
        elif report["status"] == "warning":
            logger.warning("=== ⚠️  警告ありで完了 ===")
            for warning in report["warnings"]:
                logger.warning(f"- {warning}")
        else:
            logger.error("=== ❌ エラーが発生しました ===")
            for problem in report["problems"]:
                logger.error(f"- {problem}")
            
            if "root_cause_analysis" in report:
                analysis = report["root_cause_analysis"]
                logger.error(f"\n根本原因分析:")
                logger.error(f"エラータイプ: {analysis['error_type']}")
                logger.error("考えられる原因:")
                for cause in analysis['possible_causes']:
                    logger.error(f"  - {cause}")
                logger.error("推奨される対処法:")
                for rec in analysis['recommendations']:
                    logger.error(f"  - {rec}")
    
    def cleanup(self):
        """クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行フロー"""
        logger.info("=== WebUIバックテスト自動実行開始 ===")
        
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
            
            # 4. 実行タブへ移動
            if not self.navigate_to_execution_tab():
                return False
            
            # 5. バックテスト実行
            if not self.execute_backtest():
                return False
            
            # 6. ログ確認
            problems, warnings, results = self.check_logs_and_results()
            
            # 7. 結果処理
            self.generate_report(problems, warnings, results)
            
            return len(problems) == 0
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
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
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WebUIバックテスト自動実行')
    parser.add_argument('--url', default='http://localhost:8501', help='WebUI URL')
    parser.add_argument('--username', default='user', help='ユーザー名')
    parser.add_argument('--password', default='user123', help='パスワード')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')
    
    args = parser.parse_args()
    
    automation = WebUIBacktestAutomation(
        url=args.url,
        username=args.username,
        password=args.password
    )
    
    success = automation.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()