"""
ブラウザ通知サービス
Streamlit WebUIでの分析完了通知を管理
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import redis
from dataclasses import dataclass, asdict
import logging
import os

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
    
    def __init__(self, redis_url: str = None):
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()  # 接続確認
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Notifications will be disabled.")
            self.redis_client = None
            self.enabled = False
        
        self.channel = "tradingagents:notifications"
        
    def push(self, user_id: str, notification: BrowserNotification):
        """通知をキューに追加"""
        if not self.enabled:
            return
            
        try:
            key = f"notifications:{user_id}"
            self.redis_client.lpush(
                key, 
                json.dumps(asdict(notification))
            )
            # 通知は7日間保持
            self.redis_client.expire(key, 604800)
        except Exception as e:
            logger.error(f"Failed to push notification: {e}")
        
    def pop(self, user_id: str) -> Optional[BrowserNotification]:
        """通知をキューから取得"""
        if not self.enabled:
            return None
            
        try:
            key = f"notifications:{user_id}"
            data = self.redis_client.rpop(key)
            if data:
                notification_dict = json.loads(data)
                return BrowserNotification(**notification_dict)
        except Exception as e:
            logger.error(f"Failed to pop notification: {e}")
        return None
    
    def get_all(self, user_id: str) -> List[BrowserNotification]:
        """全ての未送信通知を取得"""
        notifications = []
        
        if not self.enabled:
            return notifications
            
        try:
            key = f"notifications:{user_id}"
            
            # 全ての通知を取得（破壊的でない）
            all_data = self.redis_client.lrange(key, 0, -1)
            for data in all_data:
                notification_dict = json.loads(data)
                notifications.append(BrowserNotification(**notification_dict))
                
            # 取得後にクリア
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to get all notifications: {e}")
            
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
        }.get(recommendation.upper(), recommendation)
        
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
        if not self.queue.enabled:
            logger.info("Notifications are disabled (Redis not available)")
            return
            
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