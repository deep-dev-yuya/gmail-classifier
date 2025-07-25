
# Google Sheets対応版設定手順

## 🚨 重要な注意点
**Google SheetsノードはExcelファイル（.xlsx）を直接読み込めません**
Google Spreadsheetのみ対応しているため、以下の手順が必要です。

---

## 📋 ステップ1: Google Sheetsファイルの作成

### **方法A: 手動アップロード（推奨）**

1. **Google Drive を開く**
   ```
   https://drive.google.com
   ```

2. **新しいスプレッドシートを作成**
   - 「新規」→「Google スプレッドシート」→「空白のスプレッドシート」

3. **シート名を設定**
   - シート名: `Gmail分類正解ラベル付け`
   - ファイル名: `retraining_candidates_enhanced`

4. **列ヘッダーを設定**
   ```
   A: timestamp
   B: messageId  
   C: subject
   D: predictedClass
   E: confidence
   F: reason
   G: groundTruth
   H: correctionReason
   I: correctedAt
   J: correctedBy
   ```

5. **データ検証を設定**
   - G列（groundTruth）を選択
   - データ→データの入力規則
   - 条件：「リストを直接指定」
   - 項目：
     ```
     支払い関係
     重要
     プロモーション
     仕事・学習
     ```
   - 「無効なデータの場合」：「入力を拒否」を選択

---

## 📋 ステップ2: Google Sheets APIの設定

### **Google Cloud Console設定**

1. **Google Cloud Console を開く**
   ```
   https://console.cloud.google.com
   ```

2. **APIs & Services を開く**
   - 「APIとサービス」→「ライブラリ」

3. **Google Sheets API を有効化**
   - 「Google Sheets API」を検索
   - 「有効にする」をクリック

4. **サービスアカウントを作成**
   - 「認証情報」→「認証情報を作成」→「サービスアカウント」
   - 名前：`gmail-classifier-sheets`
   - 役割：「編集者」

5. **キーファイルをダウンロード**
   - サービスアカウント→「キー」→「新しいキーを作成」
   - 形式：JSON
   - ダウンロードしたファイルを安全な場所に保存

### **スプレッドシートの共有**

1. **作成したGoogle Sheetsを開く**
2. **「共有」ボタンをクリック**
3. **サービスアカウントのメールアドレスを追加**
   - 権限：「編集者」
   - 通知しない設定でOK

---

## 📋 ステップ3: n8nワークフローの更新

### **Google Sheetsノードの設定**

```json
{
  "parameters": {
    "authentication": "serviceAccount",
    "resource": "append",
    "sheetId": "YOUR_GOOGLE_SHEETS_ID",
    "range": "Gmail分類正解ラベル付け!A:J",
    "options": {},
    "columns": {
      "mappingMode": "defineBelow",
      "value": {
        "timestamp": "={{ $('Email Preprocessing with Timestamps').item.json.japanTime }}",
        "messageId": "={{ $json.messageId }}",
        "subject": "={{ $json.subject }}",
        "predictedClass": "={{ $json.classification }}",
        "confidence": "={{ $json.confidence }}",
        "reason": "信頼度不足",
        "groundTruth": "",
        "correctionReason": "",
        "correctedAt": "",
        "correctedBy": ""
      }
    }
  },
  "credentials": {
    "googleSheetsApi": {
      "id": "google_sheets_service_account",
      "name": "Gmail Classifier Sheets Account"
    }
  }
}
```

### **認証情報の設定**

1. **n8n管理画面を開く**
2. **「認証情報」→「新しい認証情報を作成」**
3. **「Google Sheets API (Service Account)」を選択**
4. **設定項目**:
   - 名前: `Gmail Classifier Sheets Account`
   - Service Account Email: `サービスアカウントのメール`
   - Private Key: `ダウンロードしたJSONファイルの private_key`

---

## 📋 ステップ4: ハイブリッド運用の提案

### **方法B: CSV + 定期同期（実用的）**

Google Sheetsの制約を考慮し、以下のハイブリッド運用を推奨：

1. **n8nはCSVファイルに直接書き込み（現行通り）**
   ```
   retraining_candidates_enhanced.csv
   ```

2. **定期的にGoogle Sheetsと同期**
   ```python
   # 同期スクリプト例
   def sync_csv_to_google_sheets():
       # CSVを読み込み
       df = pd.read_csv('retraining_candidates_enhanced.csv')
       
       # Google Sheetsに書き込み
       # (Google Sheets APIを使用)
   ```

3. **ラベル付けはGoogle Sheetsで実行**
   - データ検証（ドロップダウン）機能を活用
   - 複数人での同時作業が可能

4. **完了後はCSVに反映**
   ```python
   # Google Sheets → CSV同期
   def sync_google_sheets_to_csv():
       # Google Sheetsから読み込み
       # CSVファイルを更新
   ```

---

## 🎯 推奨アプローチ

### **最も実用的な解決策**

1. **n8nワークフロー**: CSVに直接書き込み（現行維持）
2. **ラベル付け作業**: Excelファイル使用（ドロップダウン活用）
3. **モデル更新**: CSVから直接読み込み

**理由**:
- Google Sheets APIの複雑性を回避
- Excelのドロップダウン機能を最大活用
- ローカルファイルでの高速処理
- オフライン作業も可能

---

## 🔧 既存Excelファイルの活用継続

現在作成済みの以下ファイルを継続使用：

```
📁 使用継続ファイル:
├── retraining_candidates_enhanced.csv    # n8n書き込み先
├── retraining_candidates_enhanced.xlsx   # ラベル付け作業用
├── 正解ラベル付け_使用方法.md            # 操作手順書
└── update_groundtruth_model.py          # モデル更新スクリプト
```

**運用フロー**:
```
n8n → CSV書き込み → Excelでラベル付け → モデル更新 → API反映
```

---

## 📞 サポート

Google Sheets版が必要な場合は、上記手順に従って設定してください。
ただし、現在のExcel + CSV方式の方が実用的で効率的です。
