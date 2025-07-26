#!/usr/bin/env python3
"""
バックテスト自動動作検証スクリプト
Playwrightを使用してWebUIの動作を自動検証
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
import sys

# Playwrightのインポートを試みる
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwrightがインストールされていません。")
    print("インストール: pip install playwright")
    print("ブラウザのインストール: playwright install chromium")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_backtest_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BacktestValidator:
    """バックテスト動作検証クラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8501"
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "errors": [],
            "success": False
        }
    
    async def test_login(self, page):
        """ログイン機能のテスト"""
        logger.info("ログイン機能のテスト開始")
        
        try:
            # ログインページの確認
            await page.goto(self.base_url)
            await page.wait_for_timeout(3000)
            
            # スクリーンショット
            await page.screenshot(path="test_01_login_page.png")
            
            # ログインフォームの存在確認
            username_input = await page.query_selector('input[aria-label="Username"]')
            password_input = await page.query_selector('input[aria-label="Password"]')
            
            if not username_input or not password_input:
                raise Exception("ログインフォームが見つかりません")
            
            # ログイン情報入力
            await username_input.fill("user")
            await password_input.fill("user123")
            
            # ログインボタンクリック
            login_button = await page.query_selector('button:has-text("Login")')
            if login_button:
                await login_button.click()
            else:
                # Streamlitのボタンは特殊な構造の場合がある
                await page.click('text="Login"')
            
            # ログイン後の確認
            await page.wait_for_timeout(3000)
            await page.screenshot(path="test_02_after_login.png")
            
            # ダッシュボードの表示確認
            dashboard_title = await page.query_selector('h1:has-text("Trading Agents WebUI")')
            if dashboard_title:
                logger.info("ログイン成功: ダッシュボードが表示されました")
                self.results["tests"].append({
                    "test": "login",
                    "status": "passed",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                raise Exception("ログイン後のダッシュボードが表示されません")
                
        except Exception as e:
            logger.error(f"ログインテスト失敗: {e}")
            self.results["errors"].append({
                "test": "login",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def test_navigate_to_backtest(self, page):
        """バックテストページへの遷移テスト"""
        logger.info("バックテストページ遷移テスト開始")
        
        try:
            # サイドバーのバックテストボタンを探す
            backtest_button = await page.query_selector('button:has-text("バックテスト")')
            if not backtest_button:
                # テキストで直接クリック
                await page.click('text="バックテスト"')
            else:
                await backtest_button.click()
            
            await page.wait_for_timeout(2000)
            await page.screenshot(path="test_03_backtest_page.png")
            
            # バックテストページの確認
            backtest_title = await page.query_selector('h2:has-text("バックテスト"), h1:has-text("バックテスト")')
            if backtest_title:
                logger.info("バックテストページへの遷移成功")
                self.results["tests"].append({
                    "test": "navigate_to_backtest",
                    "status": "passed",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                raise Exception("バックテストページが表示されません")
                
        except Exception as e:
            logger.error(f"バックテストページ遷移テスト失敗: {e}")
            self.results["errors"].append({
                "test": "navigate_to_backtest",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def test_execution_tab(self, page):
        """実行タブのテスト"""
        logger.info("実行タブテスト開始")
        
        try:
            # タブを探す（Streamlitのタブ構造に対応）
            tabs = await page.query_selector_all('[role="tab"], button:has-text("実行")')
            
            execution_tab_found = False
            for tab in tabs:
                text = await tab.inner_text()
                if "実行" in text:
                    await tab.click()
                    execution_tab_found = True
                    break
            
            if not execution_tab_found:
                # 直接テキストでクリック
                await page.click('text="実行"')
            
            await page.wait_for_timeout(2000)
            await page.screenshot(path="test_04_execution_tab.png")
            
            logger.info("実行タブへの移動成功")
            self.results["tests"].append({
                "test": "execution_tab",
                "status": "passed",
                "timestamp": datetime.now().isoformat()
            })
            return True
            
        except Exception as e:
            logger.error(f"実行タブテスト失敗: {e}")
            self.results["errors"].append({
                "test": "execution_tab",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def test_backtest_execution(self, page):
        """バックテスト実行のテスト"""
        logger.info("バックテスト実行テスト開始")
        
        try:
            # 実行ボタンを探す
            execute_buttons = await page.query_selector_all('button')
            execute_button_found = False
            
            for button in execute_buttons:
                text = await button.inner_text()
                if "実行" in text and "バックテスト" in text:
                    await button.click()
                    execute_button_found = True
                    break
            
            if not execute_button_found:
                # プライマリボタンを探す
                primary_button = await page.query_selector('button[kind="primary"]:has-text("実行")')
                if primary_button:
                    await primary_button.click()
                else:
                    await page.click('text="バックテストを実行"')
            
            await page.screenshot(path="test_05_execution_started.png")
            
            # 実行開始の確認（プログレスバーまたはログ出力）
            await page.wait_for_timeout(5000)
            
            # エラーチェック
            error_elements = await page.query_selector_all('div[class*="error"], div[class*="alert"]')
            if error_elements:
                for elem in error_elements:
                    error_text = await elem.inner_text()
                    if error_text:
                        logger.warning(f"エラー検出: {error_text}")
                        self.results["errors"].append({
                            "test": "backtest_execution",
                            "error": f"実行中エラー: {error_text}",
                            "timestamp": datetime.now().isoformat()
                        })
            
            # 実行状態のスクリーンショット
            await page.screenshot(path="test_06_execution_progress.png")
            
            logger.info("バックテスト実行開始を確認")
            self.results["tests"].append({
                "test": "backtest_execution",
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
            return True
            
        except Exception as e:
            logger.error(f"バックテスト実行テスト失敗: {e}")
            self.results["errors"].append({
                "test": "backtest_execution",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def test_results_tab(self, page):
        """結果タブのテスト"""
        logger.info("結果タブテスト開始")
        
        try:
            # 少し待つ（実行が進むのを待つ）
            await page.wait_for_timeout(10000)
            
            # 結果タブを探す
            tabs = await page.query_selector_all('[role="tab"], button:has-text("結果")')
            
            results_tab_found = False
            for tab in tabs:
                text = await tab.inner_text()
                if "結果" in text:
                    await tab.click()
                    results_tab_found = True
                    break
            
            if not results_tab_found:
                await page.click('text="結果"')
            
            await page.wait_for_timeout(2000)
            await page.screenshot(path="test_07_results_tab.png")
            
            # メトリクスの確認
            metrics = await page.query_selector_all('div[class*="metric"]')
            if metrics:
                logger.info(f"メトリクス数: {len(metrics)}")
                self.results["tests"].append({
                    "test": "results_tab",
                    "status": "passed",
                    "metrics_found": len(metrics),
                    "timestamp": datetime.now().isoformat()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"結果タブテスト失敗: {e}")
            self.results["errors"].append({
                "test": "results_tab",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def run_all_tests(self):
        """すべてのテストを実行"""
        logger.info("=== バックテスト自動動作検証開始 ===")
        
        async with async_playwright() as p:
            # ブラウザ起動
            browser = await p.chromium.launch(
                headless=False,  # GUIで確認できるように
                args=['--window-size=1920,1080']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 各テストを順番に実行
                tests = [
                    self.test_login,
                    self.test_navigate_to_backtest,
                    self.test_execution_tab,
                    self.test_backtest_execution,
                    self.test_results_tab
                ]
                
                for test in tests:
                    success = await test(page)
                    if not success:
                        logger.warning(f"{test.__name__} が失敗しました。次のテストに進みます。")
                    await page.wait_for_timeout(1000)
                
                # 最終スクリーンショット
                await page.screenshot(path="test_08_final_state.png")
                
                self.results["success"] = len(self.results["errors"]) == 0
                
            except Exception as e:
                logger.error(f"テスト実行中にエラー: {e}")
                self.results["errors"].append({
                    "test": "general",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            finally:
                await browser.close()
        
        # 結果を保存
        self.save_results()
        
        logger.info("=== バックテスト自動動作検証完了 ===")
    
    def save_results(self):
        """テスト結果を保存"""
        self.results["end_time"] = datetime.now().isoformat()
        
        filename = f"backtest_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"テスト結果を保存: {filename}")
        
        # サマリー表示
        logger.info("\n=== テストサマリー ===")
        logger.info(f"成功: {self.results['success']}")
        logger.info(f"実行テスト数: {len(self.results['tests'])}")
        logger.info(f"エラー数: {len(self.results['errors'])}")
        
        if self.results["errors"]:
            logger.info("\n=== エラー詳細 ===")
            for error in self.results["errors"]:
                logger.info(f"- {error['test']}: {error['error']}")

async def main():
    """メイン実行関数"""
    validator = BacktestValidator()
    await validator.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())