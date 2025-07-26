#!/usr/bin/env python3
"""
完全なバックテスト実行ワークフロー
実際にバックテストを実行し、結果を取得する
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from datetime import datetime
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteBacktestExecution:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.retry_count = 0
        self.max_retries = 3
        
    def setup(self):
        """1. 環境準備"""
        logger.info("=== バックテスト自動実行ワークフロー ===")
        logger.info("1. 環境準備: Chromeブラウザ起動")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=2560,1600')
        chrome_options.add_argument('--start-maximized')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_window_size(2560, 1600)
        self.driver.set_window_position(0, 0)
        
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("✓ Chromeブラウザ起動成功（解像度: 2560x1600）")
        
    def login(self):
        """2. WebUI接続"""
        logger.info("2. WebUI接続")
        
        for attempt in range(self.max_retries):
            try:
                self.driver.get("http://localhost:8501")
                logger.info("WebUIにアクセス中...")
                time.sleep(3)
                
                # ログイン処理
                try:
                    username = self.wait.until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
                    )
                    username.clear()
                    username.send_keys("user")
                    
                    password = self.driver.find_element(By.XPATH, "//input[@type='password']")
                    password.clear()
                    password.send_keys("user123")
                    
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
                    login_button.click()
                    logger.info("✓ ログイン成功")
                    time.sleep(5)
                    return True
                except:
                    logger.info("既にログイン済み")
                    return True
                    
            except Exception as e:
                logger.error(f"接続エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    raise
                    
        return False
    
    def navigate_to_backtest(self):
        """3. バックテストページへの遷移"""
        logger.info("3. バックテストページへの遷移")
        
        try:
            # まずページの状態を確認
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.debug(f"現在のページ内容（最初の300文字）: {page_text[:300]}")
            
            # バックテストボタンを探す（複数の方法）
            backtest_button = None
            
            # 方法1: テキストで検索
            buttons = self.driver.find_elements(By.XPATH, "//button")
            logger.info(f"ボタン総数: {len(buttons)}")
            
            for i, button in enumerate(buttons):
                try:
                    button_text = button.text.strip()
                    if button_text and button.is_displayed():
                        logger.debug(f"ボタン{i}: {button_text}")
                        
                        if "バックテスト" in button_text:
                            backtest_button = button
                            logger.info(f"✓ バックテストボタン発見: {button_text}")
                            break
                except:
                    continue
            
            # 方法2: クラス名とテキストで検索
            if not backtest_button:
                specific_xpath = "//button[@class='st-emotion-cache-1ub9ykg e1e4lema2' and contains(., 'バックテスト')]"
                try:
                    backtest_button = self.driver.find_element(By.XPATH, specific_xpath)
                    logger.info("✓ バックテストボタン発見（XPath）")
                except:
                    pass
            
            if backtest_button:
                # JavaScriptでクリック
                self.driver.execute_script("arguments[0].scrollIntoView(true);", backtest_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", backtest_button)
                logger.info("✓ バックテストページへ移動")
                time.sleep(3)
                
                # ページが切り替わったことを確認
                new_page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if "バックテスト" in new_page_text and ("設定" in new_page_text or "実行" in new_page_text):
                    logger.info("✓ バックテストページの表示を確認")
                    return True
                
            else:
                logger.error("バックテストボタンが見つかりません")
                # デバッグ用スクリーンショット
                self.driver.save_screenshot("debug_no_backtest_button.png")
                return False
                
        except Exception as e:
            logger.error(f"ナビゲーションエラー: {e}")
            return False
    
    def navigate_to_execution_tab(self):
        """4. バックテスト実行タブへの移動"""
        logger.info("4. バックテスト実行タブへの移動")
        
        try:
            # タブを探す
            tabs = self.driver.find_elements(By.XPATH, "//div[@role='tab'] | //button[contains(@class, 'tab')]")
            logger.info(f"タブ数: {len(tabs)}")
            
            execution_tab = None
            for tab in tabs:
                try:
                    tab_text = tab.text.strip()
                    if tab_text:
                        logger.debug(f"タブ: {tab_text}")
                        if "実行" in tab_text or "Execute" in tab_text:
                            execution_tab = tab
                            break
                except:
                    continue
            
            # Streamlitの特殊なタブ構造を考慮
            if not execution_tab:
                # タブのラベルで探す
                tab_labels = self.driver.find_elements(By.XPATH, "//p[contains(text(), 'バックテスト実行')]")
                if tab_labels:
                    # ラベルの親要素（タブボタン）を取得
                    for label in tab_labels:
                        try:
                            parent = label.find_element(By.XPATH, "./..")
                            if parent.tag_name in ['button', 'div']:
                                execution_tab = parent
                                break
                        except:
                            continue
            
            if execution_tab:
                execution_tab.click()
                logger.info("✓ バックテスト実行タブに切り替え")
                time.sleep(2)
                return True
            else:
                # 既に実行画面の可能性を確認
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if "設定サマリー" in page_text or "実行" in page_text:
                    logger.info("✓ バックテスト実行タブが既に表示されています")
                    return True
                else:
                    logger.warning("実行タブが見つかりません")
                    return True
                    
        except Exception as e:
            logger.error(f"タブ切り替えエラー: {e}")
            return True
    
    def execute_backtest(self):
        """5. バックテスト実行"""
        logger.info("5. バックテスト実行")
        
        try:
            # まずページを下にスクロールして全体を表示
            logger.info("ページをスクロールして実行ボタンを探します")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # ページの内容を確認
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.debug(f"ページ内容に含まれるキーワード: {'開始' in page_text}, {'実行' in page_text}")
            
            # 実行ボタンを探す（赤い大きなボタン）
            execute_button = None
            
            # 「マルチエージェントバックテストを開始」ボタンを探す
            button_patterns = [
                "//button[contains(text(), 'マルチエージェントバックテストを開始')]",
                "//button[contains(text(), 'バックテストを開始')]",
                "//button[contains(text(), '✓ マルチエージェントバックテストを開始')]",
                "//button[contains(@class, 'stButton') and contains(., '開始')]",
                "//button[contains(@style, 'background-color') and contains(., '開始')]"
            ]
            
            for pattern in button_patterns:
                try:
                    buttons = self.driver.find_elements(By.XPATH, pattern)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            execute_button = button
                            logger.info(f"✓ 実行ボタン発見: {button.text}")
                            break
                    if execute_button:
                        break
                except:
                    continue
            
            if not execute_button:
                # すべてのボタンから探す
                all_buttons = self.driver.find_elements(By.XPATH, "//button")
                logger.info(f"ページ内のボタン総数: {len(all_buttons)}")
                
                for i, button in enumerate(all_buttons):
                    try:
                        text = button.text.strip()
                        if text and button.is_displayed():
                            logger.debug(f"ボタン{i}: {text}")
                            
                            if "開始" in text or "バックテスト" in text:
                                # 赤いボタンかどうか確認
                                style = button.get_attribute("style") or ""
                                classes = button.get_attribute("class") or ""
                                
                                # Streamlitの赤いボタンのクラス名を確認
                                if ("red" in style.lower() or 
                                    "danger" in classes or 
                                    "primary" in classes or
                                    "e1ewe7hr3" in classes):  # Streamlitの特定のクラス
                                    execute_button = button
                                    logger.info(f"✓ 実行ボタン発見: {text}")
                                    break
                    except:
                        pass
            
            if execute_button:
                # スクリーンショット（実行前）
                self.driver.save_screenshot("before_execution.png")
                
                # ボタンをクリック
                self.driver.execute_script("arguments[0].scrollIntoView(true);", execute_button)
                time.sleep(1)
                
                # クリック試行（複数の方法）
                try:
                    execute_button.click()
                except:
                    # JavaScriptでクリック
                    self.driver.execute_script("arguments[0].click();", execute_button)
                
                logger.info("✓ バックテスト実行開始")
                
                time.sleep(5)
                return True
            else:
                logger.error("実行ボタンが見つかりません")
                # ページ全体のスクリーンショット
                self.driver.save_screenshot("no_execute_button_full.png")
                
                # 中央部分にスクロールして再度スクリーンショット
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                self.driver.save_screenshot("no_execute_button_middle.png")
                
                return False
                
        except Exception as e:
            logger.error(f"実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def monitor_execution(self):
        """実行状態を監視"""
        logger.info("実行状態を監視中...")
        
        start_time = time.time()
        timeout = 900  # 15分（推定時間14分を考慮）
        last_status = ""
        
        while time.time() - start_time < timeout:
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # プログレスバーやステータスメッセージを確認
                progress_indicators = [
                    "実行中", "Running", "処理中", "Processing",
                    "エージェント", "Agent", "決定", "Decision"
                ]
                
                for indicator in progress_indicators:
                    if indicator in page_text:
                        # ステータスの変化を検出
                        status_match = re.search(r'(\d+)/(\d+)', page_text)
                        if status_match:
                            current_status = f"進捗: {status_match.group(0)}"
                            if current_status != last_status:
                                logger.info(current_status)
                                last_status = current_status
                        break
                
                # エラーチェック
                if self._check_for_errors(page_text):
                    return False
                
                # 完了チェック
                if self._check_completion(page_text):
                    logger.info("✓ バックテスト完了")
                    return True
                
                # 定期的なスクリーンショット
                elapsed = int(time.time() - start_time)
                if elapsed % 60 == 0:  # 1分ごと
                    self.driver.save_screenshot(f"execution_progress_{elapsed}s.png")
                    logger.info(f"実行中... ({elapsed}秒経過)")
                
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"監視中のエラー: {e}")
        
        logger.warning("実行タイムアウト")
        return False
    
    def _check_for_errors(self, page_text):
        """エラーの確認"""
        error_keywords = [
            "error", "エラー", "失敗", "failed",
            "exception", "例外", "中断", "aborted"
        ]
        
        for keyword in error_keywords:
            if keyword.lower() in page_text.lower():
                # エラー要素を詳しく確認
                try:
                    error_elements = self.driver.find_elements(
                        By.XPATH, 
                        "//div[contains(@class, 'error') or contains(@class, 'alert')]"
                    )
                    for elem in error_elements:
                        if elem.is_displayed() and elem.text:
                            logger.error(f"エラー検出: {elem.text}")
                            self.driver.save_screenshot("execution_error.png")
                            return True
                except:
                    pass
        
        return False
    
    def _check_completion(self, page_text):
        """完了状態の確認"""
        completion_keywords = [
            "完了", "Complete", "Finished",
            "結果", "Results", "Summary",
            "取引数", "Total Trades",
            "リターン", "Return",
            "シャープレシオ", "Sharpe Ratio"
        ]
        
        completion_count = sum(1 for keyword in completion_keywords if keyword in page_text)
        return completion_count >= 3  # 複数のキーワードが含まれていれば完了と判断
    
    def check_results(self):
        """6. ログ確認・問題判定"""
        logger.info("6. ログ確認・問題判定")
        
        results = {}
        problems = []
        warnings = []
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 結果の抽出
            result_patterns = {
                "取引数": [r"取引数[：:]\s*(\d+)", r"Total Trades[：:]\s*(\d+)"],
                "総リターン": [r"総リターン[：:]\s*([-\d.]+)%", r"Total Return[：:]\s*([-\d.]+)%"],
                "シャープレシオ": [r"シャープレシオ[：:]\s*([-\d.]+)", r"Sharpe Ratio[：:]\s*([-\d.]+)"],
                "最大ドローダウン": [r"最大ドローダウン[：:]\s*([-\d.]+)%", r"Max Drawdown[：:]\s*([-\d.]+)%"],
                "勝率": [r"勝率[：:]\s*([-\d.]+)%", r"Win Rate[：:]\s*([-\d.]+)%"]
            }
            
            for key, patterns in result_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        results[key] = match.group(1)
                        break
            
            # 問題判定
            if not results:
                problems.append("結果データが取得できませんでした")
            else:
                # 取引数チェック
                if results.get("取引数", "0") == "0":
                    warnings.append("取引が0件です - エントリー条件を確認してください")
                
                # リターンチェック
                if "総リターン" in results:
                    total_return = float(results["総リターン"])
                    if total_return < -50:
                        problems.append(f"大幅な損失: {total_return}%")
                    elif total_return < -20:
                        warnings.append(f"損失が発生: {total_return}%")
            
            # ログセクションの確認
            self._check_logs(problems, warnings)
            
            # 最終スクリーンショット
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"backtest_complete_result_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"結果スクリーンショット保存: {screenshot_path}")
            
        except Exception as e:
            logger.error(f"結果確認エラー: {e}")
            problems.append(f"結果確認エラー: {str(e)}")
        
        return results, problems, warnings
    
    def _check_logs(self, problems, warnings):
        """ログセクションの詳細確認"""
        try:
            # エクスパンダーを開く
            expanders = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(@class, 'streamlit-expanderHeader')]"
            )
            
            for expander in expanders:
                try:
                    if "ログ" in expander.text or "Log" in expander.text:
                        expander.click()
                        time.sleep(0.5)
                except:
                    pass
            
            # ログ内容を確認
            log_elements = self.driver.find_elements(
                By.XPATH,
                "//pre | //code | //div[contains(@class, 'log')]"
            )
            
            for elem in log_elements:
                if elem.is_displayed() and elem.text:
                    log_text = elem.text.lower()
                    if "error" in log_text or "exception" in log_text:
                        problems.append(f"エラーログ: {elem.text[:100]}...")
                    elif "warning" in log_text or "warn" in log_text:
                        warnings.append(f"警告ログ: {elem.text[:100]}...")
                        
        except Exception as e:
            logger.warning(f"ログ確認中のエラー: {e}")
    
    def process_results(self, results, problems, warnings):
        """7. 結果処理"""
        logger.info("7. 結果処理")
        
        timestamp = datetime.now()
        
        # レポート生成
        report = {
            "実行日時": timestamp.isoformat(),
            "実行時間": "計測中",
            "ステータス": "エラー" if problems else ("警告" if warnings else "成功"),
            "結果": results,
            "問題": problems,
            "警告": warnings,
            "エラーハンドリング": {
                "リトライ回数": self.retry_count,
                "最大リトライ": self.max_retries
            }
        }
        
        # コンソール出力
        print("\n" + "=" * 80)
        print("【バックテスト実行結果】")
        print(f"実行日時: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"ステータス: {report['ステータス']}")
        
        if results:
            print("\n【結果サマリー】")
            for key, value in results.items():
                print(f"  {key}: {value}")
        
        if problems:
            print("\n【エラー】")
            for problem in problems:
                print(f"  ❌ {problem}")
            
            # 根本原因分析
            print("\n【根本原因分析】")
            self._analyze_root_cause(problems)
        
        if warnings:
            print("\n【警告】")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        
        if not problems:
            print("\n✅ バックテストが正常に完了しました")
        
        print("=" * 80)
        
        # JSONレポート保存
        report_file = f"backtest_execution_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レポート保存: {report_file}")
        
        return report
    
    def _analyze_root_cause(self, problems):
        """根本原因の簡易分析"""
        problem_text = " ".join(problems).lower()
        
        if "取引が0件" in problem_text:
            print("  原因: エントリー条件が厳しすぎる可能性")
            print("  対策: パラメータの緩和、期間の延長")
        elif "error" in problem_text or "エラー" in problem_text:
            print("  原因: システムエラーまたはデータエラー")
            print("  対策: ログの詳細確認、データソースの検証")
        elif "損失" in problem_text:
            print("  原因: 戦略の問題またはマーケット状況")
            print("  対策: 戦略の見直し、リスク管理の強化")
    
    def cleanup(self):
        """クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行フロー"""
        try:
            # 1. 環境準備
            self.setup()
            
            # 2. WebUI接続
            if not self.login():
                raise Exception("ログインに失敗しました")
            
            # 3. バックテストページへの遷移
            if not self.navigate_to_backtest():
                raise Exception("バックテストページへの遷移に失敗しました")
            
            # 4. バックテスト実行タブへの移動
            if not self.navigate_to_execution_tab():
                logger.warning("実行タブへの移動をスキップ")
            
            # 5. バックテスト実行
            if not self.execute_backtest():
                raise Exception("バックテスト実行に失敗しました")
            
            # 実行監視
            if not self.monitor_execution():
                logger.error("バックテスト実行中にエラーが発生しました")
            
            # 6. ログ確認・問題判定
            results, problems, warnings = self.check_results()
            
            # 7. 結果処理
            report = self.process_results(results, problems, warnings)
            
            return len(problems) == 0
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            
            # エラー時のスクリーンショット
            try:
                self.driver.save_screenshot(f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            except:
                pass
            
            # エラーレポート
            self.process_results({}, [f"システムエラー: {str(e)}"], [])
            return False
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    import sys
    automation = CompleteBacktestExecution()
    success = automation.run()
    sys.exit(0 if success else 1)