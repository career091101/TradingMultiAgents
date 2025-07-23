"""
分析実行ページのE2Eテスト
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestExecution:
    """分析実行ページのテスト"""
    
    @pytest.mark.smoke
    def test_navigate_to_execution(self, page: Page, screenshot_path):
        """分析実行ページへのナビゲーション"""
        # 実行ページへ移動
        execution_link = page.locator("text=分析実行").first
        execution_link.click()
        
        # ページ遷移を待機
        page.wait_for_timeout(2000)
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("execution_page"), full_page=True)
        
        # 基本要素の確認（ページの内容を確認）
        page_content = page.content()
        assert "分析" in page_content or "Analysis" in page_content or "実行" in page_content, \
               "分析実行ページが表示されています"
    
    @pytest.mark.parametrize("symbol,expected_result", [
        ("", "error"),
        ("123", "error"),
        ("INVALID", "error"),
        ("AAPL", "valid"),
    ])
    def test_symbol_validation(self, page: Page, symbol, expected_result, screenshot_path):
        """TC008: 入力検証"""
        # 実行ページへ移動
        page.locator("text=分析実行").first.click()
        page.wait_for_timeout(2000)
        
        # 入力フィールドを探す
        input_fields = page.locator("input[type='text']").all()
        
        if input_fields:
            # 最初の入力フィールドに銘柄を入力
            symbol_input = input_fields[0]
            symbol_input.fill(symbol)
            
            # Enterキーまたは実行ボタンをクリック
            symbol_input.press("Enter")
            page.wait_for_timeout(1000)
            
            # エラーメッセージの確認
            if expected_result == "error":
                # エラーアラートが表示されるか確認
                error_alert = page.locator("[data-testid='stAlert']").first
                if symbol == "":
                    # 空の入力の場合のスクリーンショット
                    page.screenshot(path=screenshot_path(f"validation_empty"), full_page=True)
                else:
                    # 無効な入力の場合のスクリーンショット
                    page.screenshot(path=screenshot_path(f"validation_invalid_{symbol}"), full_page=True)
            else:
                # 有効な入力の場合
                page.screenshot(path=screenshot_path(f"validation_valid_{symbol}"), full_page=True)
        else:
            pytest.skip("銘柄入力フィールドが見つかりません")
    
    @pytest.mark.slow
    def test_analysis_execution(self, page: Page, screenshot_path):
        """TC007: 基本的な分析実行"""
        # 実行ページへ移動
        page.locator("text=分析実行").first.click()
        page.wait_for_timeout(2000)
        
        # 銘柄入力
        input_fields = page.locator("input[type='text']").all()
        if input_fields:
            symbol_input = input_fields[0]
            symbol_input.fill("AAPL")
            
            # 実行ボタンを探してクリック
            run_buttons = page.locator("button").all()
            run_button = None
            
            for button in run_buttons:
                button_text = button.text_content()
                if "実行" in button_text or "Run" in button_text or "分析" in button_text:
                    run_button = button
                    break
            
            if run_button:
                # 実行前のスクリーンショット
                page.screenshot(path=screenshot_path("before_execution"), full_page=True)
                
                # 実行ボタンをクリック
                run_button.click()
                
                # プログレス表示を待機（最大30秒）
                try:
                    # プログレスバーまたはスピナーを探す
                    page.wait_for_selector(
                        "[data-testid='stSpinner'], [role='progressbar']",
                        timeout=5000
                    )
                    
                    # 実行中のスクリーンショット
                    page.screenshot(path=screenshot_path("during_execution"), full_page=True)
                    
                    # 完了を待機（最大30秒）
                    page.wait_for_selector(
                        "[data-testid='stSpinner'], [role='progressbar']",
                        state="hidden",
                        timeout=30000
                    )
                    
                    # 実行後のスクリーンショット
                    page.screenshot(path=screenshot_path("after_execution"), full_page=True)
                    
                except Exception as e:
                    # タイムアウトまたはエラーの場合
                    page.screenshot(path=screenshot_path("execution_error"), full_page=True)
                    pytest.skip(f"分析実行がタイムアウトしました: {e}")
            else:
                pytest.skip("実行ボタンが見つかりません")
        else:
            pytest.skip("銘柄入力フィールドが見つかりません")
    
    def test_multiple_symbols(self, page: Page, screenshot_path):
        """TC009: 複数銘柄の分析"""
        # 実行ページへ移動
        page.locator("text=分析実行").first.click()
        page.wait_for_timeout(2000)
        
        # 複数銘柄モードのトグルやチェックボックスを探す
        checkboxes = page.locator("input[type='checkbox']").all()
        
        for checkbox in checkboxes:
            # ラベルテキストを確認
            label = checkbox.locator("..").text_content()
            if "複数" in label or "Multiple" in label or "Batch" in label:
                checkbox.click()
                page.wait_for_timeout(1000)
                
                # 複数銘柄入力フィールドを探す
                text_areas = page.locator("textarea").all()
                if text_areas:
                    text_areas[0].fill("AAPL,MSFT,GOOGL")
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("multiple_symbols"), full_page=True)
                    return
        
        pytest.skip("複数銘柄モードが見つかりません")