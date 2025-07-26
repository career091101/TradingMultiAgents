"""Type definitions for backtest system"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class TradeAction(Enum):
    """Trading actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    
    @classmethod
    def from_string(cls, value: str) -> 'TradeAction':
        """Create TradeAction from string, handling various formats"""
        if not value:
            return cls.HOLD
            
        # Clean the value
        value = str(value).upper().strip()
        
        # Handle direct matches
        if value in cls._value2member_map_:
            return cls._value2member_map_[value]
            
        # Handle descriptions like "string (BUY/SELL/HOLD)"
        if "BUY" in value:
            return cls.BUY
        elif "SELL" in value:
            return cls.SELL
        else:
            return cls.HOLD


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class PositionStatus(Enum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


@dataclass
class MarketData:
    """Market data container"""
    date: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    adjusted_close: Optional[float] = None
    
    # Additional data
    news: Optional[List[Dict[str, Any]]] = None
    fundamentals: Optional[Dict[str, Any]] = None
    technicals: Optional[Dict[str, float]] = None
    sentiment: Optional[Dict[str, float]] = None

    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'date': self.date.isoformat() if hasattr(self.date, 'isoformat') else str(self.date),
            'symbol': self.symbol,
            'open': float(self.open),
            'high': float(self.high),
            'low': float(self.low),
            'close': float(self.close),
            'volume': int(self.volume),
            'adjusted_close': float(self.adjusted_close) if self.adjusted_close else None,
            'news': self.news,
            'fundamentals': self.fundamentals,
            'technicals': self.technicals,
            'sentiment': self.sentiment
        }


@dataclass
class TradingSignal:
    """Trading signal from agents"""
    action: TradeAction
    symbol: str
    confidence: float
    size_recommendation: Optional[float] = None
    rationale: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None


@dataclass
class Position:
    """Position information"""
    symbol: str
    entry_date: datetime
    entry_price: float
    quantity: float
    position_type: str = "long"  # or "short"
    status: PositionStatus = PositionStatus.OPEN
    
    # Exit information
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    
    # P&L
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Metadata
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None
    agent_decisions: Optional[Dict[str, Any]] = None


@dataclass
class Transaction:
    """Transaction record"""
    timestamp: datetime
    symbol: str
    action: TradeAction
    quantity: float
    price: float
    commission: float
    slippage: float
    total_cost: float
    
    # Context
    signal: Optional[TradingSignal] = None
    position_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class PortfolioState:
    """Portfolio state at a point in time"""
    timestamp: datetime
    cash: float
    positions: Dict[str, Position]
    total_value: float
    
    # Performance metrics
    unrealized_pnl: float
    realized_pnl: float
    total_return: float
    
    # Risk metrics
    exposure: float
    position_count: int
    largest_position: Optional[str] = None


@dataclass
class TradingDecision:
    """Final trading decision"""
    id: str
    timestamp: datetime
    action: TradeAction
    symbol: str
    quantity: float
    order_type: OrderType = OrderType.MARKET
    
    # Price information
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    
    # Decision context
    confidence: float = 0.0
    rationale: str = ""
    agent_outputs: Dict[str, Any] = None
    risk_assessment: Dict[str, Any] = None
    
    # Risk management
    position_size_pct: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class AgentOutput:
    """Output from an individual agent"""
    agent_name: str
    timestamp: datetime
    output_type: str
    content: Any
    confidence: float
    processing_time: float
    rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'output_type': self.output_type,
            'content': self.content,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'rationale': self.rationale,
            'metadata': self.metadata
        }
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'output_type': self.output_type,
            'content': self.content,
            'confidence': float(self.confidence),
            'processing_time': float(self.processing_time),
            'rationale': self.rationale,
            'metadata': self.metadata
        }



@dataclass
class DecisionContext:
    """Context for decision making"""
    timestamp: datetime
    market_state: Dict[str, Any]
    portfolio_state: PortfolioState
    recent_performance: Dict[str, float]
    risk_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'market_state': self.market_state,
            'portfolio_state': {
                'timestamp': self.portfolio_state.timestamp.isoformat() if self.portfolio_state else None,
                'cash': self.portfolio_state.cash if self.portfolio_state else 0,
                'total_value': self.portfolio_state.total_value if self.portfolio_state else 0,
                'position_count': self.portfolio_state.position_count if self.portfolio_state else 0,
                'positions': len(self.portfolio_state.positions) if self.portfolio_state else 0
            } if self.portfolio_state else None,
            'recent_performance': self.recent_performance,
            'risk_metrics': self.risk_metrics
        }
    
    
@dataclass
class TradingOutcome:
    """Outcome of a trading decision"""
    decision_id: str
    position: Position
    pnl: float
    holding_period: int
    return_pct: float
    max_drawdown: float
    success: bool
    
    
@dataclass
class ReflectionTask:
    """Reflection task definition"""
    level: 'ReflectionLevel'
    scope: str
    priority: int = 0
    reason: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    scheduled_time: Optional[datetime] = None