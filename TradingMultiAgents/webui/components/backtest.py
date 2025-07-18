"""
Backtest page component for the WebUI.
Provides interface for running backtests using the TradingAgents framework.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os
import json
from typing import Dict, Any, List, Optional, Tuple

from ..utils.state import SessionState, UIHelpers
from ..backend.backtest_wrapper import BacktestWrapper


class BacktestPage:
    """Backtest page component."""
    
    def __init__(self, session_state: SessionState):
        self.state = session_state
        self.ui = UIHelpers()
        self.backtest_wrapper = BacktestWrapper()
    
    def render(self):
        """Render the backtest page."""
        st.title("📊 Backtest Trading Strategy")
        
        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["⚙️ Settings", "▶️ Run Backtest", "📈 Results"])
        
        with tab1:
            self._render_settings()
        
        with tab2:
            self._render_execution()
        
        with tab3:
            self._render_results()
    
    def _render_settings(self):
        """Render backtest settings section."""
        st.markdown("### Backtest Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Settings")
            
            # Ticker selection (single or multiple)
            ticker_input = st.text_input(
                "Ticker(s)",
                value=self.state.get("backtest_tickers", "AAPL"),
                help="Enter one or more tickers separated by commas (e.g., AAPL, MSFT, GOOGL)"
            )
            tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
            self.state.set("backtest_tickers", ",".join(tickers))
            
            # Date range selection
            st.markdown("**Date Range**")
            date_col1, date_col2 = st.columns(2)
            
            with date_col1:
                start_date = st.date_input(
                    "Start Date",
                    value=self.state.get("backtest_start_date", datetime.now() - timedelta(days=365)),
                    max_value=datetime.now() - timedelta(days=1)
                )
                self.state.set("backtest_start_date", start_date)
            
            with date_col2:
                end_date = st.date_input(
                    "End Date",
                    value=self.state.get("backtest_end_date", datetime.now() - timedelta(days=1)),
                    min_value=start_date,
                    max_value=datetime.now()
                )
                self.state.set("backtest_end_date", end_date)
            
            # Initial capital
            initial_capital = st.number_input(
                "Initial Capital ($)",
                min_value=1000.0,
                max_value=10000000.0,
                value=self.state.get("backtest_capital", 10000.0),
                step=1000.0,
                format="%.2f"
            )
            self.state.set("backtest_capital", initial_capital)
        
        with col2:
            st.markdown("#### Trading Parameters")
            
            # Slippage
            slippage = st.slider(
                "Slippage (%)",
                min_value=0.0,
                max_value=1.0,
                value=self.state.get("backtest_slippage", 0.1),
                step=0.01,
                format="%.2f%%",
                help="Price slippage to simulate market impact"
            )
            self.state.set("backtest_slippage", slippage / 100)  # Convert to decimal
            
            # Risk-free rate
            risk_free_rate = st.slider(
                "Risk-Free Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=self.state.get("backtest_risk_free", 2.0),
                step=0.1,
                format="%.1f%%",
                help="Annual risk-free rate for Sharpe ratio calculation"
            )
            self.state.set("backtest_risk_free", risk_free_rate / 100)
            
            # Agent configuration options
            st.markdown("#### Agent Configuration")
            
            use_custom_config = st.checkbox(
                "Use Custom Agent Configuration",
                value=self.state.get("backtest_use_custom_config", False)
            )
            self.state.set("backtest_use_custom_config", use_custom_config)
            
            if use_custom_config:
                # LLM provider selection
                llm_provider = st.selectbox(
                    "LLM Provider",
                    options=["openai", "anthropic", "google", "ollama"],
                    index=0,
                    key="backtest_llm_provider"
                )
                
                # Debate rounds
                max_debate_rounds = st.number_input(
                    "Max Debate Rounds",
                    min_value=1,
                    max_value=5,
                    value=self.state.get("backtest_debate_rounds", 1),
                    help="Number of rounds for agent debates"
                )
                self.state.set("backtest_debate_rounds", max_debate_rounds)
                
                # Online tools
                online_tools = st.checkbox(
                    "Use Online Tools",
                    value=self.state.get("backtest_online_tools", False),
                    help="Use real-time data (less reproducible) vs cached data"
                )
                self.state.set("backtest_online_tools", online_tools)
        
        # Advanced options
        with st.expander("Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                save_trades = st.checkbox(
                    "Save Trade Log",
                    value=self.state.get("backtest_save_trades", True),
                    help="Export detailed trade history to CSV"
                )
                self.state.set("backtest_save_trades", save_trades)
                
                generate_plots = st.checkbox(
                    "Generate Plots",
                    value=self.state.get("backtest_generate_plots", True),
                    help="Create visualization charts"
                )
                self.state.set("backtest_generate_plots", generate_plots)
            
            with col2:
                debug_mode = st.checkbox(
                    "Debug Mode",
                    value=self.state.get("backtest_debug", False),
                    help="Enable verbose logging"
                )
                self.state.set("backtest_debug", debug_mode)
        
        # Summary of settings
        st.markdown("---")
        st.markdown("### Configuration Summary")
        
        config_summary = {
            "Tickers": tickers,
            "Period": f"{start_date} to {end_date}",
            "Initial Capital": f"${initial_capital:,.2f}",
            "Slippage": f"{slippage:.2f}%",
            "Risk-Free Rate": f"{risk_free_rate:.1f}%"
        }
        
        if use_custom_config:
            config_summary.update({
                "LLM Provider": llm_provider,
                "Debate Rounds": max_debate_rounds,
                "Online Tools": "Yes" if online_tools else "No"
            })
        
        for key, value in config_summary.items():
            st.write(f"**{key}:** {value}")
    
    def _render_execution(self):
        """Render backtest execution section."""
        st.markdown("### Run Backtest")
        
        # Check if settings are valid
        tickers = self.state.get("backtest_tickers", "").split(",")
        tickers = [t.strip() for t in tickers if t.strip()]
        
        if not tickers:
            st.error("Please enter at least one ticker symbol in the Settings tab.")
            return
        
        # Display what will be tested
        st.info(f"Ready to backtest {len(tickers)} ticker(s): {', '.join(tickers)}")
        
        # Estimated time
        days_to_test = (self.state.get("backtest_end_date") - self.state.get("backtest_start_date")).days
        estimated_time = len(tickers) * days_to_test * 2  # Rough estimate: 2 seconds per day per ticker
        st.write(f"**Estimated time:** ~{estimated_time // 60} minutes")
        
        # Run button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Backtest", type="primary", use_container_width=True):
                self._run_backtest()
        
        # Progress and status
        if self.state.get("backtest_running", False):
            st.markdown("---")
            st.markdown("### Backtest Progress")
            
            # Progress bar
            progress = self.state.get("backtest_progress", 0.0)
            st.progress(progress)
            
            # Current status
            status = self.state.get("backtest_status", "Initializing...")
            st.write(f"**Status:** {status}")
            
            # Current ticker being processed
            current_ticker = self.state.get("backtest_current_ticker", "")
            if current_ticker:
                st.write(f"**Processing:** {current_ticker}")
            
            # Stop button
            if st.button("⏹️ Stop Backtest", type="secondary"):
                self.state.set("backtest_running", False)
                st.warning("Backtest stopped by user.")
        
        # Recent logs
        if self.state.get("backtest_logs"):
            with st.expander("Execution Logs", expanded=True):
                logs = self.state.get("backtest_logs", [])
                for log in logs[-10:]:  # Show last 10 log entries
                    st.text(log)
    
    def _run_backtest(self):
        """Execute the backtest."""
        self.state.set("backtest_running", True)
        self.state.set("backtest_progress", 0.0)
        self.state.set("backtest_logs", [])
        
        # Prepare configuration
        config = self._prepare_backtest_config()
        
        # Execute backtest through wrapper
        try:
            with st.spinner("Running backtest..."):
                results = self.backtest_wrapper.run_backtest(
                    config=config,
                    progress_callback=self._update_progress,
                    log_callback=self._update_logs
                )
            
            # Store results
            self.state.set("backtest_results", results)
            self.state.set("backtest_running", False)
            self.state.set("backtest_completed", True)
            
            st.success(f"Backtest completed successfully! View results in the Results tab.")
            
        except Exception as e:
            self.state.set("backtest_running", False)
            st.error(f"Backtest failed: {str(e)}")
    
    def _prepare_backtest_config(self) -> Dict[str, Any]:
        """Prepare configuration for backtest execution."""
        config = {
            "tickers": self.state.get("backtest_tickers", "AAPL").split(","),
            "start_date": self.state.get("backtest_start_date").strftime("%Y-%m-%d"),
            "end_date": self.state.get("backtest_end_date").strftime("%Y-%m-%d"),
            "initial_capital": self.state.get("backtest_capital", 10000.0),
            "slippage": self.state.get("backtest_slippage", 0.001),
            "risk_free_rate": self.state.get("backtest_risk_free", 0.02),
            "save_trades": self.state.get("backtest_save_trades", True),
            "generate_plots": self.state.get("backtest_generate_plots", True),
            "debug": self.state.get("backtest_debug", False)
        }
        
        # Add custom agent configuration if enabled
        if self.state.get("backtest_use_custom_config", False):
            config["agent_config"] = {
                "llm_provider": self.state.get("backtest_llm_provider", "openai"),
                "max_debate_rounds": self.state.get("backtest_debate_rounds", 1),
                "online_tools": self.state.get("backtest_online_tools", False)
            }
        
        return config
    
    def _update_progress(self, progress: float, status: str, current_ticker: str = ""):
        """Update progress callback."""
        self.state.set("backtest_progress", progress)
        self.state.set("backtest_status", status)
        if current_ticker:
            self.state.set("backtest_current_ticker", current_ticker)
    
    def _update_logs(self, log_entry: str):
        """Update logs callback."""
        logs = self.state.get("backtest_logs", [])
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {log_entry}")
        self.state.set("backtest_logs", logs)
    
    def _render_results(self):
        """Render backtest results section."""
        st.markdown("### Backtest Results")
        
        if not self.state.get("backtest_completed", False):
            st.info("No backtest results available. Run a backtest in the 'Run Backtest' tab.")
            return
        
        results = self.state.get("backtest_results", {})
        if not results:
            st.warning("No results data found.")
            return
        
        # Results for each ticker
        for ticker, result in results.items():
            with st.expander(f"📊 {ticker} Results", expanded=True):
                self._render_ticker_results(ticker, result)
        
        # Portfolio summary if multiple tickers
        if len(results) > 1:
            st.markdown("---")
            st.markdown("### Portfolio Summary")
            self._render_portfolio_summary(results)
    
    def _render_ticker_results(self, ticker: str, result: Dict[str, Any]):
        """Render results for a single ticker."""
        metrics = result.get("metrics", {})
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Return",
                f"{metrics.get('total_return', 0):.2f}%",
                delta=f"{metrics.get('total_return', 0):.2f}%"
            )
        
        with col2:
            st.metric(
                "Sharpe Ratio",
                f"{metrics.get('sharpe_ratio', 0):.2f}"
            )
        
        with col3:
            st.metric(
                "Max Drawdown",
                f"{metrics.get('max_drawdown', 0):.2f}%",
                delta=f"-{abs(metrics.get('max_drawdown', 0)):.2f}%"
            )
        
        with col4:
            st.metric(
                "Win Rate",
                f"{metrics.get('win_rate', 0):.1f}%"
            )
        
        # Detailed metrics
        with st.expander("Detailed Metrics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Returns:**")
                st.write(f"- Annualized Return: {metrics.get('annualized_return', 0):.2f}%")
                st.write(f"- Volatility: {metrics.get('volatility', 0):.2f}%")
                st.write(f"- Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
                st.write(f"- Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}")
            
            with col2:
                st.write("**Trading Statistics:**")
                st.write(f"- Total Trades: {metrics.get('total_trades', 0)}")
                st.write(f"- Winning Trades: {metrics.get('winning_trades', 0)}")
                st.write(f"- Losing Trades: {metrics.get('losing_trades', 0)}")
                st.write(f"- Avg Win: {metrics.get('avg_win', 0):.2f}%")
                st.write(f"- Avg Loss: {metrics.get('avg_loss', 0):.2f}%")
                st.write(f"- Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        
        # Charts
        if result.get("charts"):
            st.markdown("#### Performance Charts")
            
            # Equity curve
            if result["charts"].get("equity_curve"):
                st.image(result["charts"]["equity_curve"], caption="Equity Curve")
            
            # Price with signals
            if result["charts"].get("price_signals"):
                st.image(result["charts"]["price_signals"], caption="Price with Trading Signals")
            
            # Additional charts in columns
            col1, col2 = st.columns(2)
            
            with col1:
                if result["charts"].get("drawdown"):
                    st.image(result["charts"]["drawdown"], caption="Drawdown")
            
            with col2:
                if result["charts"].get("returns_distribution"):
                    st.image(result["charts"]["returns_distribution"], caption="Returns Distribution")
        
        # Download links
        if result.get("files"):
            st.markdown("#### Download Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if result["files"].get("metrics_json"):
                    with open(result["files"]["metrics_json"], "r") as f:
                        st.download_button(
                            "📊 Download Metrics (JSON)",
                            data=f.read(),
                            file_name=f"{ticker}_metrics.json",
                            mime="application/json"
                        )
            
            with col2:
                if result["files"].get("trades_csv"):
                    with open(result["files"]["trades_csv"], "r") as f:
                        st.download_button(
                            "📋 Download Trades (CSV)",
                            data=f.read(),
                            file_name=f"{ticker}_trades.csv",
                            mime="text/csv"
                        )
            
            with col3:
                if result["files"].get("report_pdf"):
                    with open(result["files"]["report_pdf"], "rb") as f:
                        st.download_button(
                            "📄 Download Report (PDF)",
                            data=f.read(),
                            file_name=f"{ticker}_backtest_report.pdf",
                            mime="application/pdf"
                        )
    
    def _render_portfolio_summary(self, results: Dict[str, Dict[str, Any]]):
        """Render portfolio-level summary."""
        # Calculate portfolio metrics
        total_initial = sum(r.get("initial_capital", 0) for r in results.values())
        total_final = sum(r.get("final_value", 0) for r in results.values())
        portfolio_return = ((total_final - total_initial) / total_initial * 100) if total_initial > 0 else 0
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Portfolio Return",
                f"{portfolio_return:.2f}%",
                delta=f"{portfolio_return:.2f}%"
            )
        
        with col2:
            st.metric(
                "Initial Capital",
                f"${total_initial:,.2f}"
            )
        
        with col3:
            st.metric(
                "Final Value",
                f"${total_final:,.2f}"
            )
        
        # Individual ticker performance
        st.markdown("#### Individual Performance")
        
        perf_data = []
        for ticker, result in results.items():
            metrics = result.get("metrics", {})
            perf_data.append({
                "Ticker": ticker,
                "Return (%)": metrics.get("total_return", 0),
                "Sharpe": metrics.get("sharpe_ratio", 0),
                "Max DD (%)": metrics.get("max_drawdown", 0),
                "Trades": metrics.get("total_trades", 0)
            })
        
        df = pd.DataFrame(perf_data)
        st.dataframe(df, use_container_width=True, hide_index=True)