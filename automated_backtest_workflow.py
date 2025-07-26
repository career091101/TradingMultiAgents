#!/usr/bin/env python3
"""
バックテスト自動実行ワークフロー

ステップ:
1. 環境準備 - Chrome起動 (完了)
2. WebUI接続 - ログイン処理
3. バックテストページへの遷移
4. バックテスト実行タブへの移動
5. バックテスト実行
6. ログ確認・問題判定
7. 結果処理
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import requests
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BacktestAutomation:
    """バックテスト自動実行クラス"""
    
    def __init__(self, base_url: str = "http://localhost:8501"):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.session = requests.Session()
        self.max_retries = 3
        self.timeout = 600  # 10分のタイムアウト
        self.results = {
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "errors": [],
            "success": False
        }
        
    def setup_driver(self) -> bool:
        """既存のChromeインスタンスに接続"""
        logger.info("既存のChromeインスタンスに接続中...")
        
        try:
            # Chrome DevTools Protocol経由で接続
            options = Options()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 20)
            
            # 現在のURLを確認
            current_url = self.driver.current_url
            logger.info(f"接続成功: {current_url}")
            
            # localhost:8501にいることを確認
            if "localhost:8501" not in current_url:
                self.driver.get(self.base_url)
                time.sleep(3)
            
            self.results["steps"].append({
                "step": "setup_driver",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Chrome接続エラー: {e}")
            self.results["errors"].append({
                "step": "setup_driver",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def check_webui_status(self) -> bool:
        """WebUIの状態を確認"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WebUI接続エラー: {e}")
            return False
    
    def login(self, username: str = "user", password: str = "user123") -> bool:
        """WebUIにログイン"""
        logger.info(f"ログイン処理開始: {username}")
        
        try:
            # ログインフォームの検出
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='Username']"))
            )
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[aria-label='Password']")
            
            # 入力フィールドをクリア
            username_input.clear()
            password_input.clear()
            
            # 認証情報を入力
            username_input.send_keys(username)
            password_input.send_keys(password)
            
            # ログインボタンをクリック
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            login_button.click()
            
            # ログイン成功を待つ
            time.sleep(3)
            
            # ダッシュボードが表示されたことを確認
            dashboard_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Trading Agents WebUI')]")),
                message="ログイン後のダッシュボード表示を待機中"
            )
            
            logger.info("ログイン成功")
            self.results["steps"].append({
                "step": "login",
                "status": "success",
                "username": username,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except TimeoutException:
            logger.error("ログインタイムアウト")
            self.results["errors"].append({
                "step": "login",
                "error": "Login timeout",
                "timestamp": datetime.now().isoformat()
            })
            return False
        except Exception as e:
            logger.error(f"ログインエラー: {e}")
            self.results["errors"].append({
                "step": "login",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def navigate_to_backtest(self) -> bool:
        """バックテストページへ遷移"""
        logger.info("バックテストページへの遷移開始")
        
        try:
            # サイドバーのバックテストボタンを探す
            backtest_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'バックテスト')]"))
            )
            backtest_button.click()
            
            # ページ遷移を待つ
            time.sleep(2)
            
            # バックテストページが表示されたことを確認
            backtest_page = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'バックテスト2')] | //h1[contains(text(), 'バックテスト')]"))
            )
            
            logger.info("バックテストページへの遷移成功")
            self.results["steps"].append({
                "step": "navigate_to_backtest",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"バックテストページ遷移エラー: {e}")
            self.results["errors"].append({
                "step": "navigate_to_backtest",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def go_to_execution_tab(self) -> bool:
        """実行タブへ移動"""
        logger.info("実行タブへの移動開始")
        
        try:
            # タブを探す（複数の可能なセレクタを試す）
            tab_selectors = [
                "//button[contains(text(), '実行')]",
                "//div[@role='tab'][contains(text(), '実行')]",
                "//p[contains(text(), '実行')]/ancestor::button"
            ]
            
            execution_tab = None
            for selector in tab_selectors:
                try:
                    execution_tab = self.driver.find_element(By.XPATH, selector)
                    if execution_tab:
                        break
                except NoSuchElementException:
                    continue
            
            if not execution_tab:
                raise Exception("実行タブが見つかりません")
            
            execution_tab.click()
            time.sleep(2)
            
            logger.info("実行タブへの移動成功")
            self.results["steps"].append({
                "step": "go_to_execution_tab",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"実行タブ移動エラー: {e}")
            self.results["errors"].append({
                "step": "go_to_execution_tab",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def execute_backtest(self) -> bool:
        """バックテストを実行"""
        logger.info("バックテスト実行開始")
        
        try:
            # 実行ボタンを探す
            execute_button_selectors = [
                "//button[contains(text(), 'バックテストを実行')]",
                "//button[contains(text(), '実行')]",
                "//button[@type='primary'][contains(text(), '実行')]"
            ]
            
            execute_button = None
            for selector in execute_button_selectors:
                try:
                    execute_button = self.driver.find_element(By.XPATH, selector)
                    if execute_button and execute_button.is_enabled():
                        break
                except NoSuchElementException:
                    continue
            
            if not execute_button:
                raise Exception("実行ボタンが見つかりません")
            
            # 実行前のスクリーンショット
            self.driver.save_screenshot("before_execution.png")
            
            execute_button.click()
            logger.info("実行ボタンクリック完了")
            
            # 実行開始を確認
            time.sleep(3)
            
            self.results["steps"].append({
                "step": "execute_backtest",
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"バックテスト実行エラー: {e}")
            self.results["errors"].append({
                "step": "execute_backtest",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def monitor_execution(self, timeout: int = 300) -> bool:
        """実行を監視してログを確認"""
        logger.info("実行監視開始")
        start_time = time.time()
        logs = []
        
        try:
            while time.time() - start_time < timeout:
                # プログレスバーまたは完了メッセージを探す
                try:
                    # 成功メッセージ
                    success_msg = self.driver.find_element(By.XPATH, "//div[contains(@class, 'success') and contains(text(), '完了')]")
                    if success_msg:
                        logger.info("バックテスト完了検出")
                        break
                except NoSuchElementException:
                    pass
                
                try:
                    # エラーメッセージ
                    error_msg = self.driver.find_element(By.XPATH, "//div[contains(@class, 'error')]")
                    if error_msg:
                        error_text = error_msg.text
                        logger.error(f"エラー検出: {error_text}")
                        logs.append({
                            "type": "error",
                            "message": error_text,
                            "timestamp": datetime.now().isoformat()
                        })
                except NoSuchElementException:
                    pass
                
                # ログ出力を収集
                try:
                    log_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'log') or contains(@class, 'output')]")
                    for log_elem in log_elements:
                        log_text = log_elem.text
                        if log_text and log_text not in [log["message"] for log in logs]:
                            logs.append({
                                "type": "log",
                                "message": log_text,
                                "timestamp": datetime.now().isoformat()
                            })
                except:
                    pass
                
                time.sleep(5)
            
            # 実行後のスクリーンショット
            self.driver.save_screenshot("after_execution.png")
            
            self.results["steps"].append({
                "step": "monitor_execution",
                "status": "completed",
                "logs": logs,
                "duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"実行監視エラー: {e}")
            self.results["errors"].append({
                "step": "monitor_execution",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def collect_results(self) -> bool:
        """結果を収集"""
        logger.info("結果収集開始")
        
        try:
            # 結果タブに移動
            results_tab_selectors = [
                "//button[contains(text(), '結果')]",
                "//div[@role='tab'][contains(text(), '結果')]",
                "//p[contains(text(), '結果')]/ancestor::button"
            ]
            
            for selector in results_tab_selectors:
                try:
                    results_tab = self.driver.find_element(By.XPATH, selector)
                    if results_tab:
                        results_tab.click()
                        time.sleep(2)
                        break
                except NoSuchElementException:
                    continue
            
            # メトリクスを収集
            metrics = {}
            metric_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'metric')]")
            
            for elem in metric_elements:
                try:
                    label = elem.find_element(By.XPATH, ".//label").text
                    value = elem.find_element(By.XPATH, ".//div[@class='metric-value']").text
                    metrics[label] = value
                except:
                    pass
            
            # 結果のスクリーンショット
            self.driver.save_screenshot("results.png")
            
            self.results["steps"].append({
                "step": "collect_results",
                "status": "success",
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"結果収集エラー: {e}")
            self.results["errors"].append({
                "step": "collect_results",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def wait_for_webui(self, timeout: int = 30) -> bool:
        """WebUIの起動を待機"""
        logger.info("WebUIの起動を待機中...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_webui_status():
                logger.info("WebUIが起動しました")
                return True
            time.sleep(2)
        
        logger.error("WebUIの起動がタイムアウトしました")
        return False
    
    def analyze_logs(self, log_content: str) -> Dict[str, Any]:
        """ログ内容を解析して問題を判定"""
        problems = []
        warnings = []
        
        # エラーパターンの検出
        error_patterns = [
            "ERROR",
            "FAILED",
            "Exception",
            "Traceback",
            "Failed to",
            "Could not",
            "Unable to"
        ]
        
        # 警告パターンの検出
        warning_patterns = [
            "WARNING",
            "WARN",
            "Deprecated",
            "Skipping"
        ]
        
        lines = log_content.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # エラー検出
            for pattern in error_patterns:
                if pattern.lower() in line_lower:
                    context = lines[max(0, i-2):min(len(lines), i+3)]
                    problems.append({
                        'type': 'error',
                        'pattern': pattern,
                        'line': line,
                        'context': '\n'.join(context),
                        'line_number': i + 1
                    })
                    break
            
            # 警告検出
            for pattern in warning_patterns:
                if pattern.lower() in line_lower:
                    warnings.append({
                        'type': 'warning',
                        'pattern': pattern,
                        'line': line,
                        'line_number': i + 1
                    })
                    break
        
        # 実行時間の妥当性チェック
        execution_time = self._extract_execution_time(log_content)
        if execution_time and execution_time > 300:  # 5分以上
            warnings.append({
                'type': 'performance',
                'message': f'実行時間が長すぎます: {execution_time}秒'
            })
        
        return {
            'has_problems': len(problems) > 0,
            'problems': problems,
            'warnings': warnings,
            'execution_time': execution_time,
            'summary': self._generate_summary(problems, warnings)
        }
    
    def _extract_execution_time(self, log_content: str) -> Optional[float]:
        """ログから実行時間を抽出"""
        import re
        
        # 実行時間のパターンを検索
        patterns = [
            r'Execution time: ([\d.]+) seconds',
            r'Total time: ([\d.]+)s',
            r'Completed in ([\d.]+) seconds'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_content)
            if match:
                return float(match.group(1))
        
        return None
    
    def _generate_summary(self, problems: List[Dict], warnings: List[Dict]) -> str:
        """問題と警告のサマリーを生成"""
        if not problems and not warnings:
            return "問題は検出されませんでした。"
        
        summary_parts = []
        
        if problems:
            summary_parts.append(f"エラー: {len(problems)}件")
            # エラータイプの集計
            error_types = {}
            for problem in problems:
                pattern = problem['pattern']
                error_types[pattern] = error_types.get(pattern, 0) + 1
            
            for error_type, count in error_types.items():
                summary_parts.append(f"  - {error_type}: {count}件")
        
        if warnings:
            summary_parts.append(f"警告: {len(warnings)}件")
        
        return '\n'.join(summary_parts)
    
    def generate_report(self, analysis_result: Dict[str, Any], 
                       execution_status: Dict[str, Any]) -> str:
        """分析結果のレポートを生成"""
        report = []
        report.append("=" * 60)
        report.append("バックテスト自動実行レポート")
        report.append("=" * 60)
        report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"WebUI URL: {self.base_url}")
        report.append("")
        
        # 実行ステータス
        report.append("## 実行ステータス")
        report.append(f"ステータス: {execution_status.get('status', 'Unknown')}")
        report.append(f"実行時間: {execution_status.get('duration', 'N/A')}秒")
        report.append("")
        
        # 分析結果
        report.append("## ログ分析結果")
        report.append(f"問題検出: {'あり' if analysis_result['has_problems'] else 'なし'}")
        report.append("")
        
        if analysis_result['problems']:
            report.append("### エラー詳細")
            for i, problem in enumerate(analysis_result['problems'], 1):
                report.append(f"\n{i}. {problem['pattern']} (行 {problem['line_number']})")
                report.append(f"   内容: {problem['line']}")
                report.append("   コンテキスト:")
                for ctx_line in problem['context'].split('\n'):
                    report.append(f"     {ctx_line}")
        
        if analysis_result['warnings']:
            report.append("\n### 警告")
            for warning in analysis_result['warnings']:
                if warning['type'] == 'performance':
                    report.append(f"- {warning['message']}")
                else:
                    report.append(f"- {warning['pattern']} (行 {warning['line_number']})")
        
        # 推奨アクション
        report.append("\n## 推奨アクション")
        if analysis_result['has_problems']:
            report.append("1. エラーログを確認し、根本原因を特定してください")
            report.append("2. 設定ファイルやAPIキーの確認を行ってください")
            report.append("3. データソースの接続状態を確認してください")
        else:
            report.append("- 問題は検出されませんでした")
            report.append("- 定期的な監視を継続してください")
        
        report.append("\n" + "=" * 60)
        
        return '\n'.join(report)
    
    def save_report(self, report: str, filename: Optional[str] = None):
        """レポートをファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"レポートを保存しました: {filename}")
    
    def execute_workflow(self) -> Dict[str, Any]:
        """ワークフロー全体を実行"""
        logger.info("=== バックテスト自動実行ワークフロー開始 ===")
        
        try:
            # 1. Chrome接続
            if not self.setup_driver():
                raise Exception("Chrome接続失敗")
            
            # 2. ログイン
            if not self.login():
                raise Exception("ログイン失敗")
            
            # 3. バックテストページへ遷移
            if not self.navigate_to_backtest():
                raise Exception("バックテストページ遷移失敗")
            
            # 4. 実行タブへ移動
            if not self.go_to_execution_tab():
                raise Exception("実行タブ移動失敗")
            
            # 5. バックテスト実行
            if not self.execute_backtest():
                raise Exception("バックテスト実行失敗")
            
            # 6. 実行監視
            if not self.monitor_execution():
                raise Exception("実行監視失敗")
            
            # 7. 結果収集
            if not self.collect_results():
                raise Exception("結果収集失敗")
            
            self.results["success"] = True
            logger.info("=== ワークフロー正常完了 ===")
            
            # ログ分析
            if self.results["steps"]:
                logs_step = next((s for s in self.results["steps"] if s["step"] == "monitor_execution"), None)
                if logs_step and "logs" in logs_step:
                    log_content = "\n".join([log["message"] for log in logs_step["logs"]])
                    analysis_result = self.analyze_logs(log_content)
                    
                    # レポート生成
                    execution_status = {
                        "status": "completed",
                        "duration": logs_step.get("duration", 0)
                    }
                    report = self.generate_report(analysis_result, execution_status)
                    self.save_report(report)
            
            return self.results
            
        except Exception as e:
            logger.error(f"ワークフローエラー: {e}")
            self.results["success"] = False
            self.results["final_error"] = str(e)
            return self.results
        
        finally:
            # 結果を保存
            self.save_results()
    
    def save_results(self):
        """結果をファイルに保存"""
        self.results["end_time"] = datetime.now().isoformat()
        
        filename = f"backtest_automation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"結果を保存: {filename}")
        
        # サマリーを表示
        logger.info("\n=== 実行サマリー ===")
        logger.info(f"成功: {self.results['success']}")
        logger.info(f"ステップ数: {len(self.results['steps'])}")
        logger.info(f"エラー数: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            logger.info("\n=== エラー詳細 ===")
            for error in self.results["errors"]:
                logger.info(f"- {error['step']}: {error['error']}")

def main():
    """メイン実行関数"""
    automation = BacktestAutomation()
    
    # WebUIが起動していない場合は起動を試みる
    if not automation.check_webui_status():
        logger.info("WebUIが起動していません。起動を試みます...")
        
        webui_path = Path(__file__).parent / "TradingMultiAgents" / "run_webui.py"
        if webui_path.exists():
            subprocess.Popen([sys.executable, str(webui_path)], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(10)  # 起動を待つ
    
    # ワークフロー実行
    result = automation.execute_workflow()
    
    if result.get('success'):
        logger.info("ワークフローが正常に完了しました")
    else:
        logger.error("ワークフローの実行に失敗しました")
        logger.error(f"詳細: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    logger.info("Chromeブラウザは開いたままにしています。手動で確認してください。")

if __name__ == "__main__":
    main()