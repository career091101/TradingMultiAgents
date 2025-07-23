"""
Streamlit通知ハンドラー
ブラウザ通知の管理と送信を行う
"""

import streamlit as st
from typing import Optional
import time
import json
from datetime import datetime
import logging

# streamlit-push-notificationsパッケージのインポート
try:
    from streamlit_push_notifications import send_push
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    logging.warning("streamlit-push-notifications package not available")

logger = logging.getLogger(__name__)

class NotificationHandler:
    """Streamlit通知ハンドラー"""
    
    def __init__(self):
        self.notification_service = None
        self._init_service()
        
    def _init_service(self):
        """通知サービスの初期化"""
        try:
            from tradingagents.services.browser_notification import (
                AnalysisNotificationService
            )
            self.notification_service = AnalysisNotificationService()
        except ImportError:
            logger.warning("通知サービスが利用できません")
            
    def check_and_send_notifications(self, user_id: str):
        """保留中の通知をチェックして送信"""
        if not self.notification_service:
            return
            
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        # 通知権限の確認
        if not st.session_state.get("notifications_enabled", False):
            return
            
        try:
            # キューから通知を取得
            notifications = self.notification_service.queue.get_all(user_id)
            
            for notification in notifications:
                # Streamlit Push Notificationを使用
                send_push(
                    title=notification.title,
                    body=notification.body,
                    icon_path=notification.icon if notification.icon else None,
                    tag=notification.tag
                )
                
                # 通知履歴に追加
                if "notification_history" not in st.session_state:
                    st.session_state.notification_history = []
                
                st.session_state.notification_history.append({
                    "timestamp": notification.timestamp,
                    "title": notification.title,
                    "body": notification.body,
                    "data": notification.data
                })
                
                logger.info(f"Notification sent: {notification.title}")
                
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
            
    def enable_notifications(self):
        """通知を有効化"""
        st.session_state.notifications_enabled = True
        
        if not NOTIFICATIONS_AVAILABLE:
            st.error("通知機能が利用できません。streamlit-push-notificationsパッケージをインストールしてください。")
            return
        
        # 初回の通知許可リクエスト
        with st.container():
            st.info("ブラウザの通知を許可してください")
            
            # テスト通知を送信
            if st.button("テスト通知を送信", key="test_notification"):
                try:
                    send_push(
                        title="🔔 通知テスト",
                        body="TradingAgentsからの通知が有効になりました"
                    )
                    st.success("テスト通知を送信しました")
                except Exception as e:
                    st.error(f"通知送信に失敗しました: {e}")

def render_notification_settings():
    """通知設定画面"""
    st.subheader("🔔 ブラウザ通知設定")
    
    if not NOTIFICATIONS_AVAILABLE:
        st.warning("""
        通知機能を使用するには、以下のパッケージをインストールしてください：
        ```bash
        pip install streamlit-push-notifications
        ```
        """)
        return
    
    # 通知ハンドラー
    notification_handler = NotificationHandler()
    
    # 通知の有効/無効
    notifications_enabled = st.toggle(
        "ブラウザ通知を有効にする",
        value=st.session_state.get("notifications_enabled", False),
        help="分析完了時にブラウザ通知を受け取ります"
    )
    
    if notifications_enabled and not st.session_state.get("notifications_enabled", False):
        notification_handler.enable_notifications()
    
    st.session_state.notifications_enabled = notifications_enabled
    
    if notifications_enabled:
        st.info("""
        📌 通知を受け取るには：
        1. ブラウザの通知を許可してください
        2. ブラウザがバックグラウンドで動作している必要があります
        3. サイレントモードがオフになっていることを確認してください
        """)
        
        # 通知履歴
        if st.session_state.get("notification_history"):
            with st.expander("📜 通知履歴", expanded=False):
                for notif in reversed(st.session_state.notification_history[-10:]):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{notif['title']}**")
                        st.caption(f"{notif['body']}")
                    
                    with col2:
                        timestamp = datetime.fromtimestamp(notif['timestamp'])
                        st.caption(timestamp.strftime('%H:%M'))
                    
                    # 結果を見るボタン
                    if notif['data'].get('url'):
                        if st.button("結果を見る", key=f"view_{notif['timestamp']}"):
                            st.session_state.selected_ticker = notif['data']['ticker']
                            st.session_state.selected_date = notif['data']['date']
                            st.session_state.current_page = "results"
                            st.rerun()
                    
                    st.divider()
                    
        # 通知テスト
        with st.expander("🧪 通知テスト", expanded=False):
            test_ticker = st.text_input("テストティッカー", value="AAPL")
            test_recommendation = st.selectbox(
                "テスト推奨",
                ["BUY", "SELL", "HOLD"]
            )
            test_confidence = st.slider("テスト信頼度", 0.0, 1.0, 0.85, 0.05)
            
            if st.button("テスト通知を作成", key="create_test_notification"):
                if notification_handler.notification_service:
                    # テスト通知を作成してキューに追加
                    import uuid
                    user_id = st.session_state.get("user_id", "default")
                    
                    notification_handler.notification_service.send_analysis_complete(
                        user_id=user_id,
                        ticker=test_ticker,
                        analysis_date=datetime.now().strftime("%Y-%m-%d"),
                        recommendation=test_recommendation,
                        confidence=test_confidence,
                        duration_minutes=5,
                        analysis_id=str(uuid.uuid4())
                    )
                    
                    st.success("テスト通知をキューに追加しました")
                    
                    # すぐに通知をチェック
                    notification_handler.check_and_send_notifications(user_id)