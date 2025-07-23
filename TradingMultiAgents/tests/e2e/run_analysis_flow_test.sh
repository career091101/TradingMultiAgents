#!/bin/bash
# TradingAgents WebUI 完全分析フローテスト実行スクリプト

echo "=== TradingAgents WebUI 完全分析フローテスト ==="
echo

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 環境変数チェック
check_env() {
    echo "環境変数チェック..."
    
    if [ -z "$FINNHUB_API_KEY" ]; then
        echo -e "${RED}❌ FINNHUB_API_KEY が設定されていません${NC}"
        return 1
    else
        echo -e "${GREEN}✅ FINNHUB_API_KEY${NC}"
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}❌ OPENAI_API_KEY が設定されていません${NC}"
        return 1
    else
        echo -e "${GREEN}✅ OPENAI_API_KEY${NC}"
    fi
    
    return 0
}

# WebUI起動確認
check_webui() {
    echo -n "WebUI起動確認..."
    if curl -s http://localhost:8501 > /dev/null; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        return 1
    fi
}

# WebUI起動
start_webui() {
    echo "WebUIを起動します..."
    python run_webui.py > webui_flow_test.log 2>&1 &
    WEBUI_PID=$!
    echo "WebUI PID: $WEBUI_PID"
    
    # 起動待機
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

# テスト実行
run_test() {
    local test_mode=$1
    
    echo
    echo -e "${BLUE}テストモード: $test_mode${NC}"
    echo
    
    case $test_mode in
        "quick")
            echo "深度1のクイックテストを実行します（約15分）"
            echo "1" | python tests/e2e/analysis_flow_test.py
            ;;
        "standard")
            echo "深度1,3の標準テストを実行します（約50分）"
            echo "2" | python tests/e2e/analysis_flow_test.py
            ;;
        "full")
            echo "深度1,3,5の完全テストを実行します（約2時間）"
            echo "3" | python tests/e2e/analysis_flow_test.py
            ;;
        "custom")
            echo "対話モードでテストを実行します"
            python tests/e2e/analysis_flow_test.py
            ;;
        *)
            echo -e "${RED}無効なテストモード: $test_mode${NC}"
            return 1
            ;;
    esac
}

# 結果レポート生成
generate_report() {
    echo
    echo "テスト結果レポートを生成しています..."
    
    # 最新の結果ファイルを探す
    LATEST_RESULT=$(ls -t tests/e2e/analysis_flow_results/test_results_*.json 2>/dev/null | head -1)
    
    if [ -n "$LATEST_RESULT" ]; then
        echo -e "${GREEN}結果ファイル: $LATEST_RESULT${NC}"
        
        # 簡易レポート表示
        python -c "
import json
with open('$LATEST_RESULT', 'r') as f:
    data = json.load(f)
    summary = data.get('summary', {})
    print('\n=== テスト結果サマリー ===')
    print(f'成功: {summary.get(\"successful\", 0)}')
    print(f'失敗: {summary.get(\"failed\", 0)}')
        "
    else
        echo -e "${YELLOW}結果ファイルが見つかりません${NC}"
    fi
}

# メイン処理
main() {
    # 環境チェック
    if ! check_env; then
        echo -e "${RED}環境変数を設定してください${NC}"
        exit 1
    fi
    
    # Playwrightチェック
    if ! python -c "import playwright" 2>/dev/null; then
        echo -e "${YELLOW}Playwrightをインストールします...${NC}"
        pip install playwright
        playwright install chromium
    fi
    
    # WebUI確認
    CLEANUP_WEBUI=false
    if ! check_webui; then
        echo -e "${YELLOW}WebUIが起動していません${NC}"
        if ! start_webui; then
            echo -e "${RED}テストを中止します${NC}"
            exit 1
        fi
        CLEANUP_WEBUI=true
    fi
    
    # テストモード選択
    TEST_MODE=${1:-"custom"}
    
    # 結果ディレクトリ作成
    mkdir -p tests/e2e/analysis_flow_results
    
    # テスト実行
    echo
    echo -e "${BLUE}========== テスト開始 ==========${NC}"
    
    START_TIME=$(date +%s)
    run_test "$TEST_MODE"
    TEST_RESULT=$?
    END_TIME=$(date +%s)
    
    DURATION=$((END_TIME - START_TIME))
    echo
    echo -e "実行時間: $((DURATION / 60))分$((DURATION % 60))秒"
    
    # レポート生成
    generate_report
    
    # クリーンアップ
    if [ "$CLEANUP_WEBUI" = true ] && [ -n "$WEBUI_PID" ]; then
        echo
        echo "WebUIを停止します..."
        kill $WEBUI_PID 2>/dev/null
        wait $WEBUI_PID 2>/dev/null
    fi
    
    # 最終結果
    echo
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ テストが完了しました${NC}"
    else
        echo -e "${RED}❌ テストが失敗しました${NC}"
    fi
    
    echo
    echo "詳細ログ:"
    echo "- WebUIログ: webui_flow_test.log"
    echo "- テスト結果: tests/e2e/analysis_flow_results/"
    echo "- スクリーンショット: tests/e2e/analysis_flow_results/*.png"
    
    return $TEST_RESULT
}

# ヘルプ表示
show_help() {
    echo "使用方法: $0 [モード]"
    echo
    echo "モード:"
    echo "  quick     深度1のクイックテスト（約15分）"
    echo "  standard  深度1,3の標準テスト（約50分）"
    echo "  full      深度1,3,5の完全テスト（約2時間）"
    echo "  custom    対話式でテストを選択（デフォルト）"
    echo
    echo "例:"
    echo "  $0 quick    # クイックテストを実行"
    echo "  $0          # 対話モードで実行"
    echo
    echo "注意事項:"
    echo "- 事前にAPIキーの環境変数設定が必要です"
    echo "- 実際のAPI呼び出しが発生します"
    echo "- 深度5のテストは約1時間かかります"
}

# コマンドライン処理
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# 実行確認
if [ "$1" = "full" ]; then
    echo -e "${YELLOW}警告: 完全テストは約2時間かかります${NC}"
    echo -n "続行しますか？ (y/n): "
    read -r confirm
    if [ "$confirm" != "y" ]; then
        echo "テストをキャンセルしました"
        exit 0
    fi
fi

# メイン実行
main "$@"