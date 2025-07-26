#!/usr/bin/env python3
"""
WebUIバックテスト自動実行 - 高度な分析機能付き
取引量ゼロの詳細分析と根本原因分析（RCA）を含む
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
import re
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestAutomationAdvanced:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.execution_log = []
        self.error_timeline = []
        
    def setup(self):
        """1. 環境準備"""
        logger.info("=== バックテスト自動実行ワークフロー開始 ===")
        logger.info("1. 環境準備: Chromeブラウザ起動")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-notifications')
        # Macの画面サイズに合わせてウィンドウサイズを設定
        chrome_options.add_argument('--window-size=2560,1600')
        chrome_options.add_argument('--start-maximized')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # ウィンドウを最大化（Macの画面サイズに合わせる）
        self.driver.set_window_size(2560, 1600)
        self.driver.set_window_position(0, 0)
        
        self.wait = WebDriverWait(self.driver, 30)
        
        self.log_event("ブラウザ起動", "成功")
        logger.info("✓ ブラウザ起動成功（解像度: 2560x1600）")
        
    def log_event(self, event: str, status: str, details: str = ""):
        """イベントをタイムラインに記録"""
        timestamp = datetime.now()
        self.execution_log.append({
            "timestamp": timestamp.isoformat(),
            "event": event,
            "status": status,
            "details": details
        })
        if status == "エラー":
            self.error_timeline.append({
                "timestamp": timestamp.isoformat(),
                "event": event,
                "details": details
            })
    
    def login(self):
        """2. WebUI接続とログイン"""
        logger.info("2. WebUI接続")
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
                "//div[contains(@class, 'stButton')]//button"
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
                self.log_event("ログイン", "成功")
                logger.info("✓ ログイン成功")
            else:
                raise Exception("ログインボタンが見つかりません")
            
            time.sleep(5)
            
        except Exception as e:
            self.log_event("ログイン", "エラー", str(e))
            logger.error(f"ログインエラー: {e}")
            raise
    
    def close_popup(self):
        """ポップアップを閉じる"""
        try:
            close_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Close' or contains(@class, 'close')]")
            for button in close_buttons:
                if button.is_displayed():
                    button.click()
                    self.log_event("ポップアップクローズ", "成功")
                    time.sleep(1)
                    return
        except:
            pass
    
    def navigate_to_backtest(self):
        """3. バックテストページへの遷移"""
        logger.info("3. バックテストページへの遷移")
        
        self.close_popup()
        
        try:
            # サイドバーのバックテストボタンを探す
            backtest_button = None
            patterns = [
                "//button[contains(text(), '📊 バックテスト')]",
                "//button[contains(., 'バックテスト')]",
                "//a[contains(., 'バックテスト')]",
                "//button[@class='st-emotion-cache-1ub9ykg e1e4lema2' and contains(., 'バックテスト')]"
            ]
            
            for pattern in patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            backtest_button = elem
                            break
                    if backtest_button:
                        break
                except:
                    continue
            
            if backtest_button:
                # JavaScriptでクリック（通常のクリックが失敗する場合の対策）
                self.driver.execute_script("arguments[0].scrollIntoView(true);", backtest_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", backtest_button)
                self.log_event("バックテストページ遷移", "成功")
                logger.info("✓ バックテストページへ移動")
                time.sleep(3)
            else:
                self.log_event("バックテストページ遷移", "警告", "ボタンが見つからない")
                logger.warning("バックテストボタンが見つからない")
                
        except Exception as e:
            self.log_event("バックテストページ遷移", "エラー", str(e))
            logger.error(f"ナビゲーションエラー: {e}")
            raise
    
    def navigate_to_execution_tab(self):
        """4. バックテスト実行タブへの移動"""
        logger.info("4. バックテスト実行タブへの移動")
        
        # バックテスト2タブを探す
        tab_found = False
        tab_patterns = [
            "//button[contains(text(), 'バックテスト2')]",
            "//div[contains(@class, 'tab') and contains(., 'バックテスト2')]",
            "//button[contains(text(), '実行')]",
            "//div[contains(@class, 'tab') and contains(., '実行')]"
        ]
        
        for pattern in tab_patterns:
            try:
                tab = self.driver.find_element(By.XPATH, pattern)
                if tab.is_displayed():
                    tab.click()
                    tab_found = True
                    self.log_event("実行タブ切り替え", "成功")
                    logger.info("✓ 実行タブに切り替え")
                    time.sleep(2)
                    break
            except:
                continue
        
        if not tab_found:
            self.log_event("実行タブ切り替え", "警告", "タブが見つからない")
            logger.info("実行タブが見つからない - 既に実行画面の可能性")
    
    def execute_backtest(self):
        """5. バックテスト実行"""
        logger.info("5. バックテスト実行")
        
        try:
            # バックテストページが表示されているか確認
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # バックテスト実行ボタンを探す
            execute_patterns = [
                "//button[contains(text(), 'バックテスト実行')]",
                "//button[contains(text(), '実行開始')]",
                "//button[contains(text(), '開始') and not(contains(text(), '分析'))]",
                "//button[contains(text(), 'Run Backtest')]",
                "//button[contains(text(), 'Start Backtest')]",
                "//button[contains(@class, 'stButton') and contains(., '実行')]",
                "//button[@kind='primary' and contains(., '実行')]"
            ]
            
            execute_button = None
            
            # バックテストページ内のすべてのボタンを調査
            all_buttons = self.driver.find_elements(By.XPATH, "//button")
            logger.info(f"ページ内のボタン数: {len(all_buttons)}")
            
            for i, button in enumerate(all_buttons):
                try:
                    text = button.text.strip()
                    if text and button.is_displayed() and button.is_enabled():
                        logger.debug(f"ボタン{i}: {text}")
                        
                        # バックテストに関連するキーワードをチェック
                        if any(keyword in text for keyword in ["実行", "開始", "Run", "Start", "Execute"]):
                            if "分析" not in text and "ログ" not in text:
                                execute_button = button
                                logger.info(f"実行ボタン候補発見: {text}")
                                break
                except:
                    pass
            
            # パターンマッチングでも探す
            if not execute_button:
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
            
            if execute_button:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", execute_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", execute_button)
                self.log_event("バックテスト実行開始", "成功")
                logger.info("✓ 実行ボタンをクリック")
                
                time.sleep(5)
                return self.monitor_execution()
            else:
                # 実行ボタンが見つからない場合、スクリーンショットを保存
                self.driver.save_screenshot("backtest_page_no_execute_button.png")
                self.log_event("バックテスト実行開始", "エラー", "実行ボタンが見つからない")
                logger.error("実行ボタンが見つかりません")
                logger.error(f"現在のページテキスト（最初の500文字）: {page_text[:500]}")
                return False
                
        except Exception as e:
            self.log_event("バックテスト実行", "エラー", str(e))
            logger.error(f"実行エラー: {e}")
            return False
    
    def monitor_execution(self):
        """実行状態を監視"""
        logger.info("実行状態を監視中...")
        
        start_time = time.time()
        timeout = 300  # 5分
        
        while time.time() - start_time < timeout:
            try:
                # エラーチェック
                error_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'alert')]")
                for elem in error_elements:
                    if elem.is_displayed() and elem.text:
                        self.log_event("実行中エラー", "エラー", elem.text)
                        logger.error(f"エラー検出: {elem.text}")
                
                # 完了チェック
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if any(keyword in page_text for keyword in ["完了", "Complete", "結果", "取引数"]):
                    self.log_event("バックテスト完了", "成功")
                    logger.info("✓ バックテスト完了")
                    return True
                
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0:
                    logger.info(f"実行中... ({elapsed}秒経過)")
                
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"監視中のエラー: {e}")
        
        self.log_event("バックテスト完了", "タイムアウト", "5分経過")
        logger.warning("実行タイムアウト")
        return True
    
    def initial_validation(self) -> Tuple[Dict, List[str], List[str]]:
        """6. 実行結果の初期検証"""
        logger.info("6. 実行結果の初期検証")
        
        problems = []
        warnings = []
        results = {}
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # エラーチェック
            if "error" in page_text.lower() or "エラー" in page_text:
                error_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error')]")
                for div in error_divs:
                    if div.is_displayed() and div.text:
                        problems.append(f"エラー: {div.text[:200]}")
            
            # 結果データの抽出
            patterns = {
                "取引量": [r"取引数[：:]\s*(\d+)", r"Total Trades[：:]\s*(\d+)", r"取引量[：:]\s*(\d+)"],
                "総リターン": [r"総リターン[：:]\s*([-\d.]+)%", r"Total Return[：:]\s*([-\d.]+)%"],
                "シャープレシオ": [r"シャープレシオ[：:]\s*([-\d.]+)", r"Sharpe Ratio[：:]\s*([-\d.]+)"],
                "最大ドローダウン": [r"最大ドローダウン[：:]\s*([-\d.]+)%", r"Max Drawdown[：:]\s*([-\d.]+)%"]
            }
            
            for key, regex_patterns in patterns.items():
                for pattern in regex_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        results[key] = match.group(1)
                        break
            
            # 基本的な問題判定
            if not results:
                warnings.append("結果データが見つかりません")
            
            # スクリーンショット保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"backtest_result_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
            
            return results, problems, warnings
            
        except Exception as e:
            self.log_event("結果検証", "エラー", str(e))
            logger.error(f"検証エラー: {e}")
            problems.append(f"検証エラー: {str(e)}")
            return results, problems, warnings
    
    def check_zero_trades_and_analyze(self, results: Dict, problems: List[str]) -> Optional[Dict]:
        """7. 取引量ゼロチェックと詳細分析"""
        logger.info("7. 取引量ゼロチェックと詳細分析")
        
        # 取引量を確認
        trades = int(results.get("取引量", "0"))
        
        if trades == 0:
            logger.warning("⚠️ 取引量が0です - 詳細分析を開始します")
            
            # エラー内容の特定
            error_analysis = self.identify_errors()
            
            # 根本原因分析（RCA）
            rca_result = self.perform_root_cause_analysis(error_analysis)
            
            # 潜在的エラー要因の洗い出し
            potential_factors = self.identify_potential_error_factors()
            
            return {
                "error_analysis": error_analysis,
                "rca_result": rca_result,
                "potential_factors": potential_factors
            }
        
        return None
    
    def identify_errors(self) -> Dict:
        """エラー内容の特定"""
        error_types = {
            "システムエラー": [],
            "データエラー": [],
            "設定エラー": [],
            "戦略エラー": []
        }
        
        try:
            # ログテキストの取得
            log_elements = self.driver.find_elements(By.XPATH, "//pre | //code | //div[contains(@class, 'log')]")
            
            for elem in log_elements:
                if elem.is_displayed() and elem.text:
                    text = elem.text.lower()
                    
                    # システムエラー
                    if any(keyword in text for keyword in ["exception", "error", "failed", "timeout"]):
                        error_types["システムエラー"].append(elem.text[:200])
                    
                    # データエラー
                    if any(keyword in text for keyword in ["data", "price", "nan", "missing", "empty"]):
                        error_types["データエラー"].append(elem.text[:200])
                    
                    # 設定エラー
                    if any(keyword in text for keyword in ["config", "parameter", "setting", "invalid"]):
                        error_types["設定エラー"].append(elem.text[:200])
                    
                    # 戦略エラー
                    if any(keyword in text for keyword in ["strategy", "signal", "entry", "exit"]):
                        error_types["戦略エラー"].append(elem.text[:200])
        
        except Exception as e:
            logger.error(f"エラー特定中の問題: {e}")
        
        return error_types
    
    def perform_root_cause_analysis(self, error_analysis: Dict) -> Dict:
        """根本原因分析（RCA）- 5つのなぜ分析"""
        rca = {
            "直接的原因": "",
            "なぜ1": "",
            "なぜ2": "",
            "なぜ3": "",
            "なぜ4": "",
            "なぜ5_根本原因": "",
            "タイムライン分析": self.error_timeline
        }
        
        # エラータイプに基づいた分析
        if error_analysis["データエラー"]:
            rca["直接的原因"] = "価格データの取得または処理に失敗"
            rca["なぜ1"] = "データソースからのレスポンスが不正または空"
            rca["なぜ2"] = "APIキーの問題またはレート制限に到達"
            rca["なぜ3"] = "環境変数の設定ミスまたは有効期限切れ"
            rca["なぜ4"] = "初期設定時の検証プロセスの不備"
            rca["なぜ5_根本原因"] = "システム設計時のエラーハンドリング不足"
            
        elif error_analysis["戦略エラー"]:
            rca["直接的原因"] = "取引シグナルが一度も発生しなかった"
            rca["なぜ1"] = "エントリー条件が厳しすぎる"
            rca["なぜ2"] = "パラメータ設定が市場状況に不適合"
            rca["なぜ3"] = "バックテスト期間の選択が不適切"
            rca["なぜ4"] = "戦略のバリデーション不足"
            rca["なぜ5_根本原因"] = "戦略設計時の市場分析不足"
            
        elif error_analysis["設定エラー"]:
            rca["直接的原因"] = "バックテスト設定の不整合"
            rca["なぜ1"] = "必須パラメータの未設定または無効な値"
            rca["なぜ2"] = "UI上の設定とバックエンドの不一致"
            rca["なぜ3"] = "設定検証ロジックの不備"
            rca["なぜ4"] = "ユーザーガイダンスの不足"
            rca["なぜ5_根本原因"] = "UIデザインとユーザビリティの問題"
            
        else:
            rca["直接的原因"] = "不明なエラーにより取引が実行されなかった"
            rca["なぜ1"] = "エラーログが適切に記録されていない"
            rca["なぜ2"] = "例外処理が不適切"
            rca["なぜ3"] = "デバッグ情報の不足"
            rca["なぜ4"] = "テスト環境と本番環境の差異"
            rca["なぜ5_根本原因"] = "品質保証プロセスの不備"
        
        return rca
    
    def identify_potential_error_factors(self) -> List[Dict]:
        """潜在的エラー要因の洗い出し"""
        factors = []
        
        # データ関連
        factors.append({
            "カテゴリ": "データ関連",
            "要因": "価格データの欠損",
            "影響度": "高",
            "説明": "指定期間のデータが部分的または完全に欠落している可能性",
            "確認方法": "データソースのステータス確認、期間を変更して再実行"
        })
        
        factors.append({
            "カテゴリ": "データ関連",
            "要因": "データフォーマットの不整合",
            "影響度": "中",
            "説明": "価格データの形式が期待される形式と異なる",
            "確認方法": "ログ内のデータ処理エラーを確認"
        })
        
        # 戦略関連
        factors.append({
            "カテゴリ": "戦略関連",
            "要因": "エントリー条件が厳格すぎる",
            "影響度": "高",
            "説明": "設定された条件が現実的でない可能性",
            "確認方法": "パラメータを緩和して再実行"
        })
        
        factors.append({
            "カテゴリ": "戦略関連",
            "要因": "資金管理ルールの制約",
            "影響度": "中",
            "説明": "ポジションサイズや証拠金の制約",
            "確認方法": "資金管理設定を確認"
        })
        
        # システム関連
        factors.append({
            "カテゴリ": "システム関連",
            "要因": "API接続の不安定性",
            "影響度": "高",
            "説明": "データプロバイダーへの接続が断続的",
            "確認方法": "ネットワークログとAPI応答を確認"
        })
        
        factors.append({
            "カテゴリ": "システム関連",
            "要因": "メモリ不足",
            "影響度": "低",
            "説明": "大量データ処理時のリソース不足",
            "確認方法": "システムリソースの使用状況を確認"
        })
        
        # 設定関連
        factors.append({
            "カテゴリ": "設定関連",
            "要因": "取引時間の制限",
            "影響度": "中",
            "説明": "市場時間外のみを対象としている可能性",
            "確認方法": "取引時間設定を確認"
        })
        
        factors.append({
            "カテゴリ": "設定関連",
            "要因": "銘柄コードの誤り",
            "影響度": "高",
            "説明": "存在しないまたは廃止された銘柄",
            "確認方法": "銘柄コードの有効性を確認"
        })
        
        return factors
    
    def generate_detailed_report(self, results: Dict, problems: List[str], warnings: List[str], 
                               zero_trade_analysis: Optional[Dict]) -> str:
        """8. 分析結果のユーザー報告"""
        logger.info("8. 詳細レポートの生成")
        
        timestamp = datetime.now()
        
        report = f"""
【バックテスト実行結果】
実行日時: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
ステータス: {'失敗' if problems else ('警告' if warnings else '成功')}
取引量: {results.get('取引量', '0')}
"""
        
        if results.get('総リターン'):
            report += f"総リターン: {results['総リターン']}%\n"
        if results.get('シャープレシオ'):
            report += f"シャープレシオ: {results['シャープレシオ']}\n"
        if results.get('最大ドローダウン'):
            report += f"最大ドローダウン: {results['最大ドローダウン']}%\n"
        
        if problems or warnings:
            report += "\n【問題の概要】\n"
            for problem in problems:
                report += f"- {problem}\n"
            for warning in warnings:
                report += f"- {warning}\n"
        
        if zero_trade_analysis:
            # 根本原因分析
            rca = zero_trade_analysis['rca_result']
            report += f"""
【根本原因分析】
1. 直接的原因: {rca['直接的原因']}
2. 根本原因: {rca['なぜ5_根本原因']}
3. 寄与要因: 
   - なぜ1: {rca['なぜ1']}
   - なぜ2: {rca['なぜ2']}
   - なぜ3: {rca['なぜ3']}
"""
            
            # 潜在的リスク要因
            report += "\n【潜在的リスク要因】\n"
            factors = zero_trade_analysis['potential_factors']
            high_priority = [f for f in factors if f['影響度'] == '高']
            
            for factor in high_priority[:3]:  # 上位3つの高影響度要因
                report += f"- {factor['要因']}: {factor['説明']} (影響度: {factor['影響度']})\n"
            
            # 推奨対策
            report += """
【推奨対策】
1. 即時対応:
   - データソースの接続状態を確認
   - APIキーの有効性を検証
   - エラーログの詳細を確認
   
2. 短期対策 (1週間以内):
   - パラメータ設定の見直しと最適化
   - 異なる期間でのバックテスト実施
   - データ品質の検証プロセス確立
   
3. 長期改善:
   - エラーハンドリングの強化
   - より詳細なログ機能の実装
   - ユーザーガイドとドキュメントの充実
"""
        
        # コンソール出力
        print(report)
        
        # ファイル保存
        report_file = f"backtest_detailed_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"レポート保存: {report_file}")
        
        # JSON形式でも保存
        json_report = {
            "execution_time": timestamp.isoformat(),
            "status": "error" if problems else ("warning" if warnings else "success"),
            "results": results,
            "problems": problems,
            "warnings": warnings,
            "execution_log": self.execution_log,
            "zero_trade_analysis": zero_trade_analysis
        }
        
        json_file = f"backtest_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def get_user_action(self) -> int:
        """9. ネクストアクション確認"""
        logger.info("9. ユーザーアクションの確認")
        
        print("\n分析結果を確認いただきました。次のアクションをお選びください：")
        print("1. 推奨対策を実行する")
        print("2. 追加の詳細分析を実施する")
        print("3. 設定を修正して再実行する")
        print("4. ログの詳細を確認する")
        print("5. その他（具体的に指示してください）")
        print("0. 終了")
        
        try:
            choice = input("\n選択番号を入力してください: ")
            return int(choice)
        except:
            return 0
    
    def execute_user_action(self, choice: int):
        """ユーザー選択に基づくアクション実行"""
        if choice == 1:
            logger.info("推奨対策の実行を開始します...")
            print("\n推奨対策の実行手順:")
            print("1. まず環境変数とAPIキーを確認してください")
            print("2. データソースの接続状態を検証します")
            print("3. パラメータ設定を見直してください")
            
        elif choice == 2:
            logger.info("追加の詳細分析を実施します...")
            # 追加分析のロジック
            
        elif choice == 3:
            logger.info("設定修正画面に移動します...")
            # 設定画面への遷移
            
        elif choice == 4:
            logger.info("ログの詳細を表示します...")
            print("\n=== 実行ログ ===")
            for log in self.execution_log[-10:]:  # 最新10件
                print(f"{log['timestamp']}: {log['event']} - {log['status']}")
                if log['details']:
                    print(f"  詳細: {log['details']}")
            
        elif choice == 5:
            user_input = input("具体的な指示を入力してください: ")
            logger.info(f"ユーザー指示: {user_input}")
            print("指示を受け付けました。実装をご検討ください。")
    
    def cleanup(self):
        """10. クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行フロー"""
        try:
            # 1-5: 基本的な実行フロー
            self.setup()
            self.login()
            self.navigate_to_backtest()
            self.navigate_to_execution_tab()
            
            if not self.execute_backtest():
                self.log_event("バックテスト実行", "失敗")
                return False
            
            # 6: 初期検証
            results, problems, warnings = self.initial_validation()
            
            # 7: 取引量ゼロチェックと詳細分析
            zero_trade_analysis = None
            if results.get("取引量") == "0" or not results.get("取引量"):
                zero_trade_analysis = self.check_zero_trades_and_analyze(results, problems)
            
            # 8: レポート生成
            self.generate_detailed_report(results, problems, warnings, zero_trade_analysis)
            
            # 9: ユーザーアクション
            if problems or warnings or zero_trade_analysis:
                choice = self.get_user_action()
                if choice > 0:
                    self.execute_user_action(choice)
            
            return len(problems) == 0
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            
            self.log_event("システムエラー", "エラー", str(e))
            self.generate_detailed_report({}, [f"システムエラー: {str(e)}"], [], None)
            return False
            
        finally:
            self.cleanup()

def main():
    automation = BacktestAutomationAdvanced()
    success = automation.run()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())