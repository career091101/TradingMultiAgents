#!/usr/bin/env python3
"""
Enable debug logging for LLM responses
"""

import logging
import os

def setup_debug_logging():
    """Setup debug logging for LLM response troubleshooting"""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/llm_debug.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to debug
    loggers_to_debug = [
        'backtest2.agents.llm_client',
        'backtest2.agents.agent_adapter',
        'backtest2.agents.orchestrator'
    ]
    
    for logger_name in loggers_to_debug:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
    
    print("Debug logging enabled. Check logs/llm_debug.log for details.")

if __name__ == "__main__":
    setup_debug_logging()
