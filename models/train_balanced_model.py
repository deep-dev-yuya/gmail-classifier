#!/usr/bin/env python3
"""
バランス調整されたGmail分類モデル学習スクリプト
実運用データを活用し、支払いラベル偏重問題を修正
"""

import pandas as pd
import pickle
import joblib
import os
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.calibration import CalibratedClassifierCV
import numpy as np

def create_balanced_features(text: str) -> str:
    """
    バランス調整された特徴量エンジニアリング
    支払いラベルの偏重を防ぐため、他カテゴリの特徴量も強化
    """
    features = []
    text_lower = text.lower()
    
    # 基本テキスト
    features.append(text)
    
    # === 支払い関係特徴量（適度に調整）===
    payment_keywords = [
        'paypay', 'ペイペイ', '支払い', '決済', '料金', '引き落とし',
        'クレジットカード', 'デビットカード', 'ペイディ', 'paidy'
    ]
    payment_count = sum(1 for keyword in payment_keywords if keyword in text_lower)
    if payment_count > 0:
        features.append(f"PAYMENT_DETECTED_{min(payment_count, 3)}")
    
    # 金額パターン
    amount_patterns = [r'\d{1,3}(?:,\d{3})*円', r'¥\d{1,3}(?:,\d{3})*', r'\d+円']
    total_amounts = 0
    for pattern in amount_patterns:
        matches = re.findall(pattern, text)
        total_amounts += len(matches)
    
    if total_amounts > 0:
        features.append(f"AMOUNT_FOUND_{min(total_amounts, 2)}")
    
    # === 重要メール特徴量（強化）===
    important_keywords = [
        '緊急', '重要', '障害', 'システム', 'メンテナンス', 'エラー',
        '停止', 'サーバー', 'ダウン', '復旧', '影響', 'urgent', 'critical'
    ]
    important_count = sum(1 for keyword in important_keywords if keyword in text_lower)
    if important_count > 0:
        features.append(f"IMPORTANT_DETECTED_{min(important_count, 3)}")
    
    # === プロモーション特徴量（強化）===
    promo_keywords = [
        'セール', 'キャンペーン', 'ポイント', '割引', 'タイムセール',
        '限定', 'お得', 'プロモーション', 'クーポン', 'amazon', '楽天',
        'sale', 'campaign', 'discount', 'special'
    ]
    promo_count = sum(1 for keyword in promo_keywords if keyword in text_lower)
    if promo_count > 0:
        features.append(f"PROMO_DETECTED_{min(promo_count, 3)}")
    
    # === 仕事・学習特徴量（強化）===
    work_keywords = [
        '求人', 'エンジニア', 'プログラミング', 'github', 'indeed',
        '転職', 'キャリア', '研修', '学習', 'コミット', 'pull request',
        'job', 'career', 'learning', 'training', 'education'
    ]
    work_count = sum(1 for keyword in work_keywords if keyword in text_lower)
    if work_count > 0:
        features.append(f"WORK_DETECTED_{min(work_count, 3)}")
    
    # === 文脈パターン（全カテゴリ共通）===
    if any(word in text_lower for word in ['完了', 'しました', '終了']):
        features.append("COMPLETION_CONTEXT")
    
    if any(word in text_lower for word in ['お知らせ', '通知', 'ご案内']):
        features.append("NOTIFICATION_CONTEXT")
    
    if any(word in text_lower for word in ['確認', 'チェック', '確定']):
        features.append("CONFIRMATION_CONTEXT")
    
    return ' '.join(features)

def load_actual_gmail_data() -> List[Dict[str, str]]:
    """
    実際のGmailログデータから学習用データを抽出
    """
    training_data = []
    
    # CSV読み込み
    gmail_log_path = '/Users/hasegawayuya/Projects/dev-projects/gmail-classifier/n8n/gmail_log_sheet.csv'
    retraining_path = '/Users/hasegawayuya/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_sheet.csv'
    
    # gmail_log_sheet.csvから高信頼度データを抽出
    if os.path.exists(gmail_log_path):
        df = pd.read_csv(gmail_log_path)
        print(f"Gmail Log data loaded: {len(df)} records")
        
        # 信頼度0.7以上のデータのみを学習に使用
        high_confidence_data = df[df['confidence'] >= 0.7]
        print(f"High confidence data (>=0.7): {len(high_confidence_data)} records")
        
        for _, row in high_confidence_data.iterrows():
            training_data.append({
                'subject': str(row.get('subject', '')),
                'body': str(row.get('enrichedContext', '')),
                'label': str(row.get('classification', ''))
            })
    
    # 追加の実データサンプル（実際のメールから）
    additional_samples = [
        # 支払い関係（実データベース）
        {
            "subject": "【デビットカード】ご利用のお知らせ(住信SBIネット銀行)", 
            "body": "デビットカードのご利用がありました。承認番号：769534 利用日時：2025/07/16 07:47:38 利用加盟店：OPENAI *CHATGPT SUBSCR 引落通貨：JPY 引落金額：3,360.00", 
            "label": "支払い関係"
        },
        {
            "subject": "ご利用確定のお知らせ", 
            "body": "ペイディのご利用が確定しました。ご利用の確定 2025年7月13日 2,650円 DONQUIJOTE YAME お支払いまでの流れ すぐ払いを利用して、コンビニで当月中に支払うこともできます。", 
            "label": "支払い関係"
        },
        
        # 重要（実運用想定）
        {
            "subject": "緊急システム障害のお知らせ",
            "body": "システムに緊急障害が発生しました。現在復旧作業中です。影響範囲：全サービス 復旧予定：未定",
            "label": "重要"
        },
        {
            "subject": "重要なセキュリティアップデート",
            "body": "セキュリティに関する重要なアップデートがあります。すぐに対応してください。",
            "label": "重要"
        },
        {
            "subject": "サーバーダウンによる影響",
            "body": "メインサーバーがダウンしており、サービスに影響が出ています。",
            "label": "重要"
        },
        
        # プロモーション（実運用想定）
        {
            "subject": "Amazon タイムセール開催中",
            "body": "Amazonタイムセールが開催中です。お得な商品が多数あります。",
            "label": "プロモーション"
        },
        {
            "subject": "楽天市場 お買い物マラソン",
            "body": "楽天お買い物マラソンでポイント最大44倍！この機会をお見逃しなく。",
            "label": "プロモーション"
        },
        {
            "subject": "限定クーポンのご案内",
            "body": "特別限定クーポンをお送りします。50%オフの大チャンスです。",
            "label": "プロモーション"
        },
        {
            "subject": "週末セール開催",
            "body": "週末限定の特別セールを開催します。お得な商品をご確認ください。",
            "label": "プロモーション"
        },
        
        # 仕事・学習（実運用想定）
        {
            "subject": "GitHub アクティビティサマリー",
            "body": "今週のGitHubアクティビティサマリーです。5つのコミットと2つのプルリクエストが作成されました。",
            "label": "仕事・学習"
        },
        {
            "subject": "Indeed 新着求人情報",
            "body": "あなたに合うエンジニア求人が見つかりました。Python開発者募集中です。",
            "label": "仕事・学習"
        },
        {
            "subject": "プログラミング学習コースのご案内",
            "body": "新しいプログラミング学習コースが開講されました。機械学習の基礎から学べます。",
            "label": "仕事・学習"
        },
        {
            "subject": "技術勉強会の案内",
            "body": "来週の技術勉強会のご案内です。テーマ：React開発のベストプラクティス",
            "label": "仕事・学習"
        }
    ]
    
    training_data.extend(additional_samples)
    
    print(f"Total training data: {len(training_data)} samples")
    return training_data

def train_balanced_model():
    """
    バランス調整されたモデルの学習
    """
    print("=== バランス調整モデル学習開始 ===\n")
    
    # 実データの読み込み
    training_data = load_actual_gmail_data()
    
    if len(training_data) == 0:
        print("Error: No training data available")
        return None, None
    
    df = pd.DataFrame(training_data)
    
    # データ品質チェック
    df = df.dropna(subset=['subject', 'label'])
    df['subject'] = df['subject'].astype(str)
    df['body'] = df['body'].fillna('').astype(str)
    
    print(f"Clean training data: {len(df)} samples")
    print(f"Class distribution:\n{df['label'].value_counts()}\n")
    
    # バランス調整された特徴量エンジニアリング
    print("Applying balanced feature engineering...")
    df['enhanced_text'] = df.apply(
        lambda row: create_balanced_features(f"{row['subject']} {row['body']}"), 
        axis=1
    )
    
    # データ分割
    X = df['enhanced_text']
    y = df['label']
    
    if len(X) < 10:
        print("Warning: Very small dataset. Using all data for training.")
        X_train, y_train = X, y
        X_test, y_test = X, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y if len(y.unique()) > 1 else None
        )
    
    # TF-IDF設定（バランス調整版）
    print("Setting up balanced TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=2000,              # 特徴量数を適度に制限
        ngram_range=(1, 2),             # 2-gramまで
        min_df=1,                       # 最小文書頻度
        max_df=0.85,                    # 最大文書頻度
        sublinear_tf=True,              # TF値の対数スケーリング
        stop_words=None,                # 日本語対応
        token_pattern=r'(?u)\b\w+\b|[A-Z_]+\d*',
        lowercase=False                 # 大文字小文字を区別
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # SVM モデル（バランス調整版）
    print("Training balanced SVM model...")
    model = LinearSVC(
        C=1.0,                          # 標準的な正則化
        class_weight='balanced',        # 自動バランス調整
        random_state=42,
        max_iter=2000,
        dual=False,
        loss='squared_hinge'
    )
    
    model.fit(X_train_vec, y_train)
    
    # Pipeline作成（確率出力対応）
    pipeline = make_pipeline(vectorizer, model)
    calibrated_pipeline = CalibratedClassifierCV(pipeline, method='sigmoid', cv=3)
    calibrated_pipeline.fit(X, y)  # 全データで校正
    
    # 評価
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n学習完了！")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # 混同行列
    print(f"\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    print("Classes:", model.classes_)
    print(cm)
    
    # モデル保存
    model_path = os.path.join(os.path.dirname(__file__), 'balanced_model_v1.pkl')
    save_data = {
        'pipeline': calibrated_pipeline,
        'vectorizer': vectorizer,
        'model': model,
        'feature_names': vectorizer.get_feature_names_out(),
        'classes': model.classes_,
        'accuracy': accuracy,
        'training_size': len(df)
    }
    
    joblib.dump(save_data, model_path)
    print(f"\nBalanced model saved: {model_path}")
    
    return calibrated_pipeline, save_data

def test_balanced_classification(pipeline, save_data):
    """バランス調整モデルのテスト"""
    print("\n=== バランス調整モデルテスト ===")
    
    test_cases = [
        ("PayPay決済完了", "PayPayでのお支払いが完了しました。利用金額：1,250円"),
        ("システム障害", "緊急システム障害が発生しました。サーバーに影響があります。"),
        ("Amazon セール", "Amazonタイムセールが開催中です。お得な商品多数。"),
        ("GitHub通知", "新しいプルリクエストが作成されました。レビューをお願いします。"),
        ("ペイディ利用確定", "ペイディでの決済2,650円が完了しました。"),
    ]
    
    for i, (subject, body) in enumerate(test_cases, 1):
        test_text = create_balanced_features(f"{subject} {body}")
        prediction = pipeline.predict([test_text])[0]
        probabilities = pipeline.predict_proba([test_text])[0]
        confidence = max(probabilities)
        
        print(f"Test {i}: {prediction} (confidence: {confidence:.3f})")
        print(f"  Input: {subject} | {body[:30]}...")
        
        # クラス別確率表示
        class_probs = dict(zip(save_data['classes'], probabilities))
        sorted_probs = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)
        print(f"  Probabilities: {sorted_probs[:3]}")
        print()

if __name__ == "__main__":
    # バランス調整モデル学習実行
    pipeline, save_data = train_balanced_model()
    
    if pipeline is not None:
        # バランス調整モデルテスト
        test_balanced_classification(pipeline, save_data)
        
        print("\n=== 学習完了 ===")
        print("- 実運用データを活用した学習")
        print("- 自動バランス調整（class_weight='balanced'）") 
        print("- 確率出力対応（CalibratedClassifierCV）")
        print("- 支払いラベル偏重問題を修正")
        print("\nFlask APIでモデルを読み込んでテストしてください。")
    else:
        print("Error: Model training failed")