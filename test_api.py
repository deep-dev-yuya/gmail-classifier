#!/usr/bin/env python3
"""
Flask API テスト
"""

import requests
import json
import time
import subprocess
import signal
import os

def test_api():
    """API分類テスト"""
    
    # APIエンドポイント
    url = "http://localhost:5002/api/classify"
    
    # 実際のメールデータ
    test_emails = [
        {
            "subject": "PayPay利用完了のお知らせ",
            "body": "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン",
            "expected": "支払い関係"
        },
        {
            "subject": "【デビットカード】ご利用のお知らせ",
            "body": "デビットカードのご利用がありました。利用金額：3,360円 利用店舗：OPENAI",
            "expected": "支払い関係"
        },
        {
            "subject": "Amazon タイムセール",
            "body": "Amazonタイムセール開催中です。お得な商品をチェック！",
            "expected": "プロモーション"
        },
        {
            "subject": "システム障害のお知らせ",
            "body": "緊急システム障害が発生しました。復旧作業中です。",
            "expected": "重要"
        },
        {
            "subject": "GitHub 新機能",
            "body": "GitHubの新機能についてご紹介します。開発効率が向上します。",
            "expected": "仕事・学習"
        }
    ]
    
    print("=== Flask API テスト ===\n")
    
    correct_predictions = 0
    total_predictions = len(test_emails)
    
    for i, email in enumerate(test_emails, 1):
        try:
            # APIリクエスト
            response = requests.post(url, json={
                "subject": email["subject"],
                "body": email["body"]
            }, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                prediction = result["classification"]
                confidence = result["confidence"]
                
                print(f"テスト{i}:")
                print(f"  件名: {email['subject']}")
                print(f"  本文: {email['body'][:40]}...")
                print(f"  予測: {prediction} (確率: {confidence:.3f})")
                print(f"  期待: {email['expected']}")
                print(f"  結果: {'✅ 正解' if prediction == email['expected'] else '❌ 不正解'}")
                
                if prediction == email['expected']:
                    correct_predictions += 1
                    
                # 信頼度チェック
                if confidence < 0.5:
                    print(f"  ⚠️  信頼度が低い: {confidence:.3f}")
                
                print()
                
            else:
                print(f"テスト{i}: APIエラー {response.status_code}")
                print(f"  エラー内容: {response.text}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"テスト{i}: 接続エラー - {e}")
            print()
    
    accuracy = correct_predictions / total_predictions
    print(f"=== 結果サマリー ===")
    print(f"正解数: {correct_predictions}/{total_predictions}")
    print(f"精度: {accuracy:.1%}")
    
    if accuracy < 0.8:
        print(f"\n❌ API分類精度が低いです。")
        print("推奨アクション:")
        print("1. モデルの再読み込みを試す")
        print("2. 学習データを追加する")
        print("3. 特徴量エンジニアリングを見直す")
    else:
        print(f"\n✅ API分類精度は許容範囲です。")

if __name__ == "__main__":
    test_api()