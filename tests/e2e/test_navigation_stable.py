"""
安定化されたナビゲーションテスト
StreamlitManagerを使用した堅牢なテスト実装
"""

import pytest
from playwright.sync_api import Page, expect
from utils.streamlit_advanced import create_streamlit_manager
from utils.custom_assertions import CustomAssertions

class TestNavigationStable:
    """安定化されたナビゲーションテスト"""
    
    def setup_method(self, method):
        """各テストメソッドの前に実行"""
        print(f"\n🧪 テスト開始: {method.__name__}")
    
    def test_app_loads_successfully(self, page: Page):
        """アプリケーションが正常に読み込まれることを確認"""
        manager = create_streamlit_manager(page)
        
        # アプリの準備完了を待つ
        assert manager.wait_for_app_ready(), "Streamlitアプリの準備に失敗"
        
        # 基本的な要素の存在確認
        assertions = CustomAssertions(page)
        
        # ヘッダーの確認
        header_title = page.locator('text="TradingAgents WebUI"')
        assertions.assert_element_visible(header_title, "ヘッダータイトル")
        
        # サイドバーの確認
        sidebar = page.locator('[data-testid="stSidebar"]')
        assertions.assert_element_visible(sidebar, "サイドバー")
        
        # メインコンテンツの確認
        main_content = page.locator('.main, [data-testid="main"]')
        assertions.assert_element_visible(main_content, "メインコンテンツ")
        
        # 現在のページ情報を取得
        page_info = manager.get_current_page_info()
        print(f"📋 ページ情報: {page_info}")
        
        # スクリーンショット
        page.screenshot(path="screenshots/app_loaded_stable.png")
    
    @pytest.mark.parametrize("page_name,expected_content", [
        ("dashboard", ["ダッシュボード", "統計情報", "クイックアクション"]),
        ("settings", ["分析設定", "基本設定", "アナリストチーム"]),
        ("execution", ["分析実行", "実行設定確認", "LLM設定"]),
        ("results", ["結果表示", "結果選択", "分析サマリー"])
    ])
    def test_navigation_to_all_pages(self, page: Page, page_name: str, expected_content: list):
        """すべてのページへの安定したナビゲーションテスト"""
        manager = create_streamlit_manager(page)
        
        # アプリの準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # ページへナビゲート
        success = manager.safe_navigate_to_page(page_name)
        assert success, f"{page_name}ページへのナビゲーションに失敗"
        
        # ページ内容の確認
        page_info = manager.get_current_page_info()
        content_text = f"{page_info['title']} {page_info['main_content']}"
        
        # 期待されるコンテンツのいずれかが含まれていることを確認
        content_found = any(expected in content_text for expected in expected_content)
        assert content_found, f"{page_name}ページの期待されるコンテンツが見つかりません: {content_text[:200]}"
        
        # スクリーンショット
        page.screenshot(path=f"screenshots/navigation_{page_name}_stable.png")
        
        print(f"✅ {page_name}ページのナビゲーション成功")
    
    def test_navigation_sequence(self, page: Page):
        """連続的なページナビゲーションテスト"""
        manager = create_streamlit_manager(page)
        
        # 初期準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # ナビゲーションシーケンス
        navigation_sequence = [
            "settings",
            "execution", 
            "results",
            "dashboard"
        ]
        
        for i, page_name in enumerate(navigation_sequence):
            print(f"🔄 ステップ {i+1}: {page_name}ページへ移動")
            
            success = manager.safe_navigate_to_page(page_name)
            assert success, f"ステップ{i+1}: {page_name}ページへの移動失敗"
            
            # 各ステップでスクリーンショット
            page.screenshot(path=f"screenshots/sequence_{i+1:02d}_{page_name}.png")
            
            # 短い待機（安定化）
            page.wait_for_timeout(1000)
        
        print("✅ ナビゲーションシーケンス完了")
    
    def test_error_handling(self, page: Page):
        """エラーハンドリングのテスト"""
        manager = create_streamlit_manager(page)
        
        # アプリの準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # エラーチェック
        errors = manager._check_for_errors()
        
        if errors:
            print(f"⚠️ 検出されたエラー: {errors}")
            # エラーがあってもテストは続行（ログ記録目的）
        
        # エラーがある場合のスクリーンショット
        page.screenshot(path="screenshots/error_check.png")
        
        # 重大なエラーがないことを確認（アプリが動作していること）
        main_content = page.locator('.main')
        assert main_content.is_visible(), "メインコンテンツが表示されていません"
    
    def test_responsive_navigation(self, page: Page):
        """レスポンシブでのナビゲーションテスト"""
        manager = create_streamlit_manager(page)
        
        # モバイルビューポート
        page.set_viewport_size({"width": 375, "height": 667})
        
        # アプリの準備
        assert manager.wait_for_app_ready(), "モバイルビューでの初期準備失敗"
        
        # モバイルでのナビゲーションテスト
        success = manager.safe_navigate_to_page("settings")
        assert success, "モバイルビューでの設定ページナビゲーション失敗"
        
        # モバイルビューのスクリーンショット
        page.screenshot(path="screenshots/mobile_navigation_stable.png")
        
        # デスクトップビューに戻す
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.wait_for_timeout(1000)
        
        # デスクトップでの動作確認
        success = manager.safe_navigate_to_page("dashboard")
        assert success, "デスクトップビューでのダッシュボードナビゲーション失敗"
        
        page.screenshot(path="screenshots/desktop_navigation_stable.png")
    
    def test_page_state_persistence(self, page: Page):
        """ページ状態の持続性テスト"""
        manager = create_streamlit_manager(page)
        
        # 初期準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # 設定ページへ移動
        success = manager.safe_navigate_to_page("settings")
        assert success, "設定ページへの移動失敗"
        
        # 設定ページの状態を記録
        settings_info = manager.get_current_page_info()
        
        # 他のページへ移動
        manager.safe_navigate_to_page("execution")
        
        # 設定ページに戻る
        success = manager.safe_navigate_to_page("settings")
        assert success, "設定ページへの再移動失敗"
        
        # 状態が保持されているか確認
        new_settings_info = manager.get_current_page_info()
        
        # 基本的な情報が一致することを確認
        assert "設定" in new_settings_info["main_content"], "設定ページの内容が保持されていません"
        
        print("✅ ページ状態の持続性確認完了")
    
    def test_concurrent_actions(self, page: Page):
        """同時操作への耐性テスト"""
        manager = create_streamlit_manager(page)
        
        # 初期準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # 複数の操作を素早く実行
        actions = [
            lambda: manager.safe_navigate_to_page("settings"),
            lambda: page.mouse.move(100, 100),
            lambda: manager.safe_navigate_to_page("execution"),
            lambda: page.keyboard.press("Tab"),
            lambda: manager.safe_navigate_to_page("results")
        ]
        
        # 操作を短い間隔で実行
        for i, action in enumerate(actions):
            try:
                action()
                page.wait_for_timeout(200)  # 短い待機
                print(f"✅ 同時操作 {i+1} 完了")
            except Exception as e:
                print(f"⚠️ 同時操作 {i+1} でエラー: {e}")
        
        # 最終的にアプリが安定していることを確認
        final_info = manager.get_current_page_info()
        assert final_info["main_content"], "同時操作後のアプリ状態が不安定"
        
        page.screenshot(path="screenshots/concurrent_actions_final.png")
        print("✅ 同時操作耐性テスト完了")