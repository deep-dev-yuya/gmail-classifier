#!/usr/bin/env python3
"""
完全自動化ワークフロー管理スクリプト
CSV-Excel同期からモデル更新まで一元管理
"""

import os
import subprocess
import time
from datetime import datetime
import pandas as pd

def check_file_changes():
    """
    CSVファイルの変更を監視し、必要に応じて同期実行
    """
    csv_path = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.csv'
    excel_path = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.xlsx'
    
    # ファイルの最終更新時刻を取得
    csv_mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0
    excel_mtime = os.path.getmtime(excel_path) if os.path.exists(excel_path) else 0
    
    # CSVがExcelより新しい場合
    if csv_mtime > excel_mtime:
        print("📥 CSVファイルが更新されています。Excel同期を実行...")
        return 'csv_to_excel'
    
    # ExcelがCSVより新しい場合
    elif excel_mtime > csv_mtime:
        print("📝 Excelファイルが更新されています。CSV同期を実行...")
        return 'excel_to_csv'
    
    return None

def run_csv_to_excel_sync():
    """CSV → Excel 同期を実行"""
    cmd = ['python3', 'scripts/sync_csv_excel.py', '--csv-to-excel']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ CSV → Excel 同期完了")
        return True
    else:
        print(f"❌ CSV → Excel 同期エラー: {result.stderr}")
        return False

def run_excel_to_csv_sync():
    """Excel → CSV 同期を実行"""
    cmd = ['python3', 'scripts/sync_csv_excel.py', '--excel-to-csv']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Excel → CSV 同期完了")
        return True
    else:
        print(f"❌ Excel → CSV 同期エラー: {result.stderr}")
        return False

def check_labeled_data():
    """正解ラベル付きデータの数をチェック"""
    csv_path = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.csv'
    
    if not os.path.exists(csv_path):
        return 0
    
    df = pd.read_csv(csv_path)
    labeled_count = len(df[df['groundTruth'].notna() & (df['groundTruth'] != '')])
    
    return labeled_count

def run_model_update():
    """モデル更新を実行"""
    print("🤖 モデル更新を実行中...")
    
    cmd = ['python3', 'scripts/update_groundtruth_model.py']
    
    # 自動承認のため入力を送信
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input='y\n')
    
    if process.returncode == 0:
        print("✅ モデル更新完了")
        print(stdout)
        return True
    else:
        print(f"❌ モデル更新エラー: {stderr}")
        return False

def reload_api_model():
    """Flask APIでモデルリロード"""
    print("🔄 Flask APIモデルリロード中...")
    
    cmd = ['curl', '-X', 'POST', 'http://localhost:5002/api/model/reload']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ API モデルリロード完了")
        return True
    else:
        print(f"❌ API モデルリロードエラー: {result.stderr}")
        return False

def create_workflow_status():
    """ワークフローの状態をレポート"""
    csv_path = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.csv'
    
    if not os.path.exists(csv_path):
        return {
            'total_records': 0,
            'labeled_records': 0,
            'unlabeled_records': 0,
            'labeling_progress': 0
        }
    
    df = pd.read_csv(csv_path)
    total = len(df)
    labeled = len(df[df['groundTruth'].notna() & (df['groundTruth'] != '')])
    unlabeled = total - labeled
    progress = (labeled / total * 100) if total > 0 else 0
    
    return {
        'total_records': total,
        'labeled_records': labeled,
        'unlabeled_records': unlabeled,
        'labeling_progress': progress
    }

def print_workflow_status():
    """ワークフロー状態を表示"""
    status = create_workflow_status()
    
    print("\n" + "="*60)
    print("📊 Gmail分類ワークフロー状態")
    print("="*60)
    print(f"📝 総レコード数: {status['total_records']}")
    print(f"✅ ラベル付き: {status['labeled_records']}")
    print(f"⏳ 未ラベル: {status['unlabeled_records']}")
    print(f"📈 進捗率: {status['labeling_progress']:.1f}%")
    
    # モデルファイルの存在確認
    models = {
        'supervised_model_v1.pkl': '教師あり学習モデル',
        'realworld_improved_v1.pkl': '実運用改良モデル',
        'balanced_model_v1.pkl': 'バランス調整モデル'
    }
    
    print("\n🤖 利用可能モデル:")
    for model_file, description in models.items():
        model_path = f'/Users/user/Projects/dev-projects/gmail-classifier/models/{model_file}'
        status = "✅" if os.path.exists(model_path) else "❌"
        print(f"   {status} {description}")
    
    print("="*60)

def interactive_workflow():
    """対話型ワークフロー実行"""
    print("🚀 Gmail分類ワークフロー管理システム")
    print("="*60)
    
    while True:
        print("\n📋 利用可能な操作:")
        print("1. ファイル変更チェック & 自動同期")
        print("2. CSV → Excel 同期")
        print("3. Excel → CSV 同期")
        print("4. モデル更新実行")
        print("5. API モデルリロード")
        print("6. ワークフロー状態確認")
        print("7. 完全自動実行")
        print("0. 終了")
        
        choice = input("\n選択してください (0-7): ").strip()
        
        if choice == '0':
            print("👋 ワークフロー管理を終了します")
            break
        
        elif choice == '1':
            sync_type = check_file_changes()
            if sync_type == 'csv_to_excel':
                run_csv_to_excel_sync()
            elif sync_type == 'excel_to_csv':
                run_excel_to_csv_sync()
            else:
                print("📊 ファイルに変更はありません")
        
        elif choice == '2':
            run_csv_to_excel_sync()
        
        elif choice == '3':
            run_excel_to_csv_sync()
        
        elif choice == '4':
            labeled_count = check_labeled_data()
            if labeled_count > 0:
                print(f"📊 {labeled_count}件のラベル付きデータでモデル更新を実行")
                run_model_update()
            else:
                print("⚠️  ラベル付きデータがありません。先にラベル付け作業を実行してください")
        
        elif choice == '5':
            reload_api_model()
        
        elif choice == '6':
            print_workflow_status()
        
        elif choice == '7':
            print("🎯 完全自動実行を開始...")
            auto_workflow()
        
        else:
            print("❌ 無効な選択です")

def auto_workflow():
    """完全自動ワークフロー実行"""
    print("\n🤖 完全自動ワークフロー実行中...")
    
    # ステップ1: ファイル変更チェック
    sync_type = check_file_changes()
    if sync_type == 'csv_to_excel':
        if not run_csv_to_excel_sync():
            return False
        print("📝 Excelファイルでラベル付け作業を実行してください")
        print("   完了後、再度このスクリプトを実行してください")
        return True
    
    elif sync_type == 'excel_to_csv':
        if not run_excel_to_csv_sync():
            return False
    
    # ステップ2: ラベル付きデータの確認
    labeled_count = check_labeled_data()
    if labeled_count < 5:
        print(f"⚠️  ラベル付きデータが少なすぎます ({labeled_count}件)")
        print("   最低5件以上のラベル付けを推奨します")
        return False
    
    # ステップ3: モデル更新
    if not run_model_update():
        return False
    
    # ステップ4: API更新
    if not reload_api_model():
        return False
    
    # ステップ5: 状態確認
    print_workflow_status()
    
    print("\n🎉 完全自動ワークフローが正常に完了しました！")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # 自動実行モード
        auto_workflow()
    else:
        # 対話モード
        interactive_workflow()