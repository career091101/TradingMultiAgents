# WebUI トラブルシューティングガイド

このドキュメントは、TradingAgents WebUIで発生した主要なエラーとその解決方法をまとめたものです。

## 目次
1. [自動更新によるボタン無効化問題](#1-自動更新によるボタン無効化問題)
2. [datetime型のsubscriptableエラー](#2-datetime型のsubscriptableエラー)
3. [CLI実行エラー (return code: 2)](#3-cli実行エラー-return-code-2)
4. [株価データ取得エラー](#4-株価データ取得エラー)
5. [Connection Error](#5-connection-error)
6. [重要な学び](#重要な学び)

## 1. 自動更新によるボタン無効化問題

### 症状
- 分析開始ボタンがグレーアウトして押せない
- 数秒後にボタンが無効化される
- ユーザー操作が困難になる

### 原因
- Streamlitの`st.rerun()`が5秒ごとに実行され、ページ全体を再レンダリング
- 再レンダリング中はボタンが一時的に無効化される（Streamlitの仕様）
- デフォルトで自動更新がONだったため、ボタンを押すタイミングが限られる

### 解決方法

#### 1. 自動更新のデフォルト値を変更
```python
# webui/utils/state.py
"auto_refresh": False,  # デフォルトをFalseに変更してボタンの無効化を防ぐ
```

#### 2. 更新間隔の延長
```python
# webui/components/execution.py
# 5秒から10秒に変更
if current_time - last_update >= 10:
    SessionState.set("last_update_time", current_time)
    st.rerun()
```

#### 3. チェックボックスのデフォルト値を変更
```python
# webui/components/execution.py
auto_refresh = st.checkbox("自動", value=SessionState.get("auto_refresh", False), key="auto_refresh_toggle")
```

## 2. datetime型のsubscriptableエラー

### 症状
```
TypeError: 'datetime.datetime' object is not subscriptable
```

### 原因
- `timestamp[:19]`のようにスライス演算子を使用
- `timestamp`が文字列ではなくdatetimeオブジェクトの場合にエラー発生
- Pythonではdatetimeオブジェクトに対してスライス演算子が使えない

### 解決方法

```python
# webui/utils/state.py
timestamp_raw = p.get("timestamp", "")
# Handle datetime objects properly
if isinstance(timestamp_raw, str):
    timestamp = timestamp_raw[:19] if len(timestamp_raw) >= 19 else timestamp_raw
elif hasattr(timestamp_raw, 'isoformat'):
    timestamp = timestamp_raw.isoformat()[:19]
else:
    timestamp = str(timestamp_raw)[:19] if timestamp_raw else ""
```

## 3. CLI実行エラー (return code: 2)

### 症状
```
Error: Got unexpected extra argument (analyze)
分析エラー (return code: 2)
```

### 原因
- WebUIが`python -m cli.main analyze`という形式でCLIを呼び出し
- Typerフレームワークは単一コマンドの場合、サブコマンド名を省略する仕様
- `analyze`が余分な引数として認識される

### 解決方法

#### 1. CLI引数サポートの追加
```python
# cli/main.py
@app.command()
def analyze(
    ticker: str = typer.Option(None, "--ticker", help="Stock ticker symbol"),
    date: str = typer.Option(None, "--date", help="Analysis date (YYYY-MM-DD)"),
    depth: int = typer.Option(None, "--depth", help="Research depth (1-5)"),
    provider: str = typer.Option(None, "--provider", help="LLM provider"),
    shallow_model: str = typer.Option(None, "--shallow-model", help="Shallow thinking model"),
    deep_model: str = typer.Option(None, "--deep-model", help="Deep thinking model"),
    analyst: List[str] = typer.Option(None, "--analyst", help="Analyst types")
):
```

#### 2. CLIコマンドの修正
```python
# webui/backend/cli_wrapper.py
# 修正前
cmd = [python_executable, "-m", "cli.main", "analyze", "--ticker", config.ticker, ...]

# 修正後（analyzeを削除）
cmd = [python_executable, "-m", "cli.main", "--ticker", config.ticker, ...]
```

## 4. 株価データ取得エラー

### 症状
```
Error tokenizing data. C error: Expected 6 fields in line 698, saw 9
time data "5" doesn't match format "%Y-%m-%d"
```

### 原因
- CSVファイル最終行に不正データ「5,63624600」が存在
- 週末（土曜日）のデータ取得時にエラー発生
- データパースエラー

### 解決方法

#### 1. CSVファイルの修正
```bash
# バックアップを作成
cp "SPY-YFin-data-2010-07-14-2025-07-14.csv" "SPY-YFin-data-2010-07-14-2025-07-14.csv.bak"

# 最後の行を削除
sed -i '' '$d' "SPY-YFin-data-2010-07-14-2025-07-14.csv"
```

#### 2. 週末日付の回避
- 分析は平日（月曜〜金曜）の日付で実行
- 例：2025-07-11（金曜日）を使用

## 5. Connection Error

### 症状
- 「Is Streamlit still running?」エラーダイアログ
- WebUIがクラッシュして接続が切断される

### 原因
- 上記のエラーが連鎖的に発生
- エラー処理が不十分でアプリケーション全体が停止
- Streamlitプロセスがクラッシュ

### 解決方法
1. 各エラーを個別に修正（上記1-4の対応）
2. エラーハンドリングの強化
3. プロセスの安定性向上

## 重要な学び

### 1. Streamlitの制約を理解
- 頻繁な`st.rerun()`はUXを損なう
- ボタンの状態管理には注意が必要
- 部分的な更新よりも全体更新になることを考慮

### 2. 型安全性の重要性
- Pythonでも型チェックは必須
- 特に外部データとの境界では型変換を明示的に行う
- `isinstance()`や`hasattr()`を活用

### 3. CLIフレームワークの仕様理解
- Typerの動作を正しく把握
- 単一コマンドと複数コマンドの違いを理解
- コマンドライン引数の設計は慎重に

### 4. データ整合性
- 外部データソースは常に検証が必要
- CSVファイルの形式チェック
- 日付データの妥当性確認

### 5. 段階的なデバッグ
- 複合的なエラーは一つずつ解決
- ログを活用した原因特定
- 最小限の再現コードでテスト

## 推奨される運用方法

1. **初回実行時の設定**
   - 自動更新: OFF
   - 日付: 平日を選択
   - 研究深度: 1（テスト用）

2. **エラー発生時の対処**
   - 実行ログを確認
   - 日付が平日かどうか確認
   - WebUIを再起動

3. **安定運用のために**
   - 定期的なデータキャッシュのクリーンアップ
   - ログファイルのローテーション
   - 環境変数の確認

## 関連ファイル

- `/webui/components/execution.py` - 実行画面のメインコンポーネント
- `/webui/utils/state.py` - セッション状態管理
- `/cli/main.py` - CLIのメインエントリーポイント
- `/webui/backend/cli_wrapper.py` - CLI実行ラッパー
- `/e2e_test_execution_logs.py` - E2Eテストスクリプト

## 6. Streamlit Connection Error

### 症状
- ブラウザに「Connection error」ダイアログが表示される
- 「Is Streamlit still running? If you accidentally stopped Streamlit, just restart it in your terminal.」というメッセージ
- WebUIのボタンがクリックできない
- UIが完全にブロックされる

### 原因
- Streamlitプロセスが停止している
- バックエンドサーバーがクラッシュまたは終了している
- ネットワーク接続の問題
- ポート8501が解放されている

### 診断方法
```bash
# Streamlitプロセスの確認
ps aux | grep streamlit

# ポート使用状況の確認
lsof -i :8501
```

### 解決方法

#### 1. プロセスの確認と再起動
```bash
# プロセスが動いていない場合は再起動
cd /Users/y-sato/TradingAgents2/TradingMultiAgents
python run_webui.py

# またはバックグラウンドで実行
nohup python run_webui.py > webui.log 2>&1 &
```

#### 2. 既存プロセスの終了と再起動
```bash
# 既存のStreamlitプロセスを終了
pkill -f streamlit

# 少し待ってから再起動
sleep 2
python run_webui.py
```

#### 3. ポートの競合を回避
```bash
# 別のポートで起動
streamlit run webui/app.py --server.port 8502
```

### 予防策
1. WebUIの安定性向上
   - エラーハンドリングの強化
   - 適切なタイムアウト設定
   - リソースの適切な解放

2. モニタリング
   - プロセス監視の実装
   - 自動再起動スクリプトの作成
   - ログの定期的な確認

## 7. アーキテクチャ不一致エラー (M1 Mac)

### 症状
```
mach-o file, but is an incompatible architecture (have 'x86_64', need 'arm64e' or 'arm64')
```

### 原因
- M1 Mac（ARM64）環境でx86_64バイナリのパッケージがインストールされている
- Rosetta 2経由でのパッケージとネイティブARM64パッケージの混在
- 依存関係の不整合

### 解決方法

#### 1. 問題のあるパッケージを特定
```bash
# アーキテクチャを確認
file $(python -c "import grpc; print(grpc.__file__)") | grep -v arm64
```

#### 2. x86_64パッケージをアンインストール
```bash
pip uninstall grpcio protobuf google-api-core orjson -y
```

#### 3. ARM64ネイティブパッケージをインストール
```bash
# ARM64モードで強制的にインストール
arch -arm64 pip install --no-cache-dir --force-reinstall \
    grpcio==1.68.1 \
    protobuf==5.29.2 \
    google-api-core==2.25.0 \
    orjson==3.10.12
```

#### 4. 環境全体のクリーンアップ（必要に応じて）
```bash
# 新しい仮想環境を作成
conda create -n tradingagents-arm python=3.13
conda activate tradingagents-arm

# ARM64モードで依存関係をインストール
arch -arm64 pip install -r requirements.txt
```

### 予防策
1. 常にARM64モードでパッケージをインストール
2. `arch -arm64`プレフィックスを使用
3. `--no-cache-dir`オプションでキャッシュを無視
4. 仮想環境を使用して依存関係を隔離

## 8. backtest2モジュールのインポートエラー

### 症状
```
ImportError: cannot import name 'BacktestResult' from 'backtest2.core.types'
```

### 原因
- 循環インポートの問題
- モジュール構造の不整合
- 誤ったインポートパス

### 解決方法

#### 1. インポートパスの修正
```python
# 誤ったインポート
from backtest2.core.types import BacktestResult

# 正しいインポート
from backtest2.core.results_simple import BacktestResult
```

#### 2. 循環インポートの解消
```python
# backtest2/analysis/benchmark.py
# トップレベルインポートを避ける
from ..core.types import PortfolioState
from ..core.results_simple import BacktestResult  # 循環を避ける
```

#### 3. 初期化ファイルの作成
```bash
# 必要な__init__.pyファイルを作成
touch backtest2/analysis/__init__.py
```

```python
# backtest2/analysis/__init__.py
from .metrics import MetricsCalculator
from .benchmark import BenchmarkComparator

__all__ = ['MetricsCalculator', 'BenchmarkComparator']
```

## 更新履歴

- 2025-07-14: 初版作成
- 自動更新問題、datetime型エラー、CLI引数エラー、データ取得エラーの解決方法を文書化
- 2025-07-21: 追加更新
  - Streamlit Connection Errorの診断と解決方法
  - M1 Mac（ARM64）でのアーキテクチャ不一致エラーの対処法
  - backtest2モジュールのインポートエラーの解決方法