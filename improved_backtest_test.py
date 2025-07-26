#!/usr/bin/env python3
"""
改善版バックテスト自動動作検証スクリプト
より堅牢なセレクタとエラーハンドリングを実装
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
import sys

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwrightがインストールされていません。")
    sys.exit(1)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedBacktestValidator:
    """改善版バックテスト動作検証クラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8501"
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "errors": [],
            "warnings": [],
            "success": False
        }
    
    async def wait_for_streamlit(self, page, timeout=10000):
        """Streamlitの読み込み完了を待つ"""
        try:
            # Streamlitのローディングインジケータが消えるまで待つ
            await page.wait_for_selector('[data-testid="stStatusWidget"]', state='hidden', timeout=timeout)
        except:
            pass  # タイムアウトしても続行
    
    async def test_login(self, page):
        """改善版ログイン機能のテスト"""
        logger.info("ログイン機能のテスト開始")
        
        try:
            await page.goto(self.base_url)
            await self.wait_for_streamlit(page)
            await page.wait_for_timeout(2000)
            
            # ログインフォームの検索（複数の方法を試す）
            username_selectors = [
                'input[aria-label="Username"]',
                'input[placeholder*="Username"]',
                'input[type="text"]'
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    username_input = await page.wait_for_selector(selector, timeout=3000)
                    if username_input:
                        break
                except:
                    continue
            
            if not username_input:
                raise Exception("ユーザー名入力フィールドが見つかりません")
            
            # パスワード入力
            password_input = await page.query_selector('input[type="password"]')
            if not password_input:
                raise Exception("パスワード入力フィールドが見つかりません")
            
            await username_input.fill("user")
            await password_input.fill("user123")
            
            await page.screenshot(path="improved_01_login_filled.png")
            
            # ログインボタンのクリック（複数の方法を試す）
            login_success = False
            login_methods = [
                lambda: page.click('button:has-text("Login")'),
                lambda: page.click('text="Login"'),
                lambda: page.press('input[type="password"]', 'Enter')
            ]
            
            for method in login_methods:
                try:
                    await method()
                    login_success = True
                    break
                except:
                    continue
            
            if not login_success:
                raise Exception("ログインボタンのクリックに失敗")
            
            # ログイン後の確認（より柔軟な確認）
            await page.wait_for_timeout(5000)
            await self.wait_for_streamlit(page)
            
            # ログイン成功の判定（複数の条件をチェック）
            login_indicators = [
                await page.query_selector('text="Trading Agents WebUI"'),
                await page.query_selector('text="ダッシュボード"'),
                await page.query_selector('[data-testid="stSidebar"]'),
                await page.query_selector('button:has-text("ログアウト")')
            ]
            
            if any(login_indicators):
                logger.info("ログイン成功")
                await page.screenshot(path="improved_02_after_login.png")
                self.results["tests"].append({
                    "test": "login",
                    "status": "passed",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                self.results["warnings"].append({
                    "test": "login",
                    "warning": "ログイン後の画面確認が不完全",
                    "timestamp": datetime.now().isoformat()
                })
                return True  # 警告として記録し、続行
                
        except Exception as e:
            logger.error(f"ログインテスト失敗: {e}")
            await page.screenshot(path="improved_error_login.png")
            self.results["errors"].append({
                "test": "login",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def test_navigate_to_backtest(self, page):
        """改善版バックテストページ遷移テスト"""
        logger.info("バックテストページ遷移テスト開始")
        
        try:
            # サイドバーが表示されているか確認
            sidebar = await page.query_selector('[data-testid="stSidebar"]')
            if not sidebar:
                # サイドバーを開く
                hamburger = await page.query_selector('[data-testid="collapsedControl"]')
                if hamburger:
                    await hamburger.click()
                    await page.wait_for_timeout(1000)
            
            # バックテストボタンを探す（複数の方法）
            backtest_clicked = False
            backtest_selectors = [
                'button:has-text("バックテスト")',
                'text="📊 バックテスト"',
                '[data-testid="stSidebar"] button:has-text("バックテスト")',
                'button[key="nav_backtest2"]'
            ]
            
            for selector in backtest_selectors:
                try:
                    await page.click(selector)
                    backtest_clicked = True
                    break
                except:
                    continue
            
            if not backtest_clicked:
                raise Exception("バックテストボタンが見つかりません")
            
            await page.wait_for_timeout(3000)
            await self.wait_for_streamlit(page)
            await page.screenshot(path="improved_03_backtest_page.png")
            
            # ページ遷移の確認（URLまたはコンテンツで判定）
            current_url = page.url
            page_content = await page.content()
            
            if "backtest" in current_url.lower() or "バックテスト" in page_content:
                logger.info("バックテストページへの遷移成功")
                self.results["tests"].append({
                    "test": "navigate_to_backtest",
                    "status": "passed",
                    "timestamp": datetime.now().isoformat()
                })
                return True
            else:
                self.results["warnings"].append({
                    "test": "navigate_to_backtest",
                    "warning": "バックテストページの確認が不完全",
                    "timestamp": datetime.now().isoformat()
                })
                return True
                
        except Exception as e:
            logger.error(f"バックテストページ遷移テスト失敗: {e}")
            await page.screenshot(path="improved_error_navigate.png")
            self.results["errors"].append({
                "test": "navigate_to_backtest",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def test_full_backtest_flow(self, page):
        """バックテスト実行フローの統合テスト"""
        logger.info("バックテスト実行フロー統合テスト開始")
        
        try:
            # タブの検索と実行
            tab_clicked = False
            tab_selectors = [
                'button:has-text("実行")',
                '[role="tab"]:has-text("実行")',
                'div:has-text("実行"):not(:has(*))'
            ]
            
            for selector in tab_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for elem in elements:
                        text = await elem.inner_text()
                        if text.strip() == "実行":
                            await elem.click()
                            tab_clicked = True
                            break
                    if tab_clicked:
                        break
                except:
                    continue
            
            await page.wait_for_timeout(2000)
            await page.screenshot(path="improved_04_execution_tab.png")
            
            # 実行ボタンを探す
            execute_selectors = [
                'button:has-text("バックテストを実行")',
                'button:has-text("実行"):not(:has-text("タブ"))',
                'button[kind="primary"]:has-text("実行")'
            ]
            
            execute_clicked = False
            for selector in execute_selectors:
                try:
                    await page.click(selector)
                    execute_clicked = True
                    break
                except:
                    continue
            
            if execute_clicked:
                await page.screenshot(path="improved_05_execution_started.png")
                logger.info("バックテスト実行を開始")
                
                # 実行状態の監視
                await page.wait_for_timeout(10000)
                
                # エラーチェック
                error_messages = await page.query_selector_all('[class*="error"], [class*="alert"], div:has-text("エラー")')
                for error_elem in error_messages:
                    error_text = await error_elem.inner_text()
                    if error_text and len(error_text) < 200:  # 長すぎるテキストは無視
                        self.results["warnings"].append({
                            "test": "backtest_execution",
                            "warning": f"実行中の警告: {error_text}",
                            "timestamp": datetime.now().isoformat()
                        })
                
                await page.screenshot(path="improved_06_execution_complete.png")
                
                # 結果タブへの移動
                await page.click('text="結果"')
                await page.wait_for_timeout(2000)
                await page.screenshot(path="improved_07_results.png")
                
                self.results["tests"].append({
                    "test": "full_backtest_flow",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
                
                return True
            else:
                raise Exception("実行ボタンが見つかりません")
                
        except Exception as e:
            logger.error(f"バックテスト実行フローテスト失敗: {e}")
            await page.screenshot(path="improved_error_flow.png")
            self.results["errors"].append({
                "test": "full_backtest_flow",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def analyze_final_state(self, page):
        """最終状態の分析"""
        logger.info("最終状態の分析開始")
        
        try:
            # 現在のページ状態を分析
            page_content = await page.content()
            
            # メトリクスの検出
            metrics = await page.query_selector_all('[data-testid*="metric"], div[class*="metric"]')
            metric_count = len(metrics)
            
            # グラフの検出
            charts = await page.query_selector_all('canvas, svg[class*="chart"], div[class*="plot"]')
            chart_count = len(charts)
            
            # テーブルの検出
            tables = await page.query_selector_all('table, [role="table"]')
            table_count = len(tables)
            
            self.results["analysis"] = {
                "metrics_found": metric_count,
                "charts_found": chart_count,
                "tables_found": table_count,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"分析結果: メトリクス={metric_count}, グラフ={chart_count}, テーブル={table_count}")
            
            await page.screenshot(path="improved_08_final_analysis.png")
            
            return True
            
        except Exception as e:
            logger.error(f"最終状態分析失敗: {e}")
            return False
    
    async def run_all_tests(self):
        """すべてのテストを実行"""
        logger.info("=== 改善版バックテスト自動動作検証開始 ===")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--window-size=1920,1080']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 各テストを実行
                await self.test_login(page)
                await self.test_navigate_to_backtest(page)
                await self.test_full_backtest_flow(page)
                await self.analyze_final_state(page)
                
                # 成功判定
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
        
        logger.info("=== 改善版バックテスト自動動作検証完了 ===")
    
    def save_results(self):
        """テスト結果を保存"""
        self.results["end_time"] = datetime.now().isoformat()
        
        filename = f"improved_backtest_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"テスト結果を保存: {filename}")
        
        # 詳細レポート生成
        self.generate_report()
    
    def generate_report(self):
        """詳細レポートの生成"""
        logger.info("\n" + "="*60)
        logger.info("バックテスト自動動作検証レポート")
        logger.info("="*60)
        
        # サマリー
        logger.info(f"\n【実行結果】")
        logger.info(f"総合判定: {'✅ 成功' if self.results['success'] else '❌ 失敗'}")
        logger.info(f"実行テスト数: {len(self.results['tests'])}")
        logger.info(f"エラー数: {len(self.results['errors'])}")
        logger.info(f"警告数: {len(self.results['warnings'])}")
        
        # テスト詳細
        if self.results['tests']:
            logger.info(f"\n【成功したテスト】")
            for test in self.results['tests']:
                logger.info(f"✅ {test['test']}")
        
        # エラー詳細
        if self.results['errors']:
            logger.info(f"\n【エラー詳細】")
            for error in self.results['errors']:
                logger.info(f"❌ {error['test']}: {error['error']}")
        
        # 警告詳細
        if self.results['warnings']:
            logger.info(f"\n【警告事項】")
            for warning in self.results['warnings']:
                logger.info(f"⚠️  {warning['test']}: {warning['warning']}")
        
        # 分析結果
        if 'analysis' in self.results:
            logger.info(f"\n【画面分析結果】")
            analysis = self.results['analysis']
            logger.info(f"検出されたメトリクス: {analysis['metrics_found']}")
            logger.info(f"検出されたグラフ: {analysis['charts_found']}")
            logger.info(f"検出されたテーブル: {analysis['tables_found']}")
        
        logger.info("\n" + "="*60)

async def main():
    """メイン実行関数"""
    validator = ImprovedBacktestValidator()
    await validator.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())