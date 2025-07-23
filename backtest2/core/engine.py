"""Main backtest engine implementation"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from .config import BacktestConfig
from .types import (
    MarketData, TradingDecision, TradeAction, PortfolioState,
    Transaction, TradingOutcome, Position, TradingSignal
)
from .results_simple import BacktestResult, PerformanceMetrics
from ..agents.orchestrator import AgentOrchestrator
from ..data import DataManager
from ..risk.position_manager import PositionManager
from ..utils.time_manager import TimeManager
from ..memory import MemoryStore, AgentMemory
from ..utils import MetricsCalculator, BacktestLogger
from ..utils.memory_manager import CircularBuffer
from ..utils.metrics_collector import BacktestMetrics
from ..utils.tracer import get_tracer
from ..analysis.benchmark import BenchmarkComparator
from ..analysis.metrics import MetricsCalculator as AdvancedMetricsCalculator
# from ..memory.reflection import ReflectionScheduler, TradingEvent, TradeExecutedEvent


class BacktestEngine:
    """バックテストシミュレーションの中核エンジン"""
    
    def __init__(self, config: BacktestConfig):
        """Initialize backtest engine
        
        Args:
            config: Backtest configuration
        """
        # Validate configuration
        config.validate()
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.time_manager = TimeManager(
            start_date=config.time_range.start if config.time_range else config.start_date,
            end_date=config.time_range.end if config.time_range else config.end_date,
            timezone="UTC"  # Default timezone
        )
        
        # Create risk config if not provided
        if config.risk_config is None:
            from .config import RiskConfig
            risk_config = RiskConfig(
                position_limits=config.position_limits,
                max_positions=config.max_positions,
                stop_loss=getattr(config, 'stop_loss', 0.1),
                take_profit=getattr(config, 'take_profit', 0.2)
            )
        else:
            risk_config = config.risk_config
            
        self.position_manager = PositionManager(
            initial_capital=config.initial_capital,
            risk_config=risk_config
        )
        
        # Initialize memory store
        memory_path = config.result_dir / "memories.json" if config.result_dir else None
        self.memory_store = MemoryStore(memory_path)
        
        self.agent_orchestrator = AgentOrchestrator(config, self.memory_store)
        self.data_manager = DataManager(config)
        self.metrics_calculator = MetricsCalculator()
        self.backtest_logger = BacktestLogger(config.result_dir)
        
        # Reflection will be added in full implementation
        self.reflection_scheduler = None
            
        # Execution state
        self.is_running = False
        self.execution_id = str(uuid.uuid4())
        # Use circular buffer to prevent memory leak
        self.transactions = CircularBuffer(max_size=50000)  # Keep last 50k transactions
        
        # Initialize metrics and tracing
        self.metrics = BacktestMetrics()
        self.tracer = get_tracer()
        
    async def run(self) -> BacktestResult:
        """Run the backtest simulation
        
        Returns:
            BacktestResult containing performance metrics and analysis
        """
        self.logger.info(f"Starting backtest execution {self.execution_id}")
        self.is_running = True
        
        try:
            # Initialize environment
            await self._initialize()
            
            # Main simulation loop
            while self.time_manager.has_next():
                current_date = self.time_manager.current_date
                
                # Process each symbol
                for symbol in self.config.symbols:
                    await self._process_symbol(symbol, current_date)
                
                # Update portfolio values
                await self._update_portfolio(current_date)
                
                # Trigger daily reflection if enabled
                if self.reflection_scheduler:
                    await self._trigger_daily_reflection(current_date)
                
                # Move to next time period
                self.time_manager.next()
                
            # Calculate final results
            result = await self._calculate_results()
            
            # Save results if configured
            if self.config.save_results:
                await self.backtest_logger.save_results(result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}", exc_info=True)
            raise
        finally:
            self.is_running = False
            await self._cleanup()
    
    async def _initialize(self) -> None:
        """Initialize backtest environment"""
        self.logger.info("Initializing backtest environment")
        
        # Set random seeds for reproducibility
        import random
        # Use getattr with default value to handle missing attribute
        random_seed = getattr(self.config, 'random_seed', 42)
        random.seed(random_seed)
        
        # Only use numpy if available
        try:
            import numpy as np
            np.random.seed(random_seed)
        except ImportError:
            self.logger.debug("NumPy not available, using Python random only")
        
        # Initialize data sources
        await self.data_manager.initialize()
        
        # Initialize agents
        await self.agent_orchestrator.initialize()
        
        # Initialize benchmark data if needed
        if self.config.benchmark:
            await self._load_benchmark_data()
            
    async def _process_symbol(self, symbol: str, current_date: datetime) -> None:
        """Process a single symbol for the current date"""
        try:
            # Get market data
            market_data = await self.data_manager.get_data(symbol, current_date)
            
            if market_data is None:
                self.logger.warning(f"No data available for {symbol} on {current_date}")
                return
                
            # Get current portfolio state
            portfolio_state = self.position_manager.get_portfolio_state()
            
            # Make trading decision
            decision = await self.agent_orchestrator.make_decision(
                date=current_date,
                symbol=symbol,
                market_data=market_data,
                portfolio=portfolio_state
            )
            
            # Execute trade if not HOLD
            if decision.action != TradeAction.HOLD:
                await self._execute_trade(decision, market_data)
                
                # Reflection will be added in full implementation
                pass
                    
        except Exception as e:
            self.logger.error(f"Error processing {symbol} on {current_date}: {str(e)}")
            raise
            
    async def _execute_trade(self, decision: TradingDecision, market_data: MarketData) -> None:
        """Execute a trading decision"""
        # Calculate actual position size
        # Convert TradingDecision to TradingSignal for position sizing
        signal = TradingSignal(
            action=decision.action,
            symbol=decision.symbol,
            confidence=decision.confidence,
            size_recommendation=decision.quantity,
            rationale=decision.rationale,
            risk_assessment=decision.risk_assessment
        )
        position_size = self.position_manager.calculate_position_size(
            signal=signal,
            confidence=decision.confidence
        )
        
        if position_size == 0:
            self.logger.info(f"Position size is 0 for {decision.symbol}, skipping trade")
            return
            
        # Calculate execution price with slippage
        if decision.action == TradeAction.BUY:
            execution_price = market_data.close * (1 + self.config.slippage)
        else:  # SELL
            execution_price = market_data.close * (1 - self.config.slippage)
            
        # Calculate commission
        commission = position_size * self.config.commission
        
        # Create transaction
        transaction = Transaction(
            timestamp=market_data.date,
            symbol=decision.symbol,
            action=decision.action,
            quantity=position_size / execution_price,  # Number of shares
            price=execution_price,
            commission=commission,
            slippage=self.config.slippage * position_size,
            total_cost=position_size + commission,
            signal=decision
        )
        
        # Execute transaction atomically
        success = await self.position_manager.execute_transaction(transaction)
        if success:
            self.transactions.append(transaction)
        else:
            self.logger.error(f"Failed to execute transaction for {decision.symbol}")
            return
        
        # Log transaction
        self.logger.info(
            f"Executed {decision.action.value} {transaction.quantity:.2f} shares of "
            f"{decision.symbol} at ${execution_price:.2f}"
        )
        
        # Store decision in memory
        await self.memory_store.add(
            "engine",
            {
                "type": "trade_execution",
                "decision": decision.__dict__,
                "transaction": transaction.__dict__
            }
        )
        
    async def _update_portfolio(self, current_date: datetime) -> None:
        """Update portfolio values and check for closed positions"""
        # Update market values
        for symbol in self.position_manager.get_open_positions():
            market_data = await self.data_manager.get_data(symbol, current_date)
            if market_data:
                self.position_manager.update_position_value(symbol, market_data.close)
                
        # Check for positions to close
        closed_positions = self.position_manager.check_exit_conditions(current_date)
        
        # Process closed positions
        for position in closed_positions:
            outcome = TradingOutcome(
                decision_id=position.agent_decisions.get('decision_id'),
                position=position,
                pnl=position.realized_pnl,
                holding_period=(position.exit_date - position.entry_date).days,
                return_pct=position.realized_pnl / (position.entry_price * position.quantity),
                max_drawdown=position.agent_decisions.get('max_drawdown', 0),
                success=position.realized_pnl > 0
            )
            
            # Store outcome in memory
            await self.memory_store.add(
                "engine",
                {
                    "type": "position_closed",
                    "outcome": outcome.__dict__
                }
            )
                
    async def _trigger_daily_reflection(self, current_date: datetime) -> None:
        """Trigger daily reflection"""
        # Will be implemented in full version
        pass
        
    async def _trigger_trade_reflection(self, decision: TradingDecision) -> None:
        """Trigger immediate reflection after trade"""
        # Will be implemented in full version
        pass
        
    def _get_daily_transactions(self, date: datetime) -> List[Transaction]:
        """Get transactions for a specific date"""
        return [t for t in self.transactions.get_all() if t.timestamp.date() == date.date()]
        
    async def _load_benchmark_data(self) -> None:
        """Load benchmark data for comparison"""
        self.logger.info(f"Loading benchmark data for {self.config.benchmark}")
        # Implementation would load benchmark prices
        
    async def _calculate_results(self) -> BacktestResult:
        """Calculate final backtest results"""
        self.logger.info("Calculating backtest results")
        
        # Get final portfolio state
        final_portfolio = self.position_manager.get_portfolio_state()
        
        # Calculate comprehensive metrics using advanced calculator
        advanced_metrics_calc = AdvancedMetricsCalculator(self.config.risk_free_rate)
        metrics_dict = advanced_metrics_calc.calculate_all_metrics(
            self.position_manager.portfolio_history.get_all(),  # Get all from circular buffer
            self.position_manager.transaction_history.get_all(),  # Get all from circular buffer
            self.config.initial_capital
        )
        
        # Convert to PerformanceMetrics object
        metrics = PerformanceMetrics(
            total_return=metrics_dict['total_return'] * 100,
            annualized_return=metrics_dict['annual_return'] * 100,
            volatility=metrics_dict['volatility'] * 100,
            sharpe_ratio=metrics_dict['sharpe_ratio'],
            sortino_ratio=metrics_dict['sortino_ratio'],
            max_drawdown=metrics_dict['max_drawdown'] * -100,  # Convert to negative percentage
            max_drawdown_duration=metrics_dict['max_drawdown_duration'],
            total_trades=metrics_dict['total_trades'],
            winning_trades=metrics_dict['winning_trades'],
            losing_trades=metrics_dict['losing_trades'],
            win_rate=metrics_dict['win_rate'] * 100,
            profit_factor=metrics_dict['profit_factor'],
            average_win=metrics_dict['avg_win'],
            average_loss=metrics_dict['avg_loss'],
            final_value=metrics_dict['final_value'],
            peak_value=max(p.total_value for p in self.position_manager.portfolio_history.get_all()) if len(self.position_manager.portfolio_history) > 0 else self.config.initial_capital,
            lowest_value=min(p.total_value for p in self.position_manager.portfolio_history.get_all()) if len(self.position_manager.portfolio_history) > 0 else self.config.initial_capital,
            calmar_ratio=metrics_dict['calmar_ratio']
        )
        
        # Create result object
        result = BacktestResult(
            execution_id=self.execution_id,
            config=self.config,
            metrics=metrics,
            transactions=self.transactions.get_all(),
            final_portfolio=final_portfolio,
            agent_performance=await self._get_agent_performance()
        )
        
        # Add benchmark comparison if configured
        if self.config.benchmark:
            benchmark_comparator = BenchmarkComparator(self.config.benchmark)
            
            # Load benchmark data
            await benchmark_comparator.load_benchmark_data(
                self.config.time_range.start if self.config.time_range else self.config.start_date,
                self.config.time_range.end if self.config.time_range else self.config.end_date
            )
            
            # Generate comparison and add to result
            portfolio_history = self.position_manager.portfolio_history.get_all()
            comparison = benchmark_comparator.compare_with_backtest(result, portfolio_history)
            result.benchmark_comparison = comparison
            result.benchmark_report = benchmark_comparator.generate_comparison_report(comparison)
        
        return result
        
    async def _get_agent_performance(self) -> Dict[str, Any]:
        """Get performance metrics for each agent"""
        if not self.memory_store:
            return {}
            
        # Simple performance summary
        return {
            "total_decisions": len(self.transactions),
            "memory_entries": len(self.memory_store.memories)
        }
        
    async def _cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info("Cleaning up backtest resources")
        
        # Close data connections
        await self.data_manager.close()
        
        # Cleanup orchestrator and all agents
        if hasattr(self.agent_orchestrator, 'cleanup'):
            await self.agent_orchestrator.cleanup()
        
        # Save memory state if configured
        if self.config.result_dir:
            self.memory_store.save()