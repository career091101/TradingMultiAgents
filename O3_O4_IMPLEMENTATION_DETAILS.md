# o3/o4モデル実装の詳細な要件

## 現在のコードが動作しない理由

### 1. パラメータの違い

#### ❌ 現在のコード
```python
ChatOpenAI(
    model="o3-2025-04-16",
    max_tokens=2000,  # エラー: o3/o4では使用不可
)
```

#### ✅ 必要な修正
```python
ChatOpenAI(
    model="o3-2025-04-16",
    max_completion_tokens=2000,  # o3/o4専用パラメータ
)
```

### 2. メッセージ形式の違い

#### ❌ 現在のコード
```python
messages = [
    {"role": "system", "content": "You are a financial analyst"},  # エラー
    {"role": "user", "content": "Analyze AAPL stock"}
]
```

#### ✅ 必要な修正
```python
messages = [
    {"role": "user", "content": "Context: You are a financial analyst\n\nAnalyze AAPL stock"}
]
```

## 修正が必要なファイル

### 1. `/backtest2/agents/llm_client.py`
- `max_tokens` → `max_completion_tokens`の変換
- システムメッセージの変換処理

### 2. `/backtest2/agents/agent_adapter.py`
- エージェントのシステムプロンプト処理

### 3. `/backtest2/agents/prompts.py`
- プロンプトフォーマットの調整

## 完全な修正例

```python
class LLMClient:
    def __init__(self, config: LLMConfig):
        # モデルタイプを判定
        self.is_o_series = config.deep_think_model.startswith(('o1', 'o3', 'o4'))
        
        if self.is_o_series:
            # o3/o4用の初期化
            self.deep_llm = ChatOpenAI(
                model=config.deep_think_model,
                temperature=config.temperature,
                max_completion_tokens=config.max_tokens,  # 変更
                timeout=config.timeout
            )
        else:
            # 通常モデル用の初期化
            self.deep_llm = ChatOpenAI(
                model=config.deep_think_model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout
            )
    
    async def generate(self, prompt: str, system_message: Optional[str] = None):
        messages = []
        
        if self.is_o_series and system_message:
            # システムメッセージをユーザーメッセージに統合
            combined_prompt = f"Context: {system_message}\n\n{prompt}"
            messages.append(HumanMessage(content=combined_prompt))
        else:
            # 通常の処理
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
        
        return await self.deep_llm.ainvoke(messages)
```

## なぜすぐに修正できないか

1. **影響範囲が広い**
   - 12個のエージェントすべてが影響を受ける
   - プロンプト構造の大幅な変更が必要

2. **テストが必要**
   - o3/o4とgpt-4の両方で動作確認が必要
   - 後方互換性の維持

3. **LangChainの制限**
   - 使用しているLangChainライブラリがo3/o4に対応していない可能性

## 推奨される対処法

### 短期的解決策（今すぐ使える）
1. **gpt-4-turbo-preview / gpt-3.5-turbo を使用** ✅
2. **モックモードを使用** ✅

### 長期的解決策
1. LLMクライアントの全面的な書き換え
2. o3/o4専用のアダプターレイヤーの実装
3. LangChainの更新またはOpenAI SDKへの直接移行

## 結論

o3/o4モデルは**革新的な機能**を持っていますが、**従来のGPTモデルとは異なるAPI仕様**のため、現在のコードでは使用できません。大規模な修正が必要なため、当面は**gpt-4系列**または**モックモード**の使用を推奨します。