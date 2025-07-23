"""
ログメッセージ翻訳ユーティリティ
英語のログメッセージを日本語に翻訳
"""

import re
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LogTranslator:
    """ログメッセージを日本語に翻訳"""
    
    # 正規表現パターンと翻訳テンプレート
    PATTERNS = [
        # API関連
        (r"API call(?:ing)? to (.+)", "API呼び出し: {0}"),
        (r"API rate limit (?:reached|exceeded)", "APIレート制限に達しました"),
        (r"API error: (.+)", "APIエラー: {0}"),
        (r"Calling (.+) API", "{0} APIを呼び出し中"),
        (r"API response received", "APIレスポンスを受信"),
        
        # 分析関連
        (r"Starting analysis(?:\s+for\s+(.+))?", "分析を開始します{0}"),
        (r"Analysis completed?(?:\s+for\s+(.+))?", "分析が完了しました{0}"),
        (r"Analyzing (.+)", "{0}を分析中"),
        (r"Processing (.+)", "{0}を処理中"),
        (r"Generating (.+)", "{0}を生成中"),
        (r"Calculating (.+)", "{0}を計算中"),
        (r"Evaluating (.+)", "{0}を評価中"),
        
        # データ取得関連
        (r"Fetching (.+)", "{0}を取得中"),
        (r"Loading (.+)", "{0}を読み込み中"),
        (r"Downloading (.+)", "{0}をダウンロード中"),
        (r"Retrieving (.+)", "{0}を取得中"),
        
        # エラー関連
        (r"Error: (.+)", "エラー: {0}"),
        (r"Failed to (.+)", "{0}に失敗しました"),
        (r"Could not (.+)", "{0}できませんでした"),
        (r"Unable to (.+)", "{0}できません"),
        (r"(.+) failed", "{0}が失敗しました"),
        (r"Connection timeout", "接続タイムアウト"),
        (r"Connection error", "接続エラー"),
        (r"Network error", "ネットワークエラー"),
        (r"Timeout occurred", "タイムアウトが発生しました"),
        
        # ツール関連
        (r"Tool Call: (.+)", "ツール呼び出し: {0}"),
        (r"Executing tool: (.+)", "ツール実行: {0}"),
        (r"Tool execution completed", "ツール実行完了"),
        
        # ファイル操作
        (r"Saving (?:to )?(.+)", "{0}に保存中"),
        (r"Reading (?:from )?(.+)", "{0}から読み込み中"),
        (r"Writing (?:to )?(.+)", "{0}に書き込み中"),
        (r"Created (.+)", "{0}を作成しました"),
        (r"Updated (.+)", "{0}を更新しました"),
        
        # 進捗関連
        (r"Progress: (\d+)%", "進捗: {0}%"),
        (r"Step (\d+) of (\d+)", "ステップ {0}/{1}"),
        (r"Completed (\d+) of (\d+)", "{0}/{1} 完了"),
        
        # システム関連
        (r"Initializing (.+)", "{0}を初期化中"),
        (r"Starting (.+)", "{0}を開始中"),
        (r"Stopping (.+)", "{0}を停止中"),
        (r"Restarting (.+)", "{0}を再起動中"),
        (r"System ready", "システム準備完了"),
        (r"Shutting down", "シャットダウン中"),
        
        # CLI特有のパターン
        (r"Tool Calls: (\d+) \| LLM Calls: (\d+) \| Generated Reports: (\d+)", "ツール呼び出し: {0} | LLM呼び出し: {1} | 生成レポート: {2}"),
        (r"Traceback \(most recent call last\)", "トレースバック（最新の呼び出し）"),
        (r"ポートフォリオ管理決定", "ポートフォリオ管理決定"),
        
        # インポート関連
        (r"File \"(.+)\", line (\d+), in (.+)", "ファイル \"{0}\", {1}行目, {2}内"),
        (r"from (.+) import (.+)", "{0}から{1}をインポート"),
        (r"import (.+)", "{0}をインポート"),
        
        # 環境変数関連
        (r"(.+): set", "{0}: 設定済み"),
        (r"(.+): not set", "{0}: 未設定"),
        (r"Loaded (.+)", "{0}を読み込み"),
        
        # JSON形式のログ
        (r'"market_tools".*"default"', '"市場ツール"..."デフォルト"'),
        (r'"market_report":\s*"([^"]+)"', '"市場レポート": "{0}"'),
        (r'"news_report":\s*"([^"]+)"', '"ニュースレポート": "{0}"'),
        (r'"fundamentals_report":\s*"([^"]+)"', '"ファンダメンタルレポート": "{0}"'),
        (r'"sentiment_report":\s*"([^"]+)"', '"センチメントレポート": "{0}"'),
        
        # 分析関連
        (r"analysis_(.+)_(\d+)\.log", "分析_{0}_{1}.log"),
        (r'executing.*"(.+)"', '"{0}"を実行中'),
        (r"running (.+)", "{0}を実行中"),
        (r"completed (.+)", "{0}を完了"),
    ]
    
    # 固定メッセージの翻訳辞書
    MESSAGES = {
        # CLI関連メッセージ
        "CLI Command": "CLIコマンド",
        "Environment variables": "環境変数",
        "Working directory": "作業ディレクトリ",
        "Analysis started at": "分析開始時刻",
        "TradingAgentsへようこそ": "TradingAgentsへようこそ",
        "Progress": "進捗",
        "Messages & Tools": "メッセージ＆ツール",
        "Current Report": "現在のレポート",
        "Tool Calls": "ツール呼び出し",
        "LLM Calls": "LLM呼び出し",
        "Generated Reports": "生成されたレポート",
        
        # スクリーンショットに表示されているメッセージ
        "File \"tickervalids/src/tickervalids/models.py\", line 19, in <module> import BaseOHLCSpanMetric": "ファイル \"tickervalids/src/tickervalids/models.py\", 19行目, <module>内 import BaseOHLCSpanMetric",
        "from .tradingagents_openai_base_models import BaseOHLCSpanMetric, OracleModel": ".tradingagents_openai_base_modelsから BaseOHLCSpanMetric, OracleModel をインポート",
        "import openai": "openaiをインポート",
        "import pandas": "pandasをインポート",
        "Loaded .env": ".envを読み込み",
        "set": "設定済み",
        "not set": "未設定",
        
        # Market Analyst関連
        "Analyzing technical indicators": "テクニカル指標を分析中",
        "Technical analysis started": "テクニカル分析を開始",
        "Calculating RSI": "RSIを計算中",
        "Calculating MACD": "MACDを計算中",
        "Calculating Bollinger Bands": "ボリンジャーバンドを計算中",
        "Analyzing volume patterns": "出来高パターンを分析中",
        "Analyzing price trends": "価格トレンドを分析中",
        "Technical analysis completed": "テクニカル分析完了",
        
        # News Analyst関連
        "Fetching news articles": "ニュース記事を取得中",
        "Analyzing sentiment": "センチメントを分析中",
        "Processing news data": "ニュースデータを処理中",
        "Extracting key events": "重要イベントを抽出中",
        "News analysis completed": "ニュース分析完了",
        
        # Social Analyst関連
        "Fetching social media data": "ソーシャルメディアデータを取得中",
        "Analyzing Reddit posts": "Reddit投稿を分析中",
        "Analyzing Twitter sentiment": "Twitterセンチメントを分析中",
        "Social sentiment analysis completed": "ソーシャルセンチメント分析完了",
        
        # Fundamentals Analyst関連
        "Fetching financial data": "財務データを取得中",
        "Analyzing balance sheet": "貸借対照表を分析中",
        "Analyzing income statement": "損益計算書を分析中",
        "Calculating financial ratios": "財務比率を計算中",
        "Analyzing cash flow": "キャッシュフローを分析中",
        "Fundamental analysis completed": "ファンダメンタル分析完了",
        
        # Research Team関連
        "Bull researcher analyzing": "強気派研究者が分析中",
        "Bear researcher analyzing": "弱気派研究者が分析中",
        "Research manager reviewing": "研究マネージャーがレビュー中",
        "Debate in progress": "議論進行中",
        "Research team analysis completed": "研究チーム分析完了",
        
        # Risk Management関連
        "Evaluating risk factors": "リスク要因を評価中",
        "Calculating risk metrics": "リスク指標を計算中",
        "Assessing market volatility": "市場ボラティリティを評価中",
        "Risk assessment completed": "リスク評価完了",
        
        # Trading関連
        "Generating trading strategy": "取引戦略を生成中",
        "Optimizing portfolio allocation": "ポートフォリオ配分を最適化中",
        "Calculating position size": "ポジションサイズを計算中",
        "Trading plan completed": "取引計画完了",
        
        # システムメッセージ
        "Initializing system": "システムを初期化中",
        "Loading configuration": "設定を読み込み中",
        "Configuration loaded": "設定読み込み完了",
        "Saving results": "結果を保存中",
        "Results saved": "結果保存完了",
        "Analysis started": "分析開始",
        "Analysis completed": "分析完了",
        "Report generated": "レポート生成完了",
        
        # エラーメッセージ
        "Invalid input": "無効な入力",
        "Missing required data": "必要なデータが不足しています",
        "Operation cancelled": "操作がキャンセルされました",
        "Unexpected error occurred": "予期しないエラーが発生しました",
        "Please try again": "もう一度お試しください",
        
        # 接続関連
        "Connecting to server": "サーバーに接続中",
        "Connected successfully": "接続成功",
        "Connection lost": "接続が失われました",
        "Reconnecting": "再接続中",
        "Authentication required": "認証が必要です",
        "Authentication successful": "認証成功",
    }
    
    # エージェント名の翻訳
    AGENT_NAMES = {
        # アナリスト
        "Market Analyst": "市場アナリスト",
        "News Analyst": "ニュースアナリスト",
        "Social Analyst": "ソーシャルアナリスト",
        "Fundamentals Analyst": "ファンダメンタルアナリスト",
        "Sentiment Analyst": "センチメントアナリスト",
        
        # 研究チーム
        "Bull Researcher": "強気派研究者",
        "Bear Researcher": "弱気派研究者",
        "Research Manager": "研究マネージャー",
        
        # リスク管理
        "Aggressive Analyst": "積極派アナリスト",
        "Conservative Analyst": "保守派アナリスト",
        "Neutral Analyst": "中立派アナリスト",
        "Risk Manager": "リスクマネージャー",
        
        # トレーディング
        "Trader": "トレーダー",
        "Portfolio Manager": "ポートフォリオマネージャー",
        
        # システム
        "System": "システム",
        "CLI": "CLI",
        "API": "API",
        "Tool": "ツール",
        "Logger": "ロガー",
    }
    
    def __init__(self):
        # パターンをコンパイル
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), template)
            for pattern, template in self.PATTERNS
        ]
    
    def translate_message(self, message: str) -> str:
        """メッセージを日本語に翻訳"""
        if not message:
            return message
        
        # まず固定メッセージを確認
        if message in self.MESSAGES:
            return self.MESSAGES[message]
        
        # パターンマッチング
        for pattern, template in self.compiled_patterns:
            match = pattern.match(message)
            if match:
                # グループがある場合は置換
                groups = match.groups()
                if groups:
                    # グループ内の内容も翻訳を試みる
                    translated_groups = []
                    for group in groups:
                        if group:
                            # 特定の値の翻訳
                            translated_group = self._translate_value(group)
                            translated_groups.append(translated_group)
                        else:
                            translated_groups.append("")
                    
                    # フォーマット文字列の調整
                    try:
                        return template.format(*translated_groups)
                    except:
                        return template
                else:
                    return template
        
        # JSON形式のメッセージの簡易翻訳
        if message.startswith('|') and '|' in message:
            # パイプ区切りのメッセージ
            parts = message.split('|')
            translated_parts = []
            for part in parts:
                part = part.strip()
                if part:
                    # JSONのキーを翻訳
                    part = part.replace('"market_tools"', '"市場ツール"')
                    part = part.replace('"market_report"', '"市場レポート"')
                    part = part.replace('"news_report"', '"ニュースレポート"')
                    part = part.replace('"fundamentals_report"', '"ファンダメンタルレポート"')
                    part = part.replace('"sentiment_report"', '"センチメントレポート"')
                    part = part.replace('"default"', '"デフォルト"')
                    part = part.replace('"tool_calls"', '"ツール呼び出し"')
                    part = part.replace('"messages"', '"メッセージ"')
                translated_parts.append(part)
            return ' | '.join(translated_parts)
        
        # 翻訳できない場合は元のメッセージを返す
        return message
    
    def translate_agent(self, agent: str) -> str:
        """エージェント名を日本語に翻訳"""
        return self.AGENT_NAMES.get(agent, agent)
    
    def _translate_value(self, value: str) -> str:
        """値の翻訳（ファイル名、指標名など）"""
        # 一般的な値の翻訳
        value_translations = {
            # ファイル名
            "config": "設定",
            "report": "レポート",
            "results": "結果",
            "data": "データ",
            "cache": "キャッシュ",
            
            # 指標名
            "RSI": "RSI（相対力指数）",
            "MACD": "MACD",
            "volume": "出来高",
            "price": "価格",
            "trend": "トレンド",
            
            # その他
            "ticker": "ティッカー",
            "date": "日付",
            "time": "時間",
        }
        
        # 完全一致で翻訳
        if value.lower() in value_translations:
            return value_translations[value.lower()]
        
        # 部分一致で翻訳
        for key, translation in value_translations.items():
            if key in value.lower():
                return value.replace(key, translation)
        
        return value
    
    def is_japanese(self, text: str) -> bool:
        """テキストが日本語かどうか判定"""
        # 日本語文字（ひらがな、カタカナ、漢字）が含まれているか
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        return bool(japanese_pattern.search(text))

# グローバルインスタンス
_translator = None

def get_translator() -> LogTranslator:
    """グローバル翻訳インスタンスを取得"""
    global _translator
    if _translator is None:
        _translator = LogTranslator()
    return _translator