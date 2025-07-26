#!/usr/bin/env python3
"""
統合バックテスト自動実行ワークフロー
実行から取引ゼロ分析まで完全自動化
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from browser_config import create_driver, log_browser_info
from backtest_zero_trade_analyzer import ZeroTradeAnalyzer
import time
import logging
import re
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedBacktestWorkflow:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.execution_log = []
        self.retry_count = 0
        self.max_retries = 3
        
    def setup(self):
        """1. 環境準備"""
        logger.info("=== 統合バックテスト自動実行ワークフロー ===")
        logger.info("1. 環境準備: Chromeブラウザ起動")
        
        self.driver = create_driver()
        self.wait = WebDriverWait(self.driver, 30)
        log_browser_info(self.driver)
        
        self.log_event("環境準備", "完了")
        
    def log_event(self, event: str, status: str, details: str = ""):
        """イベントログ記録"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "status": status,
            "details": details
        })
        
    def login(self) -> bool:
        """2. WebUI接続"""
        logger.info("2. WebUI接続")
        
        for attempt in range(self.max_retries):
            try:
                self.driver.get("http://localhost:8501")
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
                    
                    self.log_event("ログイン", "成功")
                    logger.info("✓ ログイン成功")
                    time.sleep(5)
                    return True
                    
                except:
                    logger.info("既にログイン済み")
                    return True
                    
            except Exception as e:
                self.retry_count += 1
                self.log_event("ログイン", "エラー", str(e))
                logger.error(f"接続エラー (試行 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(5)
                else:
                    return False
                    
        return False
    
    def navigate_to_backtest(self) -> bool:
        """3. バックテストページへの遷移"""
        logger.info("3. バックテストページへの遷移")
        
        try:
            # バックテストボタンを探す（正しいボタンテキスト）
            patterns = [
                "//button[contains(text(), '📊 バックテスト')]",
                "//button[contains(., '📊 バックテスト')]",
                "//button[@key='nav_backtest2']",
                "//button[contains(., 'バックテスト') and not(contains(., '実行'))]"
            ]
            
            button_found = False
            for pattern in patterns:
                try:
                    buttons = self.driver.find_elements(By.XPATH, pattern)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", button)
                            button_found = True
                            break
                    if button_found:
                        break
                except:
                    continue
            
            if button_found:
                self.log_event("バックテスト遷移", "成功")
                logger.info("✓ バックテストページへ移動")
                time.sleep(3)
                return True
            else:
                self.log_event("バックテスト遷移", "失敗", "ボタンが見つからない")
                return False
                
        except Exception as e:
            self.log_event("バックテスト遷移", "エラー", str(e))
            logger.error(f"ナビゲーションエラー: {e}")
            return False
    
    def find_and_click_execution_button(self) -> bool:
        """4-5. 実行タブの検索と実行ボタンのクリック"""
        logger.info("4-5. バックテスト実行")
        
        try:
            # まず実行タブを探す
            tab_patterns = [
                "//p[contains(text(), 'バックテスト実行')]",
                "//button[contains(text(), 'バックテスト実行')]",
                "//div[contains(@role, 'tab') and contains(., '実行')]"
            ]
            
            for pattern in tab_patterns:
                try:
                    tab = self.driver.find_element(By.XPATH, pattern)
                    if tab.is_displayed():
                        # タブのクリック可能な要素を探す
                        clickable = tab
                        if tab.tag_name == 'p':
                            # 親要素を探す
                            parent = tab.find_element(By.XPATH, "./..")
                            if parent.tag_name in ['button', 'div']:
                                clickable = parent
                        
                        clickable.click()
                        logger.info("✓ バックテスト実行タブに切り替え")
                        time.sleep(2)
                        break
                except:
                    continue
            
            # ページを下にスクロールして実行ボタンを探す
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # スクリーンショット（デバッグ用）
            self.driver.save_screenshot("before_execution_button_search.png")
            
            # 実行ボタンを探す
            execute_patterns = [
                "//button[contains(text(), 'マルチエージェントバックテストを開始')]",
                "//button[contains(text(), '✓ マルチエージェントバックテストを開始')]",
                "//button[contains(text(), 'バックテストを開始')]",
                "//button[contains(text(), '実行') and contains(@style, 'background')]",
                "//button[contains(@class, 'stButton') and contains(., '開始')]"
            ]
            
            execute_button = None
            for pattern in execute_patterns:
                try:
                    buttons = self.driver.find_elements(By.XPATH, pattern)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            logger.info(f"実行ボタン発見: {button.text}")
                            execute_button = button
                            break
                    if execute_button:
                        break
                except:
                    continue
            
            # すべてのボタンをチェック（フォールバック）
            if not execute_button:
                all_buttons = self.driver.find_elements(By.XPATH, "//button")
                for button in all_buttons:
                    try:
                        text = button.text.strip()
                        if text and button.is_displayed():
                            if "開始" in text and "マルチ" in text:
                                execute_button = button
                                logger.info(f"実行ボタン発見（フォールバック）: {text}")
                                break
                    except:
                        pass
            
            if execute_button:
                # ボタンが見えるようにスクロール
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", execute_button)
                time.sleep(1)
                
                # クリック
                try:
                    execute_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", execute_button)
                
                self.log_event("バックテスト実行", "開始")
                logger.info("✓ バックテスト実行開始")
                
                # 実行後のスクリーンショット
                time.sleep(3)
                self.driver.save_screenshot("after_execution_click.png")
                
                return True
            else:
                self.log_event("バックテスト実行", "失敗", "実行ボタンが見つからない")
                logger.error("実行ボタンが見つかりません")
                self.driver.save_screenshot("no_execution_button_found.png")
                return False
                
        except Exception as e:
            self.log_event("バックテスト実行", "エラー", str(e))
            logger.error(f"実行エラー: {e}")
            return False
    
    def monitor_execution(self, timeout: int = 900) -> bool:
        """実行監視（最大15分）"""
        logger.info("実行状態を監視中...")
        
        start_time = time.time()
        last_screenshot_time = start_time
        
        while time.time() - start_time < timeout:
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # エラーチェック
                if self._check_for_errors(page_text):
                    return False
                
                # 完了チェック
                if self._check_completion(page_text):
                    self.log_event("バックテスト完了", "成功")
                    logger.info("✓ バックテスト完了")
                    return True
                
                # 進捗表示
                elapsed = int(time.time() - start_time)
                if elapsed % 60 == 0:
                    logger.info(f"実行中... ({elapsed}秒経過)")
                    self.driver.save_screenshot(f"execution_progress_{elapsed}s.png")
                
                # プログレス情報の抽出
                progress_match = re.search(r'(\d+)/(\d+)', page_text)
                if progress_match:
                    logger.info(f"進捗: {progress_match.group(0)}")
                
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"監視中のエラー: {e}")
        
        logger.warning("実行タイムアウト")
        return True  # タイムアウトでも結果を確認
    
    def _check_for_errors(self, page_text: str) -> bool:
        """エラーチェック"""
        error_keywords = ["error", "エラー", "失敗", "failed", "exception"]
        
        for keyword in error_keywords:
            if keyword.lower() in page_text.lower():
                # StreamlitのUIエラーは除外
                if "streamlit" not in page_text.lower():
                    return True
        
        return False
    
    def _check_completion(self, page_text: str) -> bool:
        """完了チェック"""
        completion_keywords = [
            "バックテスト実行", "設定サマリー",
            "取引", "初期資金", "ティッカー数",
            "Complete", "Finished", "Results"
        ]
        
        # 複数のキーワードが含まれていれば完了
        matches = sum(1 for keyword in completion_keywords if keyword in page_text)
        return matches >= 3
    
    def extract_results(self) -> Tuple[Dict, List[str], List[str]]:
        """6. ログ確認・問題判定"""
        logger.info("6. ログ確認・問題判定")
        
        results = {}
        problems = []
        warnings = []
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 結果の抽出（実際の画面から）
            patterns = {
                "ティッカー数": r"ティッカー数[：:\s]*(\d+)",
                "取引": r"取引[：:\s]*(\d+)",
                "初期資金": r"初期資金[：:\s]*([\$¥][0-9,]+)",
                "最大ポジション数": r"最大ポジション数[：:\s]*(\d+)",
                "LLMプロバイダー": r"LLMプロバイダー[：:\s]*(\w+)",
                "エージェント": r"エージェント[：:\s]*(.+?)(?:\n|$)"
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, page_text)
                if match:
                    results[key] = match.group(1).strip()
            
            # 取引数の特別な処理
            if "取引" in results:
                results["trades"] = int(results["取引"])
                if results["trades"] == 0:
                    warnings.append("取引が0件です - 詳細分析が必要です")
            
            # スクリーンショット保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_screenshot = f"backtest_final_result_{timestamp}.png"
            self.driver.save_screenshot(final_screenshot)
            logger.info(f"最終結果スクリーンショット: {final_screenshot}")
            
            self.log_event("結果抽出", "完了", f"取引数: {results.get('trades', 'N/A')}")
            
        except Exception as e:
            self.log_event("結果抽出", "エラー", str(e))
            problems.append(f"結果抽出エラー: {str(e)}")
            
        return results, problems, warnings
    
    def analyze_zero_trades(self, results: Dict) -> Optional[Dict]:
        """7. 取引量ゼロチェックと詳細分析"""
        if results.get("trades", 0) == 0:
            logger.info("7. 取引量ゼロの詳細分析を開始")
            
            # 分析用データを準備
            analysis_results = {
                "trades": 0,
                "initial_capital": results.get("初期資金", "$100,000"),
                "tickers": results.get("ティッカー数", 2),
                "agents": results.get("エージェント", "10専門エージェント"),
                "llm_provider": results.get("LLMプロバイダー", "openai"),
                "max_positions": results.get("最大ポジション数", 5)
            }
            
            # ZeroTradeAnalyzerを使用
            analyzer = ZeroTradeAnalyzer(analysis_results, self.execution_log)
            analysis = analyzer.perform_comprehensive_analysis()
            report = analyzer.generate_report(analysis)
            
            # レポート表示
            print("\n" + "="*80)
            print(report)
            print("="*80 + "\n")
            
            # ファイル保存
            analyzer.save_analysis(analysis, report)
            
            return analysis
        
        return None
    
    def handle_retry(self, analysis: Dict) -> bool:
        """8. エラーハンドリング - リトライ判定"""
        if self.retry_count >= self.max_retries:
            logger.warning("最大リトライ回数に到達")
            return False
        
        # 根本原因に基づいてリトライ戦略を決定
        root_cause = analysis.get("root_cause_analysis", {}).get("most_likely_root_cause", "")
        
        if "パラメータ" in root_cause:
            logger.info("パラメータ調整後のリトライを推奨")
            print("\n推奨: エントリー条件を緩和して再実行してください")
            return False  # 手動介入が必要
        elif "データ" in root_cause:
            logger.info("データソース確認後のリトライを推奨")
            return False  # 手動介入が必要
        else:
            # 単純なリトライ
            self.retry_count += 1
            logger.info(f"リトライ {self.retry_count}/{self.max_retries}")
            time.sleep(30)  # 30秒待機
            return True
    
    def generate_final_report(self, results: Dict, problems: List[str], 
                            warnings: List[str], zero_trade_analysis: Optional[Dict]):
        """9. 結果処理 - 最終レポート生成"""
        logger.info("9. 最終レポート生成")
        
        timestamp = datetime.now()
        
        # 統合レポート
        report = {
            "execution_timestamp": timestamp.isoformat(),
            "workflow_status": "completed",
            "retry_count": self.retry_count,
            "results": results,
            "problems": problems,
            "warnings": warnings,
            "execution_log": self.execution_log,
            "zero_trade_analysis": zero_trade_analysis
        }
        
        # JSON保存
        report_file = f"integrated_backtest_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"統合レポート保存: {report_file}")
        
        # サマリー表示
        print("\n" + "="*80)
        print("【バックテスト自動実行ワークフロー完了】")
        print(f"実行日時: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"リトライ回数: {self.retry_count}")
        print(f"取引数: {results.get('trades', 'N/A')}")
        
        if zero_trade_analysis:
            print("\n⚠️ 取引が0件でした。詳細分析レポートを確認してください。")
            print("推奨アクション:")
            recommendations = zero_trade_analysis.get("recommendations", {}).get("immediate_actions", [])
            for i, action in enumerate(recommendations[:2], 1):
                print(f"  {i}. {action.get('action', 'N/A')}")
        
        print("="*80)
    
    def cleanup(self):
        """10. クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self) -> bool:
        """メインワークフロー実行"""
        try:
            # 1. 環境準備
            self.setup()
            
            while self.retry_count < self.max_retries:
                # 2. WebUI接続
                if not self.login():
                    raise Exception("ログイン失敗")
                
                # 3. バックテストページへの遷移
                if not self.navigate_to_backtest():
                    raise Exception("バックテストページ遷移失敗")
                
                # 4-5. バックテスト実行
                if not self.find_and_click_execution_button():
                    raise Exception("バックテスト実行失敗")
                
                # 実行監視
                self.monitor_execution()
                
                # 6. ログ確認・問題判定
                results, problems, warnings = self.extract_results()
                
                # 7. 取引量ゼロチェックと詳細分析
                zero_trade_analysis = None
                if results.get("trades", 0) == 0:
                    zero_trade_analysis = self.analyze_zero_trades(results)
                    
                    # 8. エラーハンドリング
                    if zero_trade_analysis and self.handle_retry(zero_trade_analysis):
                        continue  # リトライ
                
                # 9. 結果処理
                self.generate_final_report(results, problems, warnings, zero_trade_analysis)
                
                return len(problems) == 0
            
            logger.warning("最大リトライ回数を超過しました")
            return False
            
        except Exception as e:
            logger.error(f"ワークフローエラー: {e}")
            import traceback
            traceback.print_exc()
            
            self.log_event("ワークフロー", "エラー", str(e))
            self.generate_final_report({}, [f"ワークフローエラー: {str(e)}"], [], None)
            return False
            
        finally:
            self.cleanup()


def main():
    """メインエントリーポイント"""
    workflow = IntegratedBacktestWorkflow()
    success = workflow.run()
    
    if not success:
        print("\n次のステップ:")
        print("1. エラーログを確認してください")
        print("2. パラメータを調整して再実行してください")
        print("3. サポートが必要な場合は、生成されたレポートを共有してください")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())