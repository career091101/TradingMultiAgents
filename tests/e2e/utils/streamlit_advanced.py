"""
Streamlit高度対応ユーティリティ
デプロイダイアログ、セレクタ安定性、状態管理の総合対応
"""

from playwright.sync_api import Page
import time
import re
from typing import Dict, List, Optional, Tuple

class StreamlitManager:
    """Streamlitアプリケーション管理クラス"""
    
    def __init__(self, page: Page):
        self.page = page
        self.deploy_dialog_patterns = [
            'button[aria-label="Close"]',
            'button:has-text("×")',
            'button:has-text("✕")',
            '[data-testid="modal-close-button"]',
            '.stModal button[kind="secondary"]'
        ]
    
    def wait_for_app_ready(self, timeout: int = 30000) -> bool:
        """Streamlitアプリの完全な準備完了を待つ"""
        try:
            print("🔄 Streamlitアプリの準備を待機中...")
            
            # 1. 基本的なページロード完了
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            
            # 2. Streamlitの初期化完了待機
            self._wait_for_streamlit_init()
            
            # 3. デプロイダイアログの処理
            self._handle_deploy_dialog()
            
            # 4. スピナーの完了待機
            self._wait_for_spinners()
            
            # 5. エラーチェック
            errors = self._check_for_errors()
            if errors:
                print(f"⚠️ Streamlitエラー検出: {errors}")
            
            # 6. 最終安定化
            time.sleep(2)
            
            print("✅ Streamlitアプリの準備完了")
            return True
            
        except Exception as e:
            print(f"❌ Streamlitアプリ準備エラー: {e}")
            return False
    
    def _wait_for_streamlit_init(self):
        """Streamlitの初期化完了を待つ"""
        # Streamlitのメインコンテナが表示されるまで待機
        main_container = self.page.locator('.main, [data-testid="main"], .stApp')
        main_container.wait_for(state="visible", timeout=15000)
        
        # サイドバーの初期化待機
        sidebar = self.page.locator('[data-testid="stSidebar"]')
        if sidebar.count() > 0:
            sidebar.wait_for(state="visible", timeout=10000)
    
    def _handle_deploy_dialog(self) -> bool:
        """デプロイダイアログを包括的に処理"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                # 複数のパターンでダイアログをチェック
                dialog_found = False
                
                # パターン1: モーダルダイアログ
                modal = self.page.locator('[data-testid="stModal"], .stModal, [role="dialog"]')
                if modal.is_visible():
                    print(f"📱 モーダルダイアログ検出 (試行 {attempt + 1})")
                    self._close_modal_dialog(modal)
                    dialog_found = True
                
                # パターン2: デプロイメントバナー
                deploy_banner = self.page.locator('text="Deploy"').first
                if deploy_banner.is_visible():
                    print(f"🚀 デプロイバナー検出 (試行 {attempt + 1})")
                    self._close_deploy_banner()
                    dialog_found = True
                
                # パターン3: オーバーレイ要素
                overlay = self.page.locator('.stOverlay, [data-testid="stOverlay"]')
                if overlay.is_visible():
                    print(f"🎭 オーバーレイ検出 (試行 {attempt + 1})")
                    self._close_overlay(overlay)
                    dialog_found = True
                
                if not dialog_found:
                    break
                
                time.sleep(1)  # ダイアログクローズ後の安定化
                
            except Exception as e:
                print(f"⚠️ ダイアログ処理エラー (試行 {attempt + 1}): {e}")
                continue
        
        return True
    
    def _close_modal_dialog(self, modal):
        """モーダルダイアログを閉じる"""
        for pattern in self.deploy_dialog_patterns:
            try:
                close_btn = modal.locator(pattern).first
                if close_btn.is_visible():
                    close_btn.click()
                    print(f"✅ モーダル閉じるボタンクリック: {pattern}")
                    return True
            except:
                continue
        
        # ESCキーでの閉じる
        try:
            self.page.keyboard.press("Escape")
            print("✅ ESCキーでモーダル閉じる")
            return True
        except:
            pass
        
        # モーダル外クリック
        try:
            self.page.mouse.click(10, 10)
            print("✅ モーダル外クリックで閉じる")
            return True
        except:
            pass
        
        return False
    
    def _close_deploy_banner(self):
        """デプロイバナーを閉じる"""
        try:
            # "Deploy now"ボタンの近くの×ボタンを探す
            close_buttons = self.page.locator('button').all()
            for btn in close_buttons:
                text = btn.inner_text().strip()
                if text in ["×", "✕", "Close", "閉じる"]:
                    btn.click()
                    return True
        except:
            pass
        
        return False
    
    def _close_overlay(self, overlay):
        """オーバーレイを閉じる"""
        try:
            # オーバーレイ内のクローズボタンを探す
            close_btn = overlay.locator('button').first
            if close_btn.is_visible():
                close_btn.click()
                return True
        except:
            pass
        
        return False
    
    def _wait_for_spinners(self):
        """すべてのスピナーが消えるまで待機"""
        spinner_selectors = [
            '[data-testid="stSpinner"]',
            '.stSpinner',
            '[class*="spinner"]',
            '[class*="loading"]'
        ]
        
        for selector in spinner_selectors:
            try:
                spinners = self.page.locator(selector)
                if spinners.count() > 0:
                    spinners.first.wait_for(state="hidden", timeout=10000)
            except:
                continue
    
    def _check_for_errors(self) -> List[str]:
        """Streamlitエラーをチェック"""
        errors = []
        
        error_selectors = [
            '[data-testid="stAlert"][kind="error"]',
            '[data-testid="stException"]',
            '.stAlert--error',
            '.streamlit-error'
        ]
        
        for selector in error_selectors:
            try:
                error_elements = self.page.locator(selector).all()
                for element in error_elements:
                    if element.is_visible():
                        errors.append(element.inner_text())
            except:
                continue
        
        return errors
    
    def get_current_page_info(self) -> Dict[str, str]:
        """現在のページ情報を取得"""
        info = {
            "title": "",
            "active_tab": "",
            "main_content": "",
            "sidebar_active": ""
        }
        
        try:
            # ページタイトル
            title_element = self.page.locator('h1, [data-testid="stTitle"]').first
            if title_element.is_visible():
                info["title"] = title_element.inner_text()
            
            # アクティブなサイドバーボタン
            active_buttons = self.page.locator('[data-testid="stSidebar"] button[kind="primary"], [data-testid="stSidebar"] .stButton--primary').all()
            for btn in active_buttons:
                if btn.is_visible():
                    info["sidebar_active"] = btn.inner_text()
                    break
            
            # メインコンテンツの特徴（複数のセレクタを試行）
            main_selectors = [
                '.main',
                '[data-testid="main"]',
                '.stApp',
                '[data-testid="stVerticalBlock"]'
            ]
            
            for selector in main_selectors:
                try:
                    main_element = self.page.locator(selector).first
                    if main_element.count() > 0:
                        main_text = main_element.inner_text(timeout=5000)[:200]
                        info["main_content"] = main_text
                        break
                except:
                    continue
            
            # フォールバック: ページ全体のテキスト
            if not info["main_content"]:
                try:
                    body_text = self.page.locator('body').inner_text(timeout=5000)[:200]
                    info["main_content"] = body_text
                except:
                    info["main_content"] = "コンテンツ取得不可"
            
        except Exception as e:
            print(f"⚠️ ページ情報取得エラー: {e}")
        
        return info
    
    def safe_navigate_to_page(self, page_name: str) -> bool:
        """安全なページナビゲーション"""
        try:
            print(f"🧭 {page_name}ページへナビゲーション開始")
            
            # デプロイダイアログを再チェック
            self._handle_deploy_dialog()
            
            # 現在のページ情報を取得
            current_info = self.get_current_page_info()
            print(f"📍 現在のページ: {current_info}")
            
            # 既に目的のページにいるかチェック
            if self._is_already_on_page(page_name, current_info):
                print(f"✅ 既に{page_name}ページにいます")
                return True
            
            # サイドバーが開いているか確認
            if not self._ensure_sidebar_open():
                print("❌ サイドバーを開けませんでした")
                return False
            
            # ナビゲーションボタンをクリック
            success = self._click_navigation_button(page_name)
            
            if success:
                # ページ遷移の完了を待つ
                self.wait_for_app_ready(timeout=15000)
                print(f"✅ {page_name}ページへのナビゲーション完了")
                return True
            else:
                print(f"❌ {page_name}ページへのナビゲーション失敗")
                return False
                
        except Exception as e:
            print(f"❌ ナビゲーションエラー: {e}")
            return False
    
    def _is_already_on_page(self, page_name: str, current_info: Dict[str, str]) -> bool:
        """既に目的のページにいるかチェック"""
        page_indicators = {
            "dashboard": ["ダッシュボード", "Dashboard", "統計情報", "クイックアクション"],
            "settings": ["分析設定", "Settings", "基本設定", "アナリストチーム"],
            "execution": ["分析実行", "Execution", "実行設定確認", "LLM設定"],
            "results": ["結果表示", "Results", "結果選択", "分析サマリー"]
        }
        
        indicators = page_indicators.get(page_name.lower(), [page_name])
        content = f"{current_info['title']} {current_info['main_content']} {current_info['sidebar_active']}"
        
        return any(indicator in content for indicator in indicators)
    
    def _ensure_sidebar_open(self) -> bool:
        """サイドバーが開いていることを確認"""
        try:
            sidebar = self.page.locator('[data-testid="stSidebar"]')
            
            if sidebar.is_visible():
                return True
            
            # ハンバーガーメニューをクリック
            hamburger_selectors = [
                'button[kind="header"]',
                '[data-testid="stSidebarNav"] button',
                'button[aria-label="Show navigation"]'
            ]
            
            for selector in hamburger_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible():
                        btn.click()
                        time.sleep(1)
                        if sidebar.is_visible():
                            return True
                except:
                    continue
            
            return False
            
        except:
            return False
    
    def _click_navigation_button(self, page_name: str) -> bool:
        """ナビゲーションボタンをクリック"""
        button_texts = {
            "dashboard": ["ダッシュボード", "Dashboard"],
            "settings": ["分析設定", "Settings"],
            "execution": ["分析実行", "Execution"],
            "results": ["結果表示", "Results"]
        }
        
        texts = button_texts.get(page_name.lower(), [page_name])
        
        for text in texts:
            success = self._try_click_button_with_text(text)
            if success:
                return True
        
        return False
    
    def _try_click_button_with_text(self, text: str) -> bool:
        """テキストでボタンをクリック（複数手法）"""
        selectors = [
            f'[data-testid="stSidebar"] button:has-text("{text}")',
            f'button:has-text("{text}")',
            f'[role="button"]:has-text("{text}")',
            f'text="{text}"'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible():
                    # 通常のクリック
                    element.click()
                    return True
                elif element.count() > 0:
                    # 強制クリック
                    element.evaluate("el => el.click()")
                    return True
            except:
                continue
        
        return False


def create_streamlit_manager(page: Page) -> StreamlitManager:
    """StreamlitManagerのファクトリ関数"""
    return StreamlitManager(page)