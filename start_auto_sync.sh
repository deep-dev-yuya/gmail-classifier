#!/bin/bash
# Gmail分類自動同期システム起動スクリプト

echo "🚀 Gmail分類自動同期システムを開始します..."

# プロジェクトディレクトリに移動
cd /Users/user/Projects/dev-projects/gmail-classifier

# 自動同期デーモンを起動
python3 scripts/auto_sync_daemon.py
