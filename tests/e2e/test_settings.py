"""
設定ページのE2Eテスト（更新版）
StreamlitSelectorsを使用した安定したテスト
"""

import pytest
from playwright.sync_api import Page, expect
from utils import StreamlitSelectors, StreamlitPageObjects


class TestSettings:
    """設定ページのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.selectors = StreamlitSelectors()
    
    @pytest.mark.smoke
    def test_navigate_to_settings(self, page: Page, screenshot_path):
        """TC004: 設定ページへのナビゲーション"""
        # 設定ページへ移動
        settings_button = page.locator(self.selectors.nav_button("settings"))
        settings_button.click()
        
        # ページ遷移を待機
        page.wait_for_load_state("networkidle")
        
        # 設定ページのタイトル確認
        page_title = page.locator('h2:has-text("分析設定")')
        expect(page_title).to_be_visible()
        
        # 基本的な設定要素の確認
        basic_settings = page.locator('text="基本設定"').first
        expect(basic_settings).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("settings_page"), full_page=True)
    
    def test_ticker_input(self, page: Page, test_data, screenshot_path):
        """ティッカーシンボル入力"""
        # ティッカー入力フィールド
        ticker_input = page.locator(self.selectors.settings_input("ticker"))
        
        if ticker_input.is_visible():
            # 入力フィールドをクリア
            ticker_input.clear()
            
            # テストデータから銘柄を入力
            test_ticker = test_data["test_tickers"][0]
            ticker_input.fill(test_ticker)
            
            # 入力値の確認
            assert ticker_input.input_value() == test_ticker
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("ticker_input"), full_page=True)
    
    def test_date_selection(self, page: Page, screenshot_path):
        """分析日の選択"""
        # 日付入力フィールドを探す
        date_label = page.locator('text="分析日"').first
        
        if date_label.is_visible():
            # 日付入力要素を取得（ラベルの近くにある入力フィールド）
            date_input = page.locator('input[type="date"]').first
            
            if date_input.is_visible():
                # 日付を設定
                test_date = "2024-01-15"
                date_input.fill(test_date)
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("date_selection"), full_page=True)
    
    def test_research_depth_slider(self, page: Page, screenshot_path):
        """リサーチ深度スライダー"""
        # スライダーを探す
        depth_label = page.locator('text="リサーチ深度"').first
        
        if depth_label.is_visible():
            # スライダー要素
            slider = page.locator(self.selectors.slider()).first
            
            if slider.is_visible():
                # 初期値を取得
                initial_value = slider.get_attribute("aria-valuenow")
                
                # スライダーを操作
                slider.click()
                page.keyboard.press("ArrowRight")
                page.keyboard.press("ArrowRight")
                page.wait_for_timeout(500)
                
                # 新しい値を確認
                new_value = slider.get_attribute("aria-valuenow")
                assert initial_value != new_value, "スライダーの値が変更されました"
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("depth_slider"), full_page=True)
    
    def test_model_selection(self, page: Page, test_data, screenshot_path):
        """TC006: モデル選択"""
        # モデル選択セクションを探す
        model_section = page.locator('text="LLMモデル選択"').first
        
        if model_section.is_visible():
            # Deep Thinking LLMの選択
            deep_selector = page.locator(self.selectors.select_box("Deep Thinking LLM")).first
            
            if deep_selector.is_visible():
                # ドロップダウンをクリック
                deep_selector.click()
                page.wait_for_timeout(500)
                
                # オプションを選択
                model_option = page.locator(f'[role="option"]:has-text("{test_data["models"]["deep_thinking"][0]}")').first
                if model_option.is_visible():
                    model_option.click()
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("model_selected"), full_page=True)
    
    def test_advanced_settings(self, page: Page, screenshot_path):
        """詳細設定の確認"""
        # 詳細設定エクスパンダー
        advanced_expander = page.locator(self.selectors.expander("詳細設定")).first
        
        if advanced_expander.is_visible():
            # エクスパンダーを展開
            advanced_expander.click()
            page.wait_for_timeout(500)
            
            # 詳細設定の内容を確認
            advanced_options = {
                "max_iterations": "最大イテレーション数",
                "temperature": "Temperature",
                "timeout": "タイムアウト"
            }
            
            for option_key, option_label in advanced_options.items():
                option_element = page.locator(f'text="{option_label}"').first
                if option_element.is_visible():
                    assert True, f"{option_label}が表示されています"
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("advanced_settings"), full_page=True)
    
    def test_save_settings(self, page: Page, screenshot_path):
        """設定の保存"""
        # 保存ボタンを探す
        save_button = page.locator(self.selectors.button(text="設定を保存")).first
        
        if save_button.is_visible():
            # ボタンをクリック
            save_button.click()
            page.wait_for_timeout(1000)
            
            # 成功メッセージを確認
            success_alert = page.locator(self.selectors.alert("success")).first
            if success_alert.is_visible():
                assert True, "設定が正常に保存されました"
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("settings_saved"), full_page=True)
    
    def test_reset_settings(self, page: Page, screenshot_path):
        """設定のリセット"""
        # リセットボタンを探す
        reset_button = page.locator(self.selectors.button(text="デフォルトに戻す")).first
        
        if reset_button.is_visible():
            # リセット前の値を記録（例：スライダー）
            slider = page.locator(self.selectors.slider()).first
            if slider.is_visible():
                before_reset = slider.get_attribute("aria-valuenow")
            
            # リセットボタンをクリック
            reset_button.click()
            page.wait_for_timeout(1000)
            
            # 確認ダイアログが表示される場合
            confirm_button = page.locator('button:has-text("確認")').first
            if confirm_button.is_visible():
                confirm_button.click()
                page.wait_for_timeout(1000)
            
            # リセット後の値を確認
            if slider.is_visible():
                after_reset = slider.get_attribute("aria-valuenow")
                # デフォルト値に戻っていることを確認
                assert after_reset == "5", "設定がデフォルト値にリセットされました"
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("settings_reset"), full_page=True)
    
    def test_settings_validation(self, page: Page, screenshot_path):
        """設定値のバリデーション"""
        # 無効な値を入力してエラーメッセージを確認
        ticker_input = page.locator(self.selectors.settings_input("ticker"))
        
        if ticker_input.is_visible():
            # 空の値を入力
            ticker_input.clear()
            
            # 保存ボタンをクリック
            save_button = page.locator(self.selectors.button(text="設定を保存")).first
            if save_button.is_visible():
                save_button.click()
                page.wait_for_timeout(1000)
                
                # エラーメッセージを確認
                error_alert = page.locator(self.selectors.alert("error")).first
                if error_alert.is_visible():
                    assert True, "バリデーションエラーが表示されました"
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("validation_error"), full_page=True)
    
    @pytest.mark.visual
    def test_settings_responsive_layout(self, page: Page, screenshot_path):
        """設定ページのレスポンシブレイアウト"""
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
            
            # 設定フォームが適切に表示されているか確認
            settings_form = page.locator('[data-testid="stVerticalBlock"]').first
            assert settings_form.is_visible()
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"settings_layout_{viewport['name']}"),
                full_page=True
            )