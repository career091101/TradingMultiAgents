# backtest2システム エラー分析レポート

## 実施日時
2025年7月22日

## エラー概要
backtest2システムで発生している主要なエラーとその根本原因を徹底的に分析しました。

## 発見されたエラー

### 1. DecisionContextのシリアライズエラー
**症状**:
- `'DecisionContext' object has no attribute 'get'`
- `Object of type DecisionContext is not JSON serializable`

**根本原因**:
- orchestrator.pyで重複した三項演算子による誤った処理
- DecisionContextデータクラスに`to_dict()`メソッドが不足

**修正内容**:
- ✅ DecisionContext.to_dict()メソッドを追加
- ✅ orchestrator.pyの重複した三項演算子を修正
- ✅ BacktestJSONEncoderでカスタムシリアライゼーション対応

### 2. TradeAction列挙型の変換エラー
**症状**:
- `'string (BUY/SELL/HOLD)' is not a valid TradeAction`

**根本原因**:
- LLMのスキーマ定義が文字列説明（"string (BUY/SELL/HOLD)"）として定義
- LLMがスキーマの説明文をそのまま値として返却

**修正内容**:
- ✅ TradeAction.from_string()メソッドを追加
- ✅ agent_adapter.pyの全スキーマ定義を適切なJSON Schema形式に修正

### 3. NoneType エラー
**症状**:
- `'NoneType' object has no attribute 'cash'`

**根本原因**:
- PortfolioStateオブジェクトがNoneで渡されるケース
- 初期化処理の不備またはエラーハンドリングの問題

**対応状況**:
- 🔄 調査継続中（ポートフォリオ初期化プロセスの確認が必要）

### 4. 非同期タスクのクリーンアップ問題
**症状**:
- `Task was destroyed but it is pending!`
- 複数のCacheManager._cleanup_loopタスクが未完了

**根本原因**:
- LLMクライアントのcleanupメソッドが呼ばれていない
- エンジンのクリーンアップでオーケストレーターのリソース解放が不完全

**対応状況**:
- 🔄 調査継続中（エンジンとオーケストレーターのクリーンアップフロー改善が必要）

### 5. 新規エラー
**症状**:
- `'int' object has no attribute 'get'`

**根本原因**:
- backtest2_wrapperでエラー発生時にticker_resultsが未定義のまま代入される
- WebUIのbacktest.pyで結果の型チェックが不足

**修正内容**:
- ✅ backtest2_wrapperのエラーハンドリングを修正
- ✅ WebUI backtest.pyに型チェックを追加
- ✅ engine.pyのself.orchestratorをself.agent_orchestratorに修正

## 修正の優先順位

### 高優先度（即座に修正必要）
1. ✅ LLMスキーマ定義の修正（完了）
2. ✅ DecisionContextのシリアライゼーション（完了）
3. 🔄 PortfolioStateのNone値対応
4. 🔄 非同期タスクのクリーンアップ

### 中優先度
1. LLMレスポンスの型検証強化
2. エラーハンドリングの改善
3. ログ出力の充実

### 低優先度
1. パフォーマンス最適化
2. メモリ使用量の削減

## 技術的詳細

### スキーマ定義の問題
修正前:
```python
"action": "string (BUY/SELL/HOLD)"
"confidence": "number (0-1)"
```

修正後:
```python
"action": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]}
"confidence": {"type": "number", "minimum": 0, "maximum": 1}
```

### 非同期処理の問題
```python
# 問題: クリーンアップタスクが適切にキャンセルされない
async def _cleanup_loop(self):
    while True:  # 無限ループがキャンセルされない
        await asyncio.sleep(self.cleanup_interval.total_seconds())
```

## 推奨される次のステップ

1. **ポートフォリオ初期化の確認**
   - PositionManagerの初期化プロセスを調査
   - Noneチェックの追加

2. **非同期タスク管理の改善**
   - エンジンのクリーンアップにオーケストレーターのクリーンアップを追加
   - 全LLMクライアントのcleanupメソッド呼び出しを確保

3. **型安全性の向上**
   - LLMレスポンスの型検証を強化
   - TypedDictやPydanticモデルの活用

4. **統合テストの追加**
   - エンドツーエンドのバックテストフロー
   - エラー発生時のリカバリーテスト

## まとめ
backtest2システムの主要なエラーの多くは、異なるシステム（TradingAgentsとbacktest2）を統合する際の型の不一致とインターフェースの相違から生じています。

### 本日修正完了した項目：
1. ✅ LLMスキーマ定義の修正（agent_adapter.py）
2. ✅ DecisionContextのシリアライゼーション（types.py, llm_client.py）
3. ✅ orchestratorの重複三項演算子修正
4. ✅ engine.pyのorchestrator参照エラー修正
5. ✅ backtest2_wrapperのエラーハンドリング改善
6. ✅ WebUI backtest.pyの型チェック追加

### 残存課題：
1. 🔄 非同期タスクのクリーンアップ（CacheManager._cleanup_loop）
2. 🔄 PortfolioStateのNone値チェック強化（必要に応じて）

これらの修正により、backtest2システムの安定性が大幅に向上しました。