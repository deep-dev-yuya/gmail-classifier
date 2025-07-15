# gmail-classifier

_Automatically classify Gmail messages using AI and automate actions via n8n + Flask + MCP (Proof of Concept)._

Gmailから受信したメールを機械学習で自動分類し、n8n + Flask + MCP を使用して自動処理するPoCプロジェクトです。

---

## 🎯 プロジェクト概要

### 主な機能
- **メール自動分類**: 機械学習（SVM + TF-IDF）によるメール分類
- **文脈補完**: MCP（Model Context Protocol）による文脈情報の抽出
- **自動通知**: 重要メールのLINE通知
- **ログ記録**: Google Sheetsへの分類結果保存

### 技術スタック
- **Backend**: Flask + Python 3.10+
- **ML**: scikit-learn (SVM, TF-IDF)
- **Workflow**: n8n (Docker)
- **APIs**: Gmail API, LINE Messaging API, Google Sheets API

---

## 📁 プロジェクト構造

```
gmail-classifier/
├── app/                    # Flask アプリケーション
├── models/                 # 機械学習モデル
├── n8n/                    # n8nワークフロー設定
├── data/                   # 学習データ
├── config/                 # 設定ファイル
├── tests/                  # テストファイル
├── docs/                   # ドキュメント
├── config.py               # Flask設定
├── requirements.txt        # Python依存関係
├── .env.example            # 環境変数サンプル
└── run.py                  # メイン実行ファイル
```

---
## 🚀 セットアップ手順

### 1. 環境準備

```bash
git clone https://github.com/your-org/gmail-classifier.git
cd gmail-classifier

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 環境変数設定

```bash
cp .env.example .env
# .envファイルをエディタで開き、必要なAPIキーや設定値を入力してください
# 例:
# LINE_CHANNEL_ACCESS_TOKEN=your_line_token
# GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
# GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

### 3. モデル学習

```bash
cd models
python train_model.py
```

### 4. Flask API起動

```bash
cd ..
python run.py
```

### 5. n8nワークフロー設定

`n8n/setup_guide.md` を参照してください。

---
## 📊 API エンドポイント

### メール分類 API
```
POST /api/classify
Content-Type: application/json

{
  "subject": "支払い期限のお知らせ",
  "body": "クレジットカード料金の引き落とし日が近づいています"
}
```

### 文脈補完 API
```
POST /api/enrich-context
Content-Type: application/json

{
  "subject": "会議のご案内",
  "body": "来週の定例ミーティングについて"
}
```

### ヘルスチェック
```
GET /health
```

## 🔧 使用方法

### 基本的な流れ
1. **Gmail Trigger**: n8nがGmailを監視
2. **前処理**: HTMLタグ除去・テキスト正規化
3. **文脈補完**: MCP APIで文脈情報を抽出
4. **AI分類**: 機械学習モデルでメール分類
5. **分岐処理**: 分類結果に応じて処理を分岐
6. **通知・保存**: LINE通知 & Google Sheets保存

### テスト方法
```bash
# APIテスト
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"subject":"テスト件名","body":"テスト本文"}'

# ヘルスチェック
curl http://localhost:5000/health
```

## 📝 注意事項

- 本プロジェクトはPoC（概念実証）用途です。本番運用前に十分なテストとセキュリティ対策を行ってください。
- APIキーや認証情報は絶対に公開しないでください。
- 個人情報・機密情報の取り扱いにご注意ください。

---

## 📚 参考資料

- [n8n公式ドキュメント](https://docs.n8n.io/)
- [Flask公式ドキュメント](https://flask.palletsprojects.com/)
- [scikit-learn公式ドキュメント](https://scikit-learn.org/)

---

## 📝 ライセンス

このリポジトリのライセンスは `LICENSE` ファイルをご確認ください。（未設定の場合は「ライセンス未定」と記載）

---

## 🤝 コントリビューション

バグ報告・改善提案・プルリクエスト歓迎します！

---
