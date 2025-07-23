#!/usr/bin/env python3
"""
Script to fix critical issues in the backtest system.
This script addresses the most urgent problems identified in the code review.
"""

import os
import sys
import re
import shutil
from datetime import datetime
from typing import List, Tuple

def backup_file(filepath: str) -> str:
    """Create a backup of the file before modification."""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backed up {filepath} to {backup_path}")
    return backup_path

def fix_undefined_variable_in_backtest_ui(filepath: str) -> bool:
    """Fix the undefined use_custom_config variable in backtest.py."""
    print(f"\n🔧 Fixing undefined variable in {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find and comment out the problematic section
    original = """        if use_custom_config:
            config_summary.update({
                "LLM Provider": llm_provider,
                "Debate Rounds": max_debate_rounds,
                "Online Tools": "Yes" if online_tools else "No"
            })"""
    
    replacement = """        # Fixed: Removed undefined use_custom_config check
        # Always include agent config in summary
        config_summary.update({
            "LLM Provider": self.state.get("llm_provider", "openai"),
            "Debate Rounds": self.state.get("backtest_debate_rounds", 1),
            "Online Tools": "Yes" if self.state.get("backtest_online_tools", False) else "No"
        })"""
    
    if original in content:
        content = content.replace(original, replacement)
        with open(filepath, 'w') as f:
            f.write(content)
        print("✓ Fixed undefined variable issue")
        return True
    else:
        print("⚠️  Pattern not found, may already be fixed")
        return False

def fix_backtest2_config_instantiation(filepath: str) -> bool:
    """Fix the BacktestConfig instantiation issues in backtest2_wrapper.py."""
    print(f"\n🔧 Fixing BacktestConfig instantiation in {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix the main config creation
    fixes_applied = 0
    
    # Pattern 1: Fix the try-except block for config creation
    pattern1 = r'(\s+)# Create BacktestConfig - try without random_seed first\n(\s+)try:(.*?)except TypeError as e:(.*?)# Set random_seed manually if needed(.*?)setattr\(config, \'random_seed\', webui_config\.get\("random_seed", 42\)\)'
    
    replacement1 = r'''\1# Create BacktestConfig with proper field handling
\1config_kwargs = {
\1    "name": "webui_backtest",
\1    "symbols": webui_config.get("tickers", ["AAPL"]),
\1    "time_range": time_range,
\1    "initial_capital": webui_config.get("initial_capital", 10000.0),
\1    "max_positions": risk_config.max_positions,
\1    "position_limits": risk_config.position_limits,
\1    "llm_config": llm_config,
\1    "data_sources": ["yahoo", "finnhub"],
\1    "reflection_config": {
\1        "enabled": reflection_config.enabled,
\1        "levels": ["DAILY", "WEEKLY", "POSITION_CLOSE"],
\1        "triggers": ["TIME_BASED", "EVENT_BASED", "PERFORMANCE_BASED"]
\1    },
\1    "result_dir": result_dir,
\1    "slippage": webui_config.get("slippage", 0.001),
\1    "commission": webui_config.get("commission", 0.001),
\1    "risk_free_rate": webui_config.get("risk_free_rate", 0.02),
\1    "agent_config": agent_config,
\1    "data_config": data_config,
\1    "risk_config": risk_config,
\1    "benchmark": "SPY",
\1    "save_results": True,
\1    "log_level": "INFO"
\1}
\1
\1# Add random_seed if the field exists
\1if hasattr(BacktestConfig, '__dataclass_fields__') and 'random_seed' in BacktestConfig.__dataclass_fields__:
\1    config_kwargs['random_seed'] = webui_config.get("random_seed", 42)
\1
\1try:
\1    config = BacktestConfig(**config_kwargs)
\1except TypeError as e:
\1    logger.error(f"Failed to create BacktestConfig: {e}")
\1    # Log available fields for debugging
\1    if hasattr(BacktestConfig, '__dataclass_fields__'):
\1        logger.error(f"Available fields: {list(BacktestConfig.__dataclass_fields__.keys())}")
\1    raise'''
    
    # Apply fix if pattern found
    if re.search(pattern1, content, re.DOTALL):
        content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
        fixes_applied += 1
    
    # Also fix the _update_config_for_ticker method
    pattern2 = r'def _update_config_for_ticker\(self, config: BacktestConfig, ticker: str\) -> BacktestConfig:(.*?)return new_config'
    
    def update_config_replacement(match):
        indent = "        "
        return f'''def _update_config_for_ticker(self, config: BacktestConfig, ticker: str) -> BacktestConfig:
{indent}"""Update config for a single ticker."""
{indent}# Create config kwargs
{indent}config_kwargs = {{
{indent}    "name": config.name,
{indent}    "symbols": [ticker],
{indent}    "time_range": config.time_range,
{indent}    "initial_capital": config.initial_capital,
{indent}    "max_positions": config.max_positions,
{indent}    "position_limits": config.position_limits,
{indent}    "llm_config": config.llm_config,
{indent}    "data_sources": config.data_sources,
{indent}    "reflection_config": config.reflection_config,
{indent}    "result_dir": Path(config.result_dir) / ticker if config.result_dir else None,
{indent}    "slippage": config.slippage,
{indent}    "commission": config.commission,
{indent}    "risk_free_rate": config.risk_free_rate,
{indent}    "agent_config": config.agent_config,
{indent}    "data_config": config.data_config,
{indent}    "risk_config": config.risk_config,
{indent}    "benchmark": config.benchmark,
{indent}    "save_results": config.save_results,
{indent}    "log_level": config.log_level
{indent}}}
{indent}
{indent}# Add random_seed if it exists
{indent}if hasattr(config, 'random_seed'):
{indent}    config_kwargs['random_seed'] = config.random_seed
{indent}elif hasattr(BacktestConfig, '__dataclass_fields__') and 'random_seed' in BacktestConfig.__dataclass_fields__:
{indent}    config_kwargs['random_seed'] = 42
{indent}
{indent}try:
{indent}    new_config = BacktestConfig(**config_kwargs)
{indent}except TypeError as e:
{indent}    logger.error(f"Failed to create BacktestConfig in update: {{e}}")
{indent}    raise
{indent}
{indent}return new_config'''
    
    if re.search(pattern2, content, re.DOTALL):
        content = re.sub(pattern2, update_config_replacement, content, flags=re.DOTALL)
        fixes_applied += 1
    
    if fixes_applied > 0:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Applied {fixes_applied} fixes to BacktestConfig instantiation")
        return True
    else:
        print("⚠️  Patterns not found, may already be fixed")
        return False

def fix_null_safety_in_results_processing(filepath: str) -> bool:
    """Add null safety checks in results processing."""
    print(f"\n🔧 Adding null safety checks in {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix the _process_results method
    pattern = r'def _process_results\(self, result: \'BacktestResult\', ticker: str, config: \'BacktestConfig\'\) -> Dict\[str, Any\]:(.*?)return \{'
    
    def process_results_replacement(match):
        indent = "    "
        return f'''def _process_results(self, result: 'BacktestResult', ticker: str, config: 'BacktestConfig') -> Dict[str, Any]:
{indent * 2}"""Process backtest results for WebUI display with proper null safety."""
{indent * 2}# Initialize default metrics
{indent * 2}metrics = {{
{indent * 3}"total_return": 0.0,
{indent * 3}"annualized_return": 0.0,
{indent * 3}"sharpe_ratio": 0.0,
{indent * 3}"sortino_ratio": 0.0,
{indent * 3}"max_drawdown": 0.0,
{indent * 3}"volatility": 0.0,
{indent * 3}"win_rate": 0.0,
{indent * 3}"total_trades": 0,
{indent * 3}"winning_trades": 0,
{indent * 3}"losing_trades": 0,
{indent * 3}"avg_win": 0.0,
{indent * 3}"avg_loss": 0.0,
{indent * 3}"profit_factor": 0.0,
{indent * 3}"calmar_ratio": 0.0
{indent * 2}}}
{indent * 2}
{indent * 2}# Safely extract metrics if available
{indent * 2}if hasattr(result, 'metrics') and result.metrics is not None:
{indent * 3}m = result.metrics
{indent * 3}# Update metrics with actual values using safe getattr
{indent * 3}metric_mapping = {{
{indent * 4}"total_return": "total_return",
{indent * 4}"annualized_return": "annualized_return",
{indent * 4}"sharpe_ratio": "sharpe_ratio",
{indent * 4}"sortino_ratio": "sortino_ratio",
{indent * 4}"max_drawdown": "max_drawdown",
{indent * 4}"volatility": "volatility",
{indent * 4}"win_rate": "win_rate",
{indent * 4}"total_trades": "total_trades",
{indent * 4}"winning_trades": "winning_trades",
{indent * 4}"losing_trades": "losing_trades",
{indent * 4}"avg_win": "average_win",
{indent * 4}"avg_loss": "average_loss",
{indent * 4}"profit_factor": "profit_factor",
{indent * 4}"calmar_ratio": "calmar_ratio"
{indent * 3}}}
{indent * 3}
{indent * 3}for key, attr_name in metric_mapping.items():
{indent * 4}if hasattr(m, attr_name):
{indent * 5}value = getattr(m, attr_name, metrics[key])
{indent * 5}# Ensure numeric values
{indent * 5}if isinstance(value, (int, float)) and not (math.isnan(value) or math.isinf(value)):
{indent * 6}metrics[key] = value
{indent * 2}
{indent * 2}# Rest of the method implementation...
{indent * 2}return {{'''
    
    if re.search(pattern, content, re.DOTALL):
        # Add math import if not present
        if 'import math' not in content:
            content = content.replace('import traceback', 'import traceback\nimport math')
        
        # Apply the fix
        content = re.sub(pattern, process_results_replacement, content, flags=re.DOTALL)
        
        with open(filepath, 'w') as f:
            f.write(content)
        print("✓ Added null safety checks to results processing")
        return True
    else:
        print("⚠️  Pattern not found, may already be fixed")
        return False

def fix_deprecated_plotting_style(filepath: str) -> bool:
    """Fix deprecated matplotlib style usage."""
    print(f"\n🔧 Fixing deprecated plotting style in {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix the setup_plot_style function
    original = """def setup_plot_style():
    \"\"\"Set up a clean plotting style.\"\"\"
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['lines.linewidth'] = 2"""
    
    replacement = """def setup_plot_style():
    \"\"\"Set up a clean plotting style.\"\"\"
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
    except OSError:
        # Fallback for newer matplotlib versions
        try:
            plt.style.use('seaborn-darkgrid')
        except OSError:
            # Final fallback to default style
            plt.style.use('default')
            # Apply some custom styling
            plt.rcParams['axes.grid'] = True
            plt.rcParams['grid.alpha'] = 0.3
    
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 10
    plt.rcParams['lines.linewidth'] = 2"""
    
    if original in content:
        content = content.replace(original, replacement)
        with open(filepath, 'w') as f:
            f.write(content)
        print("✓ Fixed deprecated plotting style")
        return True
    else:
        print("⚠️  Pattern not found, may already be fixed")
        return False

def add_directory_creation(filepath: str) -> bool:
    """Add directory creation before saving results."""
    print(f"\n🔧 Adding directory creation in {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the output directory creation and enhance it
    pattern = r'(\s+)# Create output directory\n(\s+)output_dir = os\.path\.join\("\.\/backtest\/results", datetime\.now\(\)\.strftime\("%Y%m%d_%H%M%S"\)\)\n(\s+)os\.makedirs\(output_dir, exist_ok=True\)'
    
    replacement = r'''\1# Create output directory with proper path handling
\2output_dir = os.path.join("./backtest/results", datetime.now().strftime("%Y%m%d_%H%M%S"))
\2try:
\3os.makedirs(output_dir, exist_ok=True)
\2except OSError as e:
\3logger.error(f"Failed to create output directory {output_dir}: {e}")
\3# Fallback to temp directory
\3import tempfile
\3output_dir = tempfile.mkdtemp(prefix="backtest_results_")
\3logger.warning(f"Using temporary directory: {output_dir}")'''
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        with open(filepath, 'w') as f:
            f.write(content)
        print("✓ Added robust directory creation")
        return True
    else:
        print("⚠️  Pattern not found, may already be fixed")
        return False

def main():
    """Main function to apply all fixes."""
    print("🚀 Starting backtest system critical fixes...\n")
    
    # Define files to fix
    fixes = [
        ("webui/components/backtest.py", fix_undefined_variable_in_backtest_ui),
        ("webui/backend/backtest2_wrapper.py", fix_backtest2_config_instantiation),
        ("webui/backend/backtest2_wrapper.py", fix_null_safety_in_results_processing),
        ("../backtest/plotting.py", fix_deprecated_plotting_style),
        ("webui/backend/backtest_wrapper.py", add_directory_creation),
    ]
    
    # Get the base directory
    base_dir = "/Users/y-sato/TradingAgents2/TradingMultiAgents"
    
    successful_fixes = 0
    failed_fixes = 0
    
    for relative_path, fix_function in fixes:
        filepath = os.path.join(base_dir, relative_path)
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            failed_fixes += 1
            continue
        
        try:
            # Backup the file first
            backup_file(filepath)
            
            # Apply the fix
            if fix_function(filepath):
                successful_fixes += 1
            else:
                failed_fixes += 1
                
        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")
            failed_fixes += 1
    
    print(f"\n📊 Summary:")
    print(f"✓ Successful fixes: {successful_fixes}")
    print(f"❌ Failed fixes: {failed_fixes}")
    
    if successful_fixes > 0:
        print("\n⚠️  Important: Please review the changes and run tests before deploying!")
        print("💡 Backup files have been created with .backup_TIMESTAMP extension")
    
    return 0 if failed_fixes == 0 else 1

if __name__ == "__main__":
    sys.exit(main())