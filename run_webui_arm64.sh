#\!/bin/bash
# M1 Mac ARM64ネイティブモードでWebUIを起動するスクリプト

echo "🍎 M1 Mac ARM64ネイティブモードでWebUIを起動"
echo "============================================"

# アーキテクチャ確認
ARCH=$(uname -m)
if [ "$ARCH" \!= "arm64" ]; then
    echo "❌ エラー: ARM64環境で実行してください"
    echo "   現在: $ARCH"
    exit 1
fi

# Rosetta 2チェック
if sysctl -n sysctl.proc_translated 2>/dev/null | grep -q 1; then
    echo "❌ エラー: Rosetta 2経由で実行されています"
    echo "   ネイティブターミナルで実行してください"
    exit 1
fi

# ARM64環境のアクティベート
if [ \! -d ".venv_arm64" ]; then
    echo "❌ ARM64環境が見つかりません"
    echo "   先に setup_arm64_native.sh を実行してください"
    exit 1
fi

# 環境変数の読み込み
if [ -f ".env_arm64" ]; then
    source .env_arm64
fi

# 環境のアクティベート
source .venv_arm64/bin/activate

# アーキテクチャの最終確認
PYTHON_ARCH=$(python -c "import platform; print(platform.machine())")
if [ "$PYTHON_ARCH" \!= "arm64" ]; then
    echo "❌ PythonがARM64モードで動作していません: $PYTHON_ARCH"
    exit 1
fi

echo "✅ ARM64ネイティブモードで実行中"
echo "   Python: $(which python)"
echo "   アーキテクチャ: $PYTHON_ARCH"
echo ""

# .envファイルの存在確認
if [ \! -f ".env" ]; then
    echo "⚠️  .envファイルが見つかりません"
    echo "   APIキーが設定されていることを確認してください"
fi

# WebUIの起動
echo "🚀 WebUIを起動中..."
echo ""

# ARM64ネイティブモードで実行
exec python TradingMultiAgents/run_webui.py
