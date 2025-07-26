#!/usr/bin/env python3
"""
Fix datetime type mismatch between offset-naive and offset-aware
"""

import os

def fix_datetime_issues():
    print("=== 日時型不整合エラーの修正 ===\n")
    
    # 1. Fix position_manager.py
    print("1. position_manager.pyの修正...")
    
    pm_path = "backtest2/risk/position_manager.py"
    
    with open(pm_path, 'r') as f:
        content = f.read()
    
    # Find the problematic line
    old_code = "if (current_date - position.entry_date).days > 30:"
    
    # Replace with timezone-aware comparison
    new_code = """# Ensure both dates are timezone-naive for comparison
        current_date_naive = current_date.replace(tzinfo=None) if hasattr(current_date, 'tzinfo') else current_date
        entry_date_naive = position.entry_date.replace(tzinfo=None) if hasattr(position.entry_date, 'tzinfo') else position.entry_date
        if (current_date_naive - entry_date_naive).days > 30:"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(pm_path, 'w') as f:
            f.write(content)
        
        print("   ✓ position_manager.pyを修正しました")
    else:
        print("   ⚠️  該当箇所が見つかりません")
    
    # 2. Fix TimeManager to ensure consistent datetime types
    print("\n2. TimeManagerの修正...")
    
    tm_path = "backtest2/utils/time_manager.py"
    
    with open(tm_path, 'r') as f:
        content = f.read()
    
    # Add timezone removal in _generate_trading_days
    if "_generate_trading_days" in content:
        # Find the method
        method_start = content.find("def _generate_trading_days(self):")
        if method_start > 0:
            # Find where we set current
            current_line = content.find("current = self.start_date", method_start)
            if current_line > 0:
                # Add timezone removal
                line_end = content.find("\n", current_line)
                indent = "        "
                new_code = f"{content[current_line:line_end]}\n{indent}# Ensure timezone-naive dates\n{indent}current = current.replace(tzinfo=None) if hasattr(current, 'tzinfo') else current"
                
                content = content[:current_line] + new_code + content[line_end:]
                
                with open(tm_path, 'w') as f:
                    f.write(content)
                
                print("   ✓ TimeManagerを修正しました")
    
    # 3. Fix MarketData creation in data manager
    print("\n3. DataManagerの日時型統一...")
    
    dm_path = "backtest2/data/manager_simple.py"
    
    with open(dm_path, 'r') as f:
        content = f.read()
    
    # Find MarketData creation
    if "MarketData(" in content:
        # Add timezone removal before creating MarketData
        old_line = "date=hist.index[idx].to_pydatetime(),"
        if old_line in content:
            new_line = "date=hist.index[idx].to_pydatetime().replace(tzinfo=None),"
            content = content.replace(old_line, new_line)
            
            with open(dm_path, 'w') as f:
                f.write(content)
            
            print("   ✓ DataManagerを修正しました")
    
    # 4. Add a utility function for consistent datetime handling
    print("\n4. 日時型ユーティリティの作成...")
    
    util_content = '''"""Datetime utilities for consistent timezone handling"""

from datetime import datetime
from typing import Optional

def ensure_timezone_naive(dt: datetime) -> datetime:
    """Ensure datetime is timezone-naive for consistent comparisons"""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo is not None else dt

def ensure_timezone_aware(dt: datetime, tz=None) -> datetime:
    """Ensure datetime is timezone-aware"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        import pytz
        tz = tz or pytz.UTC
        return tz.localize(dt)
    return dt
'''
    
    with open('backtest2/utils/datetime_utils.py', 'w') as f:
        f.write(util_content)
    
    print("   ✓ datetime_utils.pyを作成しました")
    
    print("\n=== 修正完了 ===")
    print("\n修正内容:")
    print("- position_manager.pyで日時比較時にタイムゾーンを除去")
    print("- TimeManagerで生成される日付をtimezone-naiveに統一")
    print("- DataManagerで作成されるMarketDataの日付をtimezone-naiveに")
    print("- 日時型ユーティリティ関数を追加")
    
    print("\n次のステップ:")
    print("1. テストを再実行して動作確認")
    print("2. WebUIでバックテストを実行")

if __name__ == "__main__":
    fix_datetime_issues()