"""
E2E test for Backtest2 WebUI integration
Tests the complete flow from configuration to results
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Dict, Any, Optional

# Add project paths
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from webui.backend.backtest2_wrapper import Backtest2Wrapper
from backtest2.core.config import BacktestConfig, TimeRange, LLMConfig

class Backtest2E2ETest:
    """End-to-end test for Backtest2"""
    
    def __init__(self):
        self.wrapper = Backtest2Wrapper()
        self.test_results = []
        self.logs = []
        
    def log(self, message: str):
        """Log test progress"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.logs.append(log_entry)
        
    def progress_callback(self, progress: float, status: str, ticker: str = ""):
        """Progress callback for testing"""
        self.log(f"Progress: {progress:.1f}% - {status} - {ticker}")
        
    def log_callback(self, message: str):
        """Log callback for testing"""
        self.log(f"Engine: {message}")
        
    async def test_minimal_backtest(self) -> Dict[str, Any]:
        """Test minimal configuration"""
        self.log("=== Test 1: Minimal Backtest ===")
        
        config = {
            "tickers": ["AAPL"],
            "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "initial_capital": 10000.0,
            "slippage": 0.001,
            "commission": 0.001,
            "risk_free_rate": 0.02,
            "aggressive_limit": 0.3,
            "neutral_limit": 0.2,
            "conservative_limit": 0.1,
            "stop_loss": 0.1,
            "take_profit": 0.2,
            "max_positions": 5,
            "agent_config": {
                "llm_provider": "openai",
                "temperature": 0.7,
                "max_tokens": 2000,
                "max_debate_rounds": 1,
                "max_risk_rounds": 1,
                "use_japanese": False,
                "online_tools": False
            },
            "enable_memory": True,
            "enable_reflection": True,
            "immediate_reflection": True,
            "force_refresh": False,
            "generate_plots": True,
            "save_trades": True,
            "debug": True
        }
        
        try:
            start_time = time.time()
            results = await self.wrapper.run_backtest_async(
                config=config,
                progress_callback=self.progress_callback,
                log_callback=self.log_callback
            )
            execution_time = time.time() - start_time
            
            # Validate results
            assert "AAPL" in results, "AAPL results missing"
            assert "metrics" in results["AAPL"], "Metrics missing"
            
            metrics = results["AAPL"]["metrics"]
            self.log(f"Total Return: {metrics['total_return']:.2f}%")
            self.log(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            self.log(f"Total Trades: {metrics['total_trades']}")
            self.log(f"Execution Time: {execution_time:.2f}s")
            
            return {
                "status": "PASSED",
                "execution_time": execution_time,
                "metrics": metrics
            }
            
        except Exception as e:
            self.log(f"Test failed: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_multi_ticker_backtest(self) -> Dict[str, Any]:
        """Test multiple tickers"""
        self.log("\n=== Test 2: Multi-Ticker Backtest ===")
        
        config = {
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "start_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "initial_capital": 50000.0,
            "slippage": 0.001,
            "commission": 0.001,
            "risk_free_rate": 0.02,
            "aggressive_limit": 0.4,
            "neutral_limit": 0.25,
            "conservative_limit": 0.15,
            "stop_loss": 0.08,
            "take_profit": 0.25,
            "max_positions": 10,
            "agent_config": {
                "llm_provider": "openai",
                "temperature": 0.7,
                "max_tokens": 2000,
                "max_debate_rounds": 2,
                "max_risk_rounds": 1,
                "use_japanese": False,
                "online_tools": False
            },
            "enable_memory": True,
            "enable_reflection": True,
            "immediate_reflection": False,
            "force_refresh": False,
            "generate_plots": False,
            "save_trades": True,
            "debug": False
        }
        
        try:
            start_time = time.time()
            results = await self.wrapper.run_backtest_async(
                config=config,
                progress_callback=self.progress_callback,
                log_callback=self.log_callback
            )
            execution_time = time.time() - start_time
            
            # Validate results for all tickers
            for ticker in ["AAPL", "MSFT", "GOOGL"]:
                assert ticker in results, f"{ticker} results missing"
                metrics = results[ticker]["metrics"]
                self.log(f"{ticker} - Return: {metrics['total_return']:.2f}%, Sharpe: {metrics['sharpe_ratio']:.2f}")
            
            # Calculate portfolio metrics
            total_return = sum(r["metrics"]["total_return"] for r in results.values()) / len(results)
            self.log(f"Portfolio Average Return: {total_return:.2f}%")
            self.log(f"Execution Time: {execution_time:.2f}s")
            
            return {
                "status": "PASSED",
                "execution_time": execution_time,
                "portfolio_return": total_return,
                "ticker_count": len(results)
            }
            
        except Exception as e:
            self.log(f"Test failed: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_risk_profiles(self) -> Dict[str, Any]:
        """Test different risk profiles"""
        self.log("\n=== Test 3: Risk Profiles ===")
        
        base_config = {
            "tickers": ["SPY"],
            "start_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "initial_capital": 25000.0,
            "slippage": 0.001,
            "commission": 0.001,
            "risk_free_rate": 0.02,
            "stop_loss": 0.1,
            "take_profit": 0.2,
            "max_positions": 5,
            "agent_config": {
                "llm_provider": "openai",
                "temperature": 0.7,
                "max_tokens": 1500,
                "max_debate_rounds": 1,
                "max_risk_rounds": 1,
                "use_japanese": False,
                "online_tools": False
            },
            "enable_memory": False,
            "enable_reflection": False,
            "immediate_reflection": False,
            "force_refresh": False,
            "generate_plots": False,
            "save_trades": False,
            "debug": False
        }
        
        risk_profiles = [
            {
                "name": "Conservative",
                "aggressive_limit": 0.1,
                "neutral_limit": 0.05,
                "conservative_limit": 0.02
            },
            {
                "name": "Neutral",
                "aggressive_limit": 0.3,
                "neutral_limit": 0.2,
                "conservative_limit": 0.1
            },
            {
                "name": "Aggressive",
                "aggressive_limit": 0.6,
                "neutral_limit": 0.4,
                "conservative_limit": 0.2
            }
        ]
        
        profile_results = {}
        
        for profile in risk_profiles:
            self.log(f"\nTesting {profile['name']} profile...")
            config = base_config.copy()
            config.update(profile)
            
            try:
                results = await self.wrapper.run_backtest_async(
                    config=config,
                    progress_callback=self.progress_callback,
                    log_callback=self.log_callback
                )
                
                metrics = results["SPY"]["metrics"]
                profile_results[profile["name"]] = {
                    "return": metrics["total_return"],
                    "sharpe": metrics["sharpe_ratio"],
                    "max_drawdown": metrics["max_drawdown"],
                    "trades": metrics["total_trades"]
                }
                
                self.log(f"{profile['name']} - Return: {metrics['total_return']:.2f}%, Trades: {metrics['total_trades']}")
                
            except Exception as e:
                self.log(f"{profile['name']} test failed: {str(e)}")
                profile_results[profile["name"]] = {"error": str(e)}
        
        # Analyze results
        successful_profiles = [p for p in profile_results if "error" not in profile_results[p]]
        
        return {
            "status": "PASSED" if len(successful_profiles) == 3 else "FAILED",
            "profiles_tested": len(risk_profiles),
            "profiles_passed": len(successful_profiles),
            "results": profile_results
        }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling scenarios"""
        self.log("\n=== Test 4: Error Handling ===")
        
        error_scenarios = [
            {
                "name": "Invalid ticker",
                "config": {
                    "tickers": ["INVALID_TICKER_12345"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                }
            },
            {
                "name": "Invalid date range",
                "config": {
                    "tickers": ["AAPL"],
                    "start_date": "2024-01-31",
                    "end_date": "2024-01-01"  # End before start
                }
            },
            {
                "name": "Zero capital",
                "config": {
                    "tickers": ["AAPL"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "initial_capital": 0
                }
            }
        ]
        
        handled_errors = 0
        
        for scenario in error_scenarios:
            self.log(f"\nTesting: {scenario['name']}")
            
            # Create full config
            config = {
                "tickers": ["AAPL"],
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "initial_capital": 10000.0,
                "slippage": 0.001,
                "commission": 0.001,
                "risk_free_rate": 0.02,
                "aggressive_limit": 0.3,
                "neutral_limit": 0.2,
                "conservative_limit": 0.1,
                "stop_loss": 0.1,
                "take_profit": 0.2,
                "max_positions": 5,
                "agent_config": {
                    "llm_provider": "openai",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "max_debate_rounds": 1,
                    "max_risk_rounds": 1,
                    "use_japanese": False,
                    "online_tools": False
                },
                "enable_memory": False,
                "enable_reflection": False,
                "immediate_reflection": False,
                "force_refresh": False,
                "generate_plots": False,
                "save_trades": False,
                "debug": False
            }
            
            # Update with error scenario
            config.update(scenario["config"])
            
            try:
                results = await self.wrapper.run_backtest_async(
                    config=config,
                    progress_callback=self.progress_callback,
                    log_callback=self.log_callback
                )
                self.log(f"Expected error but got results: {results}")
                
            except Exception as e:
                self.log(f"Error handled correctly: {str(e)}")
                handled_errors += 1
        
        return {
            "status": "PASSED" if handled_errors > 0 else "FAILED",
            "scenarios_tested": len(error_scenarios),
            "errors_handled": handled_errors
        }
    
    async def test_performance_benchmark(self) -> Dict[str, Any]:
        """Test performance with different configurations"""
        self.log("\n=== Test 5: Performance Benchmark ===")
        
        benchmarks = [
            {
                "name": "Small (1 ticker, 30 days)",
                "tickers": ["AAPL"],
                "days": 30
            },
            {
                "name": "Medium (3 tickers, 60 days)",
                "tickers": ["AAPL", "MSFT", "GOOGL"],
                "days": 60
            },
            {
                "name": "Large (5 tickers, 90 days)",
                "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
                "days": 90
            }
        ]
        
        benchmark_results = {}
        
        for benchmark in benchmarks:
            self.log(f"\nRunning benchmark: {benchmark['name']}")
            
            config = {
                "tickers": benchmark["tickers"],
                "start_date": (datetime.now() - timedelta(days=benchmark["days"])).strftime("%Y-%m-%d"),
                "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "initial_capital": 100000.0,
                "slippage": 0.001,
                "commission": 0.001,
                "risk_free_rate": 0.02,
                "aggressive_limit": 0.3,
                "neutral_limit": 0.2,
                "conservative_limit": 0.1,
                "stop_loss": 0.1,
                "take_profit": 0.2,
                "max_positions": 10,
                "agent_config": {
                    "llm_provider": "openai",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "max_debate_rounds": 1,
                    "max_risk_rounds": 1,
                    "use_japanese": False,
                    "online_tools": False
                },
                "enable_memory": False,
                "enable_reflection": False,
                "immediate_reflection": False,
                "force_refresh": False,
                "generate_plots": False,
                "save_trades": False,
                "debug": False
            }
            
            try:
                start_time = time.time()
                results = await self.wrapper.run_backtest_async(
                    config=config,
                    progress_callback=self.progress_callback,
                    log_callback=self.log_callback
                )
                execution_time = time.time() - start_time
                
                # Calculate metrics
                total_decisions = benchmark["days"] * len(benchmark["tickers"])
                time_per_decision = execution_time / total_decisions
                
                benchmark_results[benchmark["name"]] = {
                    "execution_time": execution_time,
                    "total_decisions": total_decisions,
                    "time_per_decision": time_per_decision,
                    "tickers_processed": len(results)
                }
                
                self.log(f"Completed in {execution_time:.2f}s ({time_per_decision:.2f}s per decision)")
                
            except Exception as e:
                self.log(f"Benchmark failed: {str(e)}")
                benchmark_results[benchmark["name"]] = {"error": str(e)}
        
        return {
            "status": "PASSED" if len(benchmark_results) == 3 else "FAILED",
            "benchmarks": benchmark_results
        }
    
    async def run_all_tests(self):
        """Run all E2E tests"""
        print("=" * 60)
        print("BACKTEST2 E2E TEST SUITE")
        print("=" * 60)
        
        test_methods = [
            self.test_minimal_backtest,
            self.test_multi_ticker_backtest,
            self.test_risk_profiles,
            self.test_error_handling,
            self.test_performance_benchmark
        ]
        
        all_results = {}
        passed_tests = 0
        
        for test_method in test_methods:
            test_name = test_method.__name__
            try:
                result = await test_method()
                all_results[test_name] = result
                if result["status"] == "PASSED":
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                all_results[test_name] = {"status": "ERROR", "error": str(e)}
        
        # Summary
        print("\n" + "=" * 60)
        print(f"TEST SUMMARY: {passed_tests}/{len(test_methods)} tests passed")
        print("=" * 60)
        
        # Save results
        results_file = Path("tests/e2e/backtest2_e2e_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "tests_run": len(test_methods),
                "tests_passed": passed_tests,
                "results": all_results,
                "logs": self.logs
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        return passed_tests == len(test_methods)


async def main():
    """Main test runner"""
    tester = Backtest2E2ETest()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)