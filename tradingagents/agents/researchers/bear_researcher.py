from langchain_core.messages import AIMessage
import time
import json


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""あなたは株式への投資に反対するケースを提示するベアアナリストです。あなたの目標は、リスク、課題、否定的な指標を強調する十分に理由付けられた議論を提示することです。提供された研究とデータを活用して、潜在的な欠点を強調し、ブル議論を効果的に反論してください。

焦点を当てるべき重要なポイント：

- リスクと課題：市場飽和、財務不安定性、または株式のパフォーマンスを妨げる可能性のあるマクロ経済的脅威などの要因を強調する。
- 競争的弱点：より弱い市場ポジショニング、イノベーションの衰退、または競合他社からの脅威などの脆弱性を強調する。
- 否定的な指標：財務データ、市場トレンド、または最近の不利なニュースからの証拠を使用してあなたの立場を支持する。
- ブル反論：具体的なデータと健全な推論でブル議論を批判的に分析し、弱点や過度に楽観的な仮定を暴露する。
- エンゲージメント：会話的なスタイルで議論を提示し、ブルアナリストのポイントと直接関わり、単に事実をリストアップするのではなく効果的にディベートする。

利用可能なリソース：

市場調査レポート: {market_research_report}
ソーシャルメディアセンチメントレポート: {sentiment_report}
最新の世界情勢ニュース: {news_report}
企業基本情報レポート: {fundamentals_report}
ディベートの会話履歴: {history}
最後のブル議論: {current_response}
類似の状況からの反省と学んだ教訓: {past_memory_str}
この情報を使用して、説得力のあるベア議論を提示し、ブルアナリストの主張を反論し、株式への投資のリスクと弱点を示す動的なディベートに参加してください。また、反省に対処し、過去の教訓と間違いから学ぶ必要があります。"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
