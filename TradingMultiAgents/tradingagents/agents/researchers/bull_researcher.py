from langchain_core.messages import AIMessage
import time
import json


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

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

        prompt = f"""あなたは株式への投資を提唱するブルアナリストです。あなたの任務は、成長可能性、競争優位性、ポジティブな市場指標を強調する強力で証拠に基づいたケースを構築することです。提供された研究とデータを活用して、懸念に対処し、ベア議論を効果的に反論してください。

焦点を当てるべき重要なポイント：
- 成長可能性：企業の市場機会、収益予測、スケーラビリティを強調する。
- 競争優位性：ユニークな製品、強力なブランディング、または支配的な市場ポジショニングなどの要因を強調する。
- ポジティブな指標：財務健全性、業界トレンド、最近のポジティブなニュースを証拠として使用する。
- ベア反論：具体的なデータと健全な推論でベア議論を批判的に分析し、懸念を徹底的に対処し、ブル視点がより強いメリットを持つ理由を示す。
- エンゲージメント：会話的なスタイルで議論を提示し、ベアアナリストのポイントと直接関わり、単にデータをリストアップするのではなく効果的にディベートする。

利用可能なリソース：
市場調査レポート: {market_research_report}
ソーシャルメディアセンチメントレポート: {sentiment_report}
最新の世界情勢ニュース: {news_report}
企業基本情報レポート: {fundamentals_report}
ディベートの会話履歴: {history}
最後のベア議論: {current_response}
類似の状況からの反省と学んだ教訓: {past_memory_str}
この情報を使用して、説得力のあるブル議論を提示し、ベアアナリストの懸念を反論し、ブルポジションの強みを示す動的なディベートに参加してください。また、反省に対処し、過去の教訓と間違いから学ぶ必要があります。"""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
