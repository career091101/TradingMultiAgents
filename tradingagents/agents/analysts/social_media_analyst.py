from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_social_media_analyst(llm, toolkit):
    def social_media_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_stock_news_openai]
        else:
            tools = [
                toolkit.get_reddit_stock_info,
            ]

        system_message = (
            "あなたは特定の企業の過去1週間のソーシャルメディア投稿、最近の企業ニュース、公共センチメントを分析するソーシャルメディアおよび企業固有のニュース研究者/アナリストです。企業名が与えられ、あなたの目標は、ソーシャルメディアとその企業について人々が何を言っているかを調べ、人々がその企業について毎日感じているセンチメントデータを分析し、最近の企業ニュースを見た後、この企業の現在の状況についてトレーダーと投資家に詳細な長いレポートを作成することです。ソーシャルメディアからセンチメント、ニュースまで、可能な限りすべてのソースを見てください。単にトレンドが混在していると述べるのではなく、トレーダーが意思決定に役立つ詳細で細かい分析と洞察を提供してください。"
            + """ レポートの最後に、レポートの重要なポイントを整理し、読みやすくするためのMarkdownテーブルを必ず追加してください。""",
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node
