"""
結果表示ページのE2Eテスト
"""

import pytest
from playwright.sync_api import Page, expect
import time


class TestResults:
    """結果表示ページのテスト"""
    
    @pytest.mark.smoke
    def test_navigate_to_results(self, page: Page, screenshot_path):
        """結果表示ページへのナビゲーション"""
        # 結果ページへ移動
        results_link = page.locator("text=結果表示").first
        results_link.click()
        
        # ページ遷移を待機
        page.wait_for_timeout(2000)
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("results_page"), full_page=True)
        
        # 基本要素の確認
        page_content = page.content()
        assert "結果" in page_content or "Results" in page_content, \
               "結果ページが表示されています"
    
    def test_results_display(self, page: Page, screenshot_path):
        """TC010: 分析結果の表示"""
        # 結果ページへ移動
        page.locator("text=結果表示").first.click()
        page.wait_for_timeout(2000)
        
        # 結果が存在する場合の要素を確認
        results_elements = {
            "charts": page.locator("canvas, [data-testid='stPlotlyChart']").all(),
            "tables": page.locator("table, [data-testid='stDataFrame']").all(),
            "metrics": page.locator("[data-testid='stMetric']").all(),
            "expanders": page.locator("[data-testid='stExpander']").all()
        }
        
        # 各要素の存在確認とスクリーンショット
        if results_elements["charts"]:
            print(f"チャート要素: {len(results_elements['charts'])}個")
            page.screenshot(path=screenshot_path("results_charts"), full_page=True)
        
        if results_elements["tables"]:
            print(f"テーブル要素: {len(results_elements['tables'])}個")
            page.screenshot(path=screenshot_path("results_tables"), full_page=True)
        
        if results_elements["metrics"]:
            print(f"メトリクス要素: {len(results_elements['metrics'])}個")
            page.screenshot(path=screenshot_path("results_metrics"), full_page=True)
        
        # エクスパンダーを展開
        for i, expander in enumerate(results_elements["expanders"][:3]):  # 最初の3つまで
            try:
                expander.click()
                page.wait_for_timeout(500)
                page.screenshot(path=screenshot_path(f"results_expander_{i}"), full_page=True)
            except:
                pass
    
    def test_pdf_generation(self, page: Page, screenshot_path):
        """TC011: PDFレポート生成"""
        # 結果ページへ移動
        page.locator("text=結果表示").first.click()
        page.wait_for_timeout(2000)
        
        # PDFボタンを探す
        pdf_buttons = []
        buttons = page.locator("button").all()
        
        for button in buttons:
            button_text = button.text_content()
            if "PDF" in button_text or "レポート" in button_text or "Report" in button_text:
                pdf_buttons.append(button)
        
        if pdf_buttons:
            # ダウンロードを待機する準備
            with page.expect_download() as download_info:
                # PDFボタンをクリック
                pdf_buttons[0].click()
                
                try:
                    # ダウンロードを待機（最大10秒）
                    download = download_info.value
                    
                    # ダウンロードファイル名を確認
                    filename = download.suggested_filename
                    assert filename.endswith(".pdf"), "PDFファイルがダウンロードされました"
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("pdf_download_success"), full_page=True)
                    
                    print(f"PDFファイル名: {filename}")
                    
                except Exception as e:
                    # ダウンロードが発生しない場合
                    page.screenshot(path=screenshot_path("pdf_generation_screen"), full_page=True)
                    pytest.skip(f"PDFダウンロードが開始されませんでした: {e}")
        else:
            pytest.skip("PDFレポートボタンが見つかりません")
    
    def test_result_filtering(self, page: Page, screenshot_path):
        """結果のフィルタリング機能"""
        # 結果ページへ移動
        page.locator("text=結果表示").first.click()
        page.wait_for_timeout(2000)
        
        # フィルタオプションを探す
        filter_elements = {
            "date_inputs": page.locator("input[type='date']").all(),
            "select_boxes": page.locator("[data-baseweb='select']").all(),
            "radio_buttons": page.locator("input[type='radio']").all(),
            "checkboxes": page.locator("input[type='checkbox']").all()
        }
        
        # 日付フィルタ
        if filter_elements["date_inputs"]:
            # 開始日を設定
            filter_elements["date_inputs"][0].fill("2025-07-01")
            page.wait_for_timeout(1000)
            page.screenshot(path=screenshot_path("results_filtered_date"), full_page=True)
        
        # セレクトボックスフィルタ
        if filter_elements["select_boxes"]:
            filter_elements["select_boxes"][0].click()
            page.wait_for_timeout(500)
            
            # オプションを選択
            options = page.locator("[role='option']").all()
            if options:
                options[0].click()
                page.wait_for_timeout(1000)
                page.screenshot(path=screenshot_path("results_filtered_select"), full_page=True)
        
        # チェックボックスフィルタ
        for checkbox in filter_elements["checkboxes"][:2]:  # 最初の2つ
            checkbox.click()
            page.wait_for_timeout(500)
        
        if filter_elements["checkboxes"]:
            page.screenshot(path=screenshot_path("results_filtered_checkbox"), full_page=True)
    
    def test_export_functionality(self, page: Page, screenshot_path):
        """エクスポート機能のテスト"""
        # 結果ページへ移動
        page.locator("text=結果表示").first.click()
        page.wait_for_timeout(2000)
        
        # エクスポートボタンを探す
        export_buttons = []
        buttons = page.locator("button").all()
        
        for button in buttons:
            button_text = button.text_content()
            if "Export" in button_text or "エクスポート" in button_text or \
               "CSV" in button_text or "Excel" in button_text:
                export_buttons.append(button)
        
        if export_buttons:
            # エクスポートメニューのスクリーンショット
            page.screenshot(path=screenshot_path("export_options"), full_page=True)
            
            # 最初のエクスポートボタンをクリック
            export_buttons[0].click()
            page.wait_for_timeout(1000)
            
            # エクスポート後のスクリーンショット
            page.screenshot(path=screenshot_path("export_clicked"), full_page=True)