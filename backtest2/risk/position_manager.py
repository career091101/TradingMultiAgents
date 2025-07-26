"""Position management and risk control"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import uuid
import asyncio

from ..core.config import RiskConfig, RiskProfile
from ..core.types import (
    Position, PositionStatus, Transaction, TradeAction,
    PortfolioState, TradingSignal
)
from ..utils.memory_manager import CircularBuffer
from ..utils.transaction_manager import AtomicTransactionManager, TransactionContext
from .risk_analyzer import RiskAnalyzer, EnhancedRiskMetrics
from ..config.constants import POSITION_MANAGEMENT, RISK_ANALYSIS


class PositionManager:
    """Manages positions and portfolio risk"""
    
    def __init__(self, initial_capital: float, risk_config: RiskConfig):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.risk_config = risk_config
        self.positions: Dict[str, Position] = {}
        # Use circular buffers to prevent memory leaks
        self.closed_positions = CircularBuffer(max_size=10000)  # Keep last 10k closed positions
        self.transaction_history = CircularBuffer(max_size=50000)  # Keep last 50k transactions
        self.portfolio_history = CircularBuffer(max_size=10000)  # Keep last 10k states
        self.logger = logging.getLogger(__name__)
        
        # Initialize transaction manager for atomic operations
        self.transaction_manager = AtomicTransactionManager()
        
        # Initialize risk analyzer
        self.risk_analyzer = RiskAnalyzer()
        
        # Lock for thread-safe operations
        self.position_lock = asyncio.Lock()
        self.cash_lock = asyncio.Lock()
        
        # Cache for market data (for risk analysis)
        self.market_data_cache: Dict[str, Any] = {}
        
    def calculate_position_size(
        self,
        signal: TradingSignal,
        confidence: float,
        current_price: Optional[float] = None
    ) -> float:
        """Calculate position size based on risk parameters
        
        Args:
            signal: Trading signal with recommendations
            confidence: Confidence score (0-1)
            current_price: Current price of the asset
            
        Returns:
            Position size in dollars
        """
        # Determine risk profile based on signal
        risk_profile = self._determine_risk_profile(signal, confidence)
        
        if hasattr(self, 'logger'):
            self.logger.debug(f"Risk profile: {risk_profile}, Confidence: {confidence:.2f}")
        
        # Get maximum allocation for risk profile
        max_allocation = self.risk_config.position_limits.get(
            risk_profile,
            self.risk_config.position_limits[RiskProfile.NEUTRAL]
        )
        
        # Adjust for confidence
        if confidence >= self.risk_config.confidence_thresholds['high']:
            size_multiplier = 1.0
        elif confidence >= self.risk_config.confidence_thresholds['medium']:
            size_multiplier = 0.7
        else:
            size_multiplier = 0.4
        
        if hasattr(self, 'logger'):
            self.logger.debug(f"Max allocation: {max_allocation:.2%}, Size multiplier: {size_multiplier}")
            
        # Calculate available capital
        available_capital = self._calculate_available_capital()
        
        if hasattr(self, 'logger'):
            self.logger.debug(f"Available capital: ${available_capital:.2f}, Cash: ${self.cash:.2f}")
        
        # Base position size
        base_size = available_capital * max_allocation * size_multiplier
        
        if hasattr(self, 'logger'):
            self.logger.debug(f"Base position size: ${base_size:.2f}")
        
        # Apply constraints
        position_size = self._apply_constraints(base_size, signal)
        
        if hasattr(self, 'logger'):
            self.logger.debug(f"Position size after constraints: ${position_size:.2f}")
        
        # Ensure minimum trade size
        if position_size < self.risk_config.min_trade_size:
            if hasattr(self, 'logger'):
                self.logger.debug(f"Position size ${position_size:.2f} below minimum ${self.risk_config.min_trade_size}, returning 0")
            return 0.0
            
        return position_size
        
    async def execute_transaction(self, transaction: Transaction) -> bool:
        """Execute a transaction atomically
        
        Args:
            transaction: Transaction to execute
            
        Returns:
            Success status
        """
        symbol = transaction.symbol
        transaction_id = str(uuid.uuid4())
        
        # Capture before state
        before_state = {
            "cash": self.cash,
            "positions": {k: {"quantity": v.quantity, "entry_price": v.entry_price} 
                         for k, v in self.positions.items()}
        }
        
        # Define atomic execution function
        async def _execute(context: TransactionContext):
            if transaction.action == TradeAction.BUY:
                return await self._execute_buy(transaction, context)
            elif transaction.action == TradeAction.SELL:
                return await self._execute_sell(transaction, context)
            else:
                raise ValueError(f"Unknown transaction action: {transaction.action}")
        
        try:
            # Execute with transaction manager
            result = await self.transaction_manager.execute_transaction(
                transaction_id=transaction_id,
                operation=f"{transaction.action.value} {symbol}",
                execute_fn=_execute,
                resources=["cash", "positions"],
                before_state=before_state
            )
            
            # Record transaction on success
            self.transaction_history.append(transaction)
            self.logger.info(
                f"Executed {transaction.action.value} {transaction.quantity} "
                f"{symbol} @ ${transaction.price:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            return False
            
    async def _execute_buy(self, transaction: Transaction, context: TransactionContext) -> None:
        """Execute buy transaction with rollback support"""
        symbol = transaction.symbol
        
        # Check if we have enough cash
        total_cost = transaction.total_cost
        if self.cash < total_cost:
            raise ValueError(f"Insufficient cash for {symbol}: {self.cash} < {total_cost}")
        
        # Snapshot current state
        context.snapshot_state("cash", self.cash)
        if symbol in self.positions:
            context.snapshot_state(f"position_{symbol}", {
                "quantity": self.positions[symbol].quantity,
                "entry_price": self.positions[symbol].entry_price
            })
        
        # Update or create position
        if symbol in self.positions:
            position = self.positions[symbol]
            old_quantity = position.quantity
            old_price = position.entry_price
            
            # Average up/down
            total_quantity = position.quantity + transaction.quantity
            total_cost_avg = (position.entry_price * position.quantity + 
                            transaction.price * transaction.quantity)
            position.entry_price = total_cost_avg / total_quantity
            position.quantity = total_quantity
            
            # Add rollback action
            context.add_rollback_action(lambda: setattr(position, 'quantity', old_quantity))
            context.add_rollback_action(lambda: setattr(position, 'entry_price', old_price))
        else:
            # Create new position
            position = Position(
                symbol=symbol,
                entry_date=transaction.timestamp,
                entry_price=transaction.price,
                quantity=transaction.quantity,
                entry_reason=transaction.notes
            )
            self.positions[symbol] = position
            
            # Add rollback action
            context.add_rollback_action(lambda: self.positions.pop(symbol, None))
        
        # Update cash
        old_cash = self.cash
        self.cash -= total_cost
        
        # Add rollback action
        context.add_rollback_action(lambda: setattr(self, 'cash', old_cash))
        
    async def _execute_sell(self, transaction: Transaction, context: TransactionContext) -> None:
        """Execute sell transaction with rollback support"""
        symbol = transaction.symbol
        
        # Check if we have the position
        if symbol not in self.positions:
            raise ValueError(f"No position to sell for {symbol}")
        
        position = self.positions[symbol]
        
        # Check if we have enough quantity
        if position.quantity < transaction.quantity:
            raise ValueError(
                f"Insufficient quantity for {symbol}: "
                f"{position.quantity} < {transaction.quantity}"
            )
        
        # Snapshot current state
        context.snapshot_state("cash", self.cash)
        context.snapshot_state(f"position_{symbol}", {
            "quantity": position.quantity,
            "realized_pnl": position.realized_pnl
        })
        
        # Calculate P&L
        proceeds = transaction.price * transaction.quantity - transaction.commission
        cost_basis = position.entry_price * transaction.quantity
        realized_pnl = proceeds - cost_basis
        
        # Store old values for rollback
        old_quantity = position.quantity
        old_realized_pnl = position.realized_pnl
        old_cash = self.cash
        
        # Update position
        position.quantity -= transaction.quantity
        position.realized_pnl += realized_pnl
        
        # Add rollback actions
        context.add_rollback_action(lambda: setattr(position, 'quantity', old_quantity))
        context.add_rollback_action(lambda: setattr(position, 'realized_pnl', old_realized_pnl))
        
        if position.quantity == 0:
            # Close position
            position.exit_date = transaction.timestamp
            position.exit_price = transaction.price
            position.status = PositionStatus.CLOSED
            self.closed_positions.append(position)
            del self.positions[symbol]
            
            # Add rollback action to restore position
            context.add_rollback_action(lambda: self.positions.update({symbol: position}))
            
        # Update cash
        self.cash += proceeds
        
        # Add rollback action
        context.add_rollback_action(lambda: setattr(self, 'cash', old_cash))
        
    def execute_transaction_sync(self, transaction: Transaction) -> bool:
        """Synchronous wrapper for execute_transaction (for backward compatibility)"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If called from async context, create task
                future = asyncio.ensure_future(self.execute_transaction(transaction))
                return True  # Return immediately, actual result will be in future
            else:
                # If called from sync context, run until complete
                return loop.run_until_complete(self.execute_transaction(transaction))
        except Exception as e:
            self.logger.error(f"Error in sync wrapper: {e}")
            return False
            
    def update_position_value(self, symbol: str, current_price: float) -> None:
        """Update position value with current price"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.unrealized_pnl = (
                (current_price - position.entry_price) * position.quantity
            )
            
    def check_exit_conditions(self, current_date: datetime) -> List[Position]:
        """Check if any positions should be closed
        
        Returns:
            List of positions that were closed
        """
        closed = []
        
        for symbol, position in list(self.positions.items()):
            should_close, reason = self._should_close_position(position, current_date)
            
            if should_close:
                # Create sell transaction
                sell_transaction = Transaction(
                    timestamp=current_date,
                    symbol=symbol,
                    action=TradeAction.SELL,
                    quantity=position.quantity,
                    price=position.entry_price,  # Will be updated with actual price
                    commission=0,  # Will be calculated
                    slippage=0,
                    total_cost=0,
                    notes=reason
                )
                
                # Mark for closing (actual execution happens in main loop)
                position.exit_reason = reason
                closed.append(position)
                
        return closed
        
    def get_portfolio_state(self) -> PortfolioState:
        """Get current portfolio state"""
        total_value = self.cash
        unrealized_pnl = 0.0
        realized_pnl = sum(p.realized_pnl for p in self.closed_positions.get_all())
        
        # Add position values
        for position in self.positions.values():
            position_value = position.entry_price * position.quantity
            total_value += position_value
            unrealized_pnl += position.unrealized_pnl
            
        # Calculate metrics
        total_return = (total_value - self.initial_capital) / self.initial_capital
        exposure = (total_value - self.cash) / total_value if total_value > 0 else 0
        
        state = PortfolioState(
            timestamp=datetime.now(),
            cash=self.cash,
            positions=self.positions.copy(),
            total_value=total_value,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            total_return=total_return,
            exposure=exposure,
            position_count=len(self.positions),
            largest_position=self._get_largest_position()
        )
        
        # Record history with memory limit
        self.portfolio_history.append(state)
        
        return state
        
    def get_open_positions(self) -> List[str]:
        """Get list of symbols with open positions"""
        return list(self.positions.keys())
        
    def _determine_risk_profile(
        self,
        signal: TradingSignal,
        confidence: float
    ) -> RiskProfile:
        """Determine risk profile based on signal and confidence"""
        # Check if risk stance is provided in signal
        if signal.risk_assessment and 'risk_stance' in signal.risk_assessment:
            stance = signal.risk_assessment['risk_stance']
            if stance == 'AGGRESSIVE':
                return RiskProfile.AGGRESSIVE
            elif stance == 'CONSERVATIVE':
                return RiskProfile.CONSERVATIVE
            else:
                return RiskProfile.NEUTRAL
        
        # Fallback to confidence-based logic
        if confidence >= 0.8:
            return RiskProfile.AGGRESSIVE
        elif confidence >= 0.5:
            return RiskProfile.NEUTRAL
        else:
            return RiskProfile.CONSERVATIVE
            
    def _calculate_available_capital(self) -> float:
        """Calculate capital available for new positions"""
        # Reserve some cash
        min_cash_reserve = self.initial_capital * 0.1
        available = max(0, self.cash - min_cash_reserve)
        return available
        
    def _apply_constraints(self, base_size: float, signal: TradingSignal) -> float:
        """Apply position size constraints"""
        # Maximum position size (90% of total capital)
        max_position = self.initial_capital * 0.9
        
        # Check existing position
        if signal.symbol in self.positions:
            current_position_value = (
                self.positions[signal.symbol].entry_price *
                self.positions[signal.symbol].quantity
            )
            max_additional = max_position - current_position_value
            base_size = min(base_size, max_additional)
            
        # Ensure we don't exceed position count limit
        if len(self.positions) >= self.risk_config.max_positions:
            if signal.symbol not in self.positions:
                return 0.0
                
        # Apply gap and correlation risk adjustments
        adjusted_size = self._apply_risk_adjustments(base_size, signal)
                
        return max(0, adjusted_size)
        
    def _should_close_position(
        self,
        position: Position,
        current_date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """Check if position should be closed"""
        # Stop loss
        if position.stop_loss and position.unrealized_pnl < 0:
            loss_pct = abs(position.unrealized_pnl) / (position.entry_price * position.quantity)
            if loss_pct >= self.risk_config.stop_loss:
                return True, "Stop loss triggered"
                
        # Take profit
        if position.take_profit and position.unrealized_pnl > 0:
            profit_pct = position.unrealized_pnl / (position.entry_price * position.quantity)
            if profit_pct >= self.risk_config.take_profit:
                return True, "Take profit triggered"
                
        # Time-based exit (hold for max 30 days for now)
        # Ensure both dates are timezone-naive for comparison
        current_date_naive = current_date.replace(tzinfo=None) if hasattr(current_date, 'tzinfo') else current_date
        entry_date_naive = position.entry_date.replace(tzinfo=None) if hasattr(position.entry_date, 'tzinfo') else position.entry_date
        if (current_date_naive - entry_date_naive).days > 30:
            return True, "Maximum holding period reached"
            
        return False, None
        
    def _get_largest_position(self) -> Optional[str]:
        """Get symbol of largest position by value"""
        if not self.positions:
            return None
            
        largest_symbol = None
        largest_value = 0
        
        for symbol, position in self.positions.items():
            value = position.entry_price * position.quantity
            if value > largest_value:
                largest_value = value
                largest_symbol = symbol
                
        return largest_symbol
        
    def _apply_risk_adjustments(self, base_size: float, signal: TradingSignal) -> float:
        """Apply gap and correlation risk adjustments to position size"""
        adjusted_size = base_size
        
        try:
            # Get market data if available
            if signal.symbol in self.market_data_cache:
                # Analyze gap risk
                price_data = self.market_data_cache.get(f"{signal.symbol}_prices")
                if price_data is not None:
                    gap_metrics = self.risk_analyzer.analyze_gap_risk(signal.symbol, price_data)
                    
                    # Reduce size for high gap risk
                    if gap_metrics.expected_slippage > 0.01:  # >1% expected slippage
                        gap_adjustment = 1 - (gap_metrics.expected_slippage * 2)
                        adjusted_size *= max(0.5, gap_adjustment)
                        self.logger.info(
                            f"Gap risk adjustment for {signal.symbol}: "
                            f"slippage={gap_metrics.expected_slippage:.2%}, "
                            f"adjustment={gap_adjustment:.2f}"
                        )
                
                # Analyze correlation risk if we have other positions
                if self.positions:
                    positions_list = list(self.positions.keys())
                    returns_data = {}
                    
                    # Collect returns data
                    for symbol in positions_list + [signal.symbol]:
                        returns = self.market_data_cache.get(f"{symbol}_returns")
                        if returns is not None:
                            returns_data[symbol] = returns
                    
                    if len(returns_data) >= 2:
                        correlation_metrics = self.risk_analyzer.analyze_correlation_risk(
                            list(returns_data.keys()),
                            returns_data
                        )
                        
                        # Reduce size for high correlation
                        if correlation_metrics.portfolio_correlation > 0.6:
                            corr_adjustment = 1 - (correlation_metrics.portfolio_correlation - 0.6)
                            adjusted_size *= max(0.7, corr_adjustment)
                            self.logger.info(
                                f"Correlation adjustment for {signal.symbol}: "
                                f"portfolio_corr={correlation_metrics.portfolio_correlation:.2f}, "
                                f"adjustment={corr_adjustment:.2f}"
                            )
                        
                        # Apply diversification benefit
                        if correlation_metrics.diversification_ratio > 1.2:
                            div_bonus = min(1.1, correlation_metrics.diversification_ratio / 1.2)
                            adjusted_size *= div_bonus
                            self.logger.info(
                                f"Diversification bonus for {signal.symbol}: {div_bonus:.2f}"
                            )
                            
        except Exception as e:
            self.logger.warning(f"Could not apply risk adjustments: {e}")
            
        return adjusted_size
        
    def update_market_data(self, symbol: str, price_data: Any, returns_data: Any) -> None:
        """Update market data cache for risk analysis
        
        Args:
            symbol: Stock symbol
            price_data: DataFrame with OHLC data
            returns_data: Series with return data
        """
        self.market_data_cache[f"{symbol}_prices"] = price_data
        self.market_data_cache[f"{symbol}_returns"] = returns_data