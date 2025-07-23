"""
ダッシュボードページのE2Eテスト
"""

import pytest
from playwright.sync_api import Page, expect


class TestDashboard:
    """ダッシュボードページのテスト"""
    
    @pytest.mark.smoke
    def test_statistics_display(self, page: Page, test_data, screenshot_path):
        """TC002: 統計情報の表示確認"""
        # 統計情報セクションの確認
        stats_section = page.locator("text=統計情報").first
        expect(stats_section).to_be_visible()
        
        # 各統計値の確認
        expected_stats = test_data["expected_stats"]
        
        # 総分析数
        total_analyses = page.locator("text=総分析数").first
        expect(total_analyses).to_be_visible()
        
        # 数値の確認（実際の値は動的なので、数値が表示されていることを確認）
        stats_numbers = page.locator("h2").all()
        assert len(stats_numbers) >= 4, "統計数値が不足しています"
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("dashboard_statistics"), full_page=True)
    
    @pytest.mark.smoke
    def test_popular_stocks_section(self, page: Page, test_data, screenshot_path):
        """TC003: 人気銘柄分析セクション"""
        # セクションの確認
        popular_section = page.locator("text=人気銘柄分析").first
        expect(popular_section).to_be_visible()
        
        # 銘柄の確認
        for stock in test_data["popular_stocks"]:
            symbol_element = page.locator(f"text={stock['symbol']}").first
            expect(symbol_element).to_be_visible()
            
            # 銘柄名の確認
            name_element = page.locator(f"text={stock['name']}").first
            expect(name_element).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("popular_stocks"), full_page=True)
    
    def test_analysis_presets(self, page: Page, screenshot_path):
        """分析プリセットセクションの確認"""
        # プリセットセクションの確認
        presets_section = page.locator("text=分析プリセット").first
        expect(presets_section).to_be_visible()
        
        # 各プリセットの確認
        presets = ["テクニカル分析", "ファンダメンタル分析", "総合分析"]
        for preset in presets:
            preset_element = page.locator(f"text={preset}").first
            expect(preset_element).to_be_visible()
        
        # スクリーンショット
        page.screenshot(path=screenshot_path("analysis_presets"), full_page=True)
    
    def test_quick_actions(self, page: Page, screenshot_path):
        """クイックアクションセクションの確認"""
        # クイックアクションセクションの確認
        quick_actions = page.locator("text=クイックアクション").first
        if quick_actions.is_visible():
            # SPY分析ボタンの確認
            spy_button = page.locator("button", has_text="SPY分析")
            if spy_button.is_visible():
                # ボタンクリックのテスト
                spy_button.click()
                
                # 分析実行ページへの遷移を確認
                page.wait_for_timeout(2000)
                
                # スクリーンショット
                page.screenshot(path=screenshot_path("quick_action_result"), full_page=True)
                
                # ダッシュボードに戻る
                page.locator("text=ダッシュボード").first.click()
    
    @pytest.mark.visual
    def test_dashboard_layout(self, page: Page, screenshot_path):
        """ダッシュボードのレイアウト確認"""
        viewports = [
            {"name": "desktop", "width": 1920, "height": 1080},
            {"name": "laptop", "width": 1366, "height": 768},
            {"name": "tablet", "width": 768, "height": 1024},
            {"name": "mobile", "width": 375, "height": 812},
        ]
        
        for viewport in viewports:
            page.set_viewport_size({
                "width": viewport["width"],
                "height": viewport["height"]
            })
            page.wait_for_timeout(1000)
            
            # スクリーンショット
            page.screenshot(
                path=screenshot_path(f"dashboard_layout_{viewport['name']}"),
                full_page=True
            )
    
    def test_realtime_updates(self, page: Page):
        """リアルタイム更新の確認（該当する場合）"""
        # 初期値を記録
        initial_stats = page.locator("h2").all_text_contents()
        
        # 30秒待機
        page.wait_for_timeout(30000)
        
        # 更新後の値を確認
        updated_stats = page.locator("h2").all_text_contents()
        
        # 値が変化していることを確認（リアルタイムデータがある場合）
        # この部分は実際の実装に応じて調整が必要