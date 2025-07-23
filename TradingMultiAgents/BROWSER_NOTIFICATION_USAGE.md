# ブラウザ通知機能 使用ガイド

## 概要
TradingAgents WebUIにブラウザ通知機能を実装しました。分析が完了すると、ブラウザに通知が表示されます。

## セットアップ

### 1. 必要なパッケージのインストール
```bash
pip install streamlit-push-notifications
```

### 2. Redis（オプション）
通知キューの永続化にRedisを使用します（オプション）：
```bash
# Dockerを使用する場合
docker run -d -p 6379:6379 redis:7-alpine

# Homebrewを使用する場合（Mac）
brew install redis
brew services start redis
```

Redisが利用できない場合でも、基本的な通知機能は動作します。

## 使用方法

### 1. WebUIで通知を有効化

1. WebUIを起動：
   ```bash
   python run_webui.py
   ```

2. 「⚙️ 分析設定」ページに移動

3. 「🔔 ブラウザ通知設定」セクションで「ブラウザ通知を有効にする」をON

4. ブラウザから通知許可を求められたら「許可」をクリック

5. テスト通知を送信して動作確認

### 2. 分析実行時の通知

分析を実行すると、完了時に以下の情報を含む通知が表示されます：

- ティッカーシンボル
- 推奨アクション（買い/売り/保有）
- 信頼度
- 分析時間

### 3. 通知の確認

- 通知をクリックすると結果ページに直接移動できます
- 見逃した通知は「通知履歴」で確認できます

## トラブルシューティング

### 通知が表示されない場合

1. **ブラウザの通知設定を確認**
   - ブラウザの設定で通知が許可されているか確認
   - サイレントモードがオフになっているか確認

2. **パッケージの確認**
   ```bash
   pip list | grep streamlit-push-notifications
   ```

3. **Redisの状態確認**（オプション）
   ```bash
   redis-cli ping
   # PONGが返ってくれば正常
   ```

### テスト方法

通知機能のテスト：
```bash
python test_browser_notification.py
```

## 制限事項

1. **HTTPS環境でのみ動作**
   - 本番環境ではHTTPSが必須
   - ローカル開発環境（localhost）では動作します

2. **ブラウザサポート**
   - Chrome、Firefox、Edge、Safariの最新版で動作
   - モバイルブラウザでは制限がある場合があります

3. **Streamlitの制約**
   - ページリロード時に通知状態がリセットされる可能性
   - Redisを使用することで通知の永続化が可能

## 今後の拡張予定

1. **通知のカスタマイズ**
   - 通知音の設定
   - 通知条件の詳細設定（特定の推奨時のみ等）

2. **他の通知チャネル**
   - メール通知
   - Slack/Discord連携
   - LINE通知

3. **通知分析**
   - 通知のクリック率追跡
   - 通知効果の分析

## 開発者向け情報

### アーキテクチャ

```
WebUI (Streamlit)
    ↓
通知ハンドラー
    ↓
通知サービス → Redis（オプション）
    ↓
streamlit-push-notifications
    ↓
ブラウザ通知API
```

### 主要コンポーネント

1. **`tradingagents/services/browser_notification.py`**
   - 通知サービスの実装
   - Redisキュー管理

2. **`webui/components/notification_handler.py`**
   - Streamlit統合
   - UI設定画面

3. **`webui/backend/cli_wrapper.py`**
   - 分析完了時の通知送信

### カスタマイズ

通知内容をカスタマイズする場合：

```python
# tradingagents/services/browser_notification.py
def create_analysis_notification(self, ...):
    # タイトルとボディをカスタマイズ
    title = f"📈 {ticker} 分析完了"
    body = f"{recommendation_jp} (信頼度: {confidence:.0%})"
```

---

質問や問題がある場合は、GitHubのIssueで報告してください。