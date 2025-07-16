#!/usr/bin/env python3
"""
Gmail分類システム - モデル不一致根本解決
統合ソリューション: Pipeline化 + 単一特徴量関数 + 確率化
"""

import pandas as pd
import pickle
import joblib
import os
import re
from typing import List, Dict, Tuple
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def create_paypay_specialized_features(text: str) -> str:
    """
    PayPay特化特徴量エンジニアリング - 単一定義版
    注意: この関数は model_sync_solution.py でのみ定義し、他からはimportする
    """
    features = []
    
    # 基本テキスト
    features.append(text)
    
    # === PayPay特化特徴量（重点強化） ===
    paypay_variants = [
        'PayPay', 'paypay', 'ペイペイ', 'ペイ', 'PAYPAY', 
        'PayPay残高', 'PayPay決済', 'PayPay利用'
    ]
    
    # PayPay検出強度計算
    paypay_strength = 0
    for variant in paypay_variants:
        count = text.count(variant)
        if count > 0:
            paypay_strength += count
            features.append(f"PAYPAY_VARIANT_{variant.replace(' ', '_')}")
    
    if paypay_strength > 0:
        features.append(f"PAYPAY_STRENGTH_{min(paypay_strength, 5)}")
    
    # PayPay文脈特徴量
    paypay_contexts = {
        'チャージ': ['チャージ', 'charge', '入金', '残高追加'],
        '決済': ['決済', '支払い', '購入', 'お支払い', '利用'],
        '完了': ['完了', '終了', 'しました', 'されました'],
        '通知': ['お知らせ', '通知', 'ご案内', 'notice']
    }
    
    for context_type, keywords in paypay_contexts.items():
        context_count = sum(1 for keyword in keywords if keyword in text)
        if context_count > 0:
            features.append(f"PAYPAY_CONTEXT_{context_type}_{context_count}")
    
    # === 決済サービス階層化特徴量 ===
    payment_services = {
        'major': ['PayPay', 'LINE Pay', 'Apple Pay', 'Google Pay'],
        'credit': ['ペイディ', 'Paidy', 'メルペイ', '楽天ペイ'],
        'card': ['デビットカード', 'クレジットカード', 'VISA', 'MasterCard', 'JCB'],
        'bank': ['銀行振込', '口座振替', '引き落とし', '振替']
    }
    
    for service_type, services in payment_services.items():
        service_count = sum(1 for service in services if service in text)
        if service_count > 0:
            features.append(f"PAYMENT_TYPE_{service_type.upper()}_{service_count}")
    
    # === 金額パターン拡張特徴量 ===
    amount_patterns = {
        'comma_yen': r'\d{1,3}(?:,\d{3})*円',
        'symbol_yen': r'¥\d{1,3}(?:,\d{3})*',
        'decimal': r'\d+\.\d{2}',
        'simple_yen': r'\d+円',
        'range_amount': r'\d{3,6}円'
    }
    
    total_amounts = 0
    for pattern_name, pattern in amount_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            total_amounts += len(matches)
            features.append(f"AMOUNT_{pattern_name.upper()}_{len(matches)}")
            
            # 金額レンジ分類
            for match in matches:
                numbers = re.findall(r'\d+', match.replace(',', ''))
                if numbers:
                    amount = int(numbers[0])
                    if amount < 1000:
                        features.append("AMOUNT_RANGE_SMALL")
                    elif amount < 10000:
                        features.append("AMOUNT_RANGE_MEDIUM")
                    else:
                        features.append("AMOUNT_RANGE_LARGE")
    
    if total_amounts > 0:
        features.append(f"TOTAL_AMOUNT_MENTIONS_{min(total_amounts, 3)}")
    
    # === 決済アクション詳細分類 ===
    action_categories = {
        'completion': ['完了', '終了', 'しました', 'されました', '実行'],
        'processing': ['処理中', '手続き', '確認中', 'processing'],
        'notification': ['お知らせ', '通知', 'ご案内', '連絡'],
        'charge': ['チャージ', '入金', '追加', '補充'],
        'payment': ['支払い', '決済', '購入', '引き落とし', '振替'],
        'card_usage': ['ご利用', '使用', '決済', 'transaction']
    }
    
    for action_type, actions in action_categories.items():
        action_count = sum(1 for action in actions if action in text)
        if action_count > 0:
            features.append(f"ACTION_{action_type.upper()}_{action_count}")
    
    # === PayPay特化組み合わせ特徴量 ===
    if any(variant in text for variant in paypay_variants) and any(completion in text for completion in ['完了', 'しました']):
        features.append("PAYPAY_COMPLETION_COMBO")
    
    if any(variant in text for variant in paypay_variants) and total_amounts > 0:
        features.append("PAYPAY_AMOUNT_COMBO")
    
    return ' '.join(features)

def create_training_data() -> pd.DataFrame:
    """統合学習データの作成"""
    training_data = [
        # PayPay特化学習データ
        {
            "subject": "PayPay決済完了のお知らせ",
            "body": "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン 利用日時：2025年7月15日 08:30",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay利用確定通知",
            "body": "ペイペイ決済が確定いたしました。決済額：2,480円 加盟店：ファミリーマート 決済時刻：07:45:32",
            "label": "支払い関係"
        },
        {
            "subject": "PayPayお支払い完了",
            "body": "PayPayアプリでの支払いが正常に完了しました。金額：850円 店舗：ローソン 日時：2025/07/14 19:20",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay残高チャージ完了",
            "body": "PayPay残高へのチャージが完了しました。チャージ額：5,000円 方法：銀行口座 手数料：無料",
            "label": "支払い関係"
        },
        {
            "subject": "ペイペイ残高追加のお知らせ",
            "body": "ペイペイ残高に3,000円が追加されました。現在の残高：8,420円 チャージ方法：クレジットカード",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay - オンライン決済完了",
            "body": "PayPayによるオンライン決済が完了しました。購入先：Amazon.co.jp 決済金額：3,980円 商品：日用品",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay楽天市場決済",
            "body": "楽天市場でのPayPay決済が確定しました。注文金額：6,750円 獲得ポイント：67ポイント PayPay残高から支払い",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay送金完了",
            "body": "PayPayでの送金が完了しました。送金額：2,000円 送金先：田中太郎 メッセージ：飲み代ありがとう",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay受取通知",
            "body": "PayPayで1,500円を受け取りました。送金者：佐藤花子 メッセージ：お疲れさまでした",
            "label": "支払い関係"
        },
        {
            "subject": "PayPay利用明細（月次）",
            "body": "PayPay月次利用明細をお送りします。総利用額：45,680円 利用回数：23回 主な利用先：コンビニ、飲食店",
            "label": "支払い関係"
        },
        
        # 実際のGmailデータ
        {
            "subject": "【デビットカード】ご利用のお知らせ(住信SBIネット銀行)", 
            "body": "[氏名] さま デビットカードのご利用がありました。承認番号：769534 利用日時：2025/07/16 07:47:38 利用加盟店：OPENAI *CHATGPT SUBSCR 引落通貨：JPY 引落金額：3,360.00", 
            "label": "支払い関係"
        },
        {
            "subject": "ご利用確定のお知らせ", 
            "body": "ペイディのご利用が確定しました。ご利用の確定 2025年7月13日 2,650円 DONQUIJOTE YAME お支払いまでの流れ すぐ払いを利用して、コンビニで当月中に支払うこともできます。", 
            "label": "支払い関係"
        },
        {
            "subject": "PayPay利用完了のお知らせ",
            "body": "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン 利用日時：2025年7月15日",
            "label": "支払い関係"
        },
        
        # 他カテゴリのバランス用データ
        {"subject": "Amazon タイムセール 期間限定", "body": "Amazonタイムセールが開催中です。お得な商品をチェックしてください。", "label": "プロモーション"},
        {"subject": "楽天市場 お買い物マラソン ポイント最大", "body": "楽天お買い物マラソンでポイント最大44倍！今すぐチェック！", "label": "プロモーション"},
        {"subject": "Udemy ビッグセール 90%オフ", "body": "Udemy年末ビッグセールで最大90%オフ！限定コースをお見逃しなく。", "label": "プロモーション"},
        {"subject": "メルカリ クーポン配布", "body": "メルカリで使えるクーポンをプレゼント！お得にお買い物しましょう。", "label": "プロモーション"},
        {"subject": "Yahoo!ショッピング 5のつく日", "body": "Yahoo!ショッピング5のつく日でポイント5倍！特別セール開催中。", "label": "プロモーション"},
        
        {"subject": "緊急 システム障害 サーバーエラー", "body": "システムに緊急事態が発生しました。復旧作業を開始しています。", "label": "重要"},
        {"subject": "セキュリティアラート 不正アクセス", "body": "不正アクセスの可能性があります。直ちにパスワードを変更してください。", "label": "重要"},
        {"subject": "パスワード変更 セキュリティ向上", "body": "セキュリティ向上のためパスワード変更をお願いします。", "label": "重要"},
        {"subject": "システムメンテナンス緊急", "body": "緊急システムメンテナンスを実施します。サービス停止にご注意ください。", "label": "重要"},
        {"subject": "バックアップ失敗通知", "body": "自動バックアップが失敗しました。手動バックアップを実行してください。", "label": "重要"},
        
        {"subject": "Indeed 新着求人 エンジニア職", "body": "あなたに合うエンジニア求人が見つかりました。応募をご検討ください。", "label": "仕事・学習"},
        {"subject": "GitHub アクティビティサマリー コミット", "body": "今週のGitHubアクティビティサマリーです。コミット数：15件", "label": "仕事・学習"},
        {"subject": "Udemy 学習進捗 Python入門コース", "body": "Python入門コースの学習進捗レポートです。進捗率：75%", "label": "仕事・学習"},
        {"subject": "LinkedIn 新しいつながり", "body": "LinkedInで新しいプロフェッショナルとつながりました。", "label": "仕事・学習"},
        {"subject": "Stack Overflow 週間サマリー", "body": "Stack Overflowの週間人気質問をお届けします。", "label": "仕事・学習"}
    ]
    
    return pd.DataFrame(training_data)

def create_pipeline_model() -> Tuple[object, Dict]:
    """
    Pipeline化されたモデルの作成
    vectorizer + model を単一パイプラインに統合
    """
    print("=== Pipeline化統合モデル学習開始 ===\n")
    
    # データセット作成
    df = create_training_data()
    print(f"総学習データ数: {len(df)}")
    print(f"分類クラス分布:\n{df['label'].value_counts()}\n")
    
    # 特徴量エンジニアリング適用
    print("PayPay特化特徴量エンジニアリングを適用中...")
    df['enhanced_text'] = df.apply(lambda row: create_paypay_specialized_features(f"{row['subject']} {row['body']}"), axis=1)
    
    # 学習データ準備
    X = df['enhanced_text']
    y = df['label']
    
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # TfidfVectorizer設定
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.90,
        sublinear_tf=True,
        stop_words=None,
        token_pattern=r'(?u)\b\w+\b|[A-Z_]+\d*',
        lowercase=False
    )
    
    # LinearSVC設定
    base_svm = LinearSVC(
        C=2.0,
        class_weight={
            '支払い関係': 1.5,
            '重要': 0.8,
            'プロモーション': 1.0,
            '仕事・学習': 1.0
        },
        random_state=42,
        max_iter=3000,
        dual=False,
        loss='squared_hinge'
    )
    
    # 確率キャリブレーション適用
    print("CalibratedClassifierCVで確率化を適用中...")
    calibrated_model = CalibratedClassifierCV(base_svm, cv=3)
    
    # Pipelineの作成
    print("vectorizer + model をPipeline化中...")
    pipeline = make_pipeline(vectorizer, calibrated_model)
    
    # 学習実行
    print("Pipeline学習を実行中...")
    pipeline.fit(X_train, y_train)
    
    # 評価
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n学習完了！")
    print(f"精度: {accuracy:.3f}")
    print(f"\n分類レポート:")
    print(classification_report(y_test, y_pred))
    
    # 確率化テスト
    print(f"\n=== 確率化テスト（予測確率が0-1範囲内） ===")
    for i, (pred, proba) in enumerate(zip(y_pred[:3], y_proba[:3])):
        max_prob = max(proba)
        print(f"テスト{i+1}: {pred} (確率: {max_prob:.3f})")
    
    # メタデータ
    metadata = {
        'version': 'v1.0.0',
        'total_samples': len(df),
        'accuracy': accuracy,
        'classes': list(pipeline.classes_),
        'feature_engineering': 'PayPay特化統合版'
    }
    
    return pipeline, metadata

def save_pipeline_model(pipeline, metadata, model_path="models/paypay_specialized_v1.pkl"):
    """Pipeline化されたモデルの保存"""
    # joblib形式で保存（Pipeline対応）
    joblib.dump({
        'pipeline': pipeline,
        'metadata': metadata
    }, model_path)
    
    print(f"\nPipeline化モデルを保存しました: {model_path}")
    print(f"ファイルサイズ: {os.path.getsize(model_path) / 1024 / 1024:.2f} MB")
    
    return model_path

def load_pipeline_model(model_path="models/paypay_specialized_v1.pkl"):
    """Pipeline化されたモデルの読み込み"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
    
    loaded_data = joblib.load(model_path)
    pipeline = loaded_data['pipeline']
    metadata = loaded_data['metadata']
    
    print(f"Pipeline化モデルを読み込みました: {model_path}")
    print(f"バージョン: {metadata['version']}")
    print(f"学習データ数: {metadata['total_samples']}")
    print(f"精度: {metadata['accuracy']:.3f}")
    
    return pipeline, metadata

def test_pipeline_model(pipeline):
    """Pipeline化されたモデルのテスト"""
    print("\n=== Pipeline化モデルテスト ===")
    
    test_cases = [
        ("PayPay残高チャージ完了", "PayPay残高への料金引き落としが完了しました。"),
        ("PayPay利用完了のお知らせ", "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン"),
        ("Amazon タイムセール", "Amazonタイムセールが開催中です。"),
        ("緊急システム障害", "システムに緊急事態が発生しました。"),
        ("Indeed 新着求人", "あなたに合うエンジニア求人が見つかりました。")
    ]
    
    for i, (subject, body) in enumerate(test_cases, 1):
        # 特徴量エンジニアリング適用
        text = f"{subject} {body}"
        enhanced_text = create_paypay_specialized_features(text)
        
        # Pipeline予測（特徴量エンジニアリング済みテキストを入力）
        prediction = pipeline.predict([enhanced_text])[0]
        probabilities = pipeline.predict_proba([enhanced_text])[0]
        max_prob = max(probabilities)
        
        print(f"テスト{i}: {prediction} (確率: {max_prob:.3f})")
        print(f"  入力: {subject} - {body[:30]}...")
        print()

if __name__ == "__main__":
    # Pipeline化モデル学習・保存
    pipeline, metadata = create_pipeline_model()
    model_path = save_pipeline_model(pipeline, metadata)
    
    # Pipeline化モデルテスト
    test_pipeline_model(pipeline)
    
    print("\n=== 統合ソリューション完了 ===")
    print("✅ vectorizer + model をPipeline化")
    print("✅ 特徴量関数を単一モジュールに集約")
    print("✅ CalibratedClassifierCVで確率化")
    print("✅ joblib形式で統合保存")
    print(f"✅ 保存パス: {model_path}")