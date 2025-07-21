# Gmailラベル操作の解決策

## 🚨 問題
n8nワークフローでGmailラベル付与時に以下の問題が発生：
- 事前作成したラベルが一致しない
- 不可視文字やエンコーディング問題
- ラベル自動作成が失敗

## 🔧 解決策

### 方法1: 事前にラベルIDを取得して固定指定

#### A. Gmail APIでラベル一覧取得
```bash
# Gmail APIを使用してラベルID取得
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
"https://gmail.googleapis.com/gmail/v1/users/me/labels"
```

#### B. 手動でラベル作成してIDを控える
1. Gmailで手動でラベル作成
2. Gmail APIでラベルID取得
3. n8nワークフローでIDを直接指定

### 方法2: n8nでHTTP Requestを使用

#### A. ラベル存在確認→作成→付与のフロー
```json
{
  "name": "Gmail Label Check and Create",
  "nodes": [
    {
      "name": "Check Label Exists",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googleApi"
      }
    },
    {
      "name": "Create Label If Not Exists",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        "method": "POST",
        "body": {
          "name": "{{ $json.labelName }}"
        }
      }
    },
    {
      "name": "Add Label to Message",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/{{ $json.messageId }}/modify",
        "method": "POST",
        "body": {
          "addLabelIds": ["{{ $json.labelId }}"]
        }
      }
    }
  ]
}
```

### 方法3: 英語ラベル名使用（推奨）

#### ラベル名を英語に変更
```javascript
// Label Mapping ノード（修正版）
const labelMapping = {
  '支払い関係': 'Payment',
  '重要': 'Important', 
  'プロモーション': 'Promotion',
  '仕事・学習': 'Work_Study'
};
```

### 方法4: システムラベル活用

#### 既存のGmailシステムラベルを活用
```javascript
const labelMapping = {
  '支払い関係': 'IMPORTANT',
  '重要': 'STARRED', 
  'プロモーション': 'CATEGORY_PROMOTIONS',
  '仕事・学習': 'CATEGORY_UPDATES'
};
```