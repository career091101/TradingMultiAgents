# バックテスト失敗診断レポート

## 発生日時
2025-07-25 16:11:54

## エラー概要
不明なエラー

## 発生箇所
- ファイル: `/Users/y-sato/TradingAgents2/verify_backtest_advanced.py`
- 行番号: 92
- 関数名: `run_backtest`

## 根本原因の推定
エラーの詳細を特定できませんでした

## 推奨される対処法
ログファイルを手動で確認してください

## 詳細ログ
```
実行エラー: 'Transaction' object has no attribute 'total_value'

Traceback:
Traceback (most recent call last):
  File "/Users/y-sato/TradingAgents2/verify_backtest_advanced.py", line 92, in run_backtest
    "total_value": t.total_value
                   ^^^^^^^^^^^^^
AttributeError: 'Transaction' object has no attribute 'total_value'

```
