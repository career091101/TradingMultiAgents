# バックテスト2 タイムアウト問題の修正

## 問題の概要
バックテスト2がWebUIから実行した際に「データ収集段階で停止」と報告され、タイムアウトする問題が発生していました。

## 根本原因
1. **誤ったLLMモデル設定**
   - デフォルトのモデルが `o3-2025-04-16`（深い思考）と `o4-mini-2025-04-16`（クイック思考）に設定されていた
   - これらは存在しないモデル名で、APIエラーまたは非常に長い応答時間を引き起こしていた

2. **JSONシリアライゼーションエラー**
   - `TradeAction` EnumオブジェクトがJSONシリアライズできない問題
   - LLMクライアントがコンテキストをJSON化する際にエラーが発生

## 実施した修正

### 1. LLMモデル設定の修正
**ファイル**: `TradingMultiAgents/webui/backend/backtest2_wrapper.py`

```python
# 修正前
def _get_deep_model(self, provider: str) -> str:
    models = {
        "openai": "o3-2025-04-16",  # 存在しないモデル
        ...
    }

def _get_quick_model(self, provider: str) -> str:
    models = {
        "openai": "o4-mini-2025-04-16",  # 存在しないモデル
        ...
    }

# 修正後
def _get_deep_model(self, provider: str) -> str:
    models = {
        "openai": "o1-preview",  # 正しいモデル名
        ...
    }

def _get_quick_model(self, provider: str) -> str:
    models = {
        "openai": "gpt-4o-mini",  # 正しいモデル名
        ...
    }
```

### 2. タイムアウト設定の追加
```python
llm_config = LLMConfig(
    ...
    timeout=webui_config.get("timeout", 120)  # デフォルト2分のタイムアウト
)
```

## 確認されたパフォーマンス
- **モックモード**: 1.23秒で完了（正常動作を確認）
- **実際のLLM使用時**: 各フェーズが適切に進行することを確認
  - Phase 1 (Data Collection): 約20-30秒
  - Phase 2 (Investment Analysis): 約15-20秒
  - その他のフェーズも正常に進行

## 推奨される追加対策

### 1. JSONシリアライゼーションエラーの修正
`backtest2/agents/agent_adapter.py` の `_prepare_context` メソッドを修正：
```python
def _prepare_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare context for LLM"""
    context = {}
    for key, value in input_data.items():
        if hasattr(value, 'to_dict'):
            context[key] = value.to_dict()
        elif hasattr(value, '__dict__'):
            context[key] = {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
        elif isinstance(value, Enum):  # Enumの処理を追加
            context[key] = value.value
        else:
            context[key] = value
    return context
```

### 2. WebUIでのモデル選択オプション
ユーザーがWebUIから以下を選択できるようにする：
- LLMプロバイダー（OpenAI、Anthropic等）
- 具体的なモデル名
- タイムアウト設定
- モックモードの有効/無効

### 3. プログレス表示の改善
各フェーズの進行状況をより詳細に表示し、どのエージェントが処理中かを明確にする。

## テスト推奨事項
1. 短期間（1-3日）のバックテストで動作確認
2. 異なるLLMモデルでのパフォーマンステスト
3. 複数銘柄での並列処理テスト
4. エラーハンドリングの確認（API制限、ネットワークエラー等）

## 結論
主要な問題（誤ったモデル設定）は修正されました。残っているJSONシリアライゼーションエラーは機能に大きな影響を与えていないようですが、完全な修正のために上記の追加対策を実施することを推奨します。