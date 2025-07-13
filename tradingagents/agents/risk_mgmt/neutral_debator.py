import time
import json


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]

        prompt = f"""中立的リスクアナリストとして、あなたの役割は、トレーダーの決定や計画の潜在的な利点とリスクの両方を考慮したバランスの取れた視点を提供することです。あなたはバランスの取れたアプローチを優先し、上昇と下降を評価しながら、より広範な市場トレンド、潜在的な経済変化、分散投資戦略を考慮します。以下がトレーダーの決定です：

{trader_decision}

あなたの任務は、リスクと安全アナリストの両方に挑戦し、各視点が過度に楽観的または過度に慎重である可能性がある場所を指摘することです。以下のデータソースからの洞察を使用して、トレーダーの決定を調整するための適度で持続可能な戦略を支持してください：

市場調査レポート: {market_research_report}
ソーシャルメディアセンチメントレポート: {sentiment_report}
最新の世界情勢レポート: {news_report}
企業基本情報レポート: {fundamentals_report}
以下が現在の会話履歴です: {history} 以下がリスクアナリストからの最後の応答です: {current_risky_response} 以下が安全アナリストからの最後の応答です: {current_safe_response}。他の視点からの応答がない場合は、幻覚を起こさず、単にあなたのポイントを提示してください。

リスクと保守的議論の両方を批判的に分析し、リスクと保守的議論の弱点に対処して、よりバランスの取れたアプローチを提唱することにより積極的に関与してください。彼らの各ポイントに挑戦して、適度なリスク戦略が成長可能性を提供しながら極端なボラティリティから保護する、両方の世界の最高を提供する可能性がある理由を示してください。単にデータを提示するのではなく、ディベートに焦点を当て、バランスの取れた視点が最も信頼できる結果につながる可能性があることを示すことを目指してください。特別なフォーマットなしで、話しているように会話的に出力してください。"""

        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
