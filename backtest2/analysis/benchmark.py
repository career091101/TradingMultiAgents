"""Benchmark comparison functionality"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio

from ..core.types import PortfolioState
from ..core.results_simple import BacktestResult
from ..data.sources import YahooFinanceClient


class BenchmarkComparator:
    """Compare backtest results with benchmark"""
    
    def __init__(self, benchmark_symbol: str = "SPY"):
        self.benchmark_symbol = benchmark_symbol
        self.logger = logging.getLogger(__name__)
        self.data_client = YahooFinanceClient()
        self.benchmark_data: Dict[datetime, float] = {}
        
    async def load_benchmark_data(self, start_date: datetime, end_date: datetime):
        """Load benchmark price data"""
        self.logger.info(f"Loading benchmark data for {self.benchmark_symbol}")
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Weekdays only
                try:
                    price_data = await self.data_client.get_price_data(
                        self.benchmark_symbol,
                        current_date
                    )
                    if price_data:
                        self.benchmark_data[current_date] = price_data['adjusted_close']
                except Exception as e:
                    self.logger.error(f"Failed to load benchmark data for {current_date}: {e}")
                    
            current_date += timedelta(days=1)
            
        self.logger.info(f"Loaded {len(self.benchmark_data)} benchmark data points")
        
    def calculate_benchmark_returns(self) -> Dict[str, float]:
        """Calculate benchmark returns"""
        if len(self.benchmark_data) < 2:
            return {}
            
        sorted_dates = sorted(self.benchmark_data.keys())
        first_price = self.benchmark_data[sorted_dates[0]]
        last_price = self.benchmark_data[sorted_dates[-1]]
        
        # Calculate returns
        total_return = (last_price - first_price) / first_price
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(sorted_dates)):
            prev_price = self.benchmark_data[sorted_dates[i-1]]
            curr_price = self.benchmark_data[sorted_dates[i]]
            daily_return = (curr_price - prev_price) / prev_price
            daily_returns.append(daily_return)
            
        # Calculate annualized return
        days = (sorted_dates[-1] - sorted_dates[0]).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # Calculate volatility
        if daily_returns:
            import statistics
            daily_vol = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
            annual_vol = daily_vol * (252 ** 0.5)  # Annualized volatility
        else:
            annual_vol = 0
            
        # Calculate Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (annualized_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
        
        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(sorted_dates)
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'num_days': days
        }
        
    def compare_with_backtest(self, result: BacktestResult, portfolio_history: Optional[List[PortfolioState]] = None) -> Dict[str, Dict[str, float]]:
        """Compare backtest results with benchmark
        
        Args:
            result: BacktestResult object
            portfolio_history: Optional portfolio history for beta calculation
        """
        
        # Handle backward compatibility - check if result has portfolio_history attribute
        if portfolio_history is None and hasattr(result, 'portfolio_history'):
            portfolio_history = result.portfolio_history
        
        # Get benchmark metrics
        benchmark_metrics = self.calculate_benchmark_returns()
        
        # Get portfolio metrics
        portfolio_metrics = {
            'total_return': getattr(result.metrics, 'total_return', 0),
            'annualized_return': getattr(result.metrics, 'annualized_return', 0),
            'volatility': getattr(result.metrics, 'volatility', 0),
            'sharpe_ratio': getattr(result.metrics, 'sharpe_ratio', 0),
            'max_drawdown': getattr(result.metrics, 'max_drawdown', 0)
        }
        
        # Calculate relative metrics
        relative_metrics = {}
        
        # Alpha (excess return over benchmark)
        if 'annualized_return' in benchmark_metrics:
            relative_metrics['alpha'] = (
                portfolio_metrics['annualized_return'] - 
                benchmark_metrics['annualized_return']
            )
        
        # Beta (correlation with benchmark)
        if portfolio_history:
            relative_metrics['beta'] = self._calculate_beta(portfolio_history)
        else:
            relative_metrics['beta'] = 1.0  # Default beta if no history available
        
        # Information ratio
        if 'volatility' in benchmark_metrics and benchmark_metrics['volatility'] > 0:
            tracking_error = abs(
                portfolio_metrics['volatility'] - benchmark_metrics['volatility']
            )
            if tracking_error > 0:
                relative_metrics['information_ratio'] = (
                    relative_metrics.get('alpha', 0) / tracking_error
                )
            else:
                relative_metrics['information_ratio'] = 0
        
        # Outperformance
        if 'total_return' in benchmark_metrics:
            relative_metrics['outperformance'] = (
                portfolio_metrics['total_return'] - 
                benchmark_metrics['total_return']
            )
            
        return {
            'portfolio': portfolio_metrics,
            'benchmark': benchmark_metrics,
            'relative': relative_metrics
        }
        
    def _calculate_max_drawdown(self, sorted_dates: List[datetime]) -> float:
        """Calculate maximum drawdown for benchmark"""
        if not sorted_dates:
            return 0
            
        peak = self.benchmark_data[sorted_dates[0]]
        max_dd = 0
        
        for date in sorted_dates:
            price = self.benchmark_data[date]
            if price > peak:
                peak = price
            else:
                drawdown = (peak - price) / peak
                max_dd = max(max_dd, drawdown)
                
        return max_dd
        
    def _calculate_beta(self, portfolio_history: List[PortfolioState]) -> float:
        """Calculate portfolio beta relative to benchmark"""
        if len(portfolio_history) < 2:
            return 1.0
            
        # Get matching dates
        portfolio_returns = []
        benchmark_returns = []
        
        for i in range(1, len(portfolio_history)):
            date = portfolio_history[i].timestamp.date()
            prev_date = portfolio_history[i-1].timestamp.date()
            
            if date in self.benchmark_data and prev_date in self.benchmark_data:
                # Portfolio return
                port_return = (
                    (portfolio_history[i].total_value - portfolio_history[i-1].total_value) /
                    portfolio_history[i-1].total_value
                )
                portfolio_returns.append(port_return)
                
                # Benchmark return
                bench_return = (
                    (self.benchmark_data[date] - self.benchmark_data[prev_date]) /
                    self.benchmark_data[prev_date]
                )
                benchmark_returns.append(bench_return)
                
        if len(portfolio_returns) < 2:
            return 1.0
            
        # Calculate beta using covariance/variance
        try:
            import statistics
            
            # Calculate means
            port_mean = statistics.mean(portfolio_returns)
            bench_mean = statistics.mean(benchmark_returns)
            
            # Calculate covariance
            covariance = sum(
                (p - port_mean) * (b - bench_mean)
                for p, b in zip(portfolio_returns, benchmark_returns)
            ) / (len(portfolio_returns) - 1)
            
            # Calculate benchmark variance
            bench_variance = statistics.variance(benchmark_returns)
            
            # Beta = Cov(portfolio, benchmark) / Var(benchmark)
            beta = covariance / bench_variance if bench_variance > 0 else 1.0
            
            return beta
            
        except Exception as e:
            self.logger.error(f"Failed to calculate beta: {e}")
            return 1.0
            
    def generate_comparison_report(self, comparison: Dict[str, Dict[str, float]]) -> str:
        """Generate text report of comparison"""
        
        portfolio = comparison['portfolio']
        benchmark = comparison['benchmark']
        relative = comparison['relative']
        
        report = f"""
## ベンチマーク比較レポート

### ポートフォリオパフォーマンス
- 総リターン: {portfolio.get('total_return', 0):.2%}
- 年率リターン: {portfolio.get('annualized_return', 0):.2%}
- ボラティリティ: {portfolio.get('volatility', 0):.2%}
- シャープレシオ: {portfolio.get('sharpe_ratio', 0):.2f}
- 最大ドローダウン: {portfolio.get('max_drawdown', 0):.2%}

### ベンチマーク（{self.benchmark_symbol}）パフォーマンス
- 総リターン: {benchmark.get('total_return', 0):.2%}
- 年率リターン: {benchmark.get('annualized_return', 0):.2%}
- ボラティリティ: {benchmark.get('volatility', 0):.2%}
- シャープレシオ: {benchmark.get('sharpe_ratio', 0):.2f}
- 最大ドローダウン: {benchmark.get('max_drawdown', 0):.2%}

### 相対パフォーマンス
- アルファ: {relative.get('alpha', 0):.2%}
- ベータ: {relative.get('beta', 1):.2f}
- 情報比率: {relative.get('information_ratio', 0):.2f}
- アウトパフォーマンス: {relative.get('outperformance', 0):.2%}
"""
        
        return report