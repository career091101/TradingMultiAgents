"""
TradingAgents package - Multi-Agent LLM Financial Trading Framework.

This package provides a comprehensive framework for creating and managing
multiple AI agents that collaborate to analyze financial markets and make
trading decisions.
"""

__version__ = "0.1.0"

# Import key modules for easier access
from . import agents
from . import dataflows
from . import graph

__all__ = ["agents", "dataflows", "graph"]