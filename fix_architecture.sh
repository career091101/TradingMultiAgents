#!/bin/bash
# Fix architecture mismatch issues for Intel Mac

echo "🔧 Fixing architecture mismatch issues..."

# 1. Uninstall problematic packages
echo "📦 Uninstalling packages with architecture issues..."
pip freeze | grep -E "(aiohttp|tokenizers|xxhash|rpds|orjson|yarl|frozenlist|multidict|propcache|pandas|numpy|pillow|regex|tiktoken|cffi|cryptography|curl-cffi|matplotlib|lxml|mini-racer|grpcio|psutil|Pillow|scikit|scipy|pycryptodome)" | cut -d'=' -f1 > packages_to_reinstall.txt

if [ -s packages_to_reinstall.txt ]; then
    cat packages_to_reinstall.txt | xargs pip uninstall -y
else
    echo "No packages to uninstall"
fi

# 2. Clear pip cache
echo "🗑️  Clearing pip cache..."
pip cache purge

# 3. Reinstall with correct architecture
echo "📦 Reinstalling packages with x86_64 architecture..."
arch -x86_64 pip install --no-cache-dir cffi
arch -x86_64 pip install --no-cache-dir curl-cffi
arch -x86_64 pip install --no-cache-dir yfinance

# 4. Reinstall other critical packages
echo "📦 Reinstalling other critical packages..."
arch -x86_64 pip install --no-cache-dir pandas numpy regex tiktoken aiohttp

# 5. Clean up
rm -f packages_to_reinstall.txt

echo "✅ Architecture fix completed!"
echo "🚀 You can now start the WebUI with: python run_webui.py"