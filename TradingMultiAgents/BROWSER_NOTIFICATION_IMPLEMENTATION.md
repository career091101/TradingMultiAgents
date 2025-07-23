# ブラウザ通知実装ガイド（Streamlit対応）

## 1. 実装概要と影響分析

### 1.1 Streamlitアーキテクチャの制約
Streamlitの調査結果から、以下の制約が判明：

- **WebSocket依存**: StreamlitはWebSocketプロトコルで動作するため、Service Workerの直接統合は困難
- **シングルスレッド**: バックグラウンドタスクの実行に制限
- **ステートレス**: ページリロード時にすべてのスクリプトが再実行される

### 1.2 実装方針
これらの制約を考慮し、以下の方針で実装：

1. **streamlit-push-notifications**パッケージを使用（Streamlit専用に設計）
2. **Redis**を使用した非同期通知キューシステムの構築
3. **シンプルな通知API**でStreamlitの制約を回避

## 2. 実装手順

### 2.1 パッケージインストール

```bash
# requirements.txtに追加
streamlit-push-notifications>=0.1.0
redis>=4.5.0
celery>=5.3.0
```

### 2.2 通知サービスの実装

```python
# tradingagents/services/browser_notification.py
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import redis
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrowserNotification:
    """ブラウザ通知データクラス"""
    title: str
    body: str
    icon: str = ""
    tag: str = ""
    timestamp: float = None
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()
        if self.data is None:
            self.data = {}

class NotificationQueue:
    """Redis通知キュー管理"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.channel = "tradingagents:notifications"
        
    def push(self, user_id: str, notification: BrowserNotification):
        """通知をキューに追加"""
        key = f"notifications:{user_id}"
        self.redis_client.lpush(
            key, 
            json.dumps(asdict(notification))
        )
        # 通知は7日間保持
        self.redis_client.expire(key, 604800)
        
    def pop(self, user_id: str) -> Optional[BrowserNotification]:
        """通知をキューから取得"""
        key = f"notifications:{user_id}"
        data = self.redis_client.rpop(key)
        if data:
            notification_dict = json.loads(data)
            return BrowserNotification(**notification_dict)
        return None
    
    def get_all(self, user_id: str) -> list[BrowserNotification]:
        """全ての未送信通知を取得"""
        key = f"notifications:{user_id}"
        notifications = []
        
        # 全ての通知を取得（破壊的でない）
        all_data = self.redis_client.lrange(key, 0, -1)
        for data in all_data:
            notification_dict = json.loads(data)
            notifications.append(BrowserNotification(**notification_dict))
            
        # 取得後にクリア
        self.redis_client.delete(key)
        
        return notifications

class AnalysisNotificationService:
    """分析完了通知サービス"""
    
    def __init__(self):
        self.queue = NotificationQueue()
        
    def create_analysis_notification(
        self,
        ticker: str,
        analysis_date: str,
        recommendation: str,
        confidence: float,
        duration_minutes: int,
        analysis_id: str
    ) -> BrowserNotification:
        """分析完了通知を作成"""
        
        # 推奨アクションの日本語化
        recommendation_jp = {
            "BUY": "買い推奨",
            "SELL": "売り推奨", 
            "HOLD": "保有継続"
        }.get(recommendation, recommendation)
        
        title = f"📈 {ticker} 分析完了"
        body = f"{recommendation_jp} (信頼度: {confidence:.0%}) - 分析時間: {duration_minutes}分"
        
        return BrowserNotification(
            title=title,
            body=body,
            icon="/static/img/chart-icon.png",
            tag=f"analysis-{analysis_id}",
            data={
                "ticker": ticker,
                "date": analysis_date,
                "analysis_id": analysis_id,
                "url": f"/results/{ticker}/{analysis_date}"
            }
        )
    
    def send_analysis_complete(
        self,
        user_id: str,
        ticker: str,
        analysis_date: str,
        recommendation: str,
        confidence: float,
        duration_minutes: int,
        analysis_id: str
    ):
        """分析完了通知を送信"""
        notification = self.create_analysis_notification(
            ticker=ticker,
            analysis_date=analysis_date,
            recommendation=recommendation,
            confidence=confidence,
            duration_minutes=duration_minutes,
            analysis_id=analysis_id
        )
        
        self.queue.push(user_id, notification)
        logger.info(f"Notification queued for user {user_id}: {ticker}")
```

### 2.3 Streamlit統合

```python
# webui/components/notification_handler.py
import streamlit as st
from streamlit_push_notifications import send_push
from typing import Optional
import time
import json

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
            st.warning("通知サービスが利用できません")
            
    def check_and_send_notifications(self, user_id: str):
        """保留中の通知をチェックして送信"""
        if not self.notification_service:
            return
            
        # 通知権限の確認
        if not st.session_state.get("notifications_enabled", False):
            return
            
        # キューから通知を取得
        notifications = self.notification_service.queue.get_all(user_id)
        
        for notification in notifications:
            # Streamlit Push Notificationを使用
            send_push(
                title=notification.title,
                body=notification.body,
                icon_path=notification.icon,
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
            
    def enable_notifications(self):
        """通知を有効化"""
        st.session_state.notifications_enabled = True
        
        # 初回の通知許可リクエスト
        with st.container():
            st.info("ブラウザの通知を許可してください")
            
            # テスト通知を送信
            if st.button("テスト通知を送信", key="test_notification"):
                send_push(
                    title="🔔 通知テスト",
                    body="TradingAgentsからの通知が有効になりました",
                    icon_path="/static/img/logo.png"
                )
                st.success("テスト通知を送信しました")

# webui/components/settings.py に追加
def render_notification_settings():
    """通知設定画面"""
    st.subheader("🔔 ブラウザ通知設定")
    
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
                    st.write(f"**{notif['title']}**")
                    st.caption(f"{notif['body']}")
                    st.caption(f"送信時刻: {datetime.fromtimestamp(notif['timestamp']).strftime('%Y-%m-%d %H:%M')}")
                    st.divider()
```

### 2.4 分析完了時の通知送信

```python
# webui/backend/cli_wrapper.py に追加
def _send_completion_notification(self, config: AnalysisConfig, result: Dict[str, Any]):
    """分析完了通知を送信"""
    try:
        from tradingagents.services.browser_notification import (
            AnalysisNotificationService
        )
        
        # ユーザーIDの取得（セッションベース）
        user_id = st.session_state.get("user_id", "default")
        
        # 通知が有効な場合のみ送信
        if st.session_state.get("notifications_enabled", False):
            service = AnalysisNotificationService()
            
            # 分析結果から情報を抽出
            recommendation = result.get("recommendation", "N/A")
            confidence = result.get("confidence", 0.0)
            duration_minutes = result.get("duration_minutes", 0)
            
            service.send_analysis_complete(
                user_id=user_id,
                ticker=config.ticker,
                analysis_date=config.analysis_date,
                recommendation=recommendation,
                confidence=confidence,
                duration_minutes=duration_minutes,
                analysis_id=result.get("id", "")
            )
            
            logger.info(f"Notification sent for {config.ticker}")
            
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
```

### 2.5 アプリケーション起動時の通知チェック

```python
# webui/app.py に追加
def check_pending_notifications():
    """保留中の通知をチェック"""
    if "notification_handler" not in st.session_state:
        from webui.components.notification_handler import NotificationHandler
        st.session_state.notification_handler = NotificationHandler()
    
    # ユーザーIDの初期化
    if "user_id" not in st.session_state:
        import uuid
        st.session_state.user_id = str(uuid.uuid4())
    
    # 定期的に通知をチェック（5秒ごと）
    if time.time() - st.session_state.get("last_notification_check", 0) > 5:
        st.session_state.notification_handler.check_and_send_notifications(
            st.session_state.user_id
        )
        st.session_state.last_notification_check = time.time()

# メインアプリケーションループに追加
def run(self):
    """アプリケーション実行"""
    try:
        # 通知チェック
        check_pending_notifications()
        
        self.render_header()
        self.render_sidebar()
        self.render_main_content()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"アプリケーションエラー: {e}")
```

### 2.6 静的ファイルの配置

```bash
# 通知アイコン用ディレクトリ作成
mkdir -p webui/static/img/

# アイコンファイルを配置
# - logo.png (アプリケーションロゴ)
# - chart-icon.png (チャートアイコン)
# - notification-badge.png (通知バッジ)
```

## 3. 実装の注意点

### 3.1 Streamlitの制約への対応

1. **ステートレス問題**: `st.session_state`を使用して通知状態を保持
2. **リロード問題**: Redisキューを使用して通知を永続化
3. **WebSocket制約**: streamlit-push-notificationsパッケージがブラウザAPIを直接呼び出す

### 3.2 ユーザー体験の考慮

1. **初回許可フロー**: 明確な説明とテスト通知
2. **通知履歴**: 見逃した通知を確認可能
3. **無効化オプション**: いつでも通知を無効化可能

### 3.3 パフォーマンスの考慮

1. **非同期処理**: 通知送信で分析処理をブロックしない
2. **キューの活用**: Redisで通知を効率的に管理
3. **定期チェック**: 5秒間隔で新着通知を確認

## 4. テスト方法

```python
# tests/test_browser_notification.py
import pytest
from tradingagents.services.browser_notification import (
    BrowserNotification,
    NotificationQueue,
    AnalysisNotificationService
)

def test_notification_creation():
    """通知作成のテスト"""
    notification = BrowserNotification(
        title="テスト通知",
        body="これはテストです"
    )
    assert notification.title == "テスト通知"
    assert notification.timestamp is not None

def test_notification_queue():
    """通知キューのテスト"""
    queue = NotificationQueue()
    notification = BrowserNotification(
        title="テスト",
        body="テスト本文"
    )
    
    # プッシュとポップ
    queue.push("test-user", notification)
    retrieved = queue.pop("test-user")
    
    assert retrieved.title == notification.title
    assert retrieved.body == notification.body

@pytest.mark.asyncio
async def test_analysis_notification():
    """分析通知のテスト"""
    service = AnalysisNotificationService()
    
    notification = service.create_analysis_notification(
        ticker="AAPL",
        analysis_date="2025-01-17",
        recommendation="BUY",
        confidence=0.85,
        duration_minutes=12,
        analysis_id="test-123"
    )
    
    assert "AAPL" in notification.title
    assert "買い推奨" in notification.body
    assert "85%" in notification.body
```

## 5. デプロイメント考慮事項

### 5.1 Redis設定
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### 5.2 環境変数
```bash
# .env
REDIS_URL=redis://localhost:6379
NOTIFICATION_ENABLED=true
```

### 5.3 HTTPS要件
ブラウザ通知はHTTPS環境でのみ動作するため、本番環境では必ずSSL/TLS証明書を設定すること。

## 6. 今後の拡張案

1. **通知のカスタマイズ**: ユーザーごとの通知条件設定
2. **音声通知**: 重要な推奨時に音声アラート
3. **通知分析**: どの通知がクリックされたかの追跡
4. **プッシュ通知の永続化**: Service Worker実装（将来的に）

この実装により、Streamlitの制約内で効果的なブラウザ通知システムを構築できます。