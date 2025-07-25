#!/usr/bin/env python3
"""
正解ラベル付きデータの分析と改良モデル学習スクリプト
retraining_candidates_sheet.csvのG列（groundTruth）を活用した教師あり学習
"""

import pandas as pd
import pickle
import joblib
import os
import re
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.calibration import CalibratedClassifierCV
import numpy as np
from collections import Counter

def load_groundtruth_data():
    """
    正解ラベル付きデータの読み込みと分析
    """
    print("=== 正解ラベル付きデータ分析開始 ===\n")
    
    csv_path = '/Users/hasegawayuya/Projects/dev-projects/gmail-classifier/n8n/retraining_candidates_sheet.csv - retraining_candidates_sheet.csv'
    
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return None
    
    # CSVファイル読み込み
    df = pd.read_csv(csv_path)
    print(f"Total records loaded: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # 正解ラベルが存在するデータのみ抽出
    df_labeled = df[df['groundTruth'].notna() & (df['groundTruth'] != '')]
    print(f"Records with ground truth labels: {len(df_labeled)}")
    
    if len(df_labeled) == 0:
        print("Warning: No ground truth data found")
        return None
    
    return df_labeled

def analyze_prediction_errors(df_labeled):
    """
    予測と正解の誤差パターン分析
    """
    print("\n=== 予測精度分析 ===")
    
    # 予測と正解の比較
    correct_predictions = 0
    misclassifications = []
    
    for _, row in df_labeled.iterrows():
        predicted = str(row.get('predictedClass', '')).strip()
        ground_truth = str(row.get('groundTruth', '')).strip()
        subject = str(row.get('subject', '')).strip()
        confidence = float(row.get('confidence', 0))
        
        if predicted == ground_truth:
            correct_predictions += 1
        else:
            misclassifications.append({
                'subject': subject,
                'predicted': predicted,
                'ground_truth': ground_truth,
                'confidence': confidence
            })
    
    accuracy = correct_predictions / len(df_labeled) if len(df_labeled) > 0 else 0
    print(f"Current model accuracy: {accuracy:.3f} ({correct_predictions}/{len(df_labeled)})")
    
    # 誤分類パターン分析
    print(f"\n=== 誤分類パターン分析 ({len(misclassifications)} cases) ===")
    
    pattern_counter = Counter()
    for error in misclassifications:
        pattern = f"{error['predicted']} → {error['ground_truth']}"
        pattern_counter[pattern] += 1
        
        print(f"❌ '{error['subject'][:50]}...'")
        print(f"   予測: {error['predicted']} (信頼度: {error['confidence']:.3f})")
        print(f"   正解: {error['ground_truth']}")
        print()
    
    print("誤分類パターン頻度:")
    for pattern, count in pattern_counter.most_common():
        print(f"  {pattern}: {count}回")
    
    return misclassifications

def create_supervised_features(text: str) -> str:
    """
    正解データに基づく改良された特徴量エンジニアリング
    """
    features = []
    text_lower = text.lower()
    
    # 基本テキスト
    features.append(text)
    
    # === 支払い関係の強化パターン ===
    payment_indicators = {
        'card_specific': ['デビットカード', 'クレジットカード', 'ご利用のお知らせ'],
        'payment_services': ['paypay', 'ペイペイ', 'ペイディ', 'paidy'],  
        'bank_related': ['銀行', '振込', '引き落とし', '口座振替'],
        'transaction_words': ['決済', '支払い', '料金', '請求', '利用金額']
    }
    
    for category, keywords in payment_indicators.items():
        count = sum(1 for keyword in keywords if keyword in text_lower)
        if count > 0:
            features.append(f"PAYMENT_{category.upper()}_{count}")
    
    # === 仕事・学習の判定強化 ===
    work_study_indicators = {
        'job_related': ['求人', '募集', '転職', 'エンジニア', '採用'],
        'tech_keywords': ['github', 'python', 'javascript', 'プログラミング'],
        'learning_words': ['学習', '研修', '勉強会', '講座', 'コース'],
        'work_context': ['案件', 'プロジェクト', '業務', '仕事', '職種']
    }
    
    for category, keywords in work_study_indicators.items():
        count = sum(1 for keyword in keywords if keyword in text_lower)
        if count > 0:
            features.append(f"WORK_{category.upper()}_{count}")
    
    # === 重要メールの判定強化 ===
    important_indicators = {
        'urgency': ['重要', '緊急', '至急', 'important', 'urgent'],
        'system_issues': ['システム', '障害', 'エラー', 'メンテナンス'],
        'security': ['セキュリティ', 'パスワード', 'ログイン', 'アラート'],
        'notifications': ['お知らせ', '通知', 'ご案内', '連絡']
    }
    
    for category, keywords in important_indicators.items():
        count = sum(1 for keyword in keywords if keyword in text_lower)
        if count > 0:
            features.append(f"IMPORTANT_{category.upper()}_{count}")
    
    # === プロモーションの判定強化 ===
    promo_indicators = {
        'sales_events': ['セール', 'タイムセール', '特価', '割引'],
        'campaigns': ['キャンペーン', 'ポイント', 'マラソン'],
        'retailers': ['amazon', '楽天', 'アマゾン'],
        'offers': ['お得', '限定', '特別', 'off', '％']
    }
    
    for category, keywords in promo_indicators.items():
        count = sum(1 for keyword in keywords if keyword in text_lower)
        if count > 0:
            features.append(f"PROMO_{category.upper()}_{count}")
    
    # === 文脈的特徴量 ===
    # Forwarded emailの検出
    if 'fwd:' in text_lower or 'フォワード' in text_lower:
        features.append("FORWARDED_EMAIL")
    
    # 金額パターンの検出
    amount_patterns = [
        r'\d{1,3}(?:,\d{3})*円',
        r'¥\d+',
        r'\d+円'
    ]
    
    total_amounts = 0
    for pattern in amount_patterns:
        matches = re.findall(pattern, text)
        total_amounts += len(matches)
    
    if total_amounts > 0:
        features.append(f"AMOUNT_DETECTED_{min(total_amounts, 3)}")
    
    return ' '.join(features)

def train_supervised_model(df_labeled):
    """
    正解ラベル付きデータで教師あり学習を実行
    """
    print("\n=== 教師あり学習モデル訓練開始 ===")
    
    # データ前処理
    training_data = []
    
    for _, row in df_labeled.iterrows():
        subject = str(row.get('subject', '')).strip()
        ground_truth = str(row.get('groundTruth', '')).strip()
        
        if subject and ground_truth:
            training_data.append({
                'text': subject,
                'label': ground_truth
            })
    
    if len(training_data) == 0:
        print("Error: No valid training data")
        return None, None
    
    df_train = pd.DataFrame(training_data)
    print(f"Training samples: {len(df_train)}")
    print(f"Class distribution:")
    print(df_train['label'].value_counts())
    print()
    
    # 改良された特徴量エンジニアリング適用
    print("Applying supervised feature engineering...")
    df_train['enhanced_text'] = df_train['text'].apply(create_supervised_features)
    
    # データ分割
    X = df_train['enhanced_text']
    y = df_train['label']
    
    # 小規模データセットの場合の処理
    if len(X) < 10:
        print("Small dataset: Using all data for training")
        X_train, X_test = X, X
        y_train, y_test = y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    
    # TF-IDF Vectorizer設定
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 3),  # 3-gramまで拡張
        min_df=1,
        max_df=0.85,
        sublinear_tf=True,
        token_pattern=r'(?u)\b\w+\b|[A-Z_]+\d*',
        lowercase=False
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # LinearSVC with balanced class weights
    model = LinearSVC(
        C=2.0,  # より強い正則化
        class_weight='balanced',
        random_state=42,
        max_iter=5000,
        dual=False,
        loss='squared_hinge'
    )
    
    model.fit(X_train_vec, y_train)
    
    # Pipeline作成
    pipeline = make_pipeline(vectorizer, model)
    
    # 確率校正（可能な場合）
    if len(X) >= 10 and min(y.value_counts()) >= 3:
        calibrated_pipeline = CalibratedClassifierCV(pipeline, method='sigmoid', cv=3)
        calibrated_pipeline.fit(X, y)
    else:
        print("Skipping calibration due to small dataset")
        calibrated_pipeline = pipeline
    
    # 評価
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n=== 学習結果 ===")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # 混同行列
    if len(set(y_test)) > 1:
        print(f"\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
        print("Classes:", model.classes_)
        print(cm)
    
    # モデル保存
    model_path = os.path.join(os.path.dirname(__file__), 'supervised_model_v1.pkl')
    save_data = {
        'pipeline': calibrated_pipeline,
        'vectorizer': vectorizer,
        'model': model,
        'feature_names': vectorizer.get_feature_names_out(),
        'classes': model.classes_,
        'accuracy': accuracy,
        'training_size': len(df_train),
        'ground_truth_based': True
    }
    
    joblib.dump(save_data, model_path)
    print(f"\nSupervised model saved: {model_path}")
    
    return calibrated_pipeline, save_data

def test_supervised_model(pipeline, save_data):
    """教師あり学習モデルのテスト"""
    print("\n=== 教師あり学習モデルテスト ===")
    
    test_cases = [
        "Fwd: 【デビットカード】ご利用のお知らせ(住信SBIネット銀行)",
        "Fwd: 検品・検査・調整(半導体・先端技術) @ 株式会社BREXA Next",
        "Fwd: 臨時システムメンテナンスのお知らせ",
        "Fwd: 【月々770円】からの医療保険＼SBI生命がお手頃な保険料を実現！／",
        "Fwd: 【満期日まであと3日】ﾙ-ｸｽの自動車保険のご継続手続きはお済みですか？",
        "Fwd: 【重要】『マネーフォワード ME』プレミアムサービス スタンダードコース 料金改定に関するお知らせ"
    ]
    
    for i, subject in enumerate(test_cases, 1):
        test_text = create_supervised_features(subject)
        prediction = pipeline.predict([test_text])[0]
        
        try:
            probabilities = pipeline.predict_proba([test_text])[0]
            confidence = max(probabilities)
            
            # Top 2 predictions
            class_probs = dict(zip(save_data['classes'], probabilities))
            sorted_probs = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)
            
        except AttributeError:
            # Fallback for LinearSVC
            decision_scores = pipeline.decision_function([test_text])[0]
            if hasattr(decision_scores, '__len__'):
                confidence = max(decision_scores)
                sorted_probs = [(prediction, confidence)]
            else:
                confidence = abs(decision_scores)
                sorted_probs = [(prediction, confidence)]
        
        print(f"Test {i}: {prediction} (信頼度: {confidence:.3f})")
        print(f"  Subject: {subject}")
        print(f"  Top predictions: {sorted_probs[:2]}")
        print()

if __name__ == "__main__":
    # データ読み込み
    df_labeled = load_groundtruth_data()
    
    if df_labeled is not None:
        # 誤分類パターン分析
        misclassifications = analyze_prediction_errors(df_labeled)
        
        # 教師あり学習実行
        pipeline, save_data = train_supervised_model(df_labeled)
        
        if pipeline is not None:
            # モデルテスト
            test_supervised_model(pipeline, save_data)
            
            print("\n=== 教師あり学習完了サマリー ===")
            print("✅ 正解ラベル付きデータで教師あり学習完了")
            print("✅ 誤分類パターンに基づく特徴量エンジニアリング改良")
            print("✅ バランス調整された分類モデル構築")
            print(f"✅ 学習データサイズ: {save_data['training_size']} samples")
            print(f"✅ モデル精度: {save_data['accuracy']:.3f}")
            print(f"\nModel saved: supervised_model_v1.pkl")
        else:
            print("Error: Supervised learning failed")
    else:
        print("Error: No ground truth data available")