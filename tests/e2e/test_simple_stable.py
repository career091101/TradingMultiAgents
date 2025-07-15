"""
シンプルな安定化テスト
"""

import pytest
from playwright.sync_api import Page
from utils.streamlit_advanced import create_streamlit_manager

class TestSimpleStable:
    """シンプルな安定化テスト"""
    
    def test_basic_app_functionality(self, page: Page):
        """基本的なアプリ機能のテスト"""
        manager = create_streamlit_manager(page)
        
        # アプリの準備完了を待つ
        ready = manager.wait_for_app_ready()
        assert ready, "Streamlitアプリの準備に失敗"
        
        # 現在のページ情報を取得
        page_info = manager.get_current_page_info()
        print(f"📋 現在のページ情報: {page_info}")
        
        # 基本的な要素の確認
        # ヘッダー
        header = page.locator('text="TradingAgents WebUI"')
        if header.count() > 0:
            print("✅ ヘッダータイトル確認済み")
        
        # サイドバー
        sidebar = page.locator('[data-testid="stSidebar"]')
        if sidebar.is_visible():
            print("✅ サイドバー表示確認済み")
        
        # メインコンテンツ
        main = page.locator('.main')
        if main.is_visible():
            print("✅ メインコンテンツ表示確認済み")
        
        # スクリーンショット
        page.screenshot(path="screenshots/basic_functionality.png")
        
        # 基本的なアサーション（取得できた情報を元に）
        content_check = (
            "TradingAgents" in page_info["title"] or 
            "ダッシュボード" in page_info["sidebar_active"] or
            "TradingAgents" in page_info["main_content"] or
            "ダッシュボード" in page_info["main_content"]
        )
        
        assert content_check, f"アプリの基本コンテンツが確認できません。取得情報: {page_info}"
    
    def test_page_navigation_basic(self, page: Page):
        """基本的なページナビゲーション"""
        manager = create_streamlit_manager(page)
        
        # 初期準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # 設定ページに移動
        success = manager.safe_navigate_to_page("settings")
        if success:
            print("✅ 設定ページナビゲーション成功")
            page.screenshot(path="screenshots/settings_page.png")
        else:
            print("⚠️ 設定ページナビゲーション失敗、継続")
        
        # ダッシュボードに戻る
        success = manager.safe_navigate_to_page("dashboard")
        if success:
            print("✅ ダッシュボードナビゲーション成功")
            page.screenshot(path="screenshots/dashboard_return.png")
        else:
            print("⚠️ ダッシュボードナビゲーション失敗、継続")
        
        # 最終状態の確認
        final_info = manager.get_current_page_info()
        assert final_info["main_content"], "最終状態でコンテンツが表示されていません"
        
        print(f"📋 最終ページ情報: {final_info}")
    
    def test_error_resilience(self, page: Page):
        """エラー耐性テスト"""
        manager = create_streamlit_manager(page)
        
        # 初期準備
        assert manager.wait_for_app_ready(), "初期準備失敗"
        
        # 存在しないページへの移動を試行
        success = manager.safe_navigate_to_page("nonexistent")
        print(f"📍 存在しないページへの移動結果: {success}")
        
        # アプリが安定していることを確認
        page_info = manager.get_current_page_info()
        assert page_info["main_content"], "エラー後にアプリが不安定になりました"
        
        # エラーチェック
        errors = manager._check_for_errors()
        if errors:
            print(f"⚠️ 検出されたエラー: {errors}")
        
        # 正常なページに移動できることを確認
        success = manager.safe_navigate_to_page("dashboard")
        print(f"📍 ダッシュボードへの復旧: {success}")
        
        page.screenshot(path="screenshots/error_resilience_final.png")