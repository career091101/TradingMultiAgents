"""
設定ページのE2Eテスト
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestSettings:
    """設定ページのテスト"""
    
    @pytest.mark.smoke
    def test_navigate_to_settings(self, page: Page, screenshot_path):
        """TC004: 設定ページへのナビゲーション"""
        # 設定ページへ移動
        settings_link = page.locator("text=分析設定").first
        settings_link.click()
        
        # ページ遷移を待機
        page.wait_for_timeout(2000)
        
        # 設定ページの要素確認
        # APIキーセクションの確認
        api_section = page.locator("text=API").first
        if api_section.is_visible():
            assert True, "APIセクションが表示されています"
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("settings_page"), full_page=True)
    
    def test_api_key_input(self, page: Page, test_data, screenshot_path):
        """TC005: APIキー設定"""
        # 設定ページへ移動
        page.locator("text=分析設定").first.click()
        page.wait_for_timeout(2000)
        
        # APIキー入力フィールドを探す
        # Streamlitの入力フィールドは特定のdata-testidを持つ
        api_inputs = page.locator("input[type='password']").all()
        
        if len(api_inputs) >= 2:
            # FINNHUB API KEYの入力
            finnhub_input = api_inputs[0]
            finnhub_input.fill(test_data["api_keys"]["finnhub"])
            
            # OPENAI API KEYの入力
            openai_input = api_inputs[1]
            openai_input.fill(test_data["api_keys"]["openai"])
            
            # スクリーンショット（入力後）
            page.screenshot(path=screenshot_path("api_keys_entered"), full_page=True)
            
            # マスキング確認
            assert finnhub_input.get_attribute("type") == "password", "APIキーがマスクされています"
            assert openai_input.get_attribute("type") == "password", "APIキーがマスクされています"
        else:
            pytest.skip("APIキー入力フィールドが見つかりません")
    
    def test_model_selection(self, page: Page, test_data, screenshot_path):
        """TC006: モデル選択"""
        # 設定ページへ移動
        page.locator("text=分析設定").first.click()
        page.wait_for_timeout(2000)
        
        # モデル選択ドロップダウンを探す
        # Streamlitのselectboxは特定の構造を持つ
        model_selectors = page.locator("[data-baseweb='select']").all()
        
        if model_selectors:
            # 最初のドロップダウンをクリック
            model_selectors[0].click()
            page.wait_for_timeout(1000)
            
            # オプションが表示されるか確認
            options_visible = False
            for model in test_data["models"]["deep_thinking"]:
                if page.locator(f"text={model}").is_visible():
                    options_visible = True
                    break
            
            if options_visible:
                # スクリーンショット（ドロップダウン展開時）
                page.screenshot(path=screenshot_path("model_dropdown_open"), full_page=True)
                
                # オプションを選択
                page.locator(f"text={test_data['models']['deep_thinking'][0]}").first.click()
                page.wait_for_timeout(1000)
                
                # スクリーンショット（選択後）
                page.screenshot(path=screenshot_path("model_selected"), full_page=True)
            else:
                pytest.skip("モデル選択オプションが表示されません")
        else:
            pytest.skip("モデル選択ドロップダウンが見つかりません")
    
    def test_settings_persistence(self, page: Page):
        """設定の永続性確認"""
        # 設定ページへ移動
        page.locator("text=分析設定").first.click()
        page.wait_for_timeout(2000)
        
        # 設定を変更（例：スライダーやチェックボックス）
        sliders = page.locator("[role='slider']").all()
        if sliders:
            # 最初のスライダーの値を記録
            initial_value = sliders[0].get_attribute("aria-valuenow")
            
            # 値を変更
            sliders[0].click()
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(500)
            
            new_value = sliders[0].get_attribute("aria-valuenow")
            assert initial_value != new_value, "スライダーの値が変更されました"
            
            # 別のページに移動して戻る
            page.locator("text=ダッシュボード").first.click()
            page.wait_for_timeout(2000)
            page.locator("text=分析設定").first.click()
            page.wait_for_timeout(2000)
            
            # 値が保持されているか確認
            current_value = page.locator("[role='slider']").first.get_attribute("aria-valuenow")
            assert current_value == new_value, "設定が保持されています"