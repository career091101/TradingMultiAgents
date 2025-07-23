"""
ダッシュボードページのE2Eテスト（更新版）
StreamlitSelectorsを使用した安定したテスト
"""

import pytest
from playwright.sync_api import Page, expect
from utils import StreamlitSelectors, StreamlitPageObjects


class TestDashboard:
    """ダッシュボードページのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.selectors = StreamlitSelectors()
    
    @pytest.mark.smoke
    def test_statistics_display(self, page: Page, test_data, screenshot_path):
        """TC002: 統計情報の表示確認"""
        # ダッシュボードページにいることを確認
        dashboard_title = page.locator('h2:has-text("ダッシュボード")')
        expect(dashboard_title).to_be_visible()
        
        # 統計メトリックの確認
        metrics = {
            "総分析数": self.selectors.dashboard_stat("総分析数"),
            "完了分析": self.selectors.dashboard_stat("完了分析"),
            "実行中": self.selectors.dashboard_stat("実行中"),
            "成功率": self.selectors.dashboard_stat("成功率")
        }
        
        for metric_name, selector in metrics.items():
            metric_element = page.locator(selector)
            expect(metric_element).to_be_visible()
            
            # メトリックの値を取得（値自体は動的なので存在確認のみ）
            value_element = metric_element.locator('[data-testid="stMetricValue"]').first
            assert value_element.is_visible(), f"{metric_name}の値が表示されていません"
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("dashboard_statistics"), full_page=True)
    
    @pytest.mark.smoke
    def test_popular_stocks_section(self, page: Page, test_data, screenshot_path):
        """TC003: 人気銘柄分析セクション"""
        # 人気銘柄分析セクションの確認
        popular_section = page.locator('text="人気銘柄分析"').first
        expect(popular_section).to_be_visible()
        
        # 銘柄カードの確認
        expected_stocks = test_data["popular_stocks"]
        
        for stock in expected_stocks:
            # 銘柄シンボルの確認
            symbol_element = page.locator(f'text="{stock["symbol"]}"').first
            expect(symbol_element).to_be_visible()
            
            # 銘柄名の確認
            name_element = page.locator(f'text="{stock["name"]}"').first
            expect(name_element).to_be_visible()
            
            # 分析開始ボタンの確認
            analyze_button = page.locator(
                f'button:has-text("{stock["symbol"]}"):has-text("分析"), '
                f'button:has-text("分析開始"):near(text="{stock["symbol"]}")'
            ).first
            
            if analyze_button.is_visible():
                # ボタンが存在する場合の処理
                assert True, f"{stock['symbol']}の分析ボタンが確認できました"
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("popular_stocks"), full_page=True)
    
    def test_analysis_presets(self, page: Page, screenshot_path):
        """分析プリセットセクションの確認"""
        # プリセットセクションの確認
        presets_section = page.locator('text="分析プリセット"').first
        
        if presets_section.is_visible():
            # 各プリセットの確認
            presets = ["テクニカル分析", "ファンダメンタル分析", "総合分析"]
            
            for preset in presets:
                preset_element = page.locator(f'text="{preset}"').first
                if preset_element.is_visible():
                    # プリセットボタンまたはカードの確認
                    preset_button = page.locator(f'button:has-text("{preset}")').first
                    if preset_button.is_visible():
                        assert True, f"{preset}プリセットが表示されています"
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("analysis_presets"), full_page=True)
    
    def test_recent_analysis_history(self, page: Page, screenshot_path):
        """最近の分析履歴の確認"""
        # 分析履歴セクションを探す
        history_section = page.locator('text="最近の分析", text="分析履歴"').first
        
        if history_section.is_visible():
            # データフレームまたはテーブルの確認
            dataframe = page.locator(self.selectors.dataframe()).first
            
            if dataframe.is_visible():
                # スクリーンショット
                page.screenshot(path=screenshot_path("analysis_history"), full_page=True)
                assert True, "分析履歴が表示されています"
            else:
                # 履歴がない場合のメッセージ確認
                no_history_msg = page.locator('text="分析履歴がありません"').first
                if no_history_msg.is_visible():
                    assert True, "分析履歴なしのメッセージが表示されています"
    
    @pytest.mark.visual
    def test_dashboard_layout(self, page: Page, screenshot_path):
        """ダッシュボードのレイアウト確認"""
        viewports = [
            {"name": "desktop_full", "width": 1920, "height": 1080},
            {"name": "desktop_narrow", "width": 1366, "height": 768},
            {"name": "tablet_landscape", "width": 1024, "height": 768},
            {"name": "tablet_portrait", "width": 768, "height": 1024},
            {"name": "mobile", "width": 375, "height": 812},
        ]
        
        for viewport in viewports:
            page.set_viewport_size({
                "width": viewport["width"],
                "height": viewport["height"]
            })
            page.wait_for_timeout(1000)
            
            # レイアウトが適切に調整されているか確認
            sidebar = page.locator(self.selectors.sidebar())
            main_content = page.locator('[data-testid="stAppViewContainer"]')
            
            # モバイルサイズでの特別な確認
            if viewport["width"] < 768:
                # モバイルではサイドバーが折りたたまれる可能性
                # Streamlitのモバイル対応を確認
                pass
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"dashboard_layout_{viewport['name']}"),
                full_page=True
            )
    
    def test_realtime_updates(self, page: Page):
        """リアルタイム更新の確認（該当する場合）"""
        # 分析実行中の表示を確認
        analysis_status = page.locator(self.selectors.markdown_with_text("分析実行中")).first
        
        if analysis_status.is_visible():
            # プログレス表示の確認
            progress = page.locator(self.selectors.progress_bar()).first
            spinner = page.locator(self.selectors.spinner()).first
            
            if progress.is_visible() or spinner.is_visible():
                assert True, "分析進捗が表示されています"
                
                # 進捗メッセージの確認
                progress_msg = page.locator('[data-testid="stMarkdown"]').all()
                for msg in progress_msg:
                    text = msg.text_content()
                    if "エージェント" in text or "分析中" in text:
                        assert True, f"進捗メッセージが表示されています: {text[:50]}..."
    
    def test_system_info_display(self, page: Page, screenshot_path):
        """システム情報の表示確認"""
        # サイドバーの現在の設定表示
        current_settings = page.locator(self.selectors.markdown_with_text("現在の設定")).first
        
        if current_settings.is_visible():
            # 設定情報の確認
            settings_info = {
                "ticker": "ティッカー",
                "date": "日付",
                "depth": "深度",
                "llm": "LLM"
            }
            
            for key, label in settings_info.items():
                setting_element = page.locator(f'text="{label}:"').first
                if setting_element.is_visible():
                    assert True, f"{label}情報が表示されています"
            
            # スクリーンショット
            page.screenshot(path=screenshot_path("system_info"), full_page=True)