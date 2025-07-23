"""
TradingDecision作成のヘルパー関数
テスト用の簡略化されたTradingDecision作成
"""

from datetime import datetime
import uuid
from backtest2.core.types import TradingDecision, TradeAction


def create_trading_decision(
    symbol: str,
    action: TradeAction,
    confidence: float = 0.5,
    quantity: float = 100,
    rationale: str = "Test decision"
) -> TradingDecision:
    """テスト用のTradingDecisionを作成"""
    return TradingDecision(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        symbol=symbol,
        action=action,
        confidence=confidence,
        quantity=quantity,
        rationale=rationale
    )