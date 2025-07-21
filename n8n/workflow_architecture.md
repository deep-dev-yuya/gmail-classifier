# Gmail自動ラベル分類ワークフロー - 構成説明

## 🎯 目的
Gmailで受信したメールを自動分類し、**Gmail自体にラベルを付与**するワークフロー

## 📋 ワークフロー構成

### 1. 全体フロー図
```
Gmail Trigger
    ↓
Email Preprocessing (HTMLタグ除去・正規化)
    ↓
Context Enricher (文脈補完・エンティティ抽出)
    ↓
AI Classification (Flask API分類)
    ↓
Label Mapping (分類結果→Gmailラベル変換)
    ↓
Gmail Add Label (Gmailにラベル付与)
    ↓
Classification Switch (分類別分岐)
    ├─ Google Sheets Log (通常ログ)
    └─ Low Confidence Log (要確認ログ)
```

### 2. 各ノード詳細

#### Gmail Trigger
- **機能**: 新着メールの監視
- **設定**: 毎分チェック
- **出力**: messageId, subject, textPlain/textHtml

#### Email Preprocessing
- **機能**: HTMLタグ除去・テキスト正規化
- **重要**: messageIdを保持してGmailラベル付与で使用
```javascript
return {
  json: {
    ...data,
    subject: data.subject || '',
    body: normalizedBody,
    messageId: data.id,  // Gmail messageId を保持
    processedAt: new Date().toISOString()
  }
};
```

#### Context Enricher
- **URL**: `http://localhost:5002/api/enrich-context`
- **機能**: 高度文脈補完・エンティティ抽出
- **出力**: enriched_context, priority_level, paypay_strength

#### AI Classification
- **URL**: `http://localhost:5002/api/classify`
- **機能**: Pipeline分類モデルによる分類
- **出力**: classification, confidence, context_analysis

#### Label Mapping
- **機能**: 分類結果をGmailラベルにマッピング
- **ラベルマッピング**:
```javascript
const labelMapping = {
  '支払い関係': 'AI-Payment',
  '重要': 'AI-Important', 
  'プロモーション': 'AI-Promotion',
  '仕事・学習': 'AI-Work-Study'
};
```
- **信頼度チェック**: confidence < 0.5 → 'AI-NeedsReview'

#### Gmail Add Label
- **操作**: `addLabels`
- **設定**: 
  - messageId: `={{ $json.messageId }}`
  - labelIds: `={{ $json.gmailLabel }}`
  - createLabels: true（ラベル自動作成）

#### Classification Switch
- **機能**: 分類結果による分岐処理
- **条件**:
  1. 支払い関係 → 通常ログ
  2. 重要 → 通常ログ
  3. プロモーション → 通常ログ
  4. 仕事・学習 → 通常ログ
  5. 信頼度不足 → 通常ログ + 要確認ログ

#### Google Sheets Log
- **シート**: `ログ!A:H`
- **記録項目**:
  - timestamp, messageId, subject
  - classification, confidence, gmailLabel
  - enrichedContext, status

#### Low Confidence Log
- **シート**: `再学習候補!A:F`
- **条件**: confidence < 0.5
- **記録項目**:
  - timestamp, messageId, subject
  - predictedClass, confidence, reason

## 🔧 設定要項

### 1. 必須設定
- **Gmail API**: modify権限が必要
- **Google Sheets ID**: `YOUR_GOOGLE_SHEET_ID`を実際のIDに変更
- **Flask API**: http://localhost:5002で稼働

### 2. Gmailラベル一覧
自動作成されるラベル:
- `AI-Payment`: 支払い関係
- `AI-Important`: 重要
- `AI-Promotion`: プロモーション
- `AI-Work-Study`: 仕事・学習
- `AI-NeedsReview`: 要確認（信頼度不足）
- `AI-Unclassified`: 未分類

### 3. Google Sheetsシート構成
#### ログシート
| 列 | 項目 | 例 |
|---|---|---|
| A | timestamp | 2025-07-16T10:30:00Z |
| B | messageId | 18f2a1b2c3d4e5f6 |
| C | subject | PayPay利用完了のお知らせ |
| D | classification | 支払い関係 |
| E | confidence | 0.832 |
| F | gmailLabel | AI-Payment |
| G | enrichedContext | 高優先度のメール、PayPay関連... |
| H | status | 完了 |

#### 再学習候補シート
| 列 | 項目 | 例 |
|---|---|---|
| A | timestamp | 2025-07-16T10:30:00Z |
| B | messageId | 18f2a1b2c3d4e5f6 |
| C | subject | 曖昧な件名 |
| D | predictedClass | 重要 |
| E | confidence | 0.423 |
| F | reason | 信頼度不足 |

## 🚀 主な改善点

### 従来ワークフローからの変更
1. **LINE通知削除**: 別ワークフローで処理済みのため除外
2. **Gmailラベル付与**: messageIdを使用したラベル自動付与
3. **全分類対応**: 4つの分類すべてに対応したSwitch条件
4. **信頼度処理**: 低信頼度メールを要確認として別途記録
5. **ラベル自動作成**: 存在しないラベルは自動作成

### 新機能
1. **高度文脈補完**: コンテキストガイド高度化対応
2. **エンティティ抽出**: 金額・日付・サービス情報の抽出
3. **優先度計算**: PayPay特化・緊急度による優先度判定
4. **再学習支援**: 信頼度不足メールの自動記録

## 📊 運用メリット

1. **自動分類**: 手動ラベル付与作業の削減
2. **一貫性**: AI分類による客観的なラベル付与
3. **トレーサビリティ**: 全処理履歴のGoogle Sheets記録
4. **継続改善**: 低信頼度メールの再学習データ蓄積
5. **Gmail統合**: 既存のGmailワークフローとの完全統合

## 🔧 トラブルシューティング

### よくある問題と対処法

1. **ラベル付与失敗**
   - Gmail API権限を確認
   - messageIdが正しく渡されているか確認

2. **分類精度が低い**
   - 再学習候補シートから学習データを追加
   - Flask APIのPipelineモデルを再学習

3. **Google Sheets書き込みエラー**
   - シートIDが正しいか確認
   - 権限設定を確認

4. **Flask API接続エラー**
   - http://localhost:5002でAPIが稼働しているか確認
   - /api/classify エンドポイントが応答するか確認