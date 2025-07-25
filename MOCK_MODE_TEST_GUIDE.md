# モックモードでのバックテスト実行ガイド

## 1. WebUIにアクセス
ブラウザで http://localhost:8501 を開く

## 2. サイドバーから「📊 バックテスト」をクリック

## 3. 以下の設定を入力

### 基本設定
- **バックテスト名**: `mock_test_001`
- **初期資本**: `10000`
- **開始日**: `2025-07-01`
- **終了日**: `2025-07-14`
- **シンボル**: `AAPL` (1つだけ入力)

### LLM設定
- **Deep Think Model**: `mock`
- **Quick Think Model**: `mock`
- **Temperature**: `0.0`
- **Timeout**: `600`

### 実行モード
- **Mock Mode**: ✅ チェックを入れる
- **Debug Mode**: ✅ チェックを入れる
- **Dry Run**: ❌ チェックを外す

## 4. 「バックテストを実行」ボタンをクリック

## 5. 期待される結果
- **実行時間**: 1-2分程度（モックモードのため高速）
- **取引回数**: 10回以上
- **全フェーズの完了**:
  - Phase 1: Data Collection ✓
  - Phase 2: Investment Analysis ✓
  - Phase 3: Investment Decision ✓
  - Phase 4: Trading Decision ✓
  - Phase 5: Risk Assessment ✓
  - Phase 6: Final Decision ✓

## 6. 結果の確認ポイント
- ポートフォリオサマリーに取引回数が表示される
- 個別ティッカーパフォーマンスに実際の数値が表示される
- エージェントパフォーマンスに各エージェントの活動が記録される

## トラブルシューティング
- もし取引回数が0の場合、ログを確認してください
- エラーが発生した場合、デバッグログを確認してください