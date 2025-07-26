#!/bin/bash
# ARM64環境をアクティベートするスクリプト

echo "🚀 ARM64ネイティブPython環境をアクティベート"
echo "================================================"

# 現在のディレクトリを確認
if [ ! -d ".venv_arm64" ]; then
    echo "❌ .venv_arm64ディレクトリが見つかりません"
    echo "   現在のディレクトリ: $(pwd)"
    exit 1
fi

# 環境をアクティベート
source .venv_arm64/bin/activate

# 確認
echo "✅ ARM64環境アクティベート完了"
echo ""
echo "📍 環境情報:"
echo "   Python: $(which python)"
echo "   アーキテクチャ: $(python -c 'import platform; print(platform.machine())')"
echo "   Pythonバージョン: $(python --version)"
echo ""
echo "💡 使用方法:"
echo "   - WebUIの起動: python TradingMultiAgents/run_webui.py"
echo "   - テストの実行: python test_yahoo_direct.py"
echo ""
echo "⚠️  注意: この環境はARM64ネイティブです"
echo "   Rosetta 2経由のx86_64環境ではありません"