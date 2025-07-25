#!/usr/bin/env python3
"""
修正版CSV-Excel自動同期デーモン
実際のn8nファイル（retraining_candidates_sheet.csv）を監視
"""

import os
import time
import subprocess
from datetime import datetime
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class UnifiedCSVWatcher(FileSystemEventHandler):
    """実際のn8nファイルを監視するクラス"""
    
    def __init__(self):
        # 実際にn8nが書き込むファイル
        self.actual_csv = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_sheet.csv - retraining_candidates_sheet.csv'
        # Enhanced版ファイル（同期先）
        self.enhanced_csv = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.csv'
        self.enhanced_excel = '/Users/user/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_enhanced.xlsx'
        
        self.last_sync_time = 0
        self.sync_cooldown = 30  # 30秒のクールダウン
        
    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.is_directory:
            return
            
        # 実際のn8nファイルが変更された場合
        if event.src_path == self.actual_csv:
            current_time = time.time()
            
            if current_time - self.last_sync_time < self.sync_cooldown:
                return
            
            print(f"📝 n8nファイル変更検出: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.sync_files()
            self.last_sync_time = current_time
    
    def sync_files(self):
        """実際のCSV → Enhanced版 → Excel の同期"""
        try:
            print("🔄 n8nファイル → Enhanced版 → Excel 同期開始...")
            
            # ステップ1: 実際のCSVをEnhanced版に変換
            if not self.convert_to_enhanced():
                return
            
            # ステップ2: Enhanced版をExcelに同期
            if not self.sync_to_excel():
                return
            
            print("✅ 完全同期完了")
            
        except Exception as e:
            print(f"❌ 同期処理エラー: {str(e)}")
    
    def convert_to_enhanced(self):
        """実際のCSVをEnhanced版形式に変換"""
        try:
            if not os.path.exists(self.actual_csv):
                print(f"❌ 元ファイルが存在しません: {self.actual_csv}")
                return False
            
            # 実際のCSVを読み込み
            df_actual = pd.read_csv(self.actual_csv)
            
            # Enhanced版の列構造
            required_columns = [
                'timestamp', 'messageId', 'subject', 'predictedClass', 
                'confidence', 'reason', 'groundTruth', 'correctionReason', 
                'correctedAt', 'correctedBy'
            ]
            
            # 既存のEnhanced版がある場合、ラベル情報を保持
            existing_labels = {}
            if os.path.exists(self.enhanced_csv):
                df_existing = pd.read_csv(self.enhanced_csv)
                for _, row in df_existing.iterrows():
                    if pd.notna(row.get('groundTruth')) and row.get('groundTruth') != '':
                        existing_labels[row['messageId']] = {
                            'groundTruth': row['groundTruth'],
                            'correctionReason': row.get('correctionReason', ''),
                            'correctedAt': row.get('correctedAt', ''),
                            'correctedBy': row.get('correctedBy', '')
                        }
            
            # 不足列を追加
            for col in required_columns:
                if col not in df_actual.columns:
                    df_actual[col] = ''
            
            # 既存ラベルを復元
            for idx, row in df_actual.iterrows():
                message_id = row['messageId']
                if message_id in existing_labels:
                    labels = existing_labels[message_id]
                    df_actual.at[idx, 'groundTruth'] = labels['groundTruth']
                    df_actual.at[idx, 'correctionReason'] = labels['correctionReason']
                    df_actual.at[idx, 'correctedAt'] = labels['correctedAt']
                    df_actual.at[idx, 'correctedBy'] = labels['correctedBy']
            
            # Enhanced版として保存
            df_actual[required_columns].to_csv(self.enhanced_csv, index=False, encoding='utf-8')
            
            labeled_count = len(df_actual[df_actual['groundTruth'].notna() & (df_actual['groundTruth'] != '')])
            print(f"📊 Enhanced版更新: {len(df_actual)} records ({labeled_count} labeled)")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced版変換エラー: {str(e)}")
            return False
    
    def sync_to_excel(self):
        """Enhanced版CSVをExcelに同期"""
        try:
            sync_script = '/Users/user/Projects/dev-projects/gmail-classifier/scripts/sync_csv_excel.py'
            
            if not os.path.exists(sync_script):
                print(f"❌ 同期スクリプトが見つかりません: {sync_script}")
                return False
            
            cmd = ['python3', sync_script, '--csv-to-excel']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📝 Excel同期完了")
                return True
            else:
                print(f"❌ Excel同期エラー: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Excel同期処理エラー: {str(e)}")
            return False

def start_unified_auto_sync():
    """統合自動同期デーモンを開始"""
    
    watcher = UnifiedCSVWatcher()
    
    # ファイル存在確認
    if not os.path.exists(watcher.actual_csv):
        print(f"❌ 監視対象ファイルが見つかりません: {watcher.actual_csv}")
        return False
    
    print("🚀 Gmail分類統合自動同期デーモン開始")
    print(f"📁 監視対象: {os.path.basename(watcher.actual_csv)}")
    print(f"📁 同期先Excel: {os.path.basename(watcher.enhanced_excel)}")
    print(f"🔄 同期間隔: 30秒のクールダウン")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("-" * 60)
    
    # ファイル監視設定
    observer = Observer()
    observer.schedule(watcher, os.path.dirname(watcher.actual_csv), recursive=False)
    
    try:
        observer.start()
        
        # 初回同期を実行
        print("🔄 初回同期を実行...")
        watcher.sync_files()
        
        # 無限ループで監視続行
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n⏹️  統合自動同期デーモンを停止中...")
        observer.stop()
        print("✅ 停止完了")
        
    observer.join()
    return True

if __name__ == "__main__":
    import sys
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ watchdog パッケージが必要です")
        print("インストール: pip3 install watchdog")
        sys.exit(1)
    
    start_unified_auto_sync()
