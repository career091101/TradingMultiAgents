#!/usr/bin/env python3
"""
Check LLM configuration
"""

import sys
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from backtest2.core.config import BacktestConfig, LLMConfig, TimeRange

# Test configuration
config = BacktestConfig(
    symbols=["AAPL"],
    time_range=TimeRange(
        start=datetime.now() - timedelta(days=30),
        end=datetime.now() - timedelta(days=1)
    ),
    initial_capital=100000,
    llm_config=LLMConfig(
        deep_think_model="o3-2025-04-16",
        quick_think_model="o4-mini-2025-04-16",
        temperature=0.7,
        max_tokens=2000
    )
)

print(f"LLM Config: {config.llm_config}")
print(f"Deep model: {config.llm_config.deep_think_model}")
print(f"Quick model: {config.llm_config.quick_think_model}")

# Check how orchestrator determines mock mode
from backtest2.agents.orchestrator import AgentOrchestrator
from backtest2.memory import MemoryStore

memory_store = MemoryStore()
orchestrator = AgentOrchestrator(config, memory_store)

print(f"\nChecking orchestrator...")
print(f"Config type: {type(orchestrator.config)}")
print(f"LLM config: {orchestrator.config.llm_config}")
print(f"Deep model from config: {orchestrator.config.llm_config.deep_think_model}")

# Check mock detection
use_mock = orchestrator.config.llm_config.deep_think_model == "mock"
print(f"\nMock detection: deep_think_model='{orchestrator.config.llm_config.deep_think_model}' == 'mock' => {use_mock}")

# Check for o3 detection
if "o3" in orchestrator.config.llm_config.deep_think_model.lower():
    print("Model contains 'o3' - should NOT be mock mode!")