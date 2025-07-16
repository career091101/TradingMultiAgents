# 判断理由と推奨項目の文字切れ修正

## 修正日時
2025年7月16日

## 問題
- 判断理由が300文字で切れて、重要な推奨根拠が表示されない
- ポジティブ/リスク要因が150文字で切れて、分析内容が不完全
- 推奨事項が200文字で切れて、具体的な投資計画が見えない

## 修正内容

### 1. 判断理由の文字数拡張と改善
```python
# 修正前
"reasoning": final_report[:300] + "..." if len(final_report) > 300 else final_report

# 修正後
- 基本: 800文字まで表示
- 賢い抽出: 「最終判断」「結論」「総合評価」等のキーワードを探して、重要部分を優先表示
- 信頼度: 「強く」「高い信頼」等のキーワードから自動判定
```

### 2. ポジティブ要因・リスク要因
```python
# 修正前
if len(clean_line) <= 150:
    points.append(clean_line)  # 150文字以下

# 修正後
if len(clean_line) <= 250:
    points.append(clean_line)  # 250文字以下
else:
    # 句読点で自然に区切る（200文字以降の句読点を探す）
    cutoff_point = clean_line[:250].rfind('。')
    if cutoff_point > 200:
        points.append(clean_line[:cutoff_point + 1])
    else:
        points.append(clean_line[:250] + "...")
```

### 3. 推奨事項
```python
# 修正前
if len(clean_line) <= 200:
    processed_line = clean_line

# 修正後  
if len(clean_line) <= 350:
    processed_line = clean_line
else:
    # 句読点で自然に区切る（300文字以降の句読点を探す）
    cutoff_point = clean_line[:350].rfind('。')
    if cutoff_point > 300:
        processed_line = clean_line[:cutoff_point + 1]
    else:
        processed_line = clean_line[:350] + "..."
```

## 文字数設定まとめ

| 項目 | 修正前 | 修正後 | 理由 |
|------|--------|--------|------|
| 判断理由 | 300文字 | 800文字 | 重要な推奨根拠まで表示 |
| ポジティブ/リスク要因 | 150文字 | 250文字 | 完全な分析ポイントを表示 |
| 推奨事項 | 200文字 | 350文字 | 具体的な投資計画を表示 |

## 追加改善

### インテリジェントな判断理由抽出
- 「最終判断」「結論」「総合評価」等のキーワードを検索
- 見つかった場合は、その位置から800文字を抽出
- キーワードがない場合は最初から800文字

### 信頼度の自動判定
- 「強く」「高い信頼」→ 信頼度「高」
- 「低い」「慎重」→ 信頼度「低」
- それ以外 → 信頼度「中程度」

これらの修正により、重要な情報が途切れることなく、完全な分析結果を確認できるようになりました。