````md
# CLAUDE.md

<!--
This file provides Claude Code with persistent project context and conventions.
Do not remove critical sections marked as **必須**.
-->

## 1. プロジェクト基本情報
- **名称**: TradingAgents
- **概要・目的**: 実世界の取引会社の動態を模倣するマルチエージェントLLM金融取引フレームワーク。ファンダメンタル、センチメント、ニュース、テクニカルアナリストからトレーダー、リスク管理まで複数エージェントが協調し、動的な議論を通じて最適戦略を導出する。研究・実験用。
- **主要技術スタック**:
  - 言語: Python 3.13
  - フレームワーク: LangGraph
  - **ディープシンキングLLM**: o3, DeepResearch (o3)
  - **ファストシンキングLLM**: GPT‑4.1 ,o4‑mini など
  - データソース: Tauric TradingDB（キャッシュ）, FinnHub API
  - **インターフェース**:
    - CLI: Python モジュール (`python -m cli.main`)
    - **WebUI**: Streamlit ベース (`python run_webui.py`)

## 2. **必須** 共通コマンド
```bash
# リポジトリ複製、環境作成、依存インストール
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
conda create -n tradingagents python=3.13
conda activate tradingagents
pip install -r requirements.txt

# 環境変数（**必須**）
export FINNHUB_API_KEY=$YOUR_FINNHUB_API_KEY
export OPENAI_API_KEY=$YOUR_OPENAI_API_KEY

# CLI 実行
python -m cli.main

# WebUI 実行 (**新機能**)
python run_webui.py
# または
streamlit run webui/app.py
````

## 3. コードスタイルガイドライン

* **言語仕様**: Python 3.13, PEP8 準拠
* **型定義**: `typing` を活用した厳密な型注釈
* **フォーマッタ**: `black` + `flake8` + `isort`
* **命名規則**: snake\_case（変数/関数）、PascalCase（クラス）
* **インポート順序**: 標準ライブラリ → サードパーティ → 自社モジュール

## 4. ワークフロー

1. ブランチ命名: `feature/<機能名>`, `bugfix/<チケット番号>`
2. コード変更後:

   * `pytest tests/` でユニットテスト実行
   * `black .` → `flake8 .` で品質チェック
3. プルリクエスト作成 → 自動 CI 実行 → レビュー → マージ

## 5. テストガイドライン

* **TDD** 推奨
* テストフレームワーク: `pytest`
* テスト配置: `tests/` ディレクトリ直下にモジュール毎にサブディレクトリ
* モック: `unittest.mock` または `pytest-mock`
* カバレッジ: 80%以上を目標
* **E2Eテスト**: Puppeteerを使用してブラウザベースの統合テストを実行

## 6. リポジトリの作法

* チケット連携: コミットメッセージに JIRA/Issue 番号を付与
* マージ: Squash マージを推奨
* `CLAUDE.md`: ルート直下に配置し、常に最新状態を保つ

## 7. 開発環境のセットアップ

* 推奨: `conda` + `pyenv`
* `README.md` に記載の手順に従い、環境変数設定を忘れずに

## 8. 既知の注意点\$1

## 9. LLM選定ガイドライン

* **役割分担**: ディープシンキングLLMは深い財務/マクロ解析とエージェント間の議論フェーズに、ファストシンキングLLMはニュース要約やテクニカル指標計算など高頻度タスクに使用。
* **評価指標**: 総リターン、シャープレシオ、最大ドローダウン、議論一貫性スコア、推論コスト（\$/推論）で比較し、1か月以上のバックテストを推奨。
* **推奨モデル (2025/07 現在)**:

  * **DeepResearch (o3)** — Retrieval統合・財務報告書解析向け。
    \- **Mistral‑Instruct‑8x22B** — オープンソース、高速低コスト。

### Deep‑Thinking モデルのケース分け

| シーン           | o3 | DeepResearch (o3) |   |
| ------------- | -- | ----------------- | - |
| マクロ経済シミュレーション | ✅  | ⚪️                |   |
| 企業財務レポート解析    | ⚪️ | ✅                 |   |
| 長文エージェント議論    | ✅  | ✅                 |   |
| 速報ニュース応答      | ✅  | ⚪️ (Retrieval 強)  |   |

> **指針**: 財務ドキュメントや検索ベースの質問には **DeepResearch**、汎用連鎖推論・マクロ分析・速報ニュース応答には **o3** を選択。

* **実践TIP**: `tradingagents/default_config.py` で `deep_think_llm` と `quick_think_llm` を切り替え、複数モデルのA/Bテストを実施。

```
```
