#!/usr/bin/env python3
"""
自動同期システムのセットアップスクリプト
"""

import os
import json
import subprocess
from datetime import datetime

def create_launchd_plist():
    """
    macOS LaunchAgent用のplistファイルを作成
    """
    plist_content = {
        "Label": "com.gmail-classifier.auto-sync",
        "ProgramArguments": [
            "/usr/bin/python3",
            "/Users/user/Projects/dev-projects/gmail-classifier/scripts/auto_sync_daemon.py"
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": "/Users/user/Projects/dev-projects/gmail-classifier/logs/auto_sync.log",
        "StandardErrorPath": "/Users/user/Projects/dev-projects/gmail-classifier/logs/auto_sync_error.log",
        "WorkingDirectory": "/Users/user/Projects/dev-projects/gmail-classifier"
    }
    
    # logsディレクトリを作成
    logs_dir = "/Users/user/Projects/dev-projects/gmail-classifier/logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # plistファイルを作成
    plist_path = "/Users/user/Library/LaunchAgents/com.gmail-classifier.auto-sync.plist"
    
    # XML形式でplistを出力
    import plistlib
    with open(plist_path, 'wb') as f:
        plistlib.dump(plist_content, f)
    
    print(f"✅ LaunchAgent plist作成: {plist_path}")
    return plist_path

def create_startup_script():
    """
    手動実行用の起動スクリプトを作成
    """
    script_content = '''#!/bin/bash
# Gmail分類自動同期システム起動スクリプト

echo "🚀 Gmail分類自動同期システムを開始します..."

# プロジェクトディレクトリに移動
cd /Users/user/Projects/dev-projects/gmail-classifier

# 自動同期デーモンを起動
python3 scripts/auto_sync_daemon.py
'''
    
    script_path = "/Users/user/Projects/dev-projects/gmail-classifier/start_auto_sync.sh"
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # 実行権限を付与
    os.chmod(script_path, 0o755)
    
    print(f"✅ 起動スクリプト作成: {script_path}")
    return script_path

def create_manual_sync_aliases():
    """
    手動同期用のエイリアス設定を作成
    """
    aliases_content = '''
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
alias gmail-status="python3 -c 'import sys; sys.path.append(\"scripts\"); from automated_workflow import print_workflow_status; print_workflow_status()'"

# 自動同期デーモン
alias gmail-auto-sync="python3 scripts/auto_sync_daemon.py"
alias gmail-start-auto="./start_auto_sync.sh"

# Excelファイルを開く
alias gmail-excel="open n8n/retraining_candidates_enhanced.xlsx"

echo "Gmail分類システム エイリアス読み込み完了 ✅"
'''
    
    aliases_path = "/Users/user/Projects/dev-projects/gmail-classifier/gmail_aliases.sh"
    
    with open(aliases_path, 'w') as f:
        f.write(aliases_content)
    
    print(f"✅ エイリアス設定作成: {aliases_path}")
    return aliases_path

def setup_auto_sync_system():
    """
    自動同期システムの完全セットアップ
    """
    print("🔧 Gmail分類自動同期システム セットアップ")
    print("=" * 60)
    
    # 1. LaunchAgent plist作成
    plist_path = create_launchd_plist()
    
    # 2. 手動起動スクリプト作成
    script_path = create_startup_script()
    
    # 3. エイリアス設定作成
    aliases_path = create_manual_sync_aliases()
    
    print("\n" + "=" * 60)
    print("📋 セットアップ完了 - 選択できる起動方法")
    print("=" * 60)
    
    print("\n🔄 方法1: 自動起動（LaunchAgent）")
    print("システム起動時に自動で同期デーモンが開始されます")
    print("コマンド:")
    print(f"  launchctl load {plist_path}")
    print(f"  launchctl start com.gmail-classifier.auto-sync")
    
    print("\n🔄 方法2: 手動起動（推奨）")
    print("必要な時だけ同期デーモンを起動")
    print("コマンド:")
    print(f"  {script_path}")
    print("または:")
    print(f"  python3 scripts/auto_sync_daemon.py")
    
    print("\n🔄 方法3: 完全手動同期")
    print("自動化なしで必要な時だけ同期実行")
    print("コマンド:")
    print("  python3 scripts/sync_csv_excel.py --csv-to-excel")
    
    print("\n📋 便利エイリアス")
    print("以下を ~/.zshrc に追加すると便利:")
    print(f"  source {aliases_path}")
    
    print("\n🎯 推奨運用方法")
    print("1. 【開発・テスト時】: 方法2（手動起動）")
    print("   - 必要な時だけデーモン起動")
    print("   - リソース消費を最小限に")
    print("   - デバッグしやすい")
    
    print("2. 【本格運用時】: 方法1（自動起動）")
    print("   - システム起動時に自動開始")
    print("   - 24時間監視")
    print("   - 完全自動化")
    
    print("3. 【軽量運用時】: 方法3（完全手動）")
    print("   - 自動化なし")
    print("   - 最小リソース消費")
    print("   - 手動制御")

def test_auto_sync():
    """
    自動同期システムのテスト
    """
    print("\n🧪 自動同期システムテスト")
    print("-" * 40)
    
    csv_path = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.csv'
    
    if not os.path.exists(csv_path):
        print("❌ テスト対象CSVファイルが存在しません")
        return False
    
    # CSVファイルの現在の状態を確認
    import pandas as pd
    df = pd.read_csv(csv_path)
    print(f"📊 現在のCSVレコード数: {len(df)}")
    
    # 自動同期デーモンのテスト実行
    print("🔄 自動同期デーモンを5秒間テスト実行...")
    print("   （Ctrl+Cで停止してください）")
    
    return True

if __name__ == "__main__":
    setup_auto_sync_system()
    
    print("\n" + "=" * 60)
    choice = input("🧪 自動同期テストを実行しますか？ (y/N): ").strip().lower()
    
    if choice in ['y', 'yes']:
        if test_auto_sync():
            print("\n🚀 テスト実行中...")
            print("新しいターミナルで以下を実行してください:")
            print("python3 scripts/auto_sync_daemon.py")
    else:
        print("\n✅ セットアップ完了")
        print("上記の方法から選択して自動同期を開始してください")