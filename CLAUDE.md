
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
├── app/                # Flask Blueprints（classifier, context_enricher）
│   ├── __init__.py     # アプリファクトリー、CORS設定
│   ├── classifier.py   # メール分類API Blueprint（動的モデル読み込み）
│   └── context_enricher.py # MCP文脈補完API Blueprint
├── models/             # 学習済モデル・再学習スクリプト
│   ├── balanced_model_v1.pkl        # バランス調整モデル（推奨）
│   ├── paypay_specialized_v1.pkl    # PayPay特化モデル（バックアップ）
│   ├── train_balanced_model.py      # バランス調整学習スクリプト
│   └── train_model_paypay.py        # PayPay特化学習スクリプト
├── n8n/                # ワークフロー定義 (*.json) + 実運用ログ
│   ├── gmail_log_sheet.csv          # メイン処理ログ
│   ├── retraining_candidates_sheet.csv # 再学習候補データ
│   └── dashboard_sheet.csv          # 分類統計サマリー
├── scripts/            # 補助スクリプト（ログ掃除等）
├── tests/              # pytest
├── config/             # config.py, .env.sample
├── data/               # 学習用 CSV / Parquet
├── docs/               # 仕様書・ADR など
├── docker/             # Dockerfile, docker-compose.yml
├── run.py              # 開発用ランチャー（ポート5002）
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

# Flask サーバー起動（ポート5002）
python3 run.py
# または
export FLASK_APP=run.py && python3 -m flask run --host=0.0.0.0 --port=5002

# モデル再学習（バランス調整版推奨）
python3 models/train_balanced_model.py
# または PayPay特化版
python3 models/train_model_paypay.py

# API テスト
curl -X POST http://localhost:5002/api/classify \
  -H "Content-Type: application/json" \
  -d '{"messageId":"test","subject":"テスト","body":"テスト内容"}'

# テスト実行
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
| models/train_balanced_model.py | 実運用データでバランス調整モデル学習 |

### 📊 実運用データ活用

```bash
# 実運用ログから高信頼度データを抽出して再学習
python3 models/train_balanced_model.py

# n8nフォルダ内のCSVファイルを確認
ls -la n8n/*.csv
# gmail_log_sheet.csv          # メイン処理ログ
# retraining_candidates_sheet.csv # 低信頼度・要確認データ
# dashboard_sheet.csv          # 分類統計サマリー
```

---

## 📝 FAQ

| Q | A |
|---|---|
| モデル精度が低い | `train_balanced_model.py` で実運用データを活用して再学習 |
| 支払いラベルに偏重する | `balanced_model_v1.pkl` を使用（`class_weight='balanced'`で自動調整済み） |
| 通知が来ない | `.env` 設定 & Webhook URL を確認 |
| ワークフロー消失 | Docker volume 永続化設定を確認 |
| 時刻が正確でない | Gmail APIの`internalDate`活用とタイムゾーン処理が必要 |
| APIエンドポイントが見つからない | `/api/classify` パス（Blueprint使用）、ポート5002で起動 |
| モデルが読み込まれない | `models/` フォルダに `balanced_model_v1.pkl` が存在するか確認 |

---

## 📊 モデル精度改善ノウハウ

### 🎯 クラス不均衡問題の解決

**問題**: 特定ラベル（支払い関係など）への偏重
**解決策**:
```python
# 自動バランス調整
class_weight='balanced'  # 手動重み付けより効果的

# 実運用データ活用
high_confidence_data = df[df['confidence'] >= 0.7]  # 高品質データのみ学習

# 全カテゴリ特徴量強化
# PayPay特化 → バランス型特徴量エンジニアリング
```

### 🔄 継続改善サイクル

```
実運用ログ収集 → CSV分析 → 高信頼度データ抽出 → モデル再学習 → デプロイ
    ↑                                                          ↓
フィードバック ←← 精度検証 ←← テスト実行 ←← 新モデル ←←
```

### 📝 実装記録

**Zettelkosmosノート**: `/Users/hasegawayuya/Documents/Zettelkosmos/Zettelkosmos/20_🛠️Projects/gmail-classifier/`
- 各実装の詳細記録をMarkdown形式で保存
- YAMLフロントマター使用（tags, type, status等）
- 技術的知見と改善プロセスを体系化

### 🔄 自動同期システム（Excel連携）

**概要**: n8nのCSV出力とExcel正解ラベル付けファイルの自動同期システム

**主要機能**:
```bash
# 手動同期
python3 scripts/sync_csv_excel.py --csv-to-excel  # CSV → Excel
python3 scripts/sync_csv_excel.py --excel-to-csv  # Excel → CSV

# 自動同期デーモン
python3 scripts/unified_auto_sync_daemon.py       # ファイル監視型自動同期
```

**ファイル構成**:
- `retraining_candidates_sheet.csv` - n8nが自動書き込み（実際のログ）
- `retraining_candidates_enhanced.csv` - Enhanced版（正解ラベル対応）
- `retraining_candidates_enhanced.xlsx` - ドロップダウン付きExcel（ラベル付け用）

**同期フロー**:
```
n8n → CSV（実ログ） → Enhanced CSV → Excel（ドロップダウン） → 正解ラベル → モデル再学習
```

**運用ガイド**:
- 開発時：手動同期（`scripts/sync_csv_excel.py`）
- 本格運用：自動同期デーモン（`scripts/unified_auto_sync_daemon.py`）
- 正解ラベル：重要・仕事・学習・支払い関係・プロモーション の5分類

**データクリーニング**:
- 重複レコード自動削除（messageIdベース）
- n8nテンプレート行除去
- 空白・null値行の除去

---

## 🔖 Changelog

| Version | Date | Summary |
|---------|------|---------|
| 0.3.0 | 2025-07-22 | モデル精度改善・バランス調整・実運用データ活用・ノート体系化 |
| 0.2.0 | 2025-07-13 | セキュリティ指針・CI 追記 |
| 0.1.0 | 2025-07-11 | 初版作成 |

---

## 🛑 ライセンス
MIT License。API 利用規約の遵守を厳守。
