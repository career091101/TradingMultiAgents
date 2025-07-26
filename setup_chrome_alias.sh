#!/bin/bash
# Chrome起動エイリアスのセットアップ

# エイリアスをシェル設定ファイルに追加
echo "# Trading Agents WebUI Chrome alias" >> ~/.zshrc
echo "alias chrome-webui='open -a \"Google Chrome\" --args --window-size=2048,1280 --window-position=0,0 --force-device-scale-factor=1 http://localhost:8501'" >> ~/.zshrc

echo "エイリアスを追加しました。"
echo "新しいターミナルセッションで 'chrome-webui' コマンドが使用可能になります。"
echo ""
echo "今すぐ使用するには："
echo "source ~/.zshrc"