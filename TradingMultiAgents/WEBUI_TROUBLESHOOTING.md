# WebUI Troubleshooting Guide

このドキュメントでは、TradingAgents WebUIで発生する可能性のある問題と解決方法を説明します。

## 目次
1. [接続エラー (Connection Error)](#接続エラー-connection-error)
2. [分析実行エラー](#分析実行エラー)
3. [アーキテクチャ不一致エラー](#アーキテクチャ不一致エラー)
4. [その他の一般的な問題](#その他の一般的な問題)

---

## 接続エラー (Connection Error)

### 症状
- ブラウザで「Connection error」が表示される
- 「Is Streamlit still running? If you accidentally stopped Streamlit, just restart it in your terminal.」というメッセージが表示される
- 「申し訳ございません。このページに到達できません」エラー
- ERR_CONNECTION_REFUSED

### 原因
1. **Streamlitプロセスが起動していない**
   - サーバープロセスが正常に起動していない
   - プロセスが異常終了している

2. **ポート番号の不一致**
   - ブラウザでアクセスしているポートと、実際にアプリがリッスンしているポートが異なる

3. **既存プロセスとのポート衝突**
   - 他のアプリケーションが同じポートを使用している

4. **ファイアウォール/ネットワーク設定**
   - macOSのファイアウォールやVPNソフトがlocalhost接続を遮断している

5. **ブラウザ拡張機能の干渉**
   - 広告ブロッカーやセキュリティ拡張機能がWebSocket接続を妨害している

### 解決策

#### 1. Streamlitプロセスの確認と再起動
```bash
# プロセスが動作しているか確認
ps aux | grep streamlit

# 既存のプロセスを終了
pkill -f streamlit

# WebUIを再起動
python run_webui.py
# または
streamlit run webui/app.py
```

#### 2. ポート番号の確認
```bash
# ポート8501が使用されているか確認
lsof -i :8501

# 別のポートで起動
streamlit run webui/app.py --server.port=8502
```

#### 3. ブラウザの問題解決
- プライベート/シークレットモードで試す
- ブラウザの拡張機能を無効化
- 別のブラウザ（Chrome、Firefox、Safari）で試す
- キャッシュとCookieをクリア

#### 4. ファイアウォール設定の確認
```bash
# macOSファイアウォール状態確認
sudo pfctl -s info
```

---

## 分析実行エラー

### 症状
- WebUIから分析を実行しようとするとエラーが発生
- ログに`ImportError`が記録される
- 分析が開始されない
- `BadRequestError: Error code: 400 - This model's maximum context length is 8192 tokens`

### 原因
1. **必要なパッケージがインストールされていない**
2. **環境変数が設定されていない**
3. **Pythonバージョンの不一致**
4. **アーキテクチャの不一致**（下記参照）
5. **埋め込みモデルのトークン制限超過**

### 解決策

#### 1. 依存関係の再インストール
```bash
pip install -r requirements.txt
```

#### 2. 環境変数の設定
```bash
# .envファイルを作成または編集
echo "OPENAI_API_KEY=your-api-key" >> .env
echo "FINNHUB_API_KEY=your-api-key" >> .env

# または環境変数として設定
export OPENAI_API_KEY="your-api-key"
export FINNHUB_API_KEY="your-api-key"
```

#### 3. Pythonバージョンの確認
```bash
python --version  # Python 3.12以上が必要
```

#### 4. 埋め込みモデルのトークン制限エラーの修正
**症状**: `BadRequestError: Error code: 400 - {'error': {'message': "This model's maximum context length is 8192 tokens..."`

**原因**: 
- `text-embedding-3-small`モデルの8,191トークン制限を超過
- 複数のアナリストレポートを連結した際に発生
- 各レポートが詳細な分析とデータテーブルを含むため、合計サイズが大きくなる

**解決済み**: 
`tradingagents/agents/utils/memory.py`にテキスト切り詰め機能を実装済み。30,000文字（約7,500トークン）を超えるテキストは自動的に切り詰められます。

**追加の対策**（必要な場合）:
```bash
# 分析の深さを減らす
--depth 1

# アナリストの数を減らす
--analyst market  # 1つのアナリストのみ

# 議論ラウンドを減らす
--debate-rounds 0
```

---

## アーキテクチャ不一致エラー

### 症状
- `ImportError: dlopen(...) mach-o file, but is an incompatible architecture (have 'arm64', need 'x86_64')`
- モジュールのインポート時にアーキテクチャエラーが発生
- 特に以下のパッケージで発生しやすい：
  - regex
  - tiktoken
  - cffi
  - cryptography
  - xxhash
  - aiohttp
  - tokenizers
  - pandas
  - numpy
  - pillow

### 原因
1. **システムアーキテクチャとパッケージアーキテクチャの不一致**
   - Intel Mac (x86_64) でARM64用のパッケージがインストールされている
   - Apple Silicon Mac (ARM64) でx86_64用のパッケージがインストールされている

2. **複数のPython環境の混在**
   - Miniconda/Anacondaと標準Pythonの混在
   - 異なるPythonバージョン間でのパッケージ共有

3. **pipキャッシュの問題**
   - 以前のアーキテクチャ用パッケージがキャッシュされている

### 詳細な解決手順

#### 1. システムアーキテクチャの確認
```bash
# システムアーキテクチャを確認
uname -m
# 出力例: x86_64 (Intel Mac) または arm64 (Apple Silicon)

# Pythonのアーキテクチャを確認
python -c "import platform; print(platform.machine(), platform.processor())"
```

#### 2. 問題のあるパッケージをすべてアンインストール
```bash
# バイナリコンポーネントを含むパッケージをリストアップ
pip freeze | grep -E "(aiohttp|tokenizers|xxhash|rpds|orjson|yarl|frozenlist|multidict|propcache|pandas|numpy|pillow|regex|tiktoken|cffi|cryptography|curl-cffi|matplotlib|lxml|mini-racer|grpcio|psutil|Pillow|scikit|scipy|pycryptodome)" | cut -d'=' -f1 > packages_to_reinstall.txt

# すべてアンインストール
cat packages_to_reinstall.txt | xargs pip uninstall -y
```

#### 3. pipキャッシュをクリア
```bash
pip cache purge
```

#### 4. 正しいアーキテクチャで再インストール
```bash
# キャッシュを使わずに再インストール
pip install --no-cache-dir -r requirements.txt

# または個別にインストール
pip install --no-cache-dir regex tiktoken cffi cryptography xxhash aiohttp tokenizers pandas numpy pillow
```

#### 5. 特定のアーキテクチャを強制する場合
```bash
# Intel Mac で実行する場合
arch -x86_64 pip install --no-cache-dir -r requirements.txt

# Apple Silicon Mac で実行する場合  
arch -arm64 pip install --no-cache-dir -r requirements.txt
```

### 予防策
1. **仮想環境を使用する**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **condaを使用する場合の注意**
   ```bash
   # 新しい環境を作成
   conda create -n tradingagents python=3.12
   conda activate tradingagents
   # condaではなくpipを使用してインストール
   pip install -r requirements.txt
   ```

---

## その他の一般的な問題

### ポート使用中エラー
```bash
# 使用中のポートを確認
lsof -i :8501

# プロセスを終了
kill -9 [PID]

# または別のポートを使用
python run_webui.py --server.port=8502
```

### メモリ不足エラー
- 分析の深さを減らす（depth パラメータを小さくする）
- 同時に実行する分析の数を減らす
- システムのメモリを増やす

### API制限エラー
- APIキーが正しく設定されているか確認
- API利用制限に達していないか確認
- レート制限を考慮して、分析間隔を空ける

---

## ログの確認方法

### WebUIログ
```bash
# 実行ログの確認
tail -f webui.log

# 分析ログの確認
ls -la logs/webui/
tail -f logs/webui/analysis_*.log
```

### デバッグモードでの実行
```bash
# デバッグログを有効化
STREAMLIT_LOG_LEVEL=debug streamlit run webui/app.py
```

---

## サポート

問題が解決しない場合は、以下の情報を含めて報告してください：

1. エラーメッセージの全文
2. 実行環境（OS、Pythonバージョン、アーキテクチャ）
3. `pip freeze`の出力
4. 関連するログファイル
5. 再現手順

GitHubのIssueまたはDiscussionsで報告してください。