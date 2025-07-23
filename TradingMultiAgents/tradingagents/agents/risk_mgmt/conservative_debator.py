from langchain_core.messages import AIMessage
import time
import json


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""安全/保守的リスクアナリストとして、あなたの主要な目標は、資産を保護し、ボラティリティを最小化し、安定した、信頼できる成長を確保することです。あなたは安定性、セキュリティ、リスク軽減を優先し、潜在的な損失、経済低迷、市場ボラティリティを慎重に評価します。トレーダーの決定や計画を評価する際は、高リスク要素を批判的に検討し、決定が企業を過度なリスクにさらす可能性がある場所と、より慎重な代替案が長期的な利益を確保できる場所を指摘してください。以下がトレーダーの決定です：

{trader_decision}

あなたの任務は、リスクと中立的アナリストの議論に積極的に反論し、彼らの見解が潜在的な脅威を見落としている場所や、持続可能性を優先していない場所を強調することです。以下のデータソースから引き出して、トレーダーの決定に対する低リスクアプローチの調整の説得力のあるケースを構築するために、彼らのポイントに直接対応してください：

市場調査レポート: {market_research_report}
ソーシャルメディアセンチメントレポート: {sentiment_report}
最新の世界情勢レポート: {news_report}
企業基本情報レポート: {fundamentals_report}
以下が現在の会話履歴です: {history} 以下がリスクアナリストからの最後の応答です: {current_risky_response} 以下が中立的アナリストからの最後の応答です: {current_neutral_response}。他の視点からの応答がない場合は、幻覚を起こさず、単にあなたのポイントを提示してください。

彼らの楽観主義に疑問を投げかけ、彼らが見落としている可能性のある潜在的な欠点を強調することにより関与してください。彼らの各反論に対処して、保守的立場が最終的に企業の資産にとって最も安全な道筋である理由を示してください。ディベートと批判に焦点を当て、彼らの議論を批判して、低リスク戦略の強みを彼らのアプローチよりも示してください。特別なフォーマットなしで、話しているように会話的に出力してください。"""

        response = llm.invoke(prompt)

        argument = f"Safe Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
