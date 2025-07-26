#!/usr/bin/env python3
"""
Monitor backtest2 execution in real-time
"""

import os
import sys
import logging
from pathlib import Path
import subprocess
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backtest2_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

def find_latest_log_files():
    """Find recently modified log files"""
    log_dirs = [
        '/Users/y-sato/TradingAgents2',
        '/Users/y-sato/TradingAgents2/logs',
        '/Users/y-sato/TradingAgents2/TradingMultiAgents',
        '/Users/y-sato/TradingAgents2/results'
    ]
    
    recent_logs = []
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    if file.endswith('.log'):
                        filepath = os.path.join(root, file)
                        mtime = os.path.getmtime(filepath)
                        if time.time() - mtime < 3600:  # Modified within last hour
                            recent_logs.append((filepath, mtime))
    
    return sorted(recent_logs, key=lambda x: x[1], reverse=True)

def tail_file(filepath, lines=50):
    """Get last N lines of a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            return content[-lines:]
    except Exception as e:
        return [f"Error reading {filepath}: {e}\n"]

def monitor_streamlit_logs():
    """Monitor Streamlit process output"""
    logger.info("=== MONITORING STREAMLIT LOGS ===")
    
    # Check if streamlit is running
    result = subprocess.run(['pgrep', '-f', 'streamlit'], capture_output=True, text=True)
    if result.stdout:
        pid = result.stdout.strip().split('\n')[0]
        logger.info(f"Found Streamlit process: PID {pid}")
        
        # Try to get logs using lsof
        cmd = f"lsof -p {pid} 2>/dev/null | grep -E 'log|txt' | awk '{{print $NF}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            logger.info("Streamlit log files:")
            for logfile in result.stdout.strip().split('\n'):
                if logfile and os.path.exists(logfile):
                    logger.info(f"  - {logfile}")

def check_backtest_status():
    """Check current backtest execution status"""
    logger.info("\n=== CHECKING BACKTEST STATUS ===")
    
    # Look for backtest-related processes
    cmd = "ps aux | grep -E 'backtest|agent|orchestrator' | grep -v grep"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        logger.info("Active backtest processes:")
        for line in result.stdout.strip().split('\n'):
            logger.info(f"  {line[:150]}...")

def main():
    logger.info("Starting backtest monitor...")
    logger.info(f"Current time: {datetime.now()}")
    
    # Find recent log files
    recent_logs = find_latest_log_files()
    logger.info(f"\nFound {len(recent_logs)} recent log files")
    
    # Show last few lines of each recent log
    for logpath, mtime in recent_logs[:5]:  # Top 5 most recent
        logger.info(f"\n{'='*60}")
        logger.info(f"LOG: {logpath}")
        logger.info(f"Modified: {datetime.fromtimestamp(mtime)}")
        logger.info("Last 20 lines:")
        
        lines = tail_file(logpath, 20)
        for line in lines:
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'phase', 'agent', 'llm', 'o3', 'o4', 'initializ']):
                logger.info(f"  > {line.rstrip()}")
    
    # Monitor streamlit
    monitor_streamlit_logs()
    
    # Check backtest status
    check_backtest_status()
    
    # Check for any Python error logs
    logger.info("\n=== CHECKING FOR PYTHON ERRORS ===")
    cmd = "find /Users/y-sato/TradingAgents2 -name '*.log' -type f -mmin -60 -exec grep -l 'Traceback\\|Error\\|Exception' {} \\; 2>/dev/null | head -10"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        logger.info("Files with errors:")
        for errorfile in result.stdout.strip().split('\n'):
            if errorfile:
                logger.info(f"\n  Error in: {errorfile}")
                # Show the error
                cmd = f"grep -A 5 -B 5 'Traceback\\|Error\\|Exception' '{errorfile}' | tail -20"
                error_result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if error_result.stdout:
                    for line in error_result.stdout.split('\n'):
                        logger.info(f"    {line}")

if __name__ == "__main__":
    main()