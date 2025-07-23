# 実行ログ日本語化実装ガイド

## 現状分析

TradingAgentsプロジェクトは部分的に日本語化されていますが、統一されていません：

- **日本語**: CLI UI、エージェントプロンプト
- **英語**: エラーメッセージ、内部ログ、デバッグ出力

## 実装方針

### 短期的解決策（即実装可能）

1. **ログメッセージの日本語マッピング作成**
2. **WebUIでのリアルタイム翻訳**
3. **既存ログの日本語化**

### 長期的解決策

1. **i18n対応**（gettext使用）
2. **言語切り替え機能**
3. **翻訳ファイル管理**

## 実装詳細

### 1. ログメッセージマッピング

```python
# webui/utils/log_translator.py
class LogTranslator:
    """ログメッセージを日本語に翻訳"""
    
    # 一般的なパターンの翻訳
    PATTERNS = {
        # API関連
        r"API call to (.+)": "API呼び出し: {0}",
        r"API rate limit reached": "APIレート制限に達しました",
        r"API error: (.+)": "APIエラー: {0}",
        
        # エージェント関連
        r"Starting analysis": "分析を開始します",
        r"Analysis completed": "分析が完了しました",
        r"Generating report": "レポートを生成中",
        
        # エラー関連
        r"Error: (.+)": "エラー: {0}",
        r"Failed to (.+)": "{0}に失敗しました",
        r"Connection timeout": "接続タイムアウト",
        
        # ツール関連
        r"Tool Call: (.+)": "ツール呼び出し: {0}",
        r"Fetching data": "データを取得中",
        r"Processing (.+)": "{0}を処理中",
    }
    
    # 固定メッセージの翻訳
    MESSAGES = {
        # Market Analyst
        "Analyzing technical indicators": "テクニカル指標を分析中",
        "Calculating RSI": "RSIを計算中",
        "Calculating MACD": "MACDを計算中",
        "Analyzing volume patterns": "出来高パターンを分析中",
        
        # News Analyst
        "Fetching news articles": "ニュース記事を取得中",
        "Analyzing sentiment": "センチメントを分析中",
        "Processing news data": "ニュースデータを処理中",
        
        # Fundamentals Analyst
        "Fetching financial data": "財務データを取得中",
        "Analyzing balance sheet": "貸借対照表を分析中",
        "Calculating financial ratios": "財務比率を計算中",
        
        # Research Team
        "Bull researcher analyzing": "強気派研究者が分析中",
        "Bear researcher analyzing": "弱気派研究者が分析中",
        "Research manager reviewing": "研究マネージャーがレビュー中",
        
        # Risk Management
        "Evaluating risk factors": "リスク要因を評価中",
        "Calculating risk metrics": "リスク指標を計算中",
        
        # System
        "Initializing system": "システムを初期化中",
        "Loading configuration": "設定を読み込み中",
        "Saving results": "結果を保存中",
    }
```

### 2. エージェント名の日本語化

```python
# webui/utils/agent_names.py
AGENT_NAME_MAP = {
    # アナリスト
    "Market Analyst": "市場アナリスト",
    "News Analyst": "ニュースアナリスト",
    "Social Analyst": "ソーシャルアナリスト",
    "Fundamentals Analyst": "ファンダメンタルアナリスト",
    
    # 研究チーム
    "Bull Researcher": "強気派研究者",
    "Bear Researcher": "弱気派研究者",
    "Research Manager": "研究マネージャー",
    
    # リスク管理
    "Aggressive Analyst": "積極派アナリスト",
    "Conservative Analyst": "保守派アナリスト",
    "Neutral Analyst": "中立派アナリスト",
    
    # トレーディング
    "Trader": "トレーダー",
    "Portfolio Manager": "ポートフォリオマネージャー",
    
    # システム
    "System": "システム",
    "CLI": "CLI",
    "API": "API",
}
```

### 3. ログパーサーの拡張

```python
# webui/utils/log_parser.py に追加
class JapaneseLogParser(LogParser):
    """日本語対応ログパーサー"""
    
    def __init__(self, translate=True):
        super().__init__()
        self.translate = translate
        self.translator = LogTranslator() if translate else None
        
    def _translate_message(self, message: str) -> str:
        """メッセージを日本語に翻訳"""
        if not self.translator:
            return message
            
        # パターンマッチング
        for pattern, template in self.translator.PATTERNS.items():
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                return template.format(*match.groups())
        
        # 固定メッセージ
        if message in self.translator.MESSAGES:
            return self.translator.MESSAGES[message]
        
        # 翻訳できない場合は元のメッセージを返す
        return message
    
    def _translate_agent(self, agent: str) -> str:
        """エージェント名を日本語に翻訳"""
        return AGENT_NAME_MAP.get(agent, agent)
    
    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """行をパースして翻訳"""
        entry = super().parse_line(line, line_number)
        
        if entry and self.translate:
            # メッセージとエージェント名を翻訳
            entry.message = self._translate_message(entry.message)
            entry.agent = self._translate_agent(entry.agent)
            
        return entry
```

### 4. 実行ログページの更新

```python
# webui/components/logs.py の修正
class LogsPage:
    def __init__(self):
        self.session_manager = get_session_manager()
        # 日本語対応パーサーを使用
        self.parser = JapaneseLogParser(translate=True)
        self._init_session_state()
    
    def _init_session_state(self):
        """セッション状態の初期化"""
        if "log_language" not in st.session_state:
            st.session_state.log_language = "ja"  # デフォルトは日本語
        
        # ... 既存のコード ...
    
    def _render_language_toggle(self):
        """言語切り替えUI"""
        col1, col2 = st.columns([3, 1])
        
        with col2:
            language = st.selectbox(
                "ログ言語",
                ["ja", "en"],
                format_func=lambda x: "日本語" if x == "ja" else "English",
                index=0 if st.session_state.log_language == "ja" else 1
            )
            
            if language != st.session_state.log_language:
                st.session_state.log_language = language
                # パーサーを再作成
                self.parser = JapaneseLogParser(translate=(language == "ja"))
                st.rerun()
```

### 5. CLI側の日本語化強化

```python
# cli/messages.py (新規作成)
"""CLIメッセージの定義"""

class Messages:
    """統一されたメッセージ定義"""
    
    # ウェルカムメッセージ
    WELCOME = "TradingAgents CLIへようこそ"
    
    # ステップメッセージ
    STEP_TICKER = "ステップ 1: ティッカーシンボル"
    STEP_DATE = "ステップ 2: 分析日"
    STEP_ANALYSTS = "ステップ 3: アナリスト選択"
    STEP_DEPTH = "ステップ 4: 研究深度"
    STEP_LLM = "ステップ 5: LLMプロバイダー"
    
    # 進捗メッセージ
    ANALYZING = "分析を実行中..."
    FETCHING_DATA = "データを取得中..."
    GENERATING_REPORT = "レポートを生成中..."
    
    # エラーメッセージ
    ERROR_NO_TICKER = "ティッカーシンボルが指定されていません"
    ERROR_NO_DATE = "分析日が指定されていません"
    ERROR_FUTURE_DATE = "分析日は未来の日付にできません"
    ERROR_API_KEY = "APIキーが設定されていません: {}"
    ERROR_CONNECTION = "接続エラー: {}"
    
    # 完了メッセージ
    ANALYSIS_COMPLETE = "分析が完了しました"
    REPORT_SAVED = "レポートを保存しました: {}"
```

### 6. 設定による言語切り替え

```python
# tradingagents/config.py に追加
class Config:
    # ... 既存のコード ...
    
    @property
    def language(self) -> str:
        """UI言語を取得"""
        return os.getenv("TRADINGAGENTS_LANGUAGE", "ja")
    
    @property
    def log_language(self) -> str:
        """ログ言語を取得"""
        return os.getenv("TRADINGAGENTS_LOG_LANGUAGE", self.language)
```

## 使用例

### WebUIでの日本語ログ表示

```python
# 日本語で表示される例
[14:30:15] ℹ️ [市場アナリスト] テクニカル指標を分析中
[14:30:16] 🐛 [API] API呼び出し: /quote/AAPL
[14:30:17] ⚠️ [ニュースアナリスト] APIレート制限に近づいています
[14:30:20] ❌ [システム] 接続タイムアウト
```

### 環境変数による設定

```bash
# 日本語ログ（デフォルト）
export TRADINGAGENTS_LANGUAGE=ja

# 英語ログ
export TRADINGAGENTS_LANGUAGE=en
export TRADINGAGENTS_LOG_LANGUAGE=en
```

## メリット

1. **ユーザビリティ向上**: 日本語ユーザーが理解しやすい
2. **統一性**: UI全体で一貫した言語体験
3. **柔軟性**: 必要に応じて英語表示も可能
4. **保守性**: 翻訳を一箇所で管理

## 今後の拡張

1. **完全なi18n対応**
   - gettext使用
   - .poファイルでの翻訳管理
   - 複数言語サポート

2. **動的翻訳**
   - Google Translate API統合
   - カスタム翻訳辞書

3. **コンテキスト対応翻訳**
   - エージェント別の専門用語
   - 金融用語の正確な翻訳