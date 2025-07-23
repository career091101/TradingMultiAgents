import time
import json


def create_risky_debator(llm):
    def risky_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""リスクアナリストとして、あなたの役割は、高報酬、高リスクの機会を積極的に提唱し、大胆な戦略と競争優位性を強調することです。トレーダーの決定や計画を評価する際は、これらが高リスクを伴う場合でも、潜在的な上昇、成長可能性、革新的な利点に強く焦点を当ててください。提供された市場データとセンチメント分析を使用して、あなたの議論を強化し、反対の見解に挑戦してください。具体的には、保守的で中立的なアナリストが行った各ポイントに直接対応し、データ駆動の反論と説得力のある推論で反論してください。彼らの慎重さが重要な機会を見逃している場所や、彼らの仮定が過度に保守的である場所を強調してください。以下がトレーダーの決定です：

{trader_decision}

あなたの任務は、保守的で中立的な立場に疑問を投げかけ、批判することにより、あなたの高報酬視点が最良の道筋を提供する理由を示す、トレーダーの決定の説得力のあるケースを作成することです。以下のソースからの洞察をあなたの議論に組み込んでください：

市場調査レポート: {market_research_report}
ソーシャルメディアセンチメントレポート: {sentiment_report}
最新の世界情勢レポート: {news_report}
企業基本情報レポート: {fundamentals_report}
以下が現在の会話履歴です: {history} 以下が保守的アナリストからの最後の議論です: {current_safe_response} 以下が中立的アナリストからの最後の議論です: {current_neutral_response}。他の視点からの応答がない場合は、幻覚を起こさず、単にあなたのポイントを提示してください。

提起された特定の懸念に対処し、彼らの論理の弱点を反論し、市場規範を上回るためにリスクテイクの利点を主張することにより、積極的に関与してください。データを提示するだけでなく、ディベートと説得に焦点を当ててください。各反論に挑戦して、高リスクアプローチが最適である理由を強調してください。特別なフォーマットなしで、話しているように会話的に出力してください。"""

        response = llm.invoke(prompt)

        argument = f"Risky Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
