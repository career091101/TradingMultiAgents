#!/bin/bash

# Claude Code Auto-Cleanup Script (Non-interactive)
# このスクリプトはClaude Code関連の不要ファイルを自動的に削除し、ディスク容量を確保します

echo "🧹 Claude Code 自動クリーンアップスクリプト"
echo "========================================"
echo ""

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 現在のディスク使用状況を表示
echo "📊 クリーンアップ前のディスク使用状況:"
df -h /System/Volumes/Data | grep -v Filesystem
echo ""

# 削除前の容量を記録
BEFORE_SPACE=$(df -k /System/Volumes/Data | awk 'NR==2 {print $4}')

# Claude関連ディレクトリのサイズを確認
echo "📁 Claude関連ディレクトリのサイズ (クリーンアップ前):"
CLAUDE_DIR="$HOME/Library/Application Support/Claude"
if [ -d "$CLAUDE_DIR" ]; then
    TOTAL_BEFORE=$(du -sk "$CLAUDE_DIR" 2>/dev/null | cut -f1)
    echo "総サイズ: $(($TOTAL_BEFORE / 1024)) MB"
fi
echo ""

echo "🔧 クリーンアップを開始します..."
echo ""

TOTAL_CLEANED=0

# 1. Claude キャッシュの削除
if [ -d "$CLAUDE_DIR/Cache" ]; then
    echo "📦 Claudeキャッシュを削除中..."
    CACHE_SIZE=$(du -sk "$CLAUDE_DIR/Cache" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/Cache"/*
    echo -e "${GREEN}✓ Claudeキャッシュを削除しました ($(($CACHE_SIZE / 1024)) MB)${NC}"
    TOTAL_CLEANED=$((TOTAL_CLEANED + CACHE_SIZE))
fi

# 2. Claude Code キャッシュの削除
if [ -d "$CLAUDE_DIR/Code Cache" ]; then
    echo "📦 Claude Codeキャッシュを削除中..."
    CODE_CACHE_SIZE=$(du -sk "$CLAUDE_DIR/Code Cache" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/Code Cache"/*
    echo -e "${GREEN}✓ Claude Codeキャッシュを削除しました ($(($CODE_CACHE_SIZE / 1024)) MB)${NC}"
    TOTAL_CLEANED=$((TOTAL_CLEANED + CODE_CACHE_SIZE))
fi

# 3. GPUキャッシュの削除
if [ -d "$CLAUDE_DIR/GPUCache" ]; then
    echo "🎮 GPUキャッシュを削除中..."
    GPU_SIZE=$(du -sk "$CLAUDE_DIR/GPUCache" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/GPUCache"/*
    echo -e "${GREEN}✓ GPUキャッシュを削除しました ($(($GPU_SIZE / 1024)) MB)${NC}"
    TOTAL_CLEANED=$((TOTAL_CLEANED + GPU_SIZE))
fi

# 4. WebGPUキャッシュの削除
if [ -d "$CLAUDE_DIR/DawnWebGPUCache" ]; then
    echo "🎮 WebGPUキャッシュを削除中..."
    WEBGPU_SIZE=$(du -sk "$CLAUDE_DIR/DawnWebGPUCache" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/DawnWebGPUCache"/*
    echo -e "${GREEN}✓ WebGPUキャッシュを削除しました ($(($WEBGPU_SIZE / 1024)) MB)${NC}"
    TOTAL_CLEANED=$((TOTAL_CLEANED + WEBGPU_SIZE))
fi

# 5. 古いログファイルの削除
if [ -d "$CLAUDE_DIR/logs" ]; then
    echo "📄 古いログファイルを削除中..."
    OLD_LOGS=$(find "$CLAUDE_DIR/logs" -type f -mtime +7 2>/dev/null | wc -l)
    find "$CLAUDE_DIR/logs" -type f -mtime +7 -delete 2>/dev/null
    echo -e "${GREEN}✓ $OLD_LOGS 個の古いログファイルを削除しました${NC}"
fi

# 6. 破損した設定ファイルの削除
echo "🔧 破損した設定ファイルを削除中..."
CORRUPTED_COUNT=0
for file in ~/.claude.json.corrupted.*; do
    if [ -f "$file" ]; then
        rm "$file"
        ((CORRUPTED_COUNT++))
    fi
done
if [ $CORRUPTED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ $CORRUPTED_COUNT 個の破損した設定ファイルを削除しました${NC}"
fi

# 7. Service Workerの古いデータを削除
if [ -d "$CLAUDE_DIR/Service Worker" ]; then
    echo "🔧 Service Workerの古いデータを削除中..."
    find "$CLAUDE_DIR/Service Worker" -type f -mtime +7 -delete 2>/dev/null
    echo -e "${GREEN}✓ Service Workerの古いデータを削除しました${NC}"
fi

# 8. 一時ファイルの削除
if [ -d "$CLAUDE_DIR/tmp" ]; then
    echo "🗑️  一時ファイルを削除中..."
    rm -rf "$CLAUDE_DIR/tmp"/*
    echo -e "${GREEN}✓ 一時ファイルを削除しました${NC}"
fi

# 9. TradingAgents2プロジェクトの大きなログファイルを確認
echo ""
echo "📊 TradingAgents2プロジェクトの大きなファイルを確認中..."
PROJECT_DIR="/Users/y-sato/TradingAgents2"
if [ -d "$PROJECT_DIR" ]; then
    # 100MB以上のファイルを検索
    LARGE_FILES=$(find "$PROJECT_DIR" -type f -size +100M 2>/dev/null)
    if [ ! -z "$LARGE_FILES" ]; then
        echo -e "${YELLOW}⚠️  100MB以上の大きなファイルが見つかりました:${NC}"
        echo "$LARGE_FILES" | while read file; do
            SIZE=$(du -sh "$file" 2>/dev/null | cut -f1)
            echo "  - $file ($SIZE)"
        done
    fi
    
    # ログディレクトリのサイズを確認
    if [ -d "$PROJECT_DIR/logs" ]; then
        LOGS_SIZE=$(du -sh "$PROJECT_DIR/logs" 2>/dev/null | cut -f1)
        echo "ログディレクトリサイズ: $LOGS_SIZE"
    fi
fi

echo ""
echo "========================================"
echo ""

# 削除後の容量を確認
AFTER_SPACE=$(df -k /System/Volumes/Data | awk 'NR==2 {print $4}')
FREED_SPACE=$((AFTER_SPACE - BEFORE_SPACE))
FREED_SPACE_MB=$((FREED_SPACE / 1024))

# Claude ディレクトリのサイズ (クリーンアップ後)
if [ -d "$CLAUDE_DIR" ]; then
    TOTAL_AFTER=$(du -sk "$CLAUDE_DIR" 2>/dev/null | cut -f1)
    CLAUDE_CLEANED=$((TOTAL_BEFORE - TOTAL_AFTER))
    echo "📁 Claude関連ディレクトリ:"
    echo "  クリーンアップ前: $(($TOTAL_BEFORE / 1024)) MB"
    echo "  クリーンアップ後: $(($TOTAL_AFTER / 1024)) MB"
    echo "  削除されたサイズ: $(($CLAUDE_CLEANED / 1024)) MB"
fi

echo ""
echo "🎉 クリーンアップ完了!"
echo ""
echo "📊 結果サマリー:"
echo "  トータルで解放された容量: ${FREED_SPACE_MB} MB"
echo ""
echo "📈 現在のディスク使用状況:"
df -h /System/Volumes/Data | grep -v Filesystem
echo ""

# アップデートの再試行を提案
CURRENT_FREE=$(df -k /System/Volumes/Data | awk 'NR==2 {print $4}')
CURRENT_FREE_GB=$((CURRENT_FREE / 1024 / 1024))

if [ $CURRENT_FREE_GB -gt 5 ]; then
    echo -e "${GREEN}✅ 十分な空き容量が確保されました！(${CURRENT_FREE_GB}GB)${NC}"
    echo ""
    echo "📌 次のステップ:"
    echo "1. Claude Codeを完全に終了"
    echo "2. Claude Codeを再起動"
    echo "3. アップデートが自動的に開始されるはずです"
else
    echo -e "${YELLOW}⚠️  空き容量がまだ不足しています (現在: ${CURRENT_FREE_GB}GB)${NC}"
    echo "推奨: 最低でも5GB以上の空き容量を確保してください"
    echo ""
    echo "追加でクリーンアップできる場所:"
    echo "  - ~/Downloads の不要なファイル"
    echo "  - ~/Desktop の大きなファイル"
    echo "  - ゴミ箱を空にする"
    echo ""
    echo "大きなファイルを確認するには:"
    echo "  du -sh ~/* | sort -rh | head -20"
fi