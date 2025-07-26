#!/usr/bin/env python3
"""ARM64環境の動作確認テスト"""

import platform
import sys

print("=== Python Environment Test ===")
print(f"Python Version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")
print(f"Processor: {platform.processor()}")

# Test critical imports
print("\n=== Testing Critical Imports ===")

try:
    import pyarrow
    print(f"✅ pyarrow {pyarrow.__version__} - imported successfully")
    # Test pyarrow functionality
    pa_array = pyarrow.array([1, 2, 3])
    print(f"   pyarrow test: Created array with {len(pa_array)} elements")
except Exception as e:
    print(f"❌ pyarrow - import failed: {e}")

try:
    import jiter
    print(f"✅ jiter - imported successfully")
    # Test jiter functionality
    parsed = jiter.from_json(b'{"test": "value"}')
    print(f"   jiter test: Parsed JSON: {parsed}")
except Exception as e:
    print(f"❌ jiter - import failed: {e}")

try:
    import pandas as pd
    print(f"✅ pandas {pd.__version__} - imported successfully")
    # Test pandas functionality
    df = pd.DataFrame({'col': [1, 2, 3]})
    print(f"   pandas test: Created DataFrame with {len(df)} rows")
except Exception as e:
    print(f"❌ pandas - import failed: {e}")

try:
    import numpy as np
    print(f"✅ numpy {np.__version__} - imported successfully")
    # Test numpy functionality
    arr = np.array([1, 2, 3])
    print(f"   numpy test: Created array with shape {arr.shape}")
except Exception as e:
    print(f"❌ numpy - import failed: {e}")

print("\n=== Binary Architecture Check ===")
import subprocess
import os

# Check architecture of key packages
packages = ['pyarrow', 'jiter']
for pkg in packages:
    try:
        module = sys.modules.get(pkg)
        if module and hasattr(module, '__file__'):
            # Find .so files in the package directory
            pkg_dir = os.path.dirname(module.__file__)
            so_files = []
            for root, dirs, files in os.walk(pkg_dir):
                so_files.extend([os.path.join(root, f) for f in files if f.endswith('.so')])
            
            if so_files:
                # Check first .so file
                result = subprocess.run(['file', so_files[0]], capture_output=True, text=True)
                if 'arm64' in result.stdout:
                    print(f"✅ {pkg}: ARM64 binary confirmed")
                else:
                    print(f"❌ {pkg}: Not ARM64 - {result.stdout}")
    except Exception as e:
        print(f"⚠️  {pkg}: Could not check architecture - {e}")

print("\n=== Test Complete ===")