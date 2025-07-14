# n8n ワークフロー セットアップガイド

## 概要
Gmail分類PoCのn8nワークフロー設定手順

## 前提条件
- n8n（Docker版）が稼働していること
- Flask APIサーバー（localhost:5000）が起動していること
- Gmail API認証が完了していること

## セットアップ手順

### 1. ワークフローのインポート
1. n8n Web UI（http://localhost:5678）にアクセス
2. 「New workflow」から新規作成
3. `workflow_sample.json` の内容をインポート

### 2. Gmail Trigger設定
- Gmail APIの認証設定
- 監視対象フォルダの指定（INBOX推奨）
- ポーリング間隔の調整（1分間隔がデフォルト）

### 3. HTTP Request ノード設定
- **MCP Context Enricher**: `http://localhost:5000/api/enrich-context`
- **AI Classification**: `http://localhost:5000/api/classify`

### 4. LINE通知設定
- LINE Messaging API Token の設定
- Channel Access Token の追加

### 5. Google Sheets設定
- Google Sheets API認証
- 対象スプレッドシートIDの設定
- 書き込み権限の確認

## ワークフロー構成

```
Gmail Trigger 
    ↓
Email Preprocessing 
    ↓
MCP Context Enricher
    ↓
AI Classification
    ↓
Switch分類
    ├── 重要 → LINE Message Creation → LINE通知
    └── その他 → Google Sheetsログ保存
```

## テスト方法

### 1. 手動実行
- 「Execute Workflow」ボタンでテスト実行
- 各ノードの出力データを確認

### 2. Gmail送信テスト
- 自分宛にテストメールを送信
- 分類結果とLINE通知を確認

## トラブルシューティング

### API接続エラー
- Flask APIサーバーの起動状態確認
- ファイアウォール設定の確認

### 認証エラー
- Gmail API、LINE API、Google Sheets APIの認証状態確認
- トークンの有効期限確認

### 分類精度の改善
- 学習データの追加・改善
- モデルの再学習実行

## 注意事項
- 本ワークフローはPoC用のため、本格運用前に十分なテストを実施してください
- APIトークンやシークレットは適切に管理してください