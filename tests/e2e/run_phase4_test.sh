#!/bin/bash
# Phase 4 E2E Test 実行スクリプト

echo "=== TradingAgents WebUI Phase 4 E2E Test ==="
echo

# 環境変数の設定（テスト用）
export FINNHUB_API_KEY="${FINNHUB_API_KEY:-test_finnhub_key}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-test_openai_key}"

# カラー出力の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# WebUIが起動しているか確認
check_webui() {
    echo -n "WebUIの起動を確認中..."
    if curl -s http://localhost:8501 > /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        return 1
    fi
}

# WebUIを起動
start_webui() {
    echo "WebUIを起動します..."
    python run_webui.py > webui_test.log 2>&1 &
    WEBUI_PID=$!
    echo "WebUI PID: $WEBUI_PID"
    
    # 起動を待機
    for i in {1..30}; do
        if check_webui; then
            echo -e "${GREEN}WebUIが起動しました${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo -e "${RED}WebUIの起動に失敗しました${NC}"
    return 1
}

# Playwrightのインストール確認
check_playwright() {
    echo -n "Playwrightの確認..."
    if python -c "import playwright" 2>/dev/null; then
        echo -e " ${GREEN}✓${NC}"
    else
        echo -e " ${YELLOW}インストールが必要です${NC}"
        pip install playwright pytest-playwright
        playwright install chromium --with-deps
    fi
}

# メイン処理
main() {
    # 依存関係の確認
    check_playwright
    
    # WebUIの確認と起動
    if ! check_webui; then
        echo -e "${YELLOW}WebUIが起動していません${NC}"
        if ! start_webui; then
            echo -e "${RED}テストを中止します${NC}"
            exit 1
        fi
        CLEANUP_WEBUI=true
    fi
    
    # スクリーンショットディレクトリの作成
    mkdir -p tests/e2e/screenshots
    
    # テストの実行
    echo
    echo "Phase 4 E2Eテストを実行します..."
    echo "================================"
    
    # サンプルテストの実行
    python tests/e2e/phase4_sample_test.py
    TEST_RESULT=$?
    
    # Pytestでの実行（オプション）
    if [ "$1" == "--pytest" ]; then
        echo
        echo "Pytestでテストを実行..."
        pytest tests/e2e/phase4_sample_test.py -v -s \
            --tb=short \
            --capture=no
    fi
    
    # クリーンアップ
    if [ "$CLEANUP_WEBUI" == "true" ] && [ -n "$WEBUI_PID" ]; then
        echo
        echo "WebUIを停止します..."
        kill $WEBUI_PID 2>/dev/null
        wait $WEBUI_PID 2>/dev/null
    fi
    
    # 結果の表示
    echo
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ テストが成功しました${NC}"
        echo "スクリーンショット: tests/e2e/screenshots/"
    else
        echo -e "${RED}❌ テストが失敗しました${NC}"
        echo "ログ: webui_test.log"
    fi
    
    return $TEST_RESULT
}

# ヘルプメッセージ
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "使用方法: $0 [オプション]"
    echo
    echo "オプション:"
    echo "  --pytest    Pytestフレームワークを使用してテストを実行"
    echo "  --help, -h  このヘルプメッセージを表示"
    echo
    echo "例:"
    echo "  $0          # 基本的なテスト実行"
    echo "  $0 --pytest # Pytestを使用した実行"
    exit 0
fi

# 実行
main "$@"