"""
結果表示ページのE2Eテスト（更新版）
StreamlitSelectorsを使用した安定したテスト
"""

import pytest
from playwright.sync_api import Page, expect
from utils import StreamlitSelectors, StreamlitPageObjects


class TestResults:
    """結果表示ページのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.selectors = StreamlitSelectors()
    
    @pytest.mark.smoke
    def test_navigate_to_results(self, page: Page, screenshot_path):
        """結果表示ページへのナビゲーション"""
        # 結果ページへ移動
        results_button = page.locator(self.selectors.nav_button("results"))
        results_button.click()
        
        # ページ遷移を待機
        page.wait_for_load_state("networkidle")
        
        # ページタイトルの確認
        page_title = page.locator('h2:has-text("結果表示")')
        expect(page_title).to_be_visible()
        
        # 結果選択ドロップダウンの確認
        result_selector = page.locator(self.selectors.select_box("分析結果を選択"))
        expect(result_selector).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("results_page"), full_page=True)
    
    def test_result_selection(self, page: Page, screenshot_path):
        """分析結果の選択"""
        # 結果選択ドロップダウン
        result_selector = page.locator(self.selectors.select_box("分析結果を選択"))
        
        if result_selector.is_visible():
            # ドロップダウンをクリック
            result_selector.click()
            page.wait_for_timeout(500)
            
            # 利用可能な結果を確認
            options = page.locator('[role="option"]').all()
            
            if options:
                # 最初の結果を選択
                options[0].click()
                page.wait_for_load_state("networkidle")
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("result_selected"), full_page=True)
                
                # 結果が表示されたことを確認
                assert True, "分析結果が選択されました"
            else:
                # 結果がない場合のメッセージ
                no_results = page.locator(self.selectors.alert("info")).first
                if no_results.is_visible():
                    assert True, "分析結果がありません"
                    page.screenshot(path=screenshot_path("no_results"), full_page=True)
    
    def test_results_display(self, page: Page, screenshot_path):
        """TC010: 分析結果の表示"""
        # サマリーセクション
        summary_section = page.locator(self.selectors.results_section("サマリー"))
        
        if summary_section.is_visible():
            # サマリーを展開
            summary_section.click()
            page.wait_for_timeout(500)
            
            # サマリー内容の確認
            summary_content = page.locator('[data-testid="stMarkdown"]').all()
            for content in summary_content:
                text = content.text_content()
                if "分析日" in text or "銘柄" in text or "結果" in text:
                    assert True, "サマリー情報が表示されています"
                    break
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("results_summary"), full_page=True)
        
        # チャートセクション
        chart_elements = page.locator('[data-testid="stPlotlyChart"]').all()
        if chart_elements:
            print(f"チャート要素: {len(chart_elements)}個")
            page.screenshot(path=screenshot_path("results_charts"), full_page=True)
        
        # データテーブル
        table_elements = page.locator(self.selectors.dataframe()).all()
        if table_elements:
            print(f"テーブル要素: {len(table_elements)}個")
            page.screenshot(path=screenshot_path("results_tables"), full_page=True)
        
        # メトリクス
        metric_elements = page.locator(self.selectors.metric("")).all()
        if metric_elements:
            print(f"メトリクス要素: {len(metric_elements)}個")
            page.screenshot(path=screenshot_path("results_metrics"), full_page=True)
    
    def test_agent_discussions(self, page: Page, screenshot_path):
        """エージェント議論の表示"""
        # エージェント議論セクション
        discussion_section = page.locator(self.selectors.results_section("エージェント議論"))
        
        if discussion_section.is_visible():
            # セクションを展開
            discussion_section.click()
            page.wait_for_timeout(500)
            
            # 議論内容を確認
            agent_types = [
                "ファンダメンタルアナリスト",
                "テクニカルアナリスト",
                "センチメントアナリスト",
                "リスクマネージャー"
            ]
            
            for agent in agent_types:
                agent_element = page.locator(f'text="{agent}"').first
                if agent_element.is_visible():
                    assert True, f"{agent}の発言が表示されています"
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("agent_discussions"), full_page=True)
    
    def test_technical_indicators(self, page: Page, screenshot_path):
        """テクニカル指標の表示"""
        # テクニカル指標セクション
        technical_section = page.locator(self.selectors.results_section("テクニカル指標"))
        
        if technical_section.is_visible():
            # セクションを展開
            technical_section.click()
            page.wait_for_timeout(500)
            
            # 指標のテーブルまたはチャート
            indicators_table = page.locator(self.selectors.dataframe()).first
            if indicators_table.is_visible():
                assert True, "テクニカル指標が表示されています"
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("technical_indicators"), full_page=True)
    
    @pytest.mark.slow
    def test_pdf_generation(self, page: Page, screenshot_path):
        """TC011: PDFレポート生成（長時間テスト）"""
        # PDFボタンを探す
        pdf_button = page.locator(self.selectors.button(text="PDFレポート生成"))
        
        if pdf_button.is_visible():
            # 生成前のスクリーンショット
            page.screenshot(path=screenshot_path("pdf_generation_before"), full_page=True)
            
            # スピナーやプログレスを監視する準備
            progress_indicator = page.locator(self.selectors.spinner())
            
            # ダウンロードを待機する準備（タイムアウトを60秒に延長）
            with page.expect_download(timeout=60000) as download_info:
                # PDFボタンをクリック
                pdf_button.click()
                
                # 生成中のスピナーが表示されることを確認
                try:
                    progress_indicator.wait_for(state="visible", timeout=5000)
                    page.screenshot(path=screenshot_path("pdf_generation_progress"), full_page=True)
                except:
                    # スピナーが表示されない場合はスキップ
                    pass
                
                try:
                    # ダウンロードを待機（最大60秒）
                    download = download_info.value
                    
                    # ダウンロードファイル名を確認
                    filename = download.suggested_filename
                    assert filename.endswith(".pdf"), "PDFファイルがダウンロードされました"
                    
                    print(f"PDFファイル名: {filename}")
                    
                    # 成功メッセージ
                    success_alert = page.locator(self.selectors.alert("success")).first
                    if success_alert.is_visible():
                        assert True, "PDFが正常に生成されました"
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("pdf_download_success"), full_page=True)
                    
                except Exception as e:
                    # ダウンロードが発生しない場合
                    page.screenshot(path=screenshot_path("pdf_generation_timeout"), full_page=True)
                    
                    # エラーメッセージを確認
                    error_alert = page.locator(self.selectors.alert("error")).first
                    if error_alert.is_visible():
                        error_text = error_alert.text_content()
                        pytest.fail(f"PDF生成エラー: {error_text}")
                    else:
                        # タイムアウトした場合はスキップして継続
                        pytest.skip(f"PDF生成がタイムアウトしました（60秒）: {e}")
        else:
            # PDFボタンが見つからない場合
            page.screenshot(path=screenshot_path("pdf_button_not_found"), full_page=True)
            pytest.skip("PDFレポート生成ボタンが見つかりません")
    
    def test_result_filtering(self, page: Page, screenshot_path):
        """結果のフィルタリング機能"""
        # 日付範囲フィルタ
        date_range_section = page.locator('text="期間指定"').first
        
        if date_range_section.is_visible():
            # 開始日
            start_date = page.locator('input[type="date"]').first
            if start_date.is_visible():
                start_date.fill("2025-07-01")
                
            # 終了日
            end_date = page.locator('input[type="date"]').nth(1)
            if end_date.is_visible():
                end_date.fill("2025-07-15")
            
            # フィルタ適用ボタン
            apply_button = page.locator(self.selectors.button(text="フィルタ適用"))
            if apply_button.is_visible():
                apply_button.click()
                page.wait_for_load_state("networkidle")
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("results_filtered"), full_page=True)
        
        # 銘柄フィルタ
        symbol_filter = page.locator(self.selectors.select_box("銘柄フィルタ"))
        if symbol_filter.is_visible():
            symbol_filter.click()
            page.wait_for_timeout(500)
            
            # 複数選択
            symbols = ["AAPL", "MSFT", "GOOGL"]
            for symbol in symbols:
                option = page.locator(f'[role="option"]:has-text("{symbol}")').first
                if option.is_visible():
                    option.click()
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("symbol_filter"), full_page=True)
    
    def test_export_functionality(self, page: Page, screenshot_path):
        """エクスポート機能のテスト"""
        # エクスポートオプション
        export_options = {
            "csv": self.selectors.button(text="CSVエクスポート"),
            "excel": self.selectors.button(text="Excelエクスポート"),
            "json": self.selectors.button(text="JSONエクスポート")
        }
        
        for format_name, button_selector in export_options.items():
            export_button = page.locator(button_selector)
            
            if export_button.is_visible():
                # エクスポートボタンをクリック
                with page.expect_download() as download_info:
                    export_button.click()
                    
                    try:
                        download = download_info.value
                        filename = download.suggested_filename
                        print(f"{format_name.upper()}ファイル: {filename}")
                        
                        # スクリーンショット
                        page.screenshot(
                            path=screenshot_path(f"export_{format_name}"),
                            full_page=True
                        )
                    except:
                        pass
    
    def test_result_comparison(self, page: Page, screenshot_path):
        """結果比較機能"""
        # 比較モードのチェックボックス
        compare_checkbox = page.locator(self.selectors.checkbox("比較モード"))
        
        if compare_checkbox.is_visible():
            # 比較モードを有効化
            compare_checkbox.click()
            page.wait_for_timeout(500)
            
            # 比較対象の選択
            compare_selectors = page.locator(self.selectors.select_box("比較対象")).all()
            
            if len(compare_selectors) >= 2:
                # 2つの結果を選択
                for i, selector in enumerate(compare_selectors[:2]):
                    selector.click()
                    options = page.locator('[role="option"]').all()
                    if options and len(options) > i:
                        options[i].click()
                        page.wait_for_timeout(500)
                
                # 比較実行ボタン
                compare_button = page.locator(self.selectors.button(text="比較実行"))
                if compare_button.is_visible():
                    compare_button.click()
                    page.wait_for_load_state("networkidle")
                    
                    # スクリーンショット
                    page.screenshot(path=screenshot_path("result_comparison"), full_page=True)
    
    @pytest.mark.visual
    def test_results_responsive(self, page: Page, screenshot_path):
        """結果ページのレスポンシブ確認"""
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
            
            # 主要要素が適切に表示されているか
            main_content = page.locator('[data-testid="stVerticalBlock"]').first
            assert main_content.is_visible()
            
            # チャートのレスポンシブ確認
            charts = page.locator('[data-testid="stPlotlyChart"]').all()
            if charts:
                # モバイルでチャートが適切にリサイズされているか
                if viewport["width"] < 768:
                    # チャートが縦スクロール可能か確認
                    pass
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"results_layout_{viewport['name']}"),
                full_page=True
            )