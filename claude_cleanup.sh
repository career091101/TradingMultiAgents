#!/bin/bash

# Claude Code Auto-Cleanup Script
# このスクリプトはClaude Code関連の不要ファイルを安全に削除し、ディスク容量を確保します

echo "🧹 Claude Code クリーンアップスクリプト"
echo "========================================"
echo ""

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 現在のディスク使用状況を表示
echo "📊 現在のディスク使用状況:"
df -h /System/Volumes/Data | grep -v Filesystem
echo ""

# 削除前の容量を記録
BEFORE_SPACE=$(df -k /System/Volumes/Data | awk 'NR==2 {print $4}')

# Claude関連ディレクトリのサイズを確認
echo "📁 Claude関連ディレクトリのサイズ:"
CLAUDE_DIR="$HOME/Library/Application Support/Claude"
if [ -d "$CLAUDE_DIR" ]; then
    du -sh "$CLAUDE_DIR" 2>/dev/null || echo "アクセスできません"
    echo ""
    echo "詳細:"
    du -sh "$CLAUDE_DIR"/* 2>/dev/null | sort -rh | head -10
else
    echo "Claude ディレクトリが見つかりません"
fi
echo ""

# ユーザーに確認
echo -e "${YELLOW}⚠️  以下のファイルをクリーンアップします:${NC}"
echo "1. Claude キャッシュファイル"
echo "2. Claude Code キャッシュ"
echo "3. 古いログファイル (30日以上)"
echo "4. 破損した設定ファイル"
echo "5. 一時ファイル"
echo ""
read -p "続行しますか? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "キャンセルしました。"
    exit 0
fi

echo ""
echo "🔧 クリーンアップを開始します..."
echo ""

# 1. Claude キャッシュの削除
if [ -d "$CLAUDE_DIR/Cache" ]; then
    echo "📦 Claudeキャッシュを削除中..."
    CACHE_SIZE=$(du -sh "$CLAUDE_DIR/Cache" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/Cache"/*
    echo -e "${GREEN}✓ Claudeキャッシュを削除しました ($CACHE_SIZE)${NC}"
else
    echo "⚠️  Claudeキャッシュディレクトリが見つかりません"
fi

# 2. Claude Code キャッシュの削除
if [ -d "$CLAUDE_DIR/Code Cache" ]; then
    echo "📦 Claude Codeキャッシュを削除中..."
    CODE_CACHE_SIZE=$(du -sh "$CLAUDE_DIR/Code Cache" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/Code Cache"/*
    echo -e "${GREEN}✓ Claude Codeキャッシュを削除しました ($CODE_CACHE_SIZE)${NC}"
else
    echo "⚠️  Claude Codeキャッシュディレクトリが見つかりません"
fi

# 3. 古いログファイルの削除
if [ -d "$CLAUDE_DIR/logs" ]; then
    echo "📄 古いログファイルを削除中..."
    OLD_LOGS=$(find "$CLAUDE_DIR/logs" -type f -mtime +30 2>/dev/null | wc -l)
    find "$CLAUDE_DIR/logs" -type f -mtime +30 -delete 2>/dev/null
    echo -e "${GREEN}✓ $OLD_LOGS 個の古いログファイルを削除しました${NC}"
fi

# 4. 破損した設定ファイルの削除
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
else
    echo "破損した設定ファイルは見つかりませんでした"
fi

# 5. 一時ファイルの削除
if [ -d "$CLAUDE_DIR/tmp" ]; then
    echo "🗑️  一時ファイルを削除中..."
    TMP_SIZE=$(du -sh "$CLAUDE_DIR/tmp" 2>/dev/null | cut -f1)
    rm -rf "$CLAUDE_DIR/tmp"/*
    echo -e "${GREEN}✓ 一時ファイルを削除しました ($TMP_SIZE)${NC}"
fi

# 6. 大きなセッションファイルの確認
if [ -d "$CLAUDE_DIR/Session Storage" ]; then
    echo ""
    echo "📊 セッションストレージのサイズ:"
    SESSION_SIZE=$(du -sh "$CLAUDE_DIR/Session Storage" 2>/dev/null | cut -f1)
    echo "現在のサイズ: $SESSION_SIZE"
    
    # 1GB以上の場合は警告
    SIZE_MB=$(du -sm "$CLAUDE_DIR/Session Storage" 2>/dev/null | cut -f1)
    if [ "$SIZE_MB" -gt 1024 ]; then
        echo -e "${YELLOW}⚠️  セッションストレージが1GB以上です。${NC}"
        read -p "古いセッションデータを削除しますか? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            find "$CLAUDE_DIR/Session Storage" -type f -mtime +7 -delete 2>/dev/null
            echo -e "${GREEN}✓ 7日以上前のセッションデータを削除しました${NC}"
        fi
    fi
fi

echo ""
echo "========================================"
echo ""

# 削除後の容量を確認
AFTER_SPACE=$(df -k /System/Volumes/Data | awk 'NR==2 {print $4}')
FREED_SPACE=$((AFTER_SPACE - BEFORE_SPACE))
FREED_SPACE_MB=$((FREED_SPACE / 1024))

echo "🎉 クリーンアップ完了!"
echo ""
echo "📊 結果:"
echo "解放された容量: ${FREED_SPACE_MB} MB"
echo ""
echo "📈 現在のディスク使用状況:"
df -h /System/Volumes/Data | grep -v Filesystem
echo ""

# アップデートの再試行を提案
if [ $FREED_SPACE_MB -gt 1000 ]; then
    echo -e "${GREEN}✅ 十分な空き容量が確保されました！${NC}"
    echo "Claude Codeを再起動してアップデートを再試行してください。"
else
    echo -e "${YELLOW}⚠️  追加の空き容量確保が必要かもしれません。${NC}"
    echo "以下のコマンドで大きなファイルを確認できます:"
    echo "  du -sh ~/* | sort -rh | head -20"
fi

echo ""
echo "完了しました。"