
# Gmail分類システム 便利エイリアス
# ~/.zshrc または ~/.bash_profile に追加してください

# プロジェクトディレクトリへの移動
alias gmail-cd="cd /Users/user/Projects/dev-projects/gmail-classifier"

# 同期コマンド
alias gmail-sync-to-excel="python3 scripts/sync_csv_excel.py --csv-to-excel"
alias gmail-sync-to-csv="python3 scripts/sync_csv_excel.py --excel-to-csv"
alias gmail-sync-both="python3 scripts/sync_csv_excel.py --both"

# ワークフロー管理
alias gmail-workflow="python3 scripts/automated_workflow.py"
alias gmail-status="python3 -c 'import sys; sys.path.append("scripts"); from automated_workflow import print_workflow_status; print_workflow_status()'"

# 自動同期デーモン
alias gmail-auto-sync="python3 scripts/auto_sync_daemon.py"
alias gmail-start-auto="./start_auto_sync.sh"

# Excelファイルを開く
alias gmail-excel="open n8n/retraining_candidates_enhanced.xlsx"

echo "Gmail分類システム エイリアス読み込み完了 ✅"
