"""
モバイルレスポンシブ対応のユーティリティ
"""

import streamlit as st
from pathlib import Path

def inject_mobile_css():
    """モバイル対応CSSを注入"""
    css_file = Path(__file__).parent.parent / "styles" / "mobile_responsive.css"
    
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
        
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        # CSSファイルが存在しない場合はインラインで基本的なスタイルを適用
        st.markdown("""
        <style>
        @media (max-width: 768px) {
            /* 基本的なモバイル対応 */
            .main .block-container {
                padding: 1rem !important;
            }
            
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 0 100% !important;
            }
            
            .stButton > button {
                width: 100%;
                margin: 0.25rem 0;
            }
            
            /* タッチターゲットサイズ */
            button, input, select {
                min-height: 44px;
            }
        }
        </style>
        """, unsafe_allow_html=True)

def add_mobile_meta_tags():
    """モバイル用のメタタグを追加"""
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    """, unsafe_allow_html=True)

def create_mobile_sidebar_toggle():
    """モバイル用サイドバートグルボタンを作成"""
    st.markdown("""
    <script>
    // サイドバーの自動折りたたみ
    function checkMobileView() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const width = window.innerWidth;
        
        if (width <= 768 && sidebar) {
            // モバイルビューでサイドバーを自動的に閉じる
            if (!sidebar.hasAttribute('data-mobile-handled')) {
                sidebar.setAttribute('data-mobile-handled', 'true');
                // Streamlitのサイドバー制御を使用
                const closeButton = sidebar.querySelector('[aria-label="Close sidebar"]');
                if (closeButton) {
                    closeButton.click();
                }
            }
        }
    }
    
    // 初期チェック
    setTimeout(checkMobileView, 1000);
    
    // ウィンドウリサイズ時のチェック
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(checkMobileView, 250);
    });
    </script>
    """, unsafe_allow_html=True)

def mobile_columns(*args, **kwargs):
    """モバイル対応のカラムレイアウト"""
    # デバイスの幅を推定（JavaScriptを使用できないため、セッション状態を使用）
    if 'is_mobile' not in st.session_state:
        st.session_state.is_mobile = False
    
    if st.session_state.is_mobile:
        # モバイルの場合は縦に並べる
        containers = []
        for _ in args:
            containers.append(st.container())
        return containers
    else:
        # デスクトップの場合は通常のカラムレイアウト
        return st.columns(*args, **kwargs)

def responsive_dataframe(df, **kwargs):
    """レスポンシブなデータフレーム表示"""
    # モバイル用の設定を追加
    mobile_kwargs = {
        'use_container_width': True,
        'hide_index': True,
    }
    
    # ユーザー指定の設定とマージ
    display_kwargs = {**mobile_kwargs, **kwargs}
    
    # データフレームを表示
    return st.dataframe(df, **display_kwargs)

def responsive_metric(label, value, delta=None, delta_color="normal", **kwargs):
    """レスポンシブなメトリック表示"""
    # メトリックをコンテナでラップ
    with st.container():
        st.metric(label, value, delta, delta_color, **kwargs)

def apply_mobile_optimizations():
    """すべてのモバイル最適化を適用"""
    inject_mobile_css()
    add_mobile_meta_tags()
    create_mobile_sidebar_toggle()

# Streamlitのページ設定にモバイル対応を追加する関数
def mobile_page_config(**kwargs):
    """モバイル対応のページ設定"""
    default_config = {
        'layout': 'wide',
        'initial_sidebar_state': 'auto',  # モバイルでは自動的に閉じる
    }
    
    # ユーザー指定の設定とマージ
    config = {**default_config, **kwargs}
    
    # ページ設定を適用
    st.set_page_config(**config)
    
    # モバイル最適化を適用
    apply_mobile_optimizations()