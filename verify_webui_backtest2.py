#!/usr/bin/env python
"""Verify WebUI can start with Backtest2 integration"""

import os
import sys
import subprocess
import time

# Navigate to TradingMultiAgents directory
current_dir = os.path.dirname(os.path.abspath(__file__))
trading_agents_dir = os.path.join(current_dir, 'TradingMultiAgents')
os.chdir(trading_agents_dir)

print(f"Current directory: {os.getcwd()}")

# Start WebUI in background
print("\nStarting WebUI with Backtest2...")
proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "webui/app.py", 
     "--server.headless", "true", "--server.port", "8503"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for startup
print("Waiting for WebUI to start...")
time.sleep(5)

# Check if process is still running
if proc.poll() is None:
    print("✅ WebUI is running!")
    
    # Try to fetch the page
    try:
        import urllib.request
        response = urllib.request.urlopen('http://localhost:8503')
        if response.status == 200:
            print("✅ WebUI is accessible at http://localhost:8503")
    except Exception as e:
        print(f"⚠️  Could not access WebUI: {e}")
    
    # Terminate the process
    proc.terminate()
    proc.wait()
    print("WebUI process terminated")
else:
    print("❌ WebUI failed to start")
    stdout, stderr = proc.communicate()
    print(f"STDOUT:\n{stdout}")
    print(f"STDERR:\n{stderr}")

print("\nTest complete!")