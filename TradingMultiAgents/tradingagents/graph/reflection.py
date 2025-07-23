# TradingAgents/graph/reflection.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI


class Reflector:
    """Handles reflection on decisions and updating memory."""

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize the reflector with an LLM."""
        self.quick_thinking_llm = quick_thinking_llm
        self.reflection_system_prompt = self._get_reflection_prompt()

    def _get_reflection_prompt(self) -> str:
        """Get the system prompt for reflection."""
        return """
あなたは取引決定・分析を検証し、包括的で段階的な分析を提供する専門の金融アナリストです。
投資決定への詳細な洞察を提供し、改善の機会を強調することが目標です。以下のガイドラインに厳密に従ってください：

1. 推論：
   - 各取引決定について、正しかったか間違っていたかを判断する。正しい決定はリターンの増加をもたらし、間違った決定はその逆になる。
   - 各成功や失敗の要因を分析する。以下を考慮：
     - 市場インテリジェンス
     - テクニカル指標
     - テクニカルシグナル
     - 価格動向分析
     - 全体的な市場データ分析
     - ニュース分析
     - ソーシャルメディアとセンチメント分析
     - ファンダメンタルデータ分析
     - 意思決定プロセスにおける各要因の重要度を評価

2. 改善：
   - 間違った決定については、リターンを最大化する修正案を提案する。
   - 具体的な推奨事項を含む詳細な是正措置や改善リストを提供（例：特定の日付でHOLDからBUYへの決定変更）。

3. 要約：
   - 成功と失敗から学んだ教訓を要約する。
   - これらの教訓を将来の取引シナリオにどのように適用できるかを強調し、類似の状況間の関連性を描いて得られた知識を応用する。

4. クエリ：
   - 要約から主要な洞察を1000トークン以下の簡潔な文に抽出する。
   - 凝縮された文が、参照しやすいように教訓と推論の本質を確実に捉えるようにする。

これらの指示に厳密に従い、詳細で正確かつ実行可能な出力を確保してください。価格動向、テクニカル指標、ニュース、センチメントの観点から市場の客観的な説明も提供され、分析により多くのコンテキストを提供します。
"""

    def _extract_current_situation(self, current_state: Dict[str, Any]) -> str:
        """Extract the current market situation from the state."""
        curr_market_report = current_state["market_report"]
        curr_sentiment_report = current_state["sentiment_report"]
        curr_news_report = current_state["news_report"]
        curr_fundamentals_report = current_state["fundamentals_report"]

        return f"{curr_market_report}\n\n{curr_sentiment_report}\n\n{curr_news_report}\n\n{curr_fundamentals_report}"

    def _reflect_on_component(
        self, component_type: str, report: str, situation: str, returns_losses
    ) -> str:
        """Generate reflection for a component."""
        messages = [
            ("system", self.reflection_system_prompt),
            (
                "human",
                f"Returns: {returns_losses}\n\nAnalysis/Decision: {report}\n\nObjective Market Reports for Reference: {situation}",
            ),
        ]

        result = self.quick_thinking_llm.invoke(messages).content
        return result

    def reflect_bull_researcher(self, current_state, returns_losses, bull_memory):
        """Reflect on bull researcher's analysis and update memory."""
        situation = self._extract_current_situation(current_state)
        bull_debate_history = current_state["investment_debate_state"]["bull_history"]

        result = self._reflect_on_component(
            "BULL", bull_debate_history, situation, returns_losses
        )
        bull_memory.add_situations([(situation, result)])

    def reflect_bear_researcher(self, current_state, returns_losses, bear_memory):
        """Reflect on bear researcher's analysis and update memory."""
        situation = self._extract_current_situation(current_state)
        bear_debate_history = current_state["investment_debate_state"]["bear_history"]

        result = self._reflect_on_component(
            "BEAR", bear_debate_history, situation, returns_losses
        )
        bear_memory.add_situations([(situation, result)])

    def reflect_trader(self, current_state, returns_losses, trader_memory):
        """Reflect on trader's decision and update memory."""
        situation = self._extract_current_situation(current_state)
        trader_decision = current_state["trader_investment_plan"]

        result = self._reflect_on_component(
            "TRADER", trader_decision, situation, returns_losses
        )
        trader_memory.add_situations([(situation, result)])

    def reflect_invest_judge(self, current_state, returns_losses, invest_judge_memory):
        """Reflect on investment judge's decision and update memory."""
        situation = self._extract_current_situation(current_state)
        judge_decision = current_state["investment_debate_state"]["judge_decision"]

        result = self._reflect_on_component(
            "INVEST JUDGE", judge_decision, situation, returns_losses
        )
        invest_judge_memory.add_situations([(situation, result)])

    def reflect_risk_manager(self, current_state, returns_losses, risk_manager_memory):
        """Reflect on risk manager's decision and update memory."""
        situation = self._extract_current_situation(current_state)
        judge_decision = current_state["risk_debate_state"]["judge_decision"]

        result = self._reflect_on_component(
            "RISK JUDGE", judge_decision, situation, returns_losses
        )
        risk_manager_memory.add_situations([(situation, result)])
