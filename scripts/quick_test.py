#!/usr/bin/env python3
"""
Gmail分類PoC クイックテストスクリプト
セットアップ後の動作確認用
"""

import requests
import json
import sys
import os

# 設定
API_BASE_URL = "http://localhost:5000"

def test_health_check():
    """ヘルスチェックテスト"""
    print("🔍 ヘルスチェック...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ サーバー正常: {data}")
            return True
        else:
            print(f"❌ ヘルスチェック失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def test_classification():
    """分類APIテスト"""
    print("\n🤖 メール分類テスト...")
    
    test_cases = [
        {
            "name": "支払い関係",
            "subject": "クレジットカード請求書",
            "body": "今月の利用明細をお送りします。支払い期限は月末です。"
        },
        {
            "name": "会議通知",
            "subject": "定例ミーティングのご案内",
            "body": "来週の定例ミーティングを開催します。参加をお願いします。"
        },
        {
            "name": "緊急通知",
            "subject": "緊急：システム障害",
            "body": "重要なシステム障害が発生しました。至急対応が必要です。"
        }
    ]
    
    for case in test_cases:
        try:
            payload = {
                "subject": case["subject"],
                "body": case["body"]
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/classify",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {case['name']}: {data['classification']} (信頼度: {data['confidence']:.2f})")
            else:
                print(f"❌ {case['name']}: 分類失敗 ({response.status_code})")
                
        except Exception as e:
            print(f"❌ {case['name']}: エラー - {e}")

def test_context_enrichment():
    """文脈補完APIテスト"""
    print("\n🧠 文脈補完テスト...")
    
    test_cases = [
        {
            "name": "支払い文脈",
            "subject": "支払い期限のお知らせ",
            "body": "料金の引き落としが2025年7月15日に実行されます。"
        },
        {
            "name": "会議文脈", 
            "subject": "会議のご案内",
            "body": "来週の月曜日にプロジェクト会議を開催します。"
        }
    ]
    
    for case in test_cases:
        try:
            payload = {
                "subject": case["subject"],
                "body": case["body"]
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/enrich-context",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {case['name']}:")
                print(f"   文脈: {data['enriched_context']}")
                print(f"   優先度: {data['priority_level']}")
                print(f"   キーワード: {data['keywords']}")
                if data['deadline_info']:
                    print(f"   期限: {data['deadline_info']}")
            else:
                print(f"❌ {case['name']}: 文脈補完失敗 ({response.status_code})")
                
        except Exception as e:
            print(f"❌ {case['name']}: エラー - {e}")

def test_model_status():
    """モデル状態テスト"""
    print("\n📊 モデル状態確認...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/model/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ モデル状態:")
            print(f"   ファイル存在: {data['model_file_exists']}")
            print(f"   モデル読み込み済み: {data['model_loaded']}")
            print(f"   パス: {data['model_path']}")
        else:
            print(f"❌ モデル状態確認失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ モデル状態確認エラー: {e}")

def main():
    """メイン実行"""
    print("=== Gmail分類PoC クイックテスト ===")
    
    # ヘルスチェック
    if not test_health_check():
        print("\n❌ サーバーが起動していません。")
        print("   以下のコマンドでサーバーを起動してください:")
        print("   cd /Users/hasegawayuya/Projects/dev-projects/gmail-classifier")
        print("   python run.py")
        sys.exit(1)
    
    # 各種テスト実行
    test_model_status()
    test_classification()
    test_context_enrichment()
    
    print("\n🎉 テスト完了！")
    print("\n📝 次のステップ:")
    print("1. n8nワークフローの設定 (n8n/setup_guide.md を参照)")
    print("2. LINE API、Google Sheets API の設定")
    print("3. 学習データの追加・改善")

if __name__ == "__main__":
    main()