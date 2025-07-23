# 実行ログページ 要件定義書

## 1. 概要

### 1.1 目的
TradingAgents WebUIにおいて、CLIの実行ログをリアルタイムで確認できる専用ページを提供し、分析プロセスの透明性と問題診断能力を向上させる。

### 1.2 背景
- 現状：分析実行中の詳細な進捗が見えない
- 課題：エラー発生時の原因特定が困難
- 解決：CLIと同等のログ出力をWebUIで提供

### 1.3 スコープ
- リアルタイムログ表示
- 過去の実行ログ閲覧
- ログのフィルタリング・検索
- エラー診断支援機能

## 2. 機能要件

### 2.1 ログ表示機能

#### 2.1.1 リアルタイムログストリーミング
```
要件：
- 実行中の分析ログをリアルタイムで表示
- 1秒以内の遅延で更新
- 自動スクロール（最新ログを追従）
- 手動スクロール時は自動スクロール一時停止
```

#### 2.1.2 ログフォーマット
```
[2025-01-17 14:30:15] [INFO] [Market Analyst] テクニカル分析を開始します
[2025-01-17 14:30:16] [DEBUG] [API] FinnHub API呼び出し: /quote/AAPL
[2025-01-17 14:30:17] [INFO] [Market Analyst] RSI: 65.4, MACD: 0.23
[2025-01-17 14:30:20] [ERROR] [News Analyst] APIレート制限に達しました
```

#### 2.1.3 ログレベル
- **TRACE**: 詳細なデバッグ情報
- **DEBUG**: デバッグ情報
- **INFO**: 一般的な情報
- **WARNING**: 警告
- **ERROR**: エラー
- **CRITICAL**: 致命的エラー

### 2.2 フィルタリング機能

#### 2.2.1 ログレベルフィルター
```python
# UI例
log_levels = st.multiselect(
    "表示するログレベル",
    ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default=["INFO", "WARNING", "ERROR", "CRITICAL"]
)
```

#### 2.2.2 エージェントフィルター
```python
# フィルター可能なエージェント
agents = [
    "System",
    "Market Analyst",
    "News Analyst", 
    "Social Analyst",
    "Fundamentals Analyst",
    "Bull Researcher",
    "Bear Researcher",
    "Research Manager",
    "Risk Management",
    "Trader",
    "Portfolio Manager"
]
```

#### 2.2.3 時間範囲フィルター
- 直近5分
- 直近30分
- 全期間
- カスタム時間範囲

### 2.3 検索機能

#### 2.3.1 テキスト検索
- 大文字小文字を区別しない
- 正規表現サポート
- ハイライト表示

#### 2.3.2 クイック検索
- エラーのみ表示
- API呼び出しのみ
- 特定ティッカー
- 特定日付

### 2.4 ログ管理機能

#### 2.4.1 ログの保存
```
保存形式：
- プレーンテキスト (.log)
- JSON形式 (.json)
- CSV形式 (.csv)
```

#### 2.4.2 ログのエクスポート
```python
# エクスポート例
def export_logs(logs: List[LogEntry], format: str) -> bytes:
    if format == "json":
        return json.dumps([log.dict() for log in logs])
    elif format == "csv":
        # CSV変換ロジック
    elif format == "txt":
        # テキスト変換ロジック
```

#### 2.4.3 ログの削除
- 古いログの自動削除（30日経過）
- 手動削除オプション
- 削除前の確認ダイアログ

### 2.5 視覚的機能

#### 2.5.1 色分け表示
```css
/* ログレベル別の色分け */
.log-trace { color: #gray; }
.log-debug { color: #blue; }
.log-info { color: #green; }
.log-warning { color: #orange; }
.log-error { color: #red; }
.log-critical { background: #red; color: white; }
```

#### 2.5.2 アイコン表示
```
🔍 TRACE
🐛 DEBUG
ℹ️ INFO
⚠️ WARNING
❌ ERROR
🚨 CRITICAL
```

#### 2.5.3 進捗インジケーター
- 現在実行中のエージェント
- 完了したステップ
- 推定残り時間

### 2.6 統計情報

#### 2.6.1 ログ統計
```python
statistics = {
    "total_logs": 1234,
    "by_level": {
        "INFO": 800,
        "WARNING": 50,
        "ERROR": 10
    },
    "by_agent": {
        "Market Analyst": 300,
        "News Analyst": 250
    },
    "api_calls": 45,
    "execution_time": "12:34"
}
```

#### 2.6.2 エラー分析
- エラー頻度
- エラータイプ別集計
- エラー発生箇所

## 3. 非機能要件

### 3.1 パフォーマンス
- **ログ表示**: 10,000行まで遅延なし
- **検索**: 1秒以内に結果表示
- **メモリ使用**: 最大100MB
- **更新頻度**: 最大10回/秒

### 3.2 ユーザビリティ
- **自動更新**: デフォルトで有効
- **コピー機能**: ログの選択・コピー
- **ショートカット**: キーボード操作対応
- **レスポンシブ**: モバイル対応

### 3.3 信頼性
- **ログ欠落防止**: バッファリング
- **エラー回復**: 自動再接続
- **データ整合性**: タイムスタンプ順序保証

## 4. UI/UXデザイン

### 4.1 ページレイアウト
```
┌─────────────────────────────────────────────┐
│ 🔍 実行ログ                                  │
├─────────────────────────────────────────────┤
│ [フィルター] [検索] [エクスポート] [クリア]    │
├─────────────────────────────────────────────┤
│ ┌───────────┬─────────────────────────────┐ │
│ │ サイドバー │  ログ表示エリア              │ │
│ │           │ ┌─────────────────────────┐ │ │
│ │ ログレベル │ │ [14:30:15] [INFO]      │ │ │
│ │ □ DEBUG   │ │ Market Analyst:        │ │ │
│ │ ☑ INFO    │ │ 分析を開始します        │ │ │
│ │ ☑ WARNING │ │                       │ │ │
│ │ ☑ ERROR   │ │ [14:30:16] [DEBUG]    │ │ │
│ │           │ │ API呼び出し...         │ │ │
│ │ エージェント│ └─────────────────────────┘ │ │
│ │ ☑ 全て選択 │                              │ │
│ │ □ Market  │  [自動スクロール ON]         │ │
│ │ □ News    │                              │ │
│ └───────────┴─────────────────────────────┘ │
│ 統計: 総ログ数 1,234 | エラー 10 | 実行時間 12:34 │
└─────────────────────────────────────────────┘
```

### 4.2 インタラクション

#### 4.2.1 ログエントリー操作
- **クリック**: 詳細表示
- **ダブルクリック**: 関連ログをハイライト
- **右クリック**: コンテキストメニュー
- **ドラッグ**: 複数選択

#### 4.2.2 キーボードショートカット
- `Ctrl+F`: 検索
- `Ctrl+L`: ログクリア
- `Ctrl+E`: エクスポート
- `Space`: 自動スクロール切り替え
- `↑↓`: ログ間移動

### 4.3 モバイル対応
- タッチ操作対応
- 横スクロール対応
- フィルターの折りたたみ
- 簡易表示モード

## 5. 技術仕様

### 5.1 データモデル
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class LogEntry:
    timestamp: datetime
    level: str  # TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
    agent: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
@dataclass
class LogSession:
    session_id: str
    ticker: str
    analysis_date: str
    start_time: datetime
    end_time: Optional[datetime]
    log_file_path: str
    status: str  # running, completed, error
```

### 5.2 ログストリーミング実装
```python
class LogStreamer:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.position = 0
        
    async def stream_logs(self) -> AsyncIterator[LogEntry]:
        """ログファイルから新しいエントリーをストリーミング"""
        while True:
            with open(self.log_file_path, 'r') as f:
                f.seek(self.position)
                lines = f.readlines()
                self.position = f.tell()
                
            for line in lines:
                if entry := self._parse_log_line(line):
                    yield entry
                    
            await asyncio.sleep(0.1)  # 100ms待機
```

### 5.3 Streamlit実装
```python
# ログ表示コンポーネント
def render_log_viewer(logs: List[LogEntry], filters: LogFilters):
    # ログコンテナ（自動更新対応）
    log_container = st.container()
    
    # 仮想スクロール対応
    visible_logs = logs[-1000:]  # 最新1000件のみ表示
    
    with log_container:
        for log in visible_logs:
            if should_display(log, filters):
                render_log_entry(log)
```

## 6. 実装計画

### Phase 1: 基本機能（1週間）
1. ログページの作成
2. リアルタイムログ表示
3. 基本的なフィルタリング

### Phase 2: 高度な機能（1週間）
4. 検索機能
5. エクスポート機能
6. 統計情報表示

### Phase 3: 最適化（3日）
7. パフォーマンス最適化
8. UIポリッシュ
9. テスト・デバッグ

## 7. テスト要件

### 7.1 機能テスト
- ログ表示の正確性
- フィルタリングの動作
- 検索結果の妥当性
- エクスポートデータの整合性

### 7.2 パフォーマンステスト
- 大量ログ（10,000行以上）での動作
- 長時間実行時のメモリリーク
- 同時接続時の負荷

### 7.3 ユーザビリティテスト
- 操作の直感性
- レスポンスタイム
- エラーメッセージの分かりやすさ

## 8. 成功指標

### 8.1 定量的指標
- ログ表示遅延: < 1秒
- 検索応答時間: < 1秒
- ページロード時間: < 3秒
- メモリ使用量: < 100MB

### 8.2 定性的指標
- エラー診断時間の短縮
- ユーザー満足度の向上
- 問題解決速度の改善

## 9. リスクと対策

### 9.1 技術的リスク
| リスク | 影響 | 対策 |
|--------|------|------|
| 大量ログでのパフォーマンス低下 | 高 | 仮想スクロール実装 |
| リアルタイム更新の遅延 | 中 | WebSocket検討 |
| ログファイルの破損 | 低 | エラーハンドリング強化 |

### 9.2 運用リスク
| リスク | 影響 | 対策 |
|--------|------|------|
| ディスク容量不足 | 高 | 自動削除機能 |
| 同時アクセス競合 | 中 | ファイルロック実装 |

## 10. 将来の拡張

### 10.1 高度な分析機能
- ログパターン分析
- 異常検知
- パフォーマンストレンド

### 10.2 連携機能
- 外部ログ管理システム連携
- アラート通知
- ログのアーカイブ

### 10.3 可視化
- ログ統計ダッシュボード
- エラー率グラフ
- エージェント別実行時間

---

*作成日: 2025-01-17*
*バージョン: 1.0*
*担当: TradingAgents Team*