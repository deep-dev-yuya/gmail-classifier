
# CLAUDE.md

## 📌 プロジェクト名
Gmail AI Classifier

## 🧠 プロジェクト概要
Gmail で受信したメールを機械学習モデルで自動分類し、内容に応じて **LINE Messaging API** への通知や **Google Sheets** への記録を行う PoC（概念実証）プロジェクトです。  
Flask 製の API を n8n（Docker 永続化）から呼び出し、分類 ➜ 付加情報付与 ➜ 通知・保存までを自動化します。

> **Claude Code 利用時の狙い**：  
> - **再現性** — コード・構成・依存バージョンを固定  
> - **安全性** — 機密情報の秘匿と最小権限設計  
> - **読みやすさ** — ファイル/モジュール粒度で責務を明確化

---

## 🧰 技術スタック
| 分類 | 採用技術 | 備考 |
|------|----------|------|
| 言語 | Python 3.10 以上 | 3.12 系でも検証済み |
| Web フレームワーク | Flask 2.3.3 | Blueprint 分割 |
| 機械学習 | scikit-learn（TF-IDF + LinearSVC） | spaCy に差し替え可 |
| ワークフロー | n8n + Docker Compose | volumes で完全永続化 |
| 補助 | MCP（Model Context Protocol） | 文脈強化 |
| 外部 API | Gmail (IMAP), LINE Messaging, Google Sheets | すべて OAuth2 / サービスアカウント対応 |

---

## 🗂 プロジェクト構造
```
/gmail-classifier/
├── app/                # Flask Blueprints（predict, enrich など）
│   ├── __init__.py
│   ├── predict/        # 推論エンドポイント
│   └── enrich/         # メタデータ付加
├── models/             # 学習済モデル・再学習スクリプト
├── n8n/                # ワークフロー定義 (*.json)
├── scripts/            # 補助スクリプト（ログ掃除等）
├── tests/              # pytest
├── config/             # config.py, .env.sample
├── data/               # 学習用 CSV / Parquet
├── docs/               # 仕様書・ADR など
├── docker/             # Dockerfile, docker-compose.yml
├── run.py              # 開発用ランチャー
├── requirements.txt
└── README.md
```
> フォルダー名は `snake_case`、モジュール名は `lower_snake_case`、クラス名は `UpperCamelCase` を推奨。

---

## 🛡️ セキュリティ & 秘匿情報

1. `.env.sample` をベースに各自 `.env` を作成。  
2. `.gitignore` に `.env`, `*.pkl`, `data/raw/`, `logs/` を追加。  
3. 外部サービスの認証は最小スコープに限定。  
4. n8n は Basic Auth + 内部ネットワークで保護。

---

## 📐 開発ルール

- PEP 8 + Black + isort
- pre-commit：ruff, mypy, pytest をフック
- docs/adr/ に ADR を Markdown 形式で保存
- GitHub Actions：CI 実行（pytest + flake8 + safety）

---

## 🚀 ビルド / テスト / デプロイ

```bash
# 開発環境セットアップ
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Flask
flask run --reload

# モデル再学習
python models/train_model.py

# テスト
pytest -q

# n8n 起動
docker compose -f docker/docker-compose.yml up -d
```

---

## 🛠️ 運用補助スクリプト

| スクリプト | 目的 |
|------------|------|
| clean_n8n_logs.sh | n8n ログ掃除 |
| fix_encoding_server.py | Base64/文字コード復元 |
| backup_gsheet.py | Sheets バックアップ |

---

## 📝 FAQ

| Q | A |
|---|---|
| モデル精度が低い | 教師データを増やし、ハイパラ最適化 |
| 通知が来ない | `.env` 設定 & Webhook URL を確認 |
| ワークフロー消失 | Docker volume 永続化設定を確認 |

---

## 🔖 Changelog

| Version | Date | Summary |
|---------|------|---------|
| 0.2.0 | 2025-07-13 | セキュリティ指針・CI 追記 |
| 0.1.0 | 2025-07-11 | 初版作成 |

---

## 🛑 ライセンス
MIT License。API 利用規約の遵守を厳守。
