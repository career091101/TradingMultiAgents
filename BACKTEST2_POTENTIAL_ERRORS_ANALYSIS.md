# Backtest2 潜在的エラー要因の包括的分析レポート

## エグゼクティブサマリー

本レポートでは、`'int' object has no attribute 'get'`エラーの根本原因分析と、backtest2システム全体の潜在的なエラー要因を詳細に分析しました。

### 主要な発見事項：
1. **データ型不整合**: エンジンとWebUI間でデータ構造の期待値が異なる
2. **型チェック不足**: 多くの箇所で型チェックが不十分
3. **エラーハンドリング不足**: 例外処理が不完全な箇所が存在

## 1. 根本原因分析

### 1.1 直接的な原因
- **場所**: `webui/components/backtest2.py` の `_aggregate_agent_performance` メソッド（925行目）
- **原因**: `agent_performance` のデータ構造不整合
  - エンジン側: `{"total_decisions": 10, "memory_entries": 20}`
  - WebUI側の期待: `{"agent_name": {"decisions": 10, "correct": 5}}`

### 1.2 エラー発生の流れ
1. バックテストエンジンが簡易形式の `agent_performance` を返す
2. WebUIが nested dict 形式を期待して処理
3. 整数値に対して `.get()` メソッドを呼び出してエラー

## 2. 潜在的エラー要因の洗い出し

### 2.1 型安全性の問題

#### A. 辞書アクセスの問題
```python
# 危険なパターン
result["metrics"]["total_return"]  # KeyError リスク
result["charts"].get("equity_curve")  # result["charts"] が存在しない場合 KeyError

# 安全なパターン
result.get("metrics", {}).get("total_return", 0)
```

**影響箇所**:
- `backtest2.py`: 775, 793, 881, 908, 923行目
- `backtest.py`: 421, 425, 432, 436, 445, 455, 465行目

#### B. 属性アクセスの問題
```python
# 危険なパターン
config.time_range.start  # time_range が None の場合 AttributeError
portfolio.cash  # portfolio が None の場合 AttributeError

# 安全なパターン
config.time_range.start if config.time_range else None
portfolio.cash if portfolio else 0
```

**影響箇所**:
- `backtest2_wrapper.py`: 612-613行目（time_range アクセス）
- `orchestrator.py`: portfolio アクセス箇所
- `agent_adapter.py`: context オブジェクトアクセス箇所

### 2.2 データ型変換の問題

#### A. 日付処理
```python
# 危険なパターン
(end_date - start_date).days  # 日付がNoneまたは文字列の場合エラー
date_obj.strftime("%Y-%m-%d")  # date_objが日付型でない場合エラー
```

**影響箇所**:
- `backtest.py`: 228, 301-302行目
- `backtest2_wrapper.py`: 299-300行目

#### B. 文字列処理
```python
# 危険なパターン
tickers.split(",")  # tickersが文字列でない場合エラー

# 安全なパターン
str(tickers).split(",") if tickers else []
```

**影響箇所**:
- `backtest.py`: 217, 300行目

### 2.3 非同期処理の問題

#### A. イベントループ管理
```python
# 問題のあるパターン
asyncio.run(async_function())  # 既存のイベントループ内で実行するとエラー
```

**影響箇所**:
- `backtest2_wrapper.py`: run_backtest メソッド（236-288行目）

#### B. リソースクリーンアップ
```python
# 不完全なクリーンアップ
await engine.run()
# エラー時にクリーンアップされない可能性
```

**影響箇所**:
- `backtest2_wrapper.py`: 186-190行目

### 2.4 設定値の検証不足

#### A. 必須パラメータの欠如
- LLMプロバイダー設定が不正な場合のフォールバック不足
- APIキーの存在確認不足

#### B. 値の範囲チェック
- 日付範囲の妥当性（開始日 < 終了日）
- 資本金の正値チェック
- スリッページ/手数料の妥当性チェック

### 2.5 エラーメッセージの不適切さ

現在のエラーメッセージは技術的すぎてユーザーフレンドリーではない：
- `'int' object has no attribute 'get'` → 「データ形式エラー」として表示すべき
- スタックトレースの直接表示 → ユーザー向けメッセージに変換すべき

## 3. 推奨される改善策

### 3.1 即時対応が必要な修正

1. **型チェックの強化**
```python
def safe_dict_access(obj, *keys, default=None):
    """安全な辞書アクセスヘルパー"""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, default)
        else:
            return default
    return obj
```

2. **データ検証レイヤーの追加**
```python
def validate_backtest_result(result):
    """バックテスト結果の検証"""
    required_fields = ["ticker", "metrics", "initial_capital"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")
```

3. **エラーハンドリングの改善**
```python
try:
    # 危険な操作
except AttributeError as e:
    logger.error(f"Data structure error: {e}")
    st.error("データ形式にエラーがあります。ログを確認してください。")
```

### 3.2 中長期的な改善提案

1. **型定義の統一**
   - TypedDict または Pydantic モデルの使用
   - エンジンとWebUI間のインターフェース定義

2. **単体テストの追加**
   - エッジケースのテスト
   - 型変換のテスト
   - エラーハンドリングのテスト

3. **ログ改善**
   - 構造化ログの導入
   - エラーレベルの適切な設定
   - ユーザー向けメッセージとデバッグ情報の分離

## 4. リスク評価

### 高リスク（即時対応必要）
1. `agent_performance` のデータ構造不整合 ✅ 修正済み
2. 辞書アクセスの安全性 ⚠️ 部分的に修正
3. None値のチェック不足 ⚠️ 要対応

### 中リスク（計画的対応）
1. 日付処理のエラーハンドリング
2. 非同期処理のエラーハンドリング
3. 設定値の検証

### 低リスク（改善推奨）
1. エラーメッセージの改善
2. ログレベルの最適化
3. パフォーマンス最適化

## 5. アクションアイテム

### 即時実施
- [x] `_aggregate_agent_performance` の修正
- [x] logger インスタンスの追加
- [ ] 安全な辞書アクセスヘルパーの実装
- [ ] 基本的な型チェックの追加

### 1週間以内
- [ ] データ検証レイヤーの実装
- [ ] エラーメッセージの改善
- [ ] 単体テストの追加

### 1ヶ月以内
- [ ] TypedDict/Pydantic による型定義
- [ ] 包括的なエラーハンドリング戦略の実装
- [ ] ドキュメントの整備

## 6. 結論

`'int' object has no attribute 'get'` エラーは、エンジンとWebUI間のデータ構造の不整合が原因でした。この問題は修正済みですが、システム全体には型安全性とエラーハンドリングの改善余地が多く存在します。

推奨される改善策を段階的に実装することで、より堅牢で保守性の高いシステムを構築できます。特に、型チェックの強化とデータ検証レイヤーの追加は、将来的な問題を防ぐために重要です。