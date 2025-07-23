# Backtest2 - Advanced Multi-Agent Trading Backtest Framework

## Overview

Backtest2 is an advanced backtesting framework that implements the methodology from the paper "TradingAgents: Multi-Agents LLM Financial Trading Framework" (Xiao et al., 2025). It features multi-agent coordination, learning capabilities, and strict temporal consistency.

## Current Implementation Status

### ✅ Completed Components

1. **Core Infrastructure**
   - Project structure with modular design
   - Configuration system (`BacktestConfig`, `AgentConfig`, `RiskConfig`, etc.)
   - Type definitions for all major entities
   - Basic imports and module structure

2. **BacktestEngine (Core)**
   - Main simulation loop
   - Time management
   - Transaction execution
   - Results calculation framework

3. **AgentOrchestrator**
   - 6-phase decision flow implementation
   - Agent coordination logic
   - Decision context management
   - Phase result storage

4. **Data Management (Partial)**
   - DataManager with temporal consistency checks
   - Cache management structure
   - Multi-source data fetching logic
   - Look-ahead bias prevention

### 🚧 In Progress

1. **Agent Implementations**
   - Base agent classes defined
   - Need individual agent implementations:
     - Market Analyst
     - News Analyst
     - Social Media Analyst
     - Fundamentals Analyst
     - Bull/Bear Researchers
     - Risk Debators
     - Managers

2. **Position Management**
   - Risk-based position sizing logic
   - Portfolio state tracking
   - Transaction execution

3. **Memory & Reflection**
   - Memory store structure
   - Reflection trigger system
   - Learning mechanisms

### 📋 TODO

1. **Complete Agent Implementations**
2. **Implement Position Manager**
3. **Complete Memory System**
4. **Add Data Source Connectors**
5. **Implement Metrics Calculator**
6. **Create Visualization Tools**
7. **Add Comprehensive Tests**

## Architecture

```
backtest2/
├── core/           # Core engine and types
├── agents/         # Multi-agent system
├── data/           # Data management
├── memory/         # Memory and learning
├── risk/           # Risk management
├── utils/          # Utilities
└── tests/          # Test suite
```

## Key Features

1. **Multi-Agent Decision Making**
   - 6-phase decision process
   - Specialized agents for different analyses
   - Debate and consensus mechanisms

2. **Temporal Consistency**
   - Strict look-ahead bias prevention
   - Deterministic execution
   - Complete audit trail

3. **Advanced Risk Management**
   - Dynamic position sizing
   - Multi-level risk assessment
   - Stop-loss and take-profit management

4. **Learning Capabilities**
   - Agent-specific memory
   - System-wide learning
   - Performance-based reflection

## Usage Example

```python
from backtest2 import BacktestConfig
from datetime import datetime

# Create configuration
config = BacktestConfig(
    initial_capital=10000.0,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    symbols=['AAPL', 'GOOGL', 'MSFT']
)

# Validate configuration
config.validate()

# Note: Full backtest execution requires completing the implementation
# engine = BacktestEngine(config)
# results = await engine.run()
```

## Testing

Basic functionality tests are available:

```bash
python test_backtest2_simple.py
```

## Dependencies

- Python 3.8+
- asyncio for asynchronous operations
- Additional dependencies (pandas, numpy) required for full functionality

## Development Status

This is an active development. The framework structure is complete, but several components need implementation to achieve full functionality as described in the paper.

## Contributing

When implementing new components:
1. Follow the established type system
2. Maintain temporal consistency
3. Add appropriate logging
4. Include unit tests
5. Update this README with progress