#!/usr/bin/env python3
"""
実際のメールデータでモデルテスト
"""

import sys
sys.path.append('/Users/hasegawayuya/Projects/dev-projects/gmail-classifier')

from models.model_sync_solution import create_paypay_specialized_features, load_pipeline_model

def test_real_email_data():
    """実際のメールデータでテスト"""
    
    # Pipeline化モデルの読み込み
    try:
        pipeline, metadata = load_pipeline_model()
    except Exception as e:
        print(f"モデル読み込みエラー: {e}")
        return
    
    # 実際のメールデータ（ユーザーが報告したもの）
    test_emails = [
        {
            "subject": "PayPay利用完了のお知らせ",
            "body": "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン 利用日時：2025年7月15日 08:30",
            "expected": "支払い関係"
        },
        {
            "subject": "【デビットカード】ご利用のお知らせ",
            "body": "デビットカードのご利用がありました。承認番号：769534 利用日時：2025/07/16 07:47:38 利用加盟店：OPENAI *CHATGPT SUBSCR 引落通貨：JPY 引落金額：3,360.00",
            "expected": "支払い関係"
        },
        {
            "subject": "三井住友銀行 振込完了のお知らせ",
            "body": "お振込みが完了しました。振込先：田中太郎 振込金額：50,000円 振込日時：2025/07/16 14:30 手数料：220円",
            "expected": "支払い関係"
        },
        {
            "subject": "楽天カード ご利用確定のお知らせ",
            "body": "楽天カードのご利用が確定しました。利用日：2025/07/15 利用先：Amazon.co.jp 利用金額：2,980円 支払い方法：一括払い",
            "expected": "支払い関係"
        },
        {
            "subject": "LINE Pay 決済完了通知",
            "body": "LINE Payでの決済が完了しました。決済金額：1,580円 利用店舗：ファミリーマート 決済日時：2025/07/16 12:45",
            "expected": "支払い関係"
        }
    ]
    
    print("=== 実際のメールデータでのテスト ===\n")
    
    correct_predictions = 0
    total_predictions = len(test_emails)
    
    for i, email in enumerate(test_emails, 1):
        # 特徴量エンジニアリング適用
        text = f"{email['subject']} {email['body']}"
        enhanced_text = create_paypay_specialized_features(text)
        
        # 予測
        prediction = pipeline.predict([enhanced_text])[0]
        probabilities = pipeline.predict_proba([enhanced_text])[0]
        max_prob = max(probabilities)
        
        # 結果出力
        print(f"テスト{i}:")
        print(f"  件名: {email['subject']}")
        print(f"  本文: {email['body'][:50]}...")
        print(f"  予測: {prediction} (確率: {max_prob:.3f})")
        print(f"  期待: {email['expected']}")
        print(f"  結果: {'✅ 正解' if prediction == email['expected'] else '❌ 不正解'}")
        print()
        
        if prediction == email['expected']:
            correct_predictions += 1
    
    accuracy = correct_predictions / total_predictions
    print(f"=== 結果サマリー ===")
    print(f"正解数: {correct_predictions}/{total_predictions}")
    print(f"精度: {accuracy:.1%}")
    
    if accuracy < 0.8:
        print(f"\n❌ 精度が低すぎます。追加学習が必要です。")
        print(f"推奨アクション:")
        print(f"1. 学習データを増やす")
        print(f"2. 特徴量エンジニアリングを強化")
        print(f"3. クラス重みを調整")
    else:
        print(f"\n✅ 精度は許容範囲内です。")

if __name__ == "__main__":
    test_real_email_data()