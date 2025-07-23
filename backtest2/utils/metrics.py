"""Metrics calculation utilities"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from ..core.types import Transaction, PortfolioState, TradeAction
from ..core.results import PerformanceMetrics


class MetricsCalculator:
    """Calculates performance metrics"""
    
    def __init__(self, risk_free_rate: float = 0.02, benchmark: Optional[str] = None):
        self.risk_free_rate = risk_free_rate
        self.benchmark = benchmark
        self.trading_days_per_year = 252
        
    def calculate_full_metrics(
        self,
        transactions: List[Transaction],
        portfolio_history: List[PortfolioState],
        initial_capital: float
    ) -> PerformanceMetrics:
        """Calculate all performance metrics"""
        
        # Calculate returns
        returns = self._calculate_returns(portfolio_history, initial_capital)
        
        # Basic return metrics
        total_return = self._calculate_total_return(portfolio_history, initial_capital)
        annualized_return = self._calculate_annualized_return(
            total_return,
            portfolio_history[0].timestamp,
            portfolio_history[-1].timestamp
        )
        
        # Risk metrics
        volatility = self._calculate_volatility(returns)
        sharpe_ratio = self._calculate_sharpe_ratio(returns, volatility)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        max_drawdown, max_dd_duration = self._calculate_max_drawdown(portfolio_history)
        
        # Trading metrics
        trade_stats = self._calculate_trade_statistics(transactions, portfolio_history)
        
        # Portfolio metrics
        final_value = portfolio_history[-1].total_value if portfolio_history else initial_capital
        peak_value = max(p.total_value for p in portfolio_history) if portfolio_history else initial_capital
        lowest_value = min(p.total_value for p in portfolio_history) if portfolio_history else initial_capital
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            total_trades=trade_stats['total_trades'],
            winning_trades=trade_stats['winning_trades'],
            losing_trades=trade_stats['losing_trades'],
            win_rate=trade_stats['win_rate'],
            profit_factor=trade_stats['profit_factor'],
            average_win=trade_stats['average_win'],
            average_loss=trade_stats['average_loss'],
            final_value=final_value,
            peak_value=peak_value,
            lowest_value=lowest_value
        )
        
    def calculate_daily_metrics(
        self,
        portfolio_state: PortfolioState,
        transactions: List[Transaction]
    ) -> Dict[str, float]:
        """Calculate daily metrics"""
        return {
            'total_value': portfolio_state.total_value,
            'cash': portfolio_state.cash,
            'exposure': portfolio_state.exposure,
            'position_count': portfolio_state.position_count,
            'daily_trades': len(transactions),
            'unrealized_pnl': portfolio_state.unrealized_pnl,
            'realized_pnl': portfolio_state.realized_pnl
        }
        
    def _calculate_returns(
        self,
        portfolio_history: List[PortfolioState],
        initial_capital: float
    ) -> np.ndarray:
        """Calculate daily returns"""
        if not portfolio_history:
            return np.array([])
            
        values = [initial_capital] + [p.total_value for p in portfolio_history]
        returns = np.diff(values) / values[:-1]
        return returns
        
    def _calculate_total_return(
        self,
        portfolio_history: List[PortfolioState],
        initial_capital: float
    ) -> float:
        """Calculate total return"""
        if not portfolio_history:
            return 0.0
            
        final_value = portfolio_history[-1].total_value
        return (final_value - initial_capital) / initial_capital
        
    def _calculate_annualized_return(
        self,
        total_return: float,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate annualized return"""
        days = (end_date - start_date).days
        if days == 0:
            return 0.0
            
        years = days / 365.25
        return (1 + total_return) ** (1 / years) - 1
        
    def _calculate_volatility(self, returns: np.ndarray) -> float:
        """Calculate annualized volatility"""
        if len(returns) < 2:
            return 0.0
            
        daily_vol = np.std(returns)
        return daily_vol * np.sqrt(self.trading_days_per_year)
        
    def _calculate_sharpe_ratio(self, returns: np.ndarray, volatility: float) -> float:
        """Calculate Sharpe ratio"""
        if volatility == 0 or len(returns) == 0:
            return 0.0
            
        excess_returns = returns - self.risk_free_rate / self.trading_days_per_year
        return np.mean(excess_returns) * np.sqrt(self.trading_days_per_year) / volatility
        
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 2:
            return 0.0
            
        # Downside returns only
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0.0
            
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0
            
        excess_returns = returns - self.risk_free_rate / self.trading_days_per_year
        return np.mean(excess_returns) * np.sqrt(self.trading_days_per_year) / downside_std
        
    def _calculate_max_drawdown(
        self,
        portfolio_history: List[PortfolioState]
    ) -> Tuple[float, int]:
        """Calculate maximum drawdown and duration"""
        if not portfolio_history:
            return 0.0, 0
            
        values = [p.total_value for p in portfolio_history]
        peak = values[0]
        max_dd = 0.0
        max_dd_duration = 0
        current_dd_start = 0
        
        for i, value in enumerate(values):
            if value > peak:
                peak = value
                current_dd_start = i
            else:
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
                    max_dd_duration = i - current_dd_start
                    
        return max_dd, max_dd_duration
        
    def _calculate_trade_statistics(
        self,
        transactions: List[Transaction],
        portfolio_history: List[PortfolioState]
    ) -> Dict[str, float]:
        """Calculate trading statistics"""
        # Group transactions by symbol to identify round trips
        trades = []
        positions = {}
        
        for tx in transactions:
            if tx.action == TradeAction.BUY:
                if tx.symbol not in positions:
                    positions[tx.symbol] = []
                positions[tx.symbol].append(tx)
            elif tx.action == TradeAction.SELL and tx.symbol in positions:
                # Match with buy transactions
                buy_txs = positions[tx.symbol]
                if buy_txs:
                    buy_tx = buy_txs.pop(0)
                    # Calculate P&L
                    pnl = (tx.price - buy_tx.price) * tx.quantity - tx.commission - buy_tx.commission
                    trades.append(pnl)
                    
        # Calculate statistics
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0
            }
            
        trades = np.array(trades)
        winning_trades = trades[trades > 0]
        losing_trades = trades[trades < 0]
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) if len(trades) > 0 else 0.0,
            'profit_factor': (
                np.sum(winning_trades) / abs(np.sum(losing_trades))
                if len(losing_trades) > 0 and np.sum(losing_trades) != 0
                else 0.0
            ),
            'average_win': np.mean(winning_trades) if len(winning_trades) > 0 else 0.0,
            'average_loss': np.mean(losing_trades) if len(losing_trades) > 0 else 0.0
        }