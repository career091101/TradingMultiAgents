"""Metrics calculation for backtest results"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math
import statistics


class MetricsCalculator:
    """Calculate performance metrics for backtest results"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
        
    def calculate_all_metrics(
        self,
        portfolio_history: List['PortfolioState'],
        transactions: List['Transaction'],
        initial_capital: float
    ) -> Dict[str, float]:
        """Calculate all performance metrics"""
        
        # Handle CircularBuffer if passed directly
        if hasattr(portfolio_history, 'get_all'):
            portfolio_history = portfolio_history.get_all()
        if hasattr(transactions, 'get_all'):
            transactions = transactions.get_all()
        
        if not portfolio_history:
            return self._empty_metrics()
            
        # Basic return metrics
        total_return = self._calculate_total_return(portfolio_history, initial_capital)
        annual_return = self._calculate_annual_return(portfolio_history, total_return)
        
        # Risk metrics
        daily_returns = self._calculate_daily_returns(portfolio_history)
        volatility = self._calculate_volatility(daily_returns)
        sharpe_ratio = self._calculate_sharpe_ratio(annual_return, volatility)
        sortino_ratio = self._calculate_sortino_ratio(annual_return, daily_returns)
        
        # Drawdown metrics
        drawdown_series = self._calculate_drawdown_series(portfolio_history)
        max_drawdown = max(drawdown_series) if drawdown_series else 0
        max_dd_duration = self._calculate_max_drawdown_duration(drawdown_series, portfolio_history)
        calmar_ratio = self._calculate_calmar_ratio(annual_return, max_drawdown)
        
        # Trading metrics
        trade_metrics = self._calculate_trade_metrics(transactions)
        
        # Risk metrics
        var_95 = self._calculate_var(daily_returns, 0.95)
        cvar_95 = self._calculate_cvar(daily_returns, 0.95)
        
        # Portfolio metrics
        final_value = portfolio_history[-1].total_value if portfolio_history else initial_capital
        
        return {
            # Return metrics
            'total_return': total_return,
            'annual_return': annual_return,
            'final_value': final_value,
            
            # Risk metrics
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            
            # Drawdown metrics
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_dd_duration,
            
            # Trading metrics
            'total_trades': trade_metrics['total_trades'],
            'winning_trades': trade_metrics['winning_trades'],
            'losing_trades': trade_metrics['losing_trades'],
            'win_rate': trade_metrics['win_rate'],
            'avg_win': trade_metrics['avg_win'],
            'avg_loss': trade_metrics['avg_loss'],
            'profit_factor': trade_metrics['profit_factor'],
            'avg_trade_return': trade_metrics['avg_trade_return'],
            'avg_holding_period': trade_metrics['avg_holding_period'],
            
            # Risk metrics
            'var_95': var_95,
            'cvar_95': cvar_95,
            'downside_deviation': self._calculate_downside_deviation(daily_returns),
            
            # Additional metrics
            'total_commission': trade_metrics['total_commission'],
            'total_slippage': trade_metrics['total_slippage'],
            'trading_days': len(portfolio_history),
            'annualized_turnover': self._calculate_turnover(transactions, portfolio_history)
        }
        
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dict"""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'final_value': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_duration': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'avg_trade_return': 0.0,
            'avg_holding_period': 0.0,
            'var_95': 0.0,
            'cvar_95': 0.0,
            'downside_deviation': 0.0,
            'total_commission': 0.0,
            'total_slippage': 0.0,
            'trading_days': 0,
            'annualized_turnover': 0.0
        }
        
    def _calculate_total_return(
        self,
        portfolio_history: List['PortfolioState'],
        initial_capital: float
    ) -> float:
        """Calculate total return"""
        if not portfolio_history:
            return 0.0
            
        final_value = portfolio_history[-1].total_value
        return (final_value - initial_capital) / initial_capital
        
    def _calculate_annual_return(
        self,
        portfolio_history: List['PortfolioState'],
        total_return: float
    ) -> float:
        """Calculate annualized return"""
        if len(portfolio_history) < 2:
            return 0.0
            
        start_date = portfolio_history[0].timestamp
        end_date = portfolio_history[-1].timestamp
        years = (end_date - start_date).days / 365.25
        
        if years <= 0:
            return 0.0
            
        return (1 + total_return) ** (1/years) - 1
        
    def _calculate_daily_returns(
        self,
        portfolio_history: List['PortfolioState']
    ) -> List[float]:
        """Calculate daily returns"""
        returns = []
        
        for i in range(1, len(portfolio_history)):
            prev_value = portfolio_history[i-1].total_value
            curr_value = portfolio_history[i].total_value
            
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)
                
        return returns
        
    def _calculate_volatility(self, daily_returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if len(daily_returns) < 2:
            return 0.0
            
        daily_vol = statistics.stdev(daily_returns)
        return daily_vol * math.sqrt(252)  # Annualized
        
    def _calculate_sharpe_ratio(
        self,
        annual_return: float,
        volatility: float
    ) -> float:
        """Calculate Sharpe ratio"""
        if volatility == 0:
            return 0.0
            
        return (annual_return - self.risk_free_rate) / volatility
        
    def _calculate_sortino_ratio(
        self,
        annual_return: float,
        daily_returns: List[float]
    ) -> float:
        """Calculate Sortino ratio"""
        downside_dev = self._calculate_downside_deviation(daily_returns)
        
        if downside_dev == 0:
            return 0.0
            
        # Annualize downside deviation
        annual_downside_dev = downside_dev * math.sqrt(252)
        
        return (annual_return - self.risk_free_rate) / annual_downside_dev
        
    def _calculate_downside_deviation(self, daily_returns: List[float]) -> float:
        """Calculate downside deviation"""
        if not daily_returns:
            return 0.0
            
        # Daily risk-free rate
        daily_rf = self.risk_free_rate / 252
        
        # Only consider returns below risk-free rate
        downside_returns = [r - daily_rf for r in daily_returns if r < daily_rf]
        
        if len(downside_returns) < 2:
            return 0.0
            
        # Calculate standard deviation of downside returns
        mean_downside = sum(downside_returns) / len(downside_returns)
        variance = sum((r - mean_downside)**2 for r in downside_returns) / (len(downside_returns) - 1)
        
        return math.sqrt(variance)
        
    def _calculate_drawdown_series(
        self,
        portfolio_history: List['PortfolioState']
    ) -> List[float]:
        """Calculate drawdown series"""
        if not portfolio_history:
            return []
            
        drawdowns = []
        peak = portfolio_history[0].total_value
        
        for state in portfolio_history:
            if state.total_value > peak:
                peak = state.total_value
                
            drawdown = (peak - state.total_value) / peak if peak > 0 else 0
            drawdowns.append(drawdown)
            
        return drawdowns
        
    def _calculate_max_drawdown_duration(
        self,
        drawdown_series: List[float],
        portfolio_history: List['PortfolioState']
    ) -> int:
        """Calculate maximum drawdown duration in days"""
        if not drawdown_series or not portfolio_history:
            return 0
            
        max_duration = 0
        current_duration = 0
        in_drawdown = False
        
        for i, dd in enumerate(drawdown_series):
            if dd > 0:
                if not in_drawdown:
                    in_drawdown = True
                    current_duration = 1
                else:
                    current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                in_drawdown = False
                current_duration = 0
                
        return max_duration
        
    def _calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float
    ) -> float:
        """Calculate Calmar ratio"""
        if max_drawdown == 0:
            return 0.0
            
        return annual_return / max_drawdown
        
    def _calculate_trade_metrics(
        self,
        transactions: List['Transaction']
    ) -> Dict[str, float]:
        """Calculate trading-related metrics"""
        
        # Handle CircularBuffer if passed directly
        if hasattr(transactions, 'get_all'):
            transactions = transactions.get_all()
        
        # Group transactions by symbol to identify trades
        trades = self._identify_trades(transactions)
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'avg_trade_return': 0.0,
                'avg_holding_period': 0.0,
                'total_commission': 0.0,
                'total_slippage': 0.0
            }
            
        # Calculate metrics
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        total_trades = len(trades)
        num_winners = len(winning_trades)
        num_losers = len(losing_trades)
        
        win_rate = num_winners / total_trades if total_trades > 0 else 0
        
        avg_win = sum(t['pnl'] for t in winning_trades) / num_winners if num_winners > 0 else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / num_losers if num_losers > 0 else 0
        
        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['pnl'] for t in losing_trades))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        avg_trade_return = sum(t['return'] for t in trades) / total_trades if total_trades > 0 else 0
        
        avg_holding_period = sum(t['holding_days'] for t in trades) / total_trades if total_trades > 0 else 0
        
        # Ensure transactions is a list before summing
        if hasattr(transactions, 'get_all'):
            transactions_list = transactions.get_all()
        else:
            transactions_list = transactions
            
        total_commission = sum(t.commission for t in transactions_list)
        total_slippage = sum(t.slippage for t in transactions_list)
        
        return {
            'total_trades': total_trades,
            'winning_trades': num_winners,
            'losing_trades': num_losers,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_trade_return': avg_trade_return,
            'avg_holding_period': avg_holding_period,
            'total_commission': total_commission,
            'total_slippage': total_slippage
        }
        
    def _identify_trades(self, transactions: List['Transaction']) -> List[Dict]:
        """Identify completed trades from transactions"""
        trades = []
        positions = {}  # Track open positions
        
        # Handle CircularBuffer if passed directly
        if hasattr(transactions, 'get_all'):
            transactions = transactions.get_all()
        
        for txn in transactions:
            symbol = txn.symbol
            
            if txn.action.value == 'BUY':
                # Open or add to position
                if symbol not in positions:
                    positions[symbol] = {
                        'quantity': 0,
                        'cost_basis': 0,
                        'entry_date': txn.timestamp
                    }
                    
                positions[symbol]['quantity'] += txn.quantity
                positions[symbol]['cost_basis'] += txn.total_cost
                
            elif txn.action.value == 'SELL' and symbol in positions:
                # Close or reduce position
                pos = positions[symbol]
                
                if txn.quantity >= pos['quantity']:
                    # Close entire position
                    proceeds = txn.price * pos['quantity'] - txn.commission
                    pnl = proceeds - pos['cost_basis']
                    trade_return = pnl / pos['cost_basis'] if pos['cost_basis'] > 0 else 0
                    holding_days = (txn.timestamp - pos['entry_date']).days
                    
                    trades.append({
                        'symbol': symbol,
                        'pnl': pnl,
                        'return': trade_return,
                        'holding_days': holding_days
                    })
                    
                    del positions[symbol]
                else:
                    # Partial close
                    ratio = txn.quantity / pos['quantity']
                    proceeds = txn.price * txn.quantity - txn.commission
                    cost = pos['cost_basis'] * ratio
                    pnl = proceeds - cost
                    trade_return = pnl / cost if cost > 0 else 0
                    holding_days = (txn.timestamp - pos['entry_date']).days
                    
                    trades.append({
                        'symbol': symbol,
                        'pnl': pnl,
                        'return': trade_return,
                        'holding_days': holding_days
                    })
                    
                    # Update remaining position
                    pos['quantity'] -= txn.quantity
                    pos['cost_basis'] -= cost
                    
        return trades
        
    def _calculate_var(self, daily_returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk"""
        if not daily_returns:
            return 0.0
            
        sorted_returns = sorted(daily_returns)
        index = int((1 - confidence) * len(sorted_returns))
        
        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1
            
        return -sorted_returns[index] if index >= 0 else 0.0
        
    def _calculate_cvar(self, daily_returns: List[float], confidence: float) -> float:
        """Calculate Conditional Value at Risk"""
        if not daily_returns:
            return 0.0
            
        var = self._calculate_var(daily_returns, confidence)
        
        # Get returns worse than VaR
        worse_returns = [r for r in daily_returns if r < -var]
        
        if not worse_returns:
            return var
            
        return -sum(worse_returns) / len(worse_returns)
        
    def _calculate_turnover(
        self,
        transactions: List['Transaction'],
        portfolio_history: List['PortfolioState']
    ) -> float:
        """Calculate annualized turnover"""
        # Handle CircularBuffer if passed directly
        if hasattr(transactions, 'get_all'):
            transactions = transactions.get_all()
        if hasattr(portfolio_history, 'get_all'):
            portfolio_history = portfolio_history.get_all()
            
        if not transactions or not portfolio_history:
            return 0.0
            
        # Calculate total traded value
        total_traded = sum(txn.total_cost for txn in transactions)
        
        # Calculate average portfolio value
        avg_portfolio_value = sum(
            state.total_value for state in portfolio_history
        ) / len(portfolio_history)
        
        if avg_portfolio_value == 0:
            return 0.0
            
        # Calculate time period in years
        start_date = portfolio_history[0].timestamp
        end_date = portfolio_history[-1].timestamp
        years = (end_date - start_date).days / 365.25
        
        if years <= 0:
            return 0.0
            
        # Annualized turnover
        return (total_traded / avg_portfolio_value) / years