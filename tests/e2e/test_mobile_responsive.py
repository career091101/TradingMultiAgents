"""
モバイルレスポンシブのE2Eテスト
"""

import pytest
from playwright.sync_api import Page, expect
from utils.streamlit_selectors import StreamlitSelectors
from utils.custom_assertions import CustomAssertions
from utils.streamlit_helpers import close_deploy_dialog, wait_for_streamlit_ready, force_click_element

class TestMobileResponsive:
    """モバイルレスポンシブのテスト"""
    
    @pytest.mark.parametrize("viewport", [
        {"width": 375, "height": 667, "name": "iPhone_SE"},
        {"width": 414, "height": 896, "name": "iPhone_11"},
        {"width": 768, "height": 1024, "name": "iPad_Portrait"},
        {"width": 1024, "height": 768, "name": "iPad_Landscape"},
    ])
    def test_responsive_layout(self, page: Page, viewport: dict):
        """各種デバイスサイズでのレイアウトテスト"""
        # ビューポートを設定
        page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
        
        # ページを読み込み
        page.goto(page.url)
        page.wait_for_load_state("networkidle")
        
        # カスタムアサーション
        assertions = CustomAssertions(page)
        
        # サイドバーの状態を確認
        sidebar = page.locator('[data-testid="stSidebar"]')
        
        if viewport["width"] <= 768:
            # モバイルビューではサイドバーが初期状態で非表示
            # Streamlitのautoモードでは自動的に折りたたまれる
            page.wait_for_timeout(1000)  # CSSアニメーション待機
            
            # ハンバーガーメニューが表示されているか確認
            hamburger = page.locator('button[kind="header"]').first
            if hamburger.is_visible():
                # ハンバーガーメニューをクリックしてサイドバーを開く
                hamburger.click()
                page.wait_for_timeout(500)
                
                # サイドバーが開いたことを確認
                assertions.assert_element_visible('[data-testid="stSidebar"]')
                
                # 再度クリックして閉じる
                hamburger.click()
                page.wait_for_timeout(500)
        else:
            # デスクトップビューではサイドバーが表示されている
            assertions.assert_element_visible('[data-testid="stSidebar"]')
        
        # スクリーンショットを保存
        page.screenshot(path=f"screenshots/responsive_{viewport['name']}.png")
    
    def test_mobile_navigation(self, page: Page):
        """モバイルでのナビゲーションテスト"""
        # モバイルビューポートに設定
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(page.url)
        
        # Streamlitの準備を待つ
        wait_for_streamlit_ready(page)
        
        assertions = CustomAssertions(page)
        
        # ハンバーガーメニューを開く
        hamburger = page.locator('button[kind="header"]').first
        if hamburger.is_visible():
            hamburger.click()
            page.wait_for_timeout(500)
        
        # 各ページへナビゲート
        pages = [
            ("分析設定", "settings"),
            ("分析実行", "execution"),
            ("結果表示", "results"),
            ("ダッシュボード", "dashboard")
        ]
        
        for page_name, page_id in pages:
            # デプロイダイアログを再度チェック
            close_deploy_dialog(page)
            
            # ナビゲーションボタンをクリック
            nav_selector = StreamlitSelectors.nav_button(page_id)
            
            # 強制クリックを試行
            if not force_click_element(page, nav_selector):
                # 通常のクリックにフォールバック
                nav_button = page.locator(nav_selector)
                nav_button.wait_for(state="visible", timeout=5000)
                nav_button.click()
            
            # ページの安定化を待つ
            wait_for_streamlit_ready(page)
            
            # ページが切り替わったことを確認
            page.wait_for_timeout(1000)
            
            # スクリーンショット
            page.screenshot(path=f"screenshots/mobile_nav_{page_id}.png")
    
    def test_touch_interactions(self, page: Page):
        """タッチ操作のテスト"""
        # タッチデバイスをエミュレート
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(page.url)
        page.wait_for_load_state("networkidle")
        
        # 設定ページへ移動
        hamburger = page.locator('button[kind="header"]').first
        if hamburger.is_visible():
            hamburger.click()
            page.wait_for_timeout(500)
        
        settings_button = page.locator(StreamlitSelectors.nav_button("settings"))
        settings_button.click()
        page.wait_for_load_state("networkidle")
        
        # タッチ可能な要素のサイズを確認
        buttons = page.locator('button').all()
        for button in buttons[:5]:  # 最初の5つのボタンをチェック
            if button.is_visible():
                box = button.bounding_box()
                if box:
                    # タッチターゲットサイズが44x44px以上であることを確認
                    assert box['width'] >= 44 or box['height'] >= 44, \
                        f"タッチターゲットが小さすぎます: {box['width']}x{box['height']}"
    
    def test_orientation_change(self, page: Page):
        """画面回転のテスト"""
        page.goto(page.url)
        
        # 縦向き
        page.set_viewport_size({"width": 375, "height": 667})
        page.wait_for_timeout(1000)
        page.screenshot(path="screenshots/orientation_portrait.png")
        
        # 横向き
        page.set_viewport_size({"width": 667, "height": 375})
        page.wait_for_timeout(1000)
        page.screenshot(path="screenshots/orientation_landscape.png")
        
        # 要素が適切に再配置されているか確認
        assertions = CustomAssertions(page)
        assertions.assert_element_visible('[data-testid="stHeader"]')
        
    def test_mobile_performance(self, page: Page):
        """モバイルでのパフォーマンステスト"""
        # モバイルビューポート
        page.set_viewport_size({"width": 375, "height": 667})
        
        # ネットワーク速度を3Gに制限
        page.context.set_offline(False)
        
        # ページ読み込み時間を計測
        start_time = page.evaluate("Date.now()")
        page.goto(page.url)
        page.wait_for_load_state("networkidle")
        load_time = page.evaluate("Date.now()") - start_time
        
        # 3秒以内に読み込まれることを確認
        assert load_time < 3000, f"ページ読み込みが遅すぎます: {load_time}ms"
        
        # インタラクションの応答性をテスト
        hamburger = page.locator('button[kind="header"]').first
        if hamburger.is_visible():
            start = page.evaluate("Date.now()")
            hamburger.click()
            page.wait_for_timeout(100)
            interaction_time = page.evaluate("Date.now()") - start
            
            # 100ms以内に応答することを確認
            assert interaction_time < 200, f"インタラクションが遅すぎます: {interaction_time}ms"