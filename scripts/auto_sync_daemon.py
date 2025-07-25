#!/usr/bin/env python3
"""
CSV-Excel自動同期デーモン
CSVファイルの変更を監視して自動的にExcelに同期
"""

import os
import time
import subprocess
from datetime import datetime
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CSVWatcher(FileSystemEventHandler):
    """CSVファイルの変更を監視するクラス"""
    
    def __init__(self, csv_path, sync_script_path):
        self.csv_path = csv_path
        self.sync_script_path = sync_script_path
        self.last_sync_time = 0
        self.sync_cooldown = 30  # 30秒のクールダウン（重複実行防止）
        
    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.is_directory:
            return
            
        # 監視対象のCSVファイルが変更された場合
        if event.src_path == self.csv_path:
            current_time = time.time()
            
            # クールダウン期間中は処理しない
            if current_time - self.last_sync_time < self.sync_cooldown:
                return
            
            print(f"📝 CSV変更検出: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.sync_to_excel()
            self.last_sync_time = current_time
    
    def sync_to_excel(self):
        """CSV → Excel 同期を実行"""
        try:
            print("🔄 CSV → Excel 自動同期開始...")
            
            # 同期スクリプトを実行
            cmd = ['python3', self.sync_script_path, '--csv-to-excel']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 自動同期完了")
                
                # レコード数を確認
                df = pd.read_csv(self.csv_path)
                labeled_count = len(df[df['groundTruth'].notna() & (df['groundTruth'] != '')])
                print(f"📊 総レコード: {len(df)}, ラベル付き: {labeled_count}")
                
            else:
                print(f"❌ 同期エラー: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 同期処理エラー: {str(e)}")

def start_auto_sync_daemon():
    """自動同期デーモンを開始"""
    csv_path = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.csv'
    sync_script_path = '/Users/user/Projects/dev-projects/gmail-classifier/scripts/sync_csv_excel.py'
    
    # ファイルの存在確認
    if not os.path.exists(csv_path):
        print(f"❌ CSVファイルが見つかりません: {csv_path}")
        return False
    
    if not os.path.exists(sync_script_path):
        print(f"❌ 同期スクリプトが見つかりません: {sync_script_path}")
        return False
    
    print("🚀 CSV-Excel自動同期デーモン開始")
    print(f"📁 監視対象: {os.path.basename(csv_path)}")
    print(f"🔄 同期間隔: 30秒のクールダウン")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 60)
    
    # ファイル監視設定
    event_handler = CSVWatcher(csv_path, sync_script_path)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(csv_path), recursive=False)
    
    try:
        observer.start()
        
        # 初回同期を実行
        print("🔄 初回同期を実行...")
        event_handler.sync_to_excel()
        
        # 無限ループで監視続行
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n⏹️  自動同期デーモンを停止中...")
        observer.stop()
        print("✅ 停止完了")
        
    observer.join()
    return True

if __name__ == "__main__":
    import sys
    
    # 必要なパッケージのインストール確認
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ watchdog パッケージが必要です")
        print("インストール: pip3 install watchdog")
        sys.exit(1)
    
    start_auto_sync_daemon()