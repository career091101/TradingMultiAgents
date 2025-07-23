"""
Streamlit特有の要素を扱うヘルパー関数
"""

from playwright.sync_api import Page
import time

def close_deploy_dialog(page: Page):
    """Streamlitのデプロイダイアログを閉じる"""
    try:
        # デプロイダイアログのクローズボタンを探す
        close_button = page.locator('button[aria-label="Close"]').first
        if close_button.is_visible():
            close_button.click()
            time.sleep(0.5)
            print("✅ デプロイダイアログを閉じました")
            return True
        
        # 別のクローズボタンパターン
        close_x = page.locator('button:has-text("×")').first
        if close_x.is_visible():
            close_x.click()
            time.sleep(0.5)
            print("✅ デプロイダイアログを閉じました")
            return True
            
        # ダイアログの外側をクリック
        backdrop = page.locator('[data-testid="stModal"]')
        if backdrop.is_visible():
            # モーダルの外側をクリック
            page.mouse.click(10, 10)
            time.sleep(0.5)
            print("✅ モーダルの外側をクリックしてダイアログを閉じました")
            return True
            
    except Exception as e:
        print(f"⚠️ デプロイダイアログのクローズに失敗: {e}")
    
    return False

def wait_for_streamlit_ready(page: Page, timeout: int = 30000):
    """Streamlitアプリが準備完了するまで待機"""
    try:
        # Streamlitのローディング完了を待つ
        page.wait_for_load_state("networkidle", timeout=timeout)
        
        # スピナーが消えるのを待つ
        spinner = page.locator('[data-testid="stSpinner"]')
        if spinner.count() > 0:
            spinner.wait_for(state="hidden", timeout=timeout)
        
        # デプロイダイアログを閉じる
        close_deploy_dialog(page)
        
        # 追加の安定化待機
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"⚠️ Streamlit準備待機中にエラー: {e}")
        return False

def handle_streamlit_errors(page: Page):
    """Streamlitのエラーダイアログを処理"""
    try:
        # エラーアラートを探す
        error_alert = page.locator('[data-testid="stAlert"][kind="error"]')
        if error_alert.is_visible():
            error_text = error_alert.inner_text()
            print(f"❌ Streamlitエラー検出: {error_text}")
            return error_text
            
        # 例外メッセージを探す
        exception_msg = page.locator('[data-testid="stException"]')
        if exception_msg.is_visible():
            error_text = exception_msg.inner_text()
            print(f"❌ Streamlit例外検出: {error_text}")
            return error_text
            
    except Exception as e:
        print(f"⚠️ エラーチェック中に問題: {e}")
    
    return None

def force_click_element(page: Page, selector: str, timeout: int = 5000):
    """要素を強制的にクリック（オーバーレイを回避）"""
    try:
        element = page.locator(selector)
        
        # 要素が存在することを確認
        element.wait_for(state="attached", timeout=timeout)
        
        # JavaScriptで直接クリック
        element.evaluate("el => el.click()")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 強制クリックに失敗: {e}")
        return False

def scroll_sidebar_to_element(page: Page, element_selector: str):
    """サイドバー内で要素が見えるようにスクロール"""
    try:
        sidebar = page.locator('[data-testid="stSidebar"]')
        element = page.locator(element_selector)
        
        if sidebar.is_visible() and element.count() > 0:
            # 要素をビューポートにスクロール
            element.scroll_into_view_if_needed()
            time.sleep(0.3)
            return True
            
    except Exception as e:
        print(f"⚠️ サイドバースクロールに失敗: {e}")
    
    return False