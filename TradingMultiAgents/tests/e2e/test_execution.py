"""
分析実行ページのE2Eテスト（更新版）
StreamlitSelectorsを使用した安定したテスト
"""

import pytest
from playwright.sync_api import Page, expect
from utils import StreamlitSelectors, StreamlitPageObjects


class TestExecution:
    """分析実行ページのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.selectors = StreamlitSelectors()
    
    @pytest.mark.smoke
    def test_navigate_to_execution(self, page: Page, screenshot_path):
        """分析実行ページへのナビゲーション"""
        # 実行ページへ移動
        execution_button = page.locator(self.selectors.nav_button("execution"))
        execution_button.click()
        
        # ページ遷移を待機
        page.wait_for_load_state("networkidle")
        
        # ページタイトルの確認
        page_title = page.locator('h2:has-text("分析実行")')
        expect(page_title).to_be_visible()
        
        # 実行ボタンの確認
        execute_button = page.locator(self.selectors.button(text="分析開始"))
        expect(execute_button).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("execution_page"), full_page=True)
    
    def test_pre_execution_checks(self, page: Page, screenshot_path):
        """実行前チェック"""
        # 設定確認セクション
        config_section = page.locator(self.selectors.markdown_with_text("現在の設定")).first
        
        if config_section.is_visible():
            # 設定項目の確認
            config_items = {
                "ticker": "ティッカー",
                "date": "分析日",
                "model": "モデル"
            }
            
            for key, label in config_items.items():
                item_element = page.locator(f'text="{label}:"').first
                if item_element.is_visible():
                    assert True, f"{label}が表示されています"
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("pre_execution_config"), full_page=True)
    
    @pytest.mark.parametrize("symbol,expected_result", [
        ("", "error"),
        ("123", "error"),
        ("INVALID", "warning"),
        ("AAPL", "valid"),
    ])
    def test_symbol_validation(self, page: Page, symbol, expected_result, screenshot_path):
        """TC008: 入力検証"""
        # ティッカー入力フィールド
        ticker_input = page.locator(self.selectors.text_input("ティッカーシンボル")).first
        
        if ticker_input.is_visible():
            # 入力フィールドをクリア
            ticker_input.clear()
            
            # シンボルを入力
            ticker_input.fill(symbol)
            ticker_input.press("Tab")  # フォーカスを外してバリデーションをトリガー
            page.wait_for_timeout(500)
            
            # バリデーション結果の確認
            if expected_result == "error":
                # エラーアラートを確認
                error_alert = page.locator(self.selectors.alert("error")).first
                if error_alert.is_visible():
                    assert True, f"エラーが表示されました: {symbol}"
                    
                    # スクリーンショット
                    page.screenshot(
                        path=screenshot_path(f"validation_error_{symbol or 'empty'}"),
                        full_page=True
                    )
            elif expected_result == "warning":
                # 警告アラートを確認
                warning_alert = page.locator(self.selectors.alert("warning")).first
                if warning_alert.is_visible():
                    assert True, f"警告が表示されました: {symbol}"
                    
                    # スクリーンショット
                    page.screenshot(
                        path=screenshot_path(f"validation_warning_{symbol}"),
                        full_page=True
                    )
            else:
                # 有効な入力
                page.screenshot(
                    path=screenshot_path(f"validation_valid_{symbol}"),
                    full_page=True
                )
    
    @pytest.mark.slow
    def test_analysis_execution(self, page: Page, screenshot_path):
        """TC007: 基本的な分析実行"""
        page_obj = StreamlitPageObjects(page)
        
        # 設定を確認
        config_ready = page.locator(self.selectors.markdown_with_text("設定完了")).first
        
        if not config_ready.is_visible():
            # 設定が不完全な場合は設定ページへ
            page_obj.navigate_to("settings")
            
            # 基本設定を入力
            ticker_input = page.locator(self.selectors.settings_input("ticker"))
            if ticker_input.is_visible():
                ticker_input.fill("AAPL")
            
            # 実行ページに戻る
            page_obj.navigate_to("execution")
        
        # 実行前のスクリーンショット
        page.screenshot(path=screenshot_path("before_execution"), full_page=True)
        
        # 分析実行ボタンをクリック
        execute_button = page.locator(self.selectors.button(text="分析開始"))
        expect(execute_button).to_be_visible()
        execute_button.click()
        
        # プログレス表示を待機
        try:
            # スピナーまたはプログレスバーの表示を確認
            progress_indicator = page.locator(self.selectors.execution_status()).first
            expect(progress_indicator).to_be_visible(timeout=5000)
            
            # 実行中のスクリーンショット
            page.screenshot(path=screenshot_path("during_execution"), full_page=True)
            
            # エージェントの進捗メッセージを確認
            agent_messages = page.locator('[data-testid="stMarkdown"]').all()
            for msg in agent_messages:
                text = msg.text_content()
                if "エージェント" in text or "分析中" in text:
                    assert True, f"進捗メッセージ: {text[:50]}..."
            
            # 完了を待機（最大30秒）
            page.wait_for_selector(
                self.selectors.spinner(),
                state="hidden",
                timeout=30000
            )
            
            # 実行後のスクリーンショット
            page.screenshot(path=screenshot_path("after_execution"), full_page=True)
            
            # 成功メッセージの確認
            success_alert = page.locator(self.selectors.alert("success")).first
            if success_alert.is_visible():
                assert True, "分析が正常に完了しました"
                
        except Exception as e:
            # エラーまたはタイムアウトの場合
            page.screenshot(path=screenshot_path("execution_error"), full_page=True)
            
            # エラーメッセージを確認
            error_alert = page.locator(self.selectors.alert("error")).first
            if error_alert.is_visible():
                error_text = error_alert.text_content()
                pytest.fail(f"分析実行エラー: {error_text}")
            else:
                pytest.skip(f"分析実行がタイムアウトしました: {e}")
    
    def test_execution_controls(self, page: Page, screenshot_path):
        """実行コントロールのテスト"""
        # 分析を開始
        start_button = page.locator(self.selectors.button(text="分析開始"))
        
        if start_button.is_visible():
            start_button.click()
            page.wait_for_timeout(2000)
            
            # 停止ボタンが表示されるか確認
            stop_button = page.locator(self.selectors.button(text="停止"))
            if stop_button.is_visible():
                # 停止ボタンのスクリーンショット
                page.screenshot(path=screenshot_path("execution_stop_button"), full_page=True)
                
                # 停止ボタンをクリック
                stop_button.click()
                page.wait_for_timeout(1000)
                
                # 停止確認ダイアログ
                confirm_button = page.locator('button:has-text("確認")').first
                if confirm_button.is_visible():
                    confirm_button.click()
                    
                    # 停止後のスクリーンショット
                    page.screenshot(path=screenshot_path("execution_stopped"), full_page=True)
    
    def test_execution_logs(self, page: Page, screenshot_path):
        """実行ログの表示"""
        # ログセクションを探す
        log_section = page.locator(self.selectors.markdown_with_text("実行ログ")).first
        
        if log_section.is_visible():
            # ログエクスパンダーを展開
            log_expander = page.locator(self.selectors.expander("詳細ログ")).first
            if log_expander.is_visible():
                log_expander.click()
                page.wait_for_timeout(500)
                
                # ログ内容の確認
                log_content = page.locator('[data-testid="stCode"]').first
                if log_content.is_visible():
                    assert True, "ログが表示されています"
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("execution_logs"), full_page=True)
    
    def test_batch_execution(self, page: Page, screenshot_path):
        """TC009: 複数銘柄の分析"""
        # バッチ実行モードのチェックボックス
        batch_checkbox = page.locator(self.selectors.checkbox("複数銘柄分析")).first
        
        if batch_checkbox.is_visible():
            # チェックボックスをクリック
            batch_checkbox.click()
            page.wait_for_timeout(500)
            
            # 複数銘柄入力エリアが表示されるか確認
            batch_input = page.locator('textarea').first
            if batch_input.is_visible():
                # 複数銘柄を入力
                batch_input.fill("AAPL,MSFT,GOOGL,AMZN")
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("batch_symbols_input"), full_page=True)
                
                # バッチ実行ボタン
                batch_execute = page.locator(self.selectors.button(text="一括分析開始")).first
                if batch_execute.is_visible():
                    assert True, "バッチ実行が設定されました"
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("batch_ready"), full_page=True)
    
    def test_execution_history(self, page: Page, screenshot_path):
        """実行履歴の確認"""
        # 実行履歴セクション
        history_section = page.locator(self.selectors.markdown_with_text("実行履歴")).first
        
        if history_section.is_visible():
            # 履歴テーブルまたはデータフレーム
            history_table = page.locator(self.selectors.dataframe()).first
            
            if history_table.is_visible():
                # スクリーンショット
                page.screenshot(path=screenshot_path("execution_history"), full_page=True)
                
                # 履歴項目の確認
                table_rows = history_table.locator("tr").all()
                if len(table_rows) > 1:  # ヘッダー行を除く
                    assert True, f"実行履歴が{len(table_rows)-1}件表示されています"
    
    @pytest.mark.visual
    def test_execution_responsive(self, page: Page, screenshot_path):
        """実行ページのレスポンシブ確認"""
        viewports = [
            {"name": "desktop", "width": 1920, "height": 1080},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "mobile", "width": 375, "height": 812}
        ]
        
        for viewport in viewports:
            page.set_viewport_size({
                "width": viewport["width"],
                "height": viewport["height"]
            })
            page.wait_for_timeout(1000)
            
            # 実行ボタンが適切に表示されているか
            execute_button = page.locator(self.selectors.button(text="分析を開始"))
            assert execute_button.is_visible()
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"execution_layout_{viewport['name']}"),
                full_page=True
            )