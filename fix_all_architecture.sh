#!/bin/bash
# Complete architecture fix for all packages

echo "🔧 Complete Architecture Fix Starting..."

# 1. Export required environment variables
export ARCHFLAGS="-arch x86_64"
export CFLAGS="-arch x86_64"
export LDFLAGS="-arch x86_64"

# 2. Uninstall ALL binary packages
echo "📦 Removing all binary packages..."
pip freeze > all_packages.txt
cat all_packages.txt | grep -E "(cffi|curl-cffi|cryptography|grpcio|lxml|numpy|pandas|pillow|psutil|regex|tiktoken|tokenizers|xxhash|zstandard|aiohttp|frozenlist|multidict|yarl|orjson|rpds-py|matplotlib|mini-racer|pydantic-core|kiwisolver|contourpy|propcache)" | cut -d'=' -f1 | xargs pip uninstall -y

# 3. Clear ALL caches
echo "🗑️  Clearing all caches..."
pip cache purge
rm -rf ~/.cache/pip
rm -rf ~/Library/Caches/pip

# 4. Reinstall cffi and its dependencies first
echo "📦 Installing cffi and dependencies..."
arch -x86_64 pip install --no-cache-dir --no-binary :all: cffi==1.17.1

# 5. Reinstall other critical packages
echo "📦 Installing other packages..."
arch -x86_64 pip install --no-cache-dir \
    curl-cffi \
    cryptography \
    grpcio \
    grpcio-status \
    lxml \
    numpy \
    pandas \
    pillow \
    psutil \
    regex \
    tiktoken \
    tokenizers \
    xxhash \
    zstandard \
    aiohttp \
    frozenlist \
    multidict \
    yarl \
    orjson \
    rpds-py \
    matplotlib \
    mini-racer \
    pydantic-core \
    kiwisolver \
    contourpy \
    propcache

# 6. Verify installations
echo "🔍 Verifying installations..."
python -c "import cffi; print('cffi OK')"
python -c "import curl_cffi; print('curl_cffi OK')"
python -c "import yfinance; print('yfinance OK')"

# 7. Clean up
rm -f all_packages.txt

echo "✅ Architecture fix completed!"
echo "🚀 You can now start the WebUI with: python run_webui.py"