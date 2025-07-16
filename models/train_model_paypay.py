#!/usr/bin/env python3
"""
PayPay特化Gmail分類モデル学習スクリプト
統合ガイド2の高度特徴量エンジニアリングを適用
"""

import pandas as pd
import pickle
import os
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def create_paypay_specialized_features(text: str) -> str:
    """
    PayPay分類問題に特化した拡張特徴量エンジニアリング（統合ガイド2版）
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
        features.append(f"PAYPAY_STRENGTH_{min(paypay_strength, 5)}")  # 上限5で正規化
    
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
        'comma_yen': r'\d{1,3}(?:,\d{3})*円',      # 1,000円
        'symbol_yen': r'¥\d{1,3}(?:,\d{3})*',      # ¥1,000
        'decimal': r'\d+\.\d{2}',                   # 3360.00
        'simple_yen': r'\d+円',                     # 1000円
        'range_amount': r'\d{3,6}円'                # 100-999999円
    }
    
    total_amounts = 0
    for pattern_name, pattern in amount_patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            total_amounts += len(matches)
            features.append(f"AMOUNT_{pattern_name.upper()}_{len(matches)}")
            
            # 金額レンジ分類
            for match in matches:
                # 数値のみ抽出
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
    # PayPay + 完了の組み合わせ
    if any(variant in text for variant in paypay_variants) and any(completion in text for completion in ['完了', 'しました']):
        features.append("PAYPAY_COMPLETION_COMBO")
    
    # PayPay + 金額の組み合わせ
    if any(variant in text for variant in paypay_variants) and total_amounts > 0:
        features.append("PAYPAY_AMOUNT_COMBO")
    
    return ' '.join(features)

def create_paypay_training_data() -> List[Dict[str, str]]:
    """
    PayPay分類精度向上のための追加学習データ（統合ガイド2版）
    """
    return [
        # PayPay基本決済パターン
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
        
        # PayPayチャージパターン
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
        
        # PayPayオンライン決済パターン
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
        
        # PayPay送金・受取パターン
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
        
        # 複合的なPayPayパターン
        {
            "subject": "PayPay利用明細（月次）",
            "body": "PayPay月次利用明細をお送りします。総利用額：45,680円 利用回数：23回 主な利用先：コンビニ、飲食店",
            "label": "支払い関係"
        }
    ]

def create_all_training_data() -> pd.DataFrame:
    """
    全学習データの統合作成
    """
    # 既存のGmail実データ
    gmail_data = [
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
        # 既存の基本PayPayデータ
        {
            "subject": "PayPay利用完了のお知らせ",
            "body": "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン 利用日時：2025年7月15日",
            "label": "支払い関係"
        },
        {"subject": "PayPay残高チャージ完了", "body": "PayPay残高に5,000円チャージされました。チャージ方法：銀行口座 手数料：無料", "label": "支払い関係"},
        
        # 他カテゴリのサンプルデータ
        {"subject": "Amazon タイムセール 期間限定", "body": "Amazonタイムセールが開催中です。", "label": "プロモーション"},
        {"subject": "楽天市場 お買い物マラソン ポイント最大", "body": "楽天お買い物マラソンでポイント最大44倍！", "label": "プロモーション"},
        {"subject": "緊急 システム障害 サーバーエラー", "body": "システムに緊急事態が発生しました。", "label": "重要"},
        {"subject": "システムメンテナンス緊急", "body": "緊急システムメンテナンスを実施します。", "label": "重要"},
        {"subject": "Indeed 新着求人 エンジニア職", "body": "あなたに合うエンジニア求人が見つかりました。", "label": "仕事・学習"},
        {"subject": "GitHub アクティビティサマリー コミット", "body": "今週のGitHubアクティビティサマリーです。", "label": "仕事・学習"},
    ]
    
    # PayPay特化データを追加
    paypay_data = create_paypay_training_data()
    
    # すべてのデータを統合
    all_data = gmail_data + paypay_data
    return pd.DataFrame(all_data)

def train_paypay_specialized_model():
    """
    PayPay特化拡張版モデルの学習（統合ガイド2版）
    """
    print("=== PayPay特化モデル学習開始（統合ガイド2版）===\n")
    
    # データセット作成
    df = create_all_training_data()
    print(f"総学習データ数: {len(df)}")
    print(f"分類クラス分布:\n{df['label'].value_counts()}\n")
    
    # PayPay特化特徴量エンジニアリング適用
    print("統合ガイド2のPayPay特化特徴量エンジニアリングを適用中...")
    df['enhanced_text'] = df.apply(lambda row: create_paypay_specialized_features(f"{row['subject']} {row['body']}"), axis=1)
    
    # 拡張テキストを使用
    X = df['enhanced_text']
    y = df['label']
    
    # データ分割
    if len(X) < 20:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    
    # PayPay特化TF-IDF ベクトル化設定
    print("PayPay特化TF-IDFパラメータを適用...")
    vectorizer = TfidfVectorizer(
        max_features=5000,              # 特徴量数をさらに増加
        ngram_range=(1, 3),             # 3-gramまで拡張
        min_df=1,                       # 最小文書頻度
        max_df=0.90,                    # 最大文書頻度を下げて稀少特徴量を保持
        sublinear_tf=True,              # TF値の対数スケーリング
        stop_words=None,                # 日本語対応のためストップワード無効
        token_pattern=r'(?u)\b\w+\b|[A-Z_]+\d*',  # 特徴量トークンも認識
        lowercase=False                 # 大文字小文字を区別（PayPay vs paypay）
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # PayPay特化SVM モデル学習設定
    print("PayPay特化SVMパラメータを適用...")
    model = LinearSVC(
        C=2.0,                          # より強い正則化
        class_weight={                  # 手動でクラス重み調整
            '支払い関係': 1.5,        # PayPay含む支払い関係を重視
            '重要': 0.8,
            'プロモーション': 1.0,
            '仕事・学習': 1.0
        },
        random_state=42,
        max_iter=3000,                  # 反復回数増加
        dual=False,                     # primal形式で高速化
        loss='squared_hinge'            # より滑らかな損失関数
    )
    model.fit(X_train_vec, y_train)
    
    # 評価
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n学習完了！")
    print(f"精度: {accuracy:.3f}")
    print(f"\n分類レポート:")
    print(classification_report(y_test, y_pred))
    
    # PayPay特徴量の重要度確認
    feature_names = vectorizer.get_feature_names_out()
    class_labels = model.classes_
    payment_idx = list(class_labels).index('支払い関係') if '支払い関係' in class_labels else 0
    feature_importance = model.coef_[payment_idx]
    
    # PayPay関連特徴量を探す
    paypay_features = [(name, importance) for name, importance in zip(feature_names, feature_importance) 
                       if 'paypay' in name.lower() or 'ペイ' in name or 'PAYPAY' in name]
    
    if paypay_features:
        print(f"\n=== PayPay特化特徴量の重要度（TOP 15） ===\n")
        for feature, importance in sorted(paypay_features, key=lambda x: x[1], reverse=True)[:15]:
            print(f"{feature}: {importance:.3f}")
    
    # モデル保存
    model_path = 'model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump((vectorizer, model), f)
    
    print(f"\nPayPay特化モデルを保存しました: {model_path}")
    print("\n=== PayPay特化モデル学習完了 ===")
    print("- 統合ガイド2の高度特徴量エンジニアリング適用済み")
    print("- PayPay検出強度・文脈・組み合わせ特徴量実装")
    print("- 5000特徴量 + 3-gram + 手動クラス重み調整")
    print("\nFlask APIを再起動してテストしてください。")
    
    return vectorizer, model

def test_paypay_classification(vectorizer, model):
    """PayPay分類の特別テスト"""
    print("\n=== PayPay特化分類テスト ===")
    
    test_cases = [
        "PayPay残高チャージ完了 PayPay残高への料金引き落としが完了しました。",
        "PayPay利用完了のお知らせ PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン",
        "ペイディ利用確定のお知らせ ペイディでの決済2,650円が完了しました。",
        "【デビットカード】ご利用のお知らせ OPENAI *CHATGPT SUBSCR 引落金額：3,360.00",
        "緊急システムメンテナンス 重要なシステム障害が発生しました。"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        enhanced_text = create_paypay_specialized_features(test_text)
        X_test = vectorizer.transform([enhanced_text])
        prediction = model.predict(X_test)[0]
        confidence = model.decision_function(X_test)[0]
        
        print(f"テスト{i}: {prediction} (信頼度: {max(confidence):.3f})")
        print(f"  入力: {test_text[:50]}...")
        print()

if __name__ == "__main__":
    # PayPay特化モデル学習実行
    vectorizer, model = train_paypay_specialized_model()
    
    # PayPay分類テスト
    test_paypay_classification(vectorizer, model)