#!/usr/bin/env python3
"""
Script to install remaining dependencies for TradingAgents with arm64 optimization
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}")
        print(f"Error: {e.stderr}")
        return False

def clean_caches():
    """Clean pip and conda caches to free up space"""
    print("Cleaning caches...")
    run_command("pip cache purge")
    run_command("conda clean --all -y")

def install_remaining_packages():
    """Install remaining packages from requirements.txt"""
    
    # Essential packages that should be installed first
    essential_packages = [
        "langchain-core",
        "langchain-openai", 
        "langchain-anthropic",
        "openai",
        "requests",
        "pandas",
        "pydantic"
    ]
    
    # Install essential packages one by one to avoid disk space issues
    for package in essential_packages:
        print(f"\nInstalling {package}...")
        clean_caches()
        if not run_command(f"pip install {package} --no-cache-dir"):
            print(f"Failed to install {package}")
    
    # Try to install remaining packages
    print("\nInstalling remaining packages...")
    clean_caches()
    run_command("pip install -r requirements.txt --no-cache-dir")

if __name__ == "__main__":
    print("Installing TradingAgents dependencies for arm64...")
    
    # Ensure we're in the tradingagents-arm64 environment
    if "tradingagents-arm64" not in os.environ.get("CONDA_DEFAULT_ENV", ""):
        print("Please activate the tradingagents-arm64 environment first:")
        print("conda activate tradingagents-arm64")
        sys.exit(1)
    
    install_remaining_packages()
    print("\nInstallation complete!")