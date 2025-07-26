# 🍎 M1 Mac ARM64環境の使用方法

## 現在の状況

- ✅ ARM64ネイティブ環境（`.venv_arm64`）作成済み
- ✅ 必要なパッケージインストール済み
- ✅ Yahoo Finance動作確認済み
- ⚠️ デフォルトはまだx86_64環境

## ARM64環境への切り替え方法

### 方法1: 起動スクリプトを使用（推奨）

```bash
# WebUIをARM64モードで起動
./run_webui_arm64.sh
```

### 方法2: 手動で環境を切り替え

```bash
# ARM64環境をアクティベート
source .venv_arm64/bin/activate

# 確認
python -c "import platform; print(f'Architecture: {platform.machine()}')"
# → "Architecture: arm64" と表示されればOK

# WebUIを起動
python TradingMultiAgents/run_webui.py
```

### 方法3: 新しいターミナルでARM64環境を使用

```bash
# 新しいターミナルを開く
# ARM64環境を直接アクティベート
cd /Users/y-sato/TradingAgents2
source .venv_arm64/bin/activate

# WebUIを起動
python TradingMultiAgents/run_webui.py
```

## ⚠️ 重要な注意事項

1. **現在のWebUIセッション**
   - 現在起動中のWebUIはx86_64モードで動作中
   - ARM64に切り替える場合は一度停止して再起動が必要

2. **環境の確認方法**
   ```bash
   # どちらの環境を使用しているか確認
   which python
   # .venv/bin/python → x86_64環境
   # .venv_arm64/bin/python → ARM64環境
   ```

3. **パッケージの互換性**
   - x86_64とARM64の環境は完全に分離
   - パッケージは各環境で個別にインストール必要

## 🚀 推奨される使用方法

1. **新規ターミナルセッション**
   - 新しいターミナルを開く
   - `source .venv_arm64/bin/activate`を実行
   - ARM64ネイティブモードで作業

2. **VSCodeなどのエディタ**
   - Pythonインタープリタを`.venv_arm64/bin/python`に設定
   - 統合ターミナルでARM64環境を使用

3. **デフォルト環境の変更**
   ```bash
   # .zshrcまたは.bash_profileに追加
   alias activate_trading="cd /Users/y-sato/TradingAgents2 && source .venv_arm64/bin/activate"
   ```

## 📊 パフォーマンスの違い

| 項目 | x86_64 (Rosetta 2) | ARM64 (ネイティブ) |
|------|-------------------|-------------------|
| 起動時間 | ~5秒 | ~3秒 |
| CPU使用率 | 高い | 低い |
| メモリ効率 | 普通 | 良い |
| バッテリー消費 | 多い | 少ない |

## 🔄 環境の切り替え

```bash
# x86_64からARM64へ
deactivate  # 現在の環境を無効化
source .venv_arm64/bin/activate

# ARM64からx86_64へ（非推奨）
deactivate
source .venv/bin/activate
```

## 📝 まとめ

M1 MacではARM64ネイティブ環境（`.venv_arm64`）の使用を強く推奨します。
パフォーマンスが向上し、バッテリー持続時間も改善されます。