# Streamlit接続エラー解決手順

## 状況
- Streamlitサーバーは正常に起動（ポート8501）
- HTTPレスポンスは200 OK
- ブラウザ側で接続エラー表示

## 解決方法

### 1. ブラウザのキャッシュクリア
- **Chrome/Edge**: Cmd+Shift+R（強制リロード）
- または開発者ツール → Network → Disable cache にチェック

### 2. 別のブラウザで試す
```bash
open http://localhost:8501
```

### 3. シークレット/プライベートウィンドウで開く
- Chrome: Cmd+Shift+N
- Safari: Cmd+Shift+N
- Firefox: Cmd+Shift+P

### 4. 直接IPアドレスでアクセス
```bash
open http://127.0.0.1:8501
```

### 5. ネットワークURLを使用
サーバーログに表示されている：
```
Network URL: http://192.168.50.9:8501
```

### 6. Streamlitの設定確認
現在のプロセス:
- PID: 61702
- 正常に動作中
- ログレベル: debug

## デバッグ情報
- ログファイル: `/Users/y-sato/TradingAgents2/streamlit_debug.log`
- セッションID: 12809eb8-5701-4222-bfe9-eb80587f72ca
- タイムゾーン: Asia/Tokyo