# TradingAgents WebUI デプロイガイド

## 🚀 Streamlit Cloud デプロイ

### 必要な準備

#### 1. GitHub リポジトリ準備
```bash
# GitHub にリポジトリをプッシュ
git add .
git commit -m "Add Streamlit Cloud deployment config"
git push origin main
```

#### 2. 必要なファイル確認
- ✅ `requirements.txt` - 依存関係
- ✅ `.streamlit/config.toml` - Streamlit設定
- ✅ `run_webui.py` - メインエントリーポイント

### Streamlit Cloud デプロイ手順

#### Step 1: Streamlit Cloud アカウント作成
1. [https://share.streamlit.io/](https://share.streamlit.io/) にアクセス
2. GitHub アカウントでサインイン
3. リポジトリへのアクセス許可

#### Step 2: アプリケーション設定
```
Repository: YOUR_GITHUB_USERNAME/TradingMultiAgents
Branch: main
Main file path: run_webui.py
```

#### Step 3: 環境変数設定
Streamlit Cloud の設定画面で以下の環境変数を設定：

**必須環境変数:**
```
FINNHUB_API_KEY=your_finnhub_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**オプション環境変数:**
```
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=TradingAgents/1.0
```

#### Step 4: デプロイ実行
1. 「Deploy!」ボタンをクリック
2. ビルドログを確認
3. デプロイ完了後、URLが発行される

### 🔧 ローカル開発環境

#### 環境変数設定
`.env` ファイルを作成：
```bash
# .env ファイル
FINNHUB_API_KEY=your_finnhub_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=TradingAgents/1.0
```

#### ローカル実行
```bash
# 依存関係インストール
pip install -r requirements.txt

# WebUI起動
python run_webui.py

# または直接Streamlit実行
streamlit run webui/app.py
```

### 🐳 Docker デプロイ

#### Dockerfile 例
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "run_webui.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Docker 実行
```bash
# イメージビルド
docker build -t tradingagents-webui .

# コンテナ実行
docker run -p 8501:8501 \
  -e FINNHUB_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  tradingagents-webui
```

### ⚙️ 設定カスタマイズ

#### Streamlit 設定 (`.streamlit/config.toml`)
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

#### WebUI カスタマイズ
- **カラーテーマ**: `webui/app.py` の CSS設定を編集
- **ロゴ画像**: `assets/` ディレクトリに画像を追加
- **ナビゲーション**: `webui/components/` の各コンポーネントを編集

### 🔍 トラブルシューティング

#### よくある問題

**1. 依存関係エラー**
```bash
# requirements.txt のバージョンを確認
pip freeze > current_requirements.txt
# 不要な依存関係を削除
```

**2. 環境変数未設定**
- Streamlit Cloud の Secrets 設定を確認
- ローカルでは `.env` ファイルの存在を確認

**3. ポートエラー**
```bash
# ポート8501が使用中の場合
streamlit run run_webui.py --server.port 8502
```

**4. メモリ不足**
- Streamlit Cloud は 1GB RAM制限
- 大容量データ処理は避ける
- キャッシュ機能を適切に使用

#### ログ確認
```bash
# Streamlit ログレベル設定
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run run_webui.py
```

### 📊 パフォーマンス最適化

#### キャッシュ設定
```python
@st.cache_data(ttl=3600)  # 1時間キャッシュ
def load_market_data():
    # データ読み込み処理
    pass

@st.cache_resource
def initialize_llm():
    # LLM初期化処理
    pass
```

#### セッション状態管理
```python
# 効率的なセッション状態管理
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
```

### 🌐 本番環境考慮事項

#### セキュリティ
- ✅ API キーは環境変数で管理
- ✅ HTTPS 通信を使用
- ✅ ユーザー入力のバリデーション
- ⚠️ 認証機能は未実装（必要に応じて追加）

#### スケーラビリティ
- Streamlit Cloud は単一インスタンス
- 高負荷時は AWS/GCP での自前ホスティングを検討
- 複数ユーザー対応には Redis などの外部状態管理が必要

#### モニタリング
- Streamlit Cloud の使用量ダッシュボード活用
- アプリケーションログの定期確認
- ユーザーフィードバックの収集

## 📞 サポート

デプロイに関する質問は以下で確認：
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Community](https://discuss.streamlit.io/)
- プロジェクトの Issues セクション