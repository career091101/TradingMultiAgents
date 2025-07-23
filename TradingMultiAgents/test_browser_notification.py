#!/usr/bin/env python3
"""
ブラウザ通知機能のテストスクリプト
"""

import sys
from pathlib import Path
import logging

# プロジェクトルートを追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.services.browser_notification import (
    BrowserNotification,
    NotificationQueue,
    AnalysisNotificationService
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_notification_creation():
    """通知作成のテスト"""
    print("=== 通知作成テスト ===")
    
    notification = BrowserNotification(
        title="テスト通知",
        body="これはテスト通知です",
        icon="/static/img/icon.png"
    )
    
    print(f"Title: {notification.title}")
    print(f"Body: {notification.body}")
    print(f"Icon: {notification.icon}")
    print(f"Timestamp: {notification.timestamp}")
    print()

def test_notification_queue():
    """通知キューのテスト（Redis不要）"""
    print("=== 通知キューテスト ===")
    
    queue = NotificationQueue()
    
    if not queue.enabled:
        print("警告: Redisが利用できないため、通知キューは無効です")
        return
    
    # テスト通知を作成
    notification = BrowserNotification(
        title="キューテスト",
        body="キューに追加されるテスト通知"
    )
    
    # キューに追加
    user_id = "test-user"
    queue.push(user_id, notification)
    print(f"通知をキューに追加しました (user_id: {user_id})")
    
    # キューから取得
    retrieved = queue.pop(user_id)
    if retrieved:
        print(f"キューから取得: {retrieved.title}")
    else:
        print("キューから通知を取得できませんでした")
    print()

def test_analysis_notification():
    """分析通知のテスト"""
    print("=== 分析通知テスト ===")
    
    service = AnalysisNotificationService()
    
    # テスト通知を作成
    notification = service.create_analysis_notification(
        ticker="AAPL",
        analysis_date="2025-01-17",
        recommendation="BUY",
        confidence=0.85,
        duration_minutes=12,
        analysis_id="test-123"
    )
    
    print(f"Title: {notification.title}")
    print(f"Body: {notification.body}")
    print(f"Tag: {notification.tag}")
    print(f"Data: {notification.data}")
    
    # 実際に送信（Redisが利用可能な場合）
    if service.queue.enabled:
        service.send_analysis_complete(
            user_id="test-user",
            ticker="AAPL",
            analysis_date="2025-01-17",
            recommendation="BUY",
            confidence=0.85,
            duration_minutes=12,
            analysis_id="test-123"
        )
        print("\n通知をキューに送信しました")
    else:
        print("\nRedisが利用できないため、通知は送信されませんでした")

def main():
    """メイン関数"""
    print("TradingAgents ブラウザ通知テスト\n")
    
    test_notification_creation()
    test_notification_queue()
    test_analysis_notification()
    
    print("\nテスト完了")

if __name__ == "__main__":
    main()