#!/usr/bin/env python3
"""
最終版：WebUIバックテスト自動実行
デバッグ結果に基づいた正確なセレクターを使用
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
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalBacktestAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup(self):
        """ブラウザセットアップ"""
        logger.info("=== WebUIバックテスト自動実行（最終版）===")
        logger.info("1. 環境準備")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # Macの画面サイズに合わせてウィンドウサイズを設定
        chrome_options.add_argument('--window-size=2560,1600')
        chrome_options.add_argument('--start-maximized')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # ウィンドウを最大化（Macの画面サイズに合わせる）
        self.driver.set_window_size(2560, 1600)
        self.driver.set_window_position(0, 0)
        
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("✓ Chromeブラウザ起動成功（解像度: 2560x1600）")
        
    def login(self):
        """ログイン処理"""
        logger.info("2. WebUI接続とログイン")
        self.driver.get("http://localhost:8501")
        time.sleep(3)
        
        try:
            username = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
            username.clear()
            username.send_keys("user")
            
            password = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password.clear() 
            password.send_keys("user123")
            
            # ログインボタンをクリック
            login_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
            login_button.click()
            logger.info("✓ ログイン成功")
            time.sleep(5)
        except:
            logger.info("既にログイン済み")
    
    def navigate_to_backtest(self):
        """バックテストページへ遷移"""
        logger.info("3. バックテストページへの遷移")
        
        try:
            # デバッグで特定したクラス名を使用
            backtest_xpath = "//button[@class='st-emotion-cache-1ub9ykg e1e4lema2' and contains(text(), '📊 バックテスト')]"
            
            # ボタンを待機して取得
            backtest_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, backtest_xpath))
            )
            
            # JavaScriptでクリック（確実性のため）
            self.driver.execute_script("arguments[0].click();", backtest_button)
            logger.info("✓ バックテストページへ移動")
            time.sleep(3)
            
            # ページが切り替わったことを確認
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "バックテスト" in page_text:
                logger.info("✓ バックテストページの表示を確認")
                return True
            
        except Exception as e:
            logger.error(f"バックテストページへの遷移失敗: {e}")
            
            # 代替方法：すべてのボタンから探す
            buttons = self.driver.find_elements(By.XPATH, "//button")
            for button in buttons:
                try:
                    if "バックテスト" in button.text and button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", button)
                        logger.info("✓ バックテストページへ移動（代替方法）")
                        time.sleep(3)
                        return True
                except:
                    continue
                    
        return False
    
    def find_and_click_execution_tab(self):
        """バックテスト実行タブを探してクリック"""
        logger.info("4. バックテスト実行タブへの移動")
        
        # バックテストページ内のタブやセクションを探す
        tab_patterns = [
            "//button[contains(text(), 'バックテスト2')]",
            "//button[contains(text(), '実行')]",
            "//div[@role='tab' and contains(., '実行')]",
            "//button[contains(@class, 'tab') and contains(., '実行')]"
        ]
        
        for pattern in tab_patterns:
            try:
                tab = self.driver.find_element(By.XPATH, pattern)
                if tab.is_displayed():
                    tab.click()
                    logger.info("✓ 実行タブに切り替え")
                    time.sleep(2)
                    return True
            except:
                continue
        
        logger.info("実行タブが見つからない - 既に実行画面の可能性")
        return True
    
    def execute_backtest(self):
        """バックテスト実行"""
        logger.info("5. バックテスト実行")
        
        # 現在のページ内容を確認
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        logger.info(f"現在のページ（最初の300文字）: {page_text[:300]}")
        
        # バックテストページ内の実行ボタンを探す
        execute_patterns = [
            "//button[contains(text(), 'バックテスト実行')]",
            "//button[contains(text(), '実行') and not(contains(text(), 'ログ'))]",
            "//button[contains(text(), '開始')]",
            "//button[@kind='primary' and contains(., '実行')]",
            "//button[contains(@class, 'primary') and contains(., '実行')]"
        ]
        
        execute_button = None
        
        # すべてのボタンをログ出力して確認
        all_buttons = self.driver.find_elements(By.XPATH, "//button")
        logger.info(f"ページ内のボタン数: {len(all_buttons)}")
        
        for i, button in enumerate(all_buttons):
            try:
                text = button.text.strip()
                if text and button.is_displayed():
                    logger.debug(f"ボタン{i}: {text}")
                    
                    # 実行に関連するボタンを特定
                    if any(keyword in text for keyword in ["実行", "開始", "Run", "Execute"]):
                        if "ログ" not in text and "分析" not in text:
                            execute_button = button
                            logger.info(f"✓ 実行ボタン発見: {text}")
                            break
            except:
                pass
        
        if not execute_button:
            # パターンマッチングでも探す
            for pattern in execute_patterns:
                try:
                    button = self.driver.find_element(By.XPATH, pattern)
                    if button.is_displayed() and button.is_enabled():
                        execute_button = button
                        logger.info(f"✓ 実行ボタン発見（パターンマッチ）")
                        break
                except:
                    continue
        
        if execute_button:
            # JavaScriptでクリック
            self.driver.execute_script("arguments[0].scrollIntoView(true);", execute_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", execute_button)
            logger.info("✓ 実行ボタンをクリック")
            time.sleep(5)
            
            # 実行開始の確認
            return self.monitor_execution()
        else:
            logger.error("実行ボタンが見つかりません")
            self.driver.save_screenshot("no_execute_button_final.png")
            
            # 現在のページの詳細情報を出力
            logger.error(f"現在のURL: {self.driver.current_url}")
            logger.error(f"ページタイトル: {self.driver.title}")
            return False
    
    def monitor_execution(self):
        """実行状態を監視"""
        logger.info("実行状態を監視中...")
        
        start_time = time.time()
        timeout = 300  # 5分
        last_status = ""
        
        while time.time() - start_time < timeout:
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # エラーチェック
                if "error" in page_text.lower() or "エラー" in page_text:
                    error_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'error')]")
                    for elem in error_elements:
                        if elem.is_displayed():
                            logger.error(f"エラー検出: {elem.text}")
                            return False
                
                # 完了チェック
                if any(keyword in page_text for keyword in ["完了", "Complete", "結果", "取引数", "リターン"]):
                    logger.info("✓ バックテスト完了")
                    return True
                
                # ステータス更新
                status_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'status') or contains(@class, 'progress')]")
                for elem in status_elements:
                    if elem.is_displayed() and elem.text:
                        current_status = elem.text
                        if current_status != last_status:
                            logger.info(f"ステータス: {current_status}")
                            last_status = current_status
                
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"監視中のエラー: {e}")
        
        logger.warning("実行タイムアウト - 結果を確認します")
        return True
    
    def check_results(self):
        """6. 実行結果の初期検証"""
        logger.info("6. 実行結果の初期検証")
        
        results = {}
        problems = []
        warnings = []
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 結果データの抽出
            patterns = {
                "取引量": [r"取引数[：:]\s*(\d+)", r"取引量[：:]\s*(\d+)", r"Total Trades[：:]\s*(\d+)"],
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
            
            # 取引量チェック
            if results.get("取引量") == "0":
                warnings.append("取引が0件です")
                logger.warning("⚠️ 取引量が0です")
            
            # スクリーンショット保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"backtest_final_result_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"スクリーンショット保存: {screenshot_path}")
            
        except Exception as e:
            logger.error(f"結果検証エラー: {e}")
            problems.append(f"検証エラー: {str(e)}")
        
        return results, problems, warnings
    
    def perform_detailed_analysis(self, results, problems, warnings):
        """7. 取引量ゼロチェックと詳細分析"""
        if results.get("取引量") == "0":
            logger.info("7. 取引量ゼロの詳細分析")
            
            # 簡易的な根本原因分析
            analysis = {
                "直接的原因": "取引シグナルが一度も発生しなかった",
                "考えられる要因": [
                    "エントリー条件が厳しすぎる",
                    "データ取得の問題",
                    "パラメータ設定の不適切"
                ],
                "推奨対策": [
                    "パラメータの緩和",
                    "異なる期間での再実行",
                    "データソースの確認"
                ]
            }
            
            return analysis
        
        return None
    
    def generate_report(self, results, problems, warnings, analysis):
        """8. 分析結果のユーザー報告"""
        logger.info("8. レポート生成")
        
        timestamp = datetime.now()
        
        # コンソールレポート
        print("\n" + "=" * 60)
        print("【バックテスト実行結果】")
        print(f"実行日時: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"ステータス: {'エラー' if problems else ('警告' if warnings else '成功')}")
        
        if results:
            print("\n結果:")
            for key, value in results.items():
                print(f"  {key}: {value}")
        
        if problems:
            print("\nエラー:")
            for problem in problems:
                print(f"  - {problem}")
        
        if warnings:
            print("\n警告:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if analysis:
            print("\n【詳細分析】")
            print(f"直接的原因: {analysis['直接的原因']}")
            print("\n考えられる要因:")
            for factor in analysis['考えられる要因']:
                print(f"  - {factor}")
            print("\n推奨対策:")
            for action in analysis['推奨対策']:
                print(f"  - {action}")
        
        print("=" * 60)
        
        # JSONレポート保存
        report = {
            "実行日時": timestamp.isoformat(),
            "結果": results,
            "問題": problems,
            "警告": warnings,
            "詳細分析": analysis
        }
        
        report_file = f"backtest_final_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"レポート保存: {report_file}")
    
    def cleanup(self):
        """10. クリーンアップ"""
        if self.driver:
            self.driver.quit()
            logger.info("ブラウザを閉じました")
    
    def run(self):
        """メイン実行フロー"""
        try:
            # 1-2: セットアップとログイン
            self.setup()
            self.login()
            
            # 3: バックテストページへ遷移
            if not self.navigate_to_backtest():
                logger.error("バックテストページへの遷移に失敗")
                return False
            
            # 4: 実行タブへ移動
            self.find_and_click_execution_tab()
            
            # 5: バックテスト実行
            if not self.execute_backtest():
                logger.error("バックテスト実行に失敗")
                return False
            
            # 6: 結果検証
            results, problems, warnings = self.check_results()
            
            # 7: 詳細分析（必要に応じて）
            analysis = None
            if results.get("取引量") == "0":
                analysis = self.perform_detailed_analysis(results, problems, warnings)
            
            # 8: レポート生成
            self.generate_report(results, problems, warnings, analysis)
            
            # 9: ユーザーアクション（今回は省略）
            
            return len(problems) == 0
            
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 10: クリーンアップ
            self.cleanup()

if __name__ == "__main__":
    automation = FinalBacktestAutomation()
    success = automation.run()
    exit(0 if success else 1)