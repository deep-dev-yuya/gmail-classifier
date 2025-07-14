# Gmail分類PoC プロジェクト

Gmailから受信したメールを機械学習で自動分類し、n8n + Flask + MCP を使用して自動処理するプロジェクトです。

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

## 📁 プロジェクト構造

```
gmail-classifier/
├── app/                    # Flask アプリケーション
│   ├── __init__.py        # アプリファクトリー
│   ├── classifier.py      # メール分類API
│   └── context_enricher.py # MCP文脈補完API
├── models/                 # 機械学習モデル
│   ├── train_model.py     # モデル学習スクリプト
│   └── model.pkl          # 学習済みモデル（生成後）
├── n8n/                   # n8nワークフロー設定
│   ├── workflow_sample.json # サンプルワークフロー
│   └── setup_guide.md     # セットアップガイド
├── data/                  # 学習データ
├── config/               # 設定ファイル
├── tests/               # テストファイル
├── docs/               # ドキュメント
├── config.py          # Flask設定
├── requirements.txt   # Python依存関係
├── .env.example      # 環境変数サンプル
└── run.py           # メイン実行ファイル
```

## 🚀 セットアップ手順

### 1. 環境準備
```bash
# プロジェクトディレクトリに移動
cd /Users/hasegawayuya/Projects/dev-projects/gmail-classifier

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. 環境変数設定
```bash
# .env ファイル作成
cp .env.example .env

# 必要なAPIキーを設定
# - LINE_CHANNEL_ACCESS_TOKEN
# - GOOGLE_SHEETS_CREDENTIALS_FILE
# - GOOGLE_SHEETS_SPREADSHEET_ID
```

### 3. モデル学習
```bash
# 学習データディレクトリで実行
cd models
python train_model.py
```

### 4. Flask API起動
```bash
# プロジェクトルートで実行
python run.py
```

### 5. n8nワークフロー設定
`n8n/setup_guide.md` を参照してワークフロー設定を行ってください。

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

## 📝 開発メモ

### 分類ラベル
- **支払い関係**: 請求書、支払い通知など
- **通知**: 会議案内、一般的なお知らせ
- **重要**: 緊急連絡、システム障害など

### モデル改善
- 学習データの追加・改善
- 特徴量エンジニアリング
- ハイパーパラメータ調整

## 🔍 トラブルシューティング

### よくある問題
1. **モデルファイルが見つからない**: `models/train_model.py` を実行
2. **API接続エラー**: Flask サーバーの起動状態確認
3. **認証エラー**: 各種API キーの設定確認

### ログ確認
```bash
# アプリケーションログ
tail -f logs/app.log
```

## 📚 参考資料

- [n8n公式ドキュメント](https://docs.n8n.io/)
- [Flask公式ドキュメント](https://flask.palletsprojects.com/)
- [scikit-learn公式ドキュメント](https://scikit-learn.org/)

## 🤝 開発・拡張

### 今後の改善案
- [ ] 信頼度の低い分類の人間確認フロー
- [ ] モデルの自動再学習機能
- [ ] 多言語対応
- [ ] リアルタイム分類精度モニタリング

---

**注意**: 本プロジェクトはPoC（概念実証）用途です。本格運用前に十分なテストと設定見直しを行ってください。