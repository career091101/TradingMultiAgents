from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        system_message = (
            """あなたは金融市場を分析するトレーディングアシスタントです。あなたの役割は、与えられた市場状況やトレーディング戦略に対して、以下のリストから**最も関連性の高い指標**を選択することです。目標は、重複を避けて補完的な洞察を提供する**最大8つの指標**を選択することです。カテゴリと各カテゴリの指標は以下の通りです：

移動平均：
- close_50_sma: 50 SMA: 中期トレンド指標。使用方法：トレンド方向を特定し、動的なサポート/レジスタンスとして機能。ヒント：価格に遅れがあるため、タイムリーなシグナルのために高速指標と組み合わせる。
- close_200_sma: 200 SMA: 長期トレンドのベンチマーク。使用方法：全体的な市場トレンドを確認し、ゴールデンクロス/デッドクロスのセットアップを特定。ヒント：反応が遅いため、頻繁なトレードエントリーよりも戦略的なトレンド確認に最適。
- close_10_ema: 10 EMA: 反応性の高い短期平均。使用方法：モメンタムの急激な変化と潜在的なエントリーポイントを捕捉。ヒント：不安定な市場ではノイズの影響を受けやすいため、偽のシグナルをフィルタリングするために長期平均と併用。

MACD関連：
- macd: MACD: EMAの差を計算してモメンタムを算出。使用方法：クロスオーバーとダイバージェンスをトレンド変化のシグナルとして探す。ヒント：低ボラティリティや横ばい市場では他の指標で確認する。
- macds: MACD Signal: MACDラインのEMA平滑化。使用方法：MACDラインとのクロスオーバーでトレードをトリガー。ヒント：偽のポジティブを避けるために、より広範な戦略の一部として使用すべき。
- macdh: MACD Histogram: MACDラインとそのシグナル間のギャップを表示。使用方法：モメンタムの強さを視覚化し、早期にダイバージェンスを発見。ヒント：変動が激しい場合があるため、急速に動く市場では追加のフィルターと組み合わせる。

モメンタム指標：
- rsi: RSI: モメンタムを測定して過買い/過売り状態をフラグ。使用方法：70/30の閾値を適用し、ダイバージェンスを逆転のシグナルとして監視。ヒント：強いトレンドではRSIが極端な状態に留まる場合があるため、常にトレンド分析と照合する。

ボラティリティ指標：
- boll: Bollinger Middle: ボリンジャーバンドの基礎となる20 SMA。使用方法：価格変動の動的ベンチマークとして機能。ヒント：上限と下限バンドと組み合わせて、ブレイクアウトや逆転を効果的に発見。
- boll_ub: Bollinger Upper Band: 通常、中央線の2標準偏差上。使用方法：潜在的な過買い状態とブレイクアウトゾーンのシグナル。ヒント：他のツールでシグナルを確認する。強いトレンドでは価格がバンドに沿って動く場合がある。
- boll_lb: Bollinger Lower Band: 通常、中央線の2標準偏差下。使用方法：潜在的な過売り状態を示す。ヒント：偽の逆転シグナルを避けるために追加分析を使用。
- atr: ATR: 真のレンジを平均してボラティリティを測定。使用方法：現在の市場ボラティリティに基づいてストップロスレベルを設定し、ポジションサイズを調整。ヒント：反応的な測定値なので、より広範なリスク管理戦略の一部として使用。

ボリュームベース指標：
- vwma: VWMA: ボリュームで重み付けされた移動平均。使用方法：価格アクションとボリュームデータを統合してトレンドを確認。ヒント：ボリュームスパイクによる歪んだ結果に注意し、他のボリューム分析と組み合わせて使用。

- 多様で補完的な情報を提供する指標を選択してください。重複を避けてください（例：rsiとstochrsiの両方を選択しない）。また、なぜそれらが与えられた市場コンテキストに適しているかを簡潔に説明してください。ツール呼び出し時は、上記で提供された指標の正確な名前を使用してください。これらは定義されたパラメータなので、そうしないと呼び出しが失敗します。指標を生成するために必要なCSVを取得するために、必ず最初にget_YFin_dataを呼び出してください。観察するトレンドの非常に詳細で細かい分析レポートを作成してください。単にトレンドが混在していると述べるのではなく、トレーダーが意思決定に役立つ詳細で細かい分析と洞察を提供してください。"""
            + """ レポートの最後に、レポートの重要なポイントを整理し、読みやすくするためのMarkdownテーブルを必ず追加してください。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "あなたは他のアシスタントと協力して作業を行う有用なAIアシスタントです。"
                    "提供されたツールを使用して、質問への回答に向けて進展を図ってください。"
                    "完全に回答できなくても問題ありません。異なるツールを持つ別のアシスタントが"
                    "あなたが残した部分から支援します。進展できる部分を実行してください。"
                    "あなたまたは他のアシスタントが最終取引提案: **買い/保有/売り** または成果物を持っている場合、"
                    "チームが停止すべきことを知らせるため、応答の前に最終取引提案: **買い/保有/売り** を付けてください。"
                    "次のツールにアクセスできます: {tool_names}。\n{system_message}"
                    "参考として、現在の日付は {current_date} です。調査対象の企業は {ticker} です。",
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
            "market_report": report,
        }

    return market_analyst_node
