"""
Backtest2 wrapper for integrating the new backtesting framework with the WebUI.
Implements the paper's 6-phase decision flow and multi-agent architecture.
"""

import os
import sys
import json
import logging
import asyncio
import math
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)

# Add paths for imports
current_file = os.path.abspath(__file__)
webui_backend_dir = os.path.dirname(current_file)
webui_dir = os.path.dirname(webui_backend_dir)
trading_multi_agents_dir = os.path.dirname(webui_dir)
project_root = os.path.dirname(trading_multi_agents_dir)

# Add project root to path (contains backtest2)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also try adding the parent of the current file's directory
# This handles cases where the script is run from different locations
alt_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if alt_root not in sys.path and os.path.exists(os.path.join(alt_root, 'backtest2')):
    sys.path.insert(0, alt_root)

# Debug logging
logger.debug(f"Current file: {current_file}")
logger.debug(f"Project root: {project_root}")
logger.debug(f"Alt root: {alt_root}")
logger.debug(f"Python path: {sys.path[:3]}")

# Import backtest2 modules with simplified logic
try:
    # Add the most likely path first
    backtest2_parent = '/Users/y-sato/TradingAgents2'
    if os.path.exists(os.path.join(backtest2_parent, 'backtest2')) and backtest2_parent not in sys.path:
        sys.path.insert(0, backtest2_parent)
    
    # Import required modules
    from backtest2.core.config import (
        BacktestConfig, TimeRange, LLMConfig, RiskProfile,
        AgentConfig, DataConfig, RiskConfig, ReflectionConfig
    )
    from backtest2.core.engine import BacktestEngine
    from backtest2.core.types import TradeAction
    from backtest2.core.results_simple import BacktestResult
    
    logger.info("Successfully imported backtest2 modules")
    logger.debug(f"BacktestConfig type: {type(BacktestConfig)}")
    logger.debug(f"BacktestConfig module: {BacktestConfig.__module__}")
    
except ImportError as e:
    # Try alternative paths
    alternative_paths = [
        project_root,
        alt_root,
        os.path.dirname(project_root)
    ]
    
    import_success = False
    for path in alternative_paths:
        if os.path.exists(os.path.join(path, 'backtest2')) and path not in sys.path:
            sys.path.insert(0, path)
            try:
                from backtest2.core.config import (
                    BacktestConfig, TimeRange, LLMConfig, RiskProfile,
                    AgentConfig, DataConfig, RiskConfig, ReflectionConfig
                )
                from backtest2.core.engine import BacktestEngine
                from backtest2.core.types import TradeAction
                from backtest2.core.results_simple import BacktestResult
                logger.info(f"Successfully imported backtest2 modules from {path}")
                import_success = True
                break
            except ImportError:
                continue
    
    if not import_success:
        error_msg = f"Failed to import backtest2 modules. Original error: {e}\nPython path: {sys.path[:5]}"
        logger.error(error_msg)
        raise ImportError(error_msg)

# Remove the old patching code as it's no longer needed
# BacktestConfig field validation is now handled dynamically in _create_backtest_config


class Backtest2Wrapper:
    """Wrapper class for running Backtest2 (paper-compliant version) from the WebUI."""
    
    def __init__(self):
        self.engine = None
        self.is_running = False
        self.should_stop = False
        self.current_task = None
        
    async def run_backtest_async(
        self, 
        config: Dict[str, Any], 
        progress_callback: Optional[Callable] = None,
        log_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run backtest asynchronously with the given configuration.
        
        Args:
            config: Backtest configuration dictionary from WebUI
            progress_callback: Function to call with progress updates (progress, status, ticker)
            log_callback: Function to call with log messages
            
        Returns:
            Dictionary with results for each ticker
        """
        self.is_running = True
        self.should_stop = False
        results = {}
        
        try:
            # Log start
            if log_callback:
                log_callback("Starting Backtest2 (Paper-compliant version)")
                log_callback(f"Configuration: {json.dumps(config, indent=2)}")
            
            # Convert WebUI config to Backtest2Config
            backtest_config = self._create_backtest_config(config)
            
            # Initialize progress
            tickers = config.get("tickers", ["AAPL"])
            total_tickers = len(tickers)
            
            for idx, ticker in enumerate(tickers):
                if self.should_stop:
                    if log_callback:
                        log_callback("Backtest stopped by user")
                    break
                
                # Update progress
                progress = (idx / total_tickers) * 100
                if progress_callback:
                    progress_callback(progress, f"Processing {ticker}", ticker)
                
                if log_callback:
                    log_callback(f"Starting backtest for {ticker}")
                
                # Update config for single ticker
                ticker_config = self._update_config_for_ticker(backtest_config, ticker)
                
                # Create and run engine
                engine = BacktestEngine(ticker_config)
                self.engine = engine
                
                # Run backtest
                if log_callback:
                    log_callback(f"Running 6-phase decision flow for {ticker}")
                
                try:
                    result = await engine.run()
                    
                    # Process results
                    ticker_results = self._process_results(result, ticker, ticker_config)
                    results[ticker] = ticker_results
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Store error result
                    results[ticker] = {
                        "ticker": ticker,
                        "error": str(e),
                        "metrics": {},
                        "initial_capital": ticker_config.initial_capital,
                        "final_value": ticker_config.initial_capital,
                        "files": {}
                    }
                    if log_callback:
                        log_callback(f"Error processing {ticker}: {str(e)}")
                finally:
                    # Clean up engine resources
                    if hasattr(engine, 'cleanup'):
                        await engine.cleanup()
                    elif hasattr(engine, 'close'):
                        await engine.close()
                
                if log_callback:
                    # Safe access to nested dictionary values
                    return_value = 0.0
                    logger.debug(f"ticker_results type: {type(ticker_results)}")
                    logger.debug(f"ticker_results value: {ticker_results}")
                    if isinstance(ticker_results, dict) and 'metrics' in ticker_results:
                        metrics = ticker_results['metrics']
                        if isinstance(metrics, dict) and 'total_return' in metrics:
                            return_value = metrics['total_return']
                    log_callback(f"Completed {ticker}: Return={return_value:.2f}%")
                
                # Update progress
                progress = ((idx + 1) / total_tickers) * 100
                if progress_callback:
                    progress_callback(progress, f"Completed {ticker}", ticker)
            
            # Final log
            if log_callback:
                log_callback("Backtest2 completed successfully")
                
        except Exception as e:
            logger.error(f"Backtest2 failed: {str(e)}")
            logger.error(traceback.format_exc())
            if log_callback:
                log_callback(f"Error: {str(e)}")
            raise
            
        finally:
            self.is_running = False
            self.engine = None
            
        logger.debug(f"Final results type: {type(results)}")
        logger.debug(f"Final results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
        for ticker, result in results.items():
            logger.debug(f"{ticker} result type: {type(result)}")
        return results
    
    def run_backtest(self, config: Dict[str, Any], 
                    progress_callback: Optional[Callable] = None,
                    log_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for run_backtest_async.
        """
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, we can't use run_until_complete
            logger.warning("Already inside an event loop. Consider using run_backtest_async directly.")
            # Create a new thread to run the async function
            import concurrent.futures
            import threading
            
            result = None
            exception = None
            
            def run_in_thread():
                nonlocal result, exception
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result = new_loop.run_until_complete(
                        self.run_backtest_async(config, progress_callback, log_callback)
                    )
                except Exception as e:
                    exception = e
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return result
            
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(
                    self.run_backtest_async(config, progress_callback, log_callback)
                )
            finally:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(loop) if hasattr(asyncio, 'all_tasks') else asyncio.Task.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Run event loop until all tasks are cancelled
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Close the loop
                loop.close()
    
    def stop_backtest(self):
        """Stop the running backtest."""
        self.should_stop = True
        if self.engine:
            self.engine.is_running = False
    
    def _create_backtest_config(self, webui_config: Dict[str, Any]) -> BacktestConfig:
        """Convert WebUI configuration to Backtest2Config."""
        # Time range
        start_date = datetime.strptime(webui_config.get("start_date", "2024-01-01"), "%Y-%m-%d")
        end_date = datetime.strptime(webui_config.get("end_date", "2024-12-31"), "%Y-%m-%d")
        time_range = TimeRange(start=start_date, end=end_date)
        
        # LLM configuration with safe dictionary access
        agent_config_dict = webui_config.get("agent_config", {})
        if not isinstance(agent_config_dict, dict):
            agent_config_dict = {}
            
        llm_provider = agent_config_dict.get("llm_provider", "openai")
        deep_model = agent_config_dict.get("deep_model", None)
        fast_model = agent_config_dict.get("fast_model", None)
        
        llm_config = LLMConfig(
            deep_think_model="mock" if webui_config.get("use_mock", False) else (deep_model or self._get_deep_model(llm_provider)),
            quick_think_model="mock" if webui_config.get("use_mock", False) else (fast_model or self._get_quick_model(llm_provider)),
            temperature=webui_config.get("temperature", 0.7),
            max_tokens=webui_config.get("max_tokens", 2000)
        )
        
        # Agent configuration
        agent_config = AgentConfig(
            max_debate_rounds=agent_config_dict.get("max_debate_rounds", 1),
            max_risk_discuss_rounds=agent_config_dict.get("max_risk_rounds", 1),
            llm_config=llm_config,
            use_japanese_prompts=webui_config.get("use_japanese", False),
            enable_memory=webui_config.get("enable_memory", True)
        )
        
        # Data configuration
        data_config = DataConfig(
            primary_source="YahooFinance",  # For minimal version
            fallback_sources=["FinnHub"],
            cache_enabled=not agent_config_dict.get("online_tools", False),
            force_refresh=webui_config.get("force_refresh", False)
        )
        
        # Risk configuration
        risk_config = RiskConfig(
            position_limits={
                RiskProfile.AGGRESSIVE: webui_config.get("aggressive_limit", 0.3),
                RiskProfile.NEUTRAL: webui_config.get("neutral_limit", 0.2),
                RiskProfile.CONSERVATIVE: webui_config.get("conservative_limit", 0.1)
            },
            stop_loss=webui_config.get("stop_loss", 0.1),
            take_profit=webui_config.get("take_profit", 0.2),
            max_positions=webui_config.get("max_positions", 5)
        )
        
        # Reflection configuration
        reflection_config = ReflectionConfig(
            enabled=webui_config.get("enable_reflection", True),
            immediate_on_trade=webui_config.get("immediate_reflection", True),
            daily_enabled=True,
            weekly_enabled=True
        )
        
        # Result directory
        result_dir = Path("results") / f"backtest2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Debug: Check BacktestConfig class
        logger.info(f"Creating BacktestConfig - class type: {type(BacktestConfig)}")
        logger.info(f"BacktestConfig module: {BacktestConfig.__module__}")
        logger.info(f"BacktestConfig MRO: {BacktestConfig.__mro__}")
        
        # Check if it's a dataclass
        import dataclasses
        logger.info(f"Is dataclass: {dataclasses.is_dataclass(BacktestConfig)}")
        if hasattr(BacktestConfig, '__dataclass_fields__'):
            logger.info(f"Dataclass fields: {list(BacktestConfig.__dataclass_fields__.keys())}")
        
        # Check if random_seed is in the class
        logger.info(f"Has random_seed attr: {hasattr(BacktestConfig, 'random_seed')}")
        logger.info(f"BacktestConfig.__init__ signature: {BacktestConfig.__init__.__annotations__ if hasattr(BacktestConfig.__init__, '__annotations__') else 'No annotations'}")
        
        # Create BacktestConfig - build kwargs dynamically based on available fields
        config_kwargs = {
            "name": "webui_backtest",
            "symbols": webui_config.get("tickers", ["AAPL"]),
            "time_range": time_range,
            "initial_capital": webui_config.get("initial_capital", 10000.0),
            "max_positions": risk_config.max_positions,
            "position_limits": risk_config.position_limits,
            "llm_config": llm_config,
            "data_sources": ["yahoo", "finnhub"],
            "result_dir": result_dir,
            "slippage": webui_config.get("slippage", 0.001),
            "commission": webui_config.get("commission", 0.001),
            "risk_free_rate": webui_config.get("risk_free_rate", 0.02),
            "agent_config": agent_config,
            "data_config": data_config,
            "risk_config": risk_config,
            "benchmark": "SPY",
            "save_results": True,
            "log_level": "INFO"
        }
        
        # Add optional fields if they exist in the dataclass
        if hasattr(BacktestConfig, '__dataclass_fields__'):
            fields = BacktestConfig.__dataclass_fields__.keys()
            if 'random_seed' in fields:
                config_kwargs['random_seed'] = webui_config.get("random_seed", 42)
            if 'reflection_config' in fields:
                config_kwargs['reflection_config'] = reflection_config
        
        try:
            config = BacktestConfig(**config_kwargs)
        except TypeError as e:
            logger.warning(f"Failed to create BacktestConfig: {e}")
            logger.warning("Retrying with minimal required fields")
            # Try with only the most essential fields
            minimal_kwargs = {
                "name": "webui_backtest",
                "symbols": webui_config.get("tickers", ["AAPL"]),
                "time_range": time_range,
                "initial_capital": webui_config.get("initial_capital", 10000.0),
                "llm_config": llm_config,
            }
            
            # Add only fields that exist in the dataclass
            if hasattr(BacktestConfig, '__dataclass_fields__'):
                available_fields = set(BacktestConfig.__dataclass_fields__.keys())
                for field, value in config_kwargs.items():
                    if field in available_fields and field not in minimal_kwargs:
                        minimal_kwargs[field] = value
            
            config = BacktestConfig(**minimal_kwargs)
        
        return config
    
    def _update_config_for_ticker(self, config: BacktestConfig, ticker: str) -> BacktestConfig:
        """Update config for a single ticker."""
        # Build config kwargs from existing config
        config_kwargs = {}
        
        # Get all attributes from the original config
        if hasattr(BacktestConfig, '__dataclass_fields__'):
            for field_name in BacktestConfig.__dataclass_fields__.keys():
                if hasattr(config, field_name):
                    value = getattr(config, field_name)
                    if field_name == 'symbols':
                        config_kwargs[field_name] = [ticker]
                    elif field_name == 'result_dir' and value:
                        config_kwargs[field_name] = Path(value) / ticker
                    else:
                        config_kwargs[field_name] = value
        else:
            # Fallback if dataclass fields not available
            config_kwargs = {
                "name": config.name,
                "symbols": [ticker],
                "time_range": config.time_range,
                "initial_capital": config.initial_capital,
                "llm_config": config.llm_config,
            }
            
            # Copy all other attributes that exist
            optional_attrs = [
                'max_positions', 'position_limits', 'data_sources', 'reflection_config',
                'slippage', 'commission', 'risk_free_rate', 'agent_config',
                'data_config', 'risk_config', 'benchmark', 'save_results', 'log_level'
            ]
            
            for attr in optional_attrs:
                if hasattr(config, attr):
                    config_kwargs[attr] = getattr(config, attr)
            
            if hasattr(config, 'result_dir') and config.result_dir:
                config_kwargs['result_dir'] = Path(config.result_dir) / ticker
        
        try:
            new_config = BacktestConfig(**config_kwargs)
        except TypeError as e:
            logger.error(f"Failed to create ticker-specific BacktestConfig: {e}")
            raise
        
        return new_config
    
    def _get_deep_model(self, provider: str) -> str:
        """Get deep thinking model based on provider."""
        models = {
            "openai": "o1-preview",
            "anthropic": "claude-3-opus",
            "google": "gemini-ultra",
            "ollama": "llama2:70b"
        }
        return models.get(provider, "o1-preview")
    
    def _get_quick_model(self, provider: str) -> str:
        """Get quick thinking model based on provider."""
        models = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-sonnet",
            "google": "gemini-pro",
            "ollama": "llama2:7b"
        }
        return models.get(provider, "gpt-4o")
    
    def _process_results(self, result: 'BacktestResult', ticker: str, config: 'BacktestConfig') -> Dict[str, Any]:
        """Process backtest results for WebUI display with enhanced null safety."""
        # Initialize default metrics
        metrics = {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "calmar_ratio": 0.0
        }
        
        # Safely extract metrics if available
        if hasattr(result, 'metrics') and result.metrics is not None:
            m = result.metrics
            # Map of metric names to possible attribute names
            metric_mapping = {
                "total_return": ["total_return", "totalReturn"],
                "annualized_return": ["annualized_return", "annualizedReturn"],
                "sharpe_ratio": ["sharpe_ratio", "sharpeRatio"],
                "sortino_ratio": ["sortino_ratio", "sortinoRatio"],
                "max_drawdown": ["max_drawdown", "maxDrawdown"],
                "volatility": ["volatility"],
                "win_rate": ["win_rate", "winRate"],
                "total_trades": ["total_trades", "totalTrades"],
                "winning_trades": ["winning_trades", "winningTrades"],
                "losing_trades": ["losing_trades", "losingTrades"],
                "avg_win": ["average_win", "avg_win", "avgWin"],
                "avg_loss": ["average_loss", "avg_loss", "avgLoss"],
                "profit_factor": ["profit_factor", "profitFactor"],
                "calmar_ratio": ["calmar_ratio", "calmarRatio"]
            }
            
            for metric_key, attr_names in metric_mapping.items():
                for attr_name in attr_names:
                    if hasattr(m, attr_name):
                        value = getattr(m, attr_name, metrics[metric_key])
                        # Validate numeric values
                        if isinstance(value, (int, float)) and not (math.isnan(value) or math.isinf(value)):
                            metrics[metric_key] = value
                            break
        
        # Prepare file paths
        files = {}
        # Check if config has results_path or result_dir
        result_path = None
        if hasattr(config, 'results_path') and config.results_path:
            try:
                result_path = Path(config.results_path) / ticker
            except (TypeError, ValueError):
                logger.warning(f"Invalid results_path: {config.results_path}")
        elif hasattr(config, 'result_dir') and config.result_dir:
            try:
                result_path = Path(config.result_dir) / ticker
            except (TypeError, ValueError):
                logger.warning(f"Invalid result_dir: {config.result_dir}")
        elif hasattr(result, 'result_path') and result.result_path:
            try:
                result_path = Path(result.result_path)
            except (TypeError, ValueError):
                logger.warning(f"Invalid result_path: {result.result_path}")
            
        if result_path and result_path.exists():
            result_dir = result_path
            
            # Metrics JSON
            metrics_file = result_dir / "metrics.json"
            if metrics_file.exists():
                files["metrics_json"] = str(metrics_file)
            
            # Trades CSV
            trades_file = result_dir / "trades.csv"
            if trades_file.exists():
                files["trades_csv"] = str(trades_file)
            
            # Report PDF (if generated)
            report_file = result_dir / "report.pdf"
            if report_file.exists():
                files["report_pdf"] = str(report_file)
        
        # Prepare charts (placeholder for now)
        charts = {}
        generate_plots = getattr(config, 'generate_plots', True) if hasattr(config, 'generate_plots') else True
        if generate_plots:
            # Charts would be generated here
            # For now, we'll use the result directory
            if result_path and result_path.exists():
                chart_dir = result_path / "charts"
                if chart_dir.exists():
                    for chart_file in chart_dir.glob("*.png"):
                        chart_name = chart_file.stem
                        charts[chart_name] = str(chart_file)
        
        # Agent performance summary
        agent_performance = {}
        if hasattr(result, 'agent_performance') and result.agent_performance:
            agent_performance = result.agent_performance
            logger.info(f"Result agent_performance type: {type(agent_performance)}")
            logger.info(f"Result agent_performance content: {agent_performance}")
        
        return {
            "ticker": ticker,
            "metrics": metrics,
            "initial_capital": getattr(config, 'initial_capital', 10000.0),
            "final_value": getattr(result.metrics, 'final_value', 0.0) if hasattr(result, 'metrics') and result.metrics else 0.0,
            "files": files,
            "charts": charts,
            "agent_performance": agent_performance,
            "trade_count": getattr(result.metrics, 'total_trades', 0) if hasattr(result, 'metrics') and result.metrics else 0,
            "start_date": config.time_range.start if hasattr(config, 'time_range') and config.time_range else getattr(config, 'start_date', None),
            "end_date": config.time_range.end if hasattr(config, 'time_range') and config.time_range else getattr(config, 'end_date', None)
        }