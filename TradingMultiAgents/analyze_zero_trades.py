#!/usr/bin/env python3
"""
Analyze why backtest2 is reporting zero trades
"""

import os
import sys
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyze_zero_trades.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, '/Users/y-sato/TradingAgents2')

def analyze_agent_performance():
    """Analyze the agent performance calculation"""
    logger.info("=== Analyzing Agent Performance Calculation ===")
    
    # Check the engine._get_agent_performance method
    from backtest2.core.engine import BacktestEngine
    
    # The issue is in engine.py line 409-412:
    # return {
    #     "total_decisions": len(self.transactions),
    #     "memory_entries": len(self.memory_store.memories)
    # }
    
    logger.info("Found issue: total_decisions is calculated from len(self.transactions)")
    logger.info("This counts the number of executed transactions, not decisions made")
    logger.info("If all decisions are HOLD, transactions list will be empty, resulting in total_decisions=0")
    
    return True

def analyze_decision_flow():
    """Analyze the decision making flow"""
    logger.info("\n=== Analyzing Decision Making Flow ===")
    
    # From orchestrator.py, the flow is:
    # 1. make_decision() is called for each symbol/date
    # 2. 6-phase flow is executed
    # 3. Final decision is returned
    # 4. Engine checks if action != HOLD before executing trade
    
    logger.info("Decision flow:")
    logger.info("1. Engine calls orchestrator.make_decision()")
    logger.info("2. Orchestrator runs 6-phase decision flow")
    logger.info("3. Final decision is returned to engine")
    logger.info("4. Engine only executes trade if action != HOLD (line 197)")
    logger.info("5. Only executed trades are added to transactions list")
    
    return True

def analyze_mock_agents():
    """Analyze mock agent behavior"""
    logger.info("\n=== Analyzing Mock Agent Behavior ===")
    
    # Check if mock agents are being used
    config_path = "/Users/y-sato/TradingAgents2/TradingMultiAgents/webui_config_o3_o4.json"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            logger.info(f"WebUI config: {json.dumps(config, indent=2)}")
    
    # From backtest2_wrapper.py line 324:
    # llm_config = LLMConfig(
    #     deep_think_model="mock" if webui_config.get("use_mock", False) else ...
    
    logger.info("\nMock agent detection:")
    logger.info("1. If use_mock=True in WebUI config, mock agents are used")
    logger.info("2. Mock agents may always return HOLD decisions")
    logger.info("3. This would result in zero trades")
    
    return True

def check_mock_agent_implementation():
    """Check mock agent implementation"""
    logger.info("\n=== Checking Mock Agent Implementation ===")
    
    try:
        from backtest2.agents.traders import Trader
        logger.info("Checking Trader mock implementation...")
        
        # The mock Trader would need to return decisions
        # If it always returns HOLD, no trades will be executed
        
    except ImportError as e:
        logger.error(f"Failed to import: {e}")
    
    return True

def propose_solutions():
    """Propose solutions to fix the issue"""
    logger.info("\n=== Proposed Solutions ===")
    
    logger.info("1. Fix agent performance calculation:")
    logger.info("   - Count all decisions made, not just executed trades")
    logger.info("   - Track decisions in orchestrator or engine")
    
    logger.info("\n2. Fix mock agents:")
    logger.info("   - Ensure mock agents return varied decisions (BUY/SELL/HOLD)")
    logger.info("   - Add realistic mock decision logic")
    
    logger.info("\n3. Add decision tracking:")
    logger.info("   - Store all decisions, not just trades")
    logger.info("   - Include HOLD decisions in metrics")
    
    logger.info("\n4. Enable debug logging:")
    logger.info("   - Set debug=True in config")
    logger.info("   - Log decision details in engine")
    
    return True

def main():
    """Main analysis function"""
    logger.info("Starting analysis of zero trades issue...")
    
    # Run analyses
    analyze_agent_performance()
    analyze_decision_flow()
    analyze_mock_agents()
    check_mock_agent_implementation()
    propose_solutions()
    
    logger.info("\n=== Analysis Complete ===")
    logger.info("Root cause: Agent performance tracks executed trades, not decisions")
    logger.info("If all decisions are HOLD, total_decisions will be 0")
    logger.info("Check analyze_zero_trades.log for full details")

if __name__ == "__main__":
    main()