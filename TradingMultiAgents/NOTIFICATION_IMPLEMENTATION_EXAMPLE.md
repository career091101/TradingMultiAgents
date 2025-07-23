# 通知機能 実装例

## 1. Service Worker実装（ブラウザ通知）

### 1.1 Service Worker登録
```javascript
// webui/static/js/notification-setup.js
class NotificationManager {
    constructor() {
        this.swRegistration = null;
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Notifications not supported');
            return false;
        }

        try {
            // Service Worker登録
            this.swRegistration = await navigator.serviceWorker.register('/sw.js');
            console.log('Service Worker registered');

            // 通知権限の確認
            const permission = await this.requestPermission();
            return permission === 'granted';
        } catch (error) {
            console.error('Failed to register service worker:', error);
            return false;
        }
    }

    async requestPermission() {
        const permission = await Notification.requestPermission();
        return permission;
    }

    async subscribeToNotifications() {
        if (!this.swRegistration) {
            throw new Error('Service Worker not registered');
        }

        const subscription = await this.swRegistration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: this.urlBase64ToUint8Array(PUBLIC_VAPID_KEY)
        });

        // サーバーに登録
        await fetch('/api/notifications/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(subscription)
        });

        return subscription;
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    const notificationManager = new NotificationManager();
    const isEnabled = await notificationManager.init();
    
    if (isEnabled) {
        await notificationManager.subscribeToNotifications();
    }
});
```

### 1.2 Service Worker
```javascript
// webui/static/sw.js
self.addEventListener('push', event => {
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/static/img/icon-192.png',
        badge: '/static/img/badge-72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: data.analysis_id,
            url: data.result_url
        },
        actions: [
            {
                action: 'view',
                title: '結果を見る',
                icon: '/static/img/checkmark.png'
            },
            {
                action: 'close',
                title: '閉じる',
                icon: '/static/img/xmark.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', event => {
    const notification = event.notification;
    const action = event.action;
    
    if (action === 'close') {
        notification.close();
    } else {
        // 結果ページを開く
        event.waitUntil(
            clients.openWindow(notification.data.url)
        );
        notification.close();
    }
});
```

## 2. バックエンド実装

### 2.1 通知サービス
```python
# tradingagents/services/notification_service.py
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    EMAIL = "email"
    BROWSER_PUSH = "browser_push"
    SLACK = "slack"
    DISCORD = "discord"
    LINE = "line"

@dataclass
class NotificationConfig:
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any]

@dataclass
class AnalysisNotification:
    analysis_id: str
    ticker: str
    analysis_date: str
    status: str
    recommendation: Optional[str]
    confidence: Optional[float]
    key_points: List[str]
    result_url: str
    completion_time: datetime
    duration_minutes: int

class NotificationService:
    def __init__(self):
        self.providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """通知プロバイダーの初期化"""
        from .providers import (
            EmailProvider,
            BrowserPushProvider,
            SlackProvider,
            DiscordProvider,
            LINEProvider
        )
        
        self.providers = {
            NotificationChannel.EMAIL: EmailProvider(),
            NotificationChannel.BROWSER_PUSH: BrowserPushProvider(),
            NotificationChannel.SLACK: SlackProvider(),
            NotificationChannel.DISCORD: DiscordProvider(),
            NotificationChannel.LINE: LINEProvider(),
        }
    
    async def send_analysis_complete(
        self,
        user_id: str,
        notification: AnalysisNotification,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """分析完了通知を送信"""
        # ユーザー設定を取得
        user_settings = await self.get_user_settings(user_id)
        
        if not user_settings.enabled:
            logger.info(f"Notifications disabled for user {user_id}")
            return
        
        # 送信チャネルを決定
        active_channels = channels or self._get_active_channels(user_settings)
        
        # 並列で通知送信
        tasks = []
        for channel in active_channels:
            if channel in self.providers:
                task = self._send_to_channel(
                    user_id,
                    channel,
                    notification,
                    user_settings.channels.get(channel)
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果をログ
        for channel, result in zip(active_channels, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send {channel} notification: {result}")
            else:
                logger.info(f"Successfully sent {channel} notification")
    
    async def _send_to_channel(
        self,
        user_id: str,
        channel: NotificationChannel,
        notification: AnalysisNotification,
        channel_config: Optional[NotificationConfig]
    ):
        """特定チャネルに通知を送信"""
        provider = self.providers[channel]
        
        try:
            # 通知内容を生成
            content = self._generate_content(notification, channel)
            
            # プロバイダー経由で送信
            await provider.send(user_id, content, channel_config)
            
            # 履歴を記録
            await self._record_notification(
                user_id=user_id,
                channel=channel,
                notification=notification,
                status="sent"
            )
            
        except Exception as e:
            logger.error(f"Error sending {channel} notification: {e}")
            await self._record_notification(
                user_id=user_id,
                channel=channel,
                notification=notification,
                status="failed",
                error=str(e)
            )
            raise
    
    def _generate_content(
        self,
        notification: AnalysisNotification,
        channel: NotificationChannel
    ) -> Dict[str, Any]:
        """チャネル別の通知内容を生成"""
        base_content = {
            "title": f"📈 {notification.ticker} 分析完了",
            "body": f"推奨: {notification.recommendation or 'N/A'} (信頼度: {notification.confidence or 0:.0%})",
            "analysis_id": notification.analysis_id,
            "result_url": notification.result_url,
        }
        
        if channel == NotificationChannel.EMAIL:
            return {
                **base_content,
                "subject": base_content["title"],
                "html_body": self._generate_email_html(notification),
                "text_body": self._generate_email_text(notification),
            }
        
        elif channel == NotificationChannel.SLACK:
            return {
                **base_content,
                "blocks": self._generate_slack_blocks(notification),
            }
        
        elif channel == NotificationChannel.DISCORD:
            return {
                **base_content,
                "embeds": [self._generate_discord_embed(notification)],
            }
        
        return base_content
    
    def _generate_email_html(self, notification: AnalysisNotification) -> str:
        """HTMLメール本文を生成"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">📈 {notification.ticker} 分析が完了しました</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">分析結果サマリー</h3>
                    <p><strong>推奨:</strong> <span style="font-size: 1.2em; color: {'#28a745' if notification.recommendation == 'BUY' else '#dc3545'};">{notification.recommendation or 'N/A'}</span></p>
                    <p><strong>信頼度:</strong> {notification.confidence or 0:.0%}</p>
                    <p><strong>分析時間:</strong> {notification.duration_minutes}分</p>
                </div>
                
                <h3>主要ポイント</h3>
                <ul>
                    {''.join(f'<li>{point}</li>' for point in notification.key_points)}
                </ul>
                
                <div style="margin: 30px 0;">
                    <a href="{notification.result_url}" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                        詳細な結果を見る
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="color: #6c757d; font-size: 0.9em;">
                    このメールは TradingAgents から自動送信されました。<br>
                    通知設定は<a href="{notification.result_url.replace('/results/', '/settings/notifications/')}">こちら</a>から変更できます。
                </p>
            </div>
        </body>
        </html>
        """
    
    def _generate_slack_blocks(self, notification: AnalysisNotification) -> List[Dict]:
        """Slackブロック形式のメッセージを生成"""
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📈 {notification.ticker} 分析完了"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*推奨:*\n{notification.recommendation or 'N/A'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*信頼度:*\n{notification.confidence or 0:.0%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*分析日:*\n{notification.analysis_date}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*所要時間:*\n{notification.duration_minutes}分"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*主要ポイント:*\n" + "\n".join(f"• {point}" for point in notification.key_points)
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "詳細を見る"
                        },
                        "url": notification.result_url,
                        "style": "primary"
                    }
                ]
            }
        ]
```

### 2.2 Celeryタスク
```python
# tradingagents/tasks/notification_tasks.py
from celery import shared_task
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_analysis_notification(self, user_id: str, analysis_data: Dict[str, Any]):
    """非同期で分析完了通知を送信"""
    try:
        from tradingagents.services.notification_service import (
            NotificationService,
            AnalysisNotification
        )
        
        # 通知データを構築
        notification = AnalysisNotification(
            analysis_id=analysis_data['id'],
            ticker=analysis_data['ticker'],
            analysis_date=analysis_data['date'],
            status=analysis_data['status'],
            recommendation=analysis_data.get('recommendation'),
            confidence=analysis_data.get('confidence'),
            key_points=analysis_data.get('key_points', []),
            result_url=f"/results/{analysis_data['ticker']}/{analysis_data['date']}",
            completion_time=datetime.now(),
            duration_minutes=analysis_data.get('duration_minutes', 0)
        )
        
        # 通知サービスで送信
        service = NotificationService()
        asyncio.run(service.send_analysis_complete(user_id, notification))
        
        logger.info(f"Notification sent for analysis {analysis_data['id']}")
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        # リトライ
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
```

### 2.3 WebUI統合
```python
# webui/components/settings.py に追加
class NotificationSettings:
    """通知設定コンポーネント"""
    
    def render(self):
        st.subheader("📢 通知設定")
        
        # グローバル設定
        notifications_enabled = st.toggle(
            "通知を有効にする",
            value=SessionState.get("notifications_enabled", False),
            help="分析完了時に通知を受け取ります"
        )
        
        if notifications_enabled:
            # ブラウザ通知
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("### 🌐 ブラウザ通知")
                browser_enabled = st.checkbox(
                    "ブラウザ通知を有効にする",
                    value=SessionState.get("browser_notifications", False)
                )
            
            with col2:
                if browser_enabled:
                    if st.button("権限を要求", key="request_notification_permission"):
                        st.components.v1.html("""
                        <script>
                        Notification.requestPermission().then(function(permission) {
                            window.parent.postMessage({
                                type: 'notification_permission',
                                permission: permission
                            }, '*');
                        });
                        </script>
                        """, height=0)
            
            # メール通知
            st.markdown("### 📧 メール通知")
            email_enabled = st.checkbox(
                "メール通知を有効にする",
                value=SessionState.get("email_notifications", False)
            )
            
            if email_enabled:
                email = st.text_input(
                    "メールアドレス",
                    value=SessionState.get("notification_email", ""),
                    placeholder="user@example.com"
                )
                
                notification_level = st.select_slider(
                    "通知レベル",
                    options=["最小限", "標準", "詳細"],
                    value=SessionState.get("notification_level", "標準")
                )
            
            # Slack通知
            with st.expander("💬 Slack通知", expanded=False):
                slack_enabled = st.checkbox(
                    "Slack通知を有効にする",
                    value=SessionState.get("slack_notifications", False)
                )
                
                if slack_enabled:
                    webhook_url = st.text_input(
                        "Webhook URL",
                        value=SessionState.get("slack_webhook", ""),
                        type="password",
                        help="https://hooks.slack.com/services/..."
                    )
                    
                    channel = st.text_input(
                        "チャンネル（オプション）",
                        value=SessionState.get("slack_channel", ""),
                        placeholder="#trading-alerts"
                    )
            
            # 通知条件
            st.markdown("### 🎯 通知条件")
            
            notify_all = st.checkbox(
                "すべての分析で通知",
                value=SessionState.get("notify_all_analyses", True)
            )
            
            if not notify_all:
                col1, col2 = st.columns(2)
                
                with col1:
                    notify_buy = st.checkbox("BUY推奨時のみ", value=False)
                    notify_sell = st.checkbox("SELL推奨時のみ", value=False)
                
                with col2:
                    notify_high_confidence = st.checkbox(
                        "高信頼度（80%以上）のみ",
                        value=False
                    )
                
                # 特定ティッカー
                specific_tickers = st.multiselect(
                    "特定のティッカーのみ",
                    options=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY", "QQQ"],
                    default=[]
                )
            
            # 保存ボタン
            if st.button("通知設定を保存", type="primary", use_container_width=True):
                self._save_notification_settings()
                st.success("通知設定を保存しました")
    
    def _save_notification_settings(self):
        """通知設定を保存"""
        settings = {
            "enabled": SessionState.get("notifications_enabled"),
            "channels": {
                "browser_push": {
                    "enabled": SessionState.get("browser_notifications"),
                },
                "email": {
                    "enabled": SessionState.get("email_notifications"),
                    "address": SessionState.get("notification_email"),
                    "level": SessionState.get("notification_level"),
                },
                "slack": {
                    "enabled": SessionState.get("slack_notifications"),
                    "webhook_url": SessionState.get("slack_webhook"),
                    "channel": SessionState.get("slack_channel"),
                }
            },
            "conditions": {
                "notify_all": SessionState.get("notify_all_analyses"),
                "filters": {
                    "recommendations": [],
                    "min_confidence": None,
                    "tickers": []
                }
            }
        }
        
        # APIに保存
        self.cli_wrapper.save_notification_settings(settings)
```

## 3. 通知プロバイダー実装例

### 3.1 メールプロバイダー
```python
# tradingagents/services/providers/email_provider.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailProvider:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@tradingagents.com")
    
    async def send(self, user_id: str, content: Dict[str, Any], config: Dict[str, Any]):
        """メール送信"""
        # ユーザーのメールアドレスを取得
        to_email = config.get("address")
        if not to_email:
            raise ValueError("Email address not configured")
        
        # メッセージ作成
        msg = MIMEMultipart('alternative')
        msg['Subject'] = content['subject']
        msg['From'] = self.from_email
        msg['To'] = to_email
        
        # テキストとHTML部分
        text_part = MIMEText(content['text_body'], 'plain')
        html_part = MIMEText(content['html_body'], 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # 送信
        async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as smtp:
            await smtp.starttls()
            await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(msg)
```

### 3.2 ブラウザプッシュプロバイダー
```python
# tradingagents/services/providers/browser_push_provider.py
from pywebpush import webpush, WebPushException
import json

class BrowserPushProvider:
    def __init__(self):
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
        self.vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@tradingagents.com")
    
    async def send(self, user_id: str, content: Dict[str, Any], config: Dict[str, Any]):
        """ブラウザプッシュ通知送信"""
        # ユーザーのサブスクリプションを取得
        subscription = await self._get_user_subscription(user_id)
        
        if not subscription:
            raise ValueError("No push subscription found")
        
        try:
            webpush(
                subscription_info=subscription,
                data=json.dumps(content),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": self.vapid_email,
                    "exp": int(time.time()) + 3600
                }
            )
        except WebPushException as e:
            logger.error(f"Web push failed: {e}")
            # 無効なサブスクリプションの場合は削除
            if e.response and e.response.status_code == 410:
                await self._remove_user_subscription(user_id)
            raise
```

## 4. データベーススキーマ

```sql
-- 通知設定テーブル
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- プッシュ通知サブスクリプション
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, endpoint)
);

-- 通知履歴
CREATE TABLE notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    analysis_id VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_notification_history_user_id ON notification_history(user_id);
CREATE INDEX idx_notification_history_analysis_id ON notification_history(analysis_id);
CREATE INDEX idx_notification_history_created_at ON notification_history(created_at);
```

## 5. テスト実装

```python
# tests/test_notification_service.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

@pytest.mark.asyncio
async def test_send_analysis_notification():
    """分析完了通知のテスト"""
    # モックの設定
    mock_email_provider = AsyncMock()
    mock_push_provider = AsyncMock()
    
    service = NotificationService()
    service.providers[NotificationChannel.EMAIL] = mock_email_provider
    service.providers[NotificationChannel.BROWSER_PUSH] = mock_push_provider
    
    # テストデータ
    notification = AnalysisNotification(
        analysis_id="test-123",
        ticker="AAPL",
        analysis_date="2025-01-17",
        status="completed",
        recommendation="BUY",
        confidence=0.85,
        key_points=["Strong fundamentals", "Positive momentum"],
        result_url="/results/AAPL/2025-01-17",
        completion_time=datetime.now(),
        duration_minutes=12
    )
    
    # 実行
    await service.send_analysis_complete("user-123", notification)
    
    # 検証
    assert mock_email_provider.send.called
    assert mock_push_provider.send.called
```

この実装例では、ブラウザ通知、メール通知、Slack/Discord通知など、複数の通知チャネルをサポートする包括的な通知システムを提供しています。Service Workerを使用したオフライン対応や、Celeryを使用した非同期処理など、実運用に必要な機能を含んでいます。