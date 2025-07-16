#!/usr/bin/env python3
"""
Gmail分類モデル学習スクリプト
CSVデータから機械学習モデルを作成
"""

import pandas as pd
import pickle
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def load_training_data(csv_path="../data/train_data.csv"):
    """学習データの読み込み"""
    if not os.path.exists(csv_path):
        print(f"学習データが見つかりません: {csv_path}")
        print("サンプルデータを作成します...")
        return create_sample_data()
    
    df = pd.read_csv(csv_path)
    return df

def create_sample_data():
    """サンプル学習データの作成"""
    sample_data = [
        {
            "subject": "支払い期限のお知らせ",
            "body": "〇〇サービスの料金が〇月〇日に引き落とされます。期限までにお支払いください。",
            "label": "支払い関係"
        },
        {
            "subject": "会議のご案内",
            "body": "以下の日程で会議を予定しています。ご参加をお願いいたします。",
            "label": "通知"
        },
        {
            "subject": "システムメンテナンスのお知らせ",
            "body": "重要なシステムメンテナンスを実施いたします。サービス停止にご注意ください。",
            "label": "重要"
        },
        {
            "subject": "クレジットカード請求書",
            "body": "今月のクレジットカード利用明細をお送りします。確認をお願いします。",
            "label": "支払い関係"
        },
        {
            "subject": "プロジェクト進捗報告",
            "body": "プロジェクトの進捗状況について報告いたします。",
            "label": "通知"
        },
        {
            "subject": "緊急：システム障害発生",
            "body": "システムに障害が発生しました。復旧まで今しばらくお待ちください。",
            "label": "重要"
        },
        {
            "subject": "月次ミーティングの件",
            "body": "来月の定例ミーティングの日程調整をお願いします。",
            "label": "通知"
        },
        {
            "subject": "振込手数料のご案内",
            "body": "振込手数料の改定についてお知らせいたします。",
            "label": "支払い関係"
        }
    ]
    
    return pd.DataFrame(sample_data)

def create_enhanced_features(text):
    """拡張特徴量エンジニアリング"""
    features = []
    
    # 基本テキスト
    features.append(text)
    
    # PayPay関連特徴量（重要！）
    paypay_keywords = ['PayPay', 'paypay', 'ペイペイ', 'ペイ']
    paypay_score = sum(1 for keyword in paypay_keywords if keyword in text)
    if paypay_score > 0:
        features.append(f"PAYPAY_DETECTED_{paypay_score}")
    
    # 決済サービス特徴量
    payment_services = ['ペイディ', 'Paidy', 'LINE Pay', 'Apple Pay', 'Google Pay']
    for service in payment_services:
        if service in text:
            features.append(f"PAYMENT_SERVICE_{service.replace(' ', '_')}")
    
    # 金額パターン特徴量
    amount_patterns = [
        r'\d{1,3}(?:,\d{3})*円',  # 1,000円形式
        r'¥\d{1,3}(?:,\d{3})*',   # ¥1,000形式
        r'\d+\.\d{2}',            # 3360.00形式
        r'\d+円'                  # 1000円形式
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, text)
        if matches:
            features.append(f"AMOUNT_PATTERN_{len(matches)}")
    
    # カード系特徴量
    card_keywords = ['デビットカード', 'クレジットカード', 'カード', 'VISA', 'MasterCard', 'JCB']
    for keyword in card_keywords:
        if keyword in text:
            features.append(f"CARD_{keyword}")
    
    # 引き落とし・振替特徴量
    payment_actions = ['引き落とし', '引落', '振替', '振込', '決済', '支払い', 'チャージ']
    for action in payment_actions:
        if action in text:
            features.append(f"PAYMENT_ACTION_{action}")
    
    return ' '.join(features)

def create_extended_training_data():
    """拡張版学習データの作成（Gmail実データ含む）"""
    extended_data = [
        # 実際のGmail分析結果を追加（支払い関係強化）
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
        # PayPay関連を重点的に追加
        {
            "subject": "PayPay利用完了のお知らせ",
            "body": "PayPayでのお支払いが完了しました。利用金額：1,250円 利用店舗：セブンイレブン 利用日時：2025年7月15日",
            "label": "支払い関係"
        },
        {"subject": "PayPay残高チャージ完了", "body": "PayPay残高に5,000円チャージされました。チャージ方法：銀行口座 手数料：無料", "label": "支払い関係"},
        {"subject": "【VISAデビット】ご利用のお知らせ", "body": "VISAデビットカードのご利用がありました。利用金額：2,480円 利用店舗：Amazon.co.jp 利用日：2025/7/14", "label": "支払い関係"},
        {"subject": "Paidy決済完了のお知らせ", "body": "Paidyでの決済が完了しました。決済金額：3,980円 加盟店：楽天市場 翌月27日にお支払いください。", "label": "支払い関係"},
        {"subject": "【重要】クレジットカード請求額確定", "body": "今月のクレジットカード請求額が確定しました。請求額：45,680円 引き落とし日：2025年8月10日", "label": "支払い関係"},
        {"subject": "Suicaチャージ完了のお知らせ", "body": "Suicaに3,000円チャージされました。チャージ方法：オートチャージ 残高：5,420円", "label": "支払い関係"},
        {"subject": "Apple Music月額料金のお知らせ", "body": "Apple Music個人プラン月額980円の決済が完了しました。次回請求日：2025年8月16日", "label": "支払い関係"},
        {"subject": "Spotify Premium料金請求", "body": "Spotify Premium月額980円が請求されました。お支払い方法：クレジットカード", "label": "支払い関係"},
        {"subject": "電気料金請求書発行のお知らせ", "body": "7月分電気料金8,450円の請求書を発行しました。支払い期限：8月31日 口座振替日：8月27日", "label": "支払い関係"},
        {"subject": "ガス料金お支払いのお知らせ", "body": "7月分都市ガス料金4,320円のお支払いが確定しました。引き落とし日：8月25日", "label": "支払い関係"},
        {"subject": "携帯電話料金確定のお知らせ", "body": "7月分携帯電話料金6,580円が確定しました。データ使用量：15GB 通話料：480円", "label": "支払い関係"},
        {"subject": "Amazon購入確定のお知らせ", "body": "Amazon.co.jpでの購入が確定しました。商品代金：2,150円 配送料：無料 お支払い方法：クレジットカード", "label": "支払い関係"},
        {"subject": "楽天市場ご注文確定のお知らせ", "body": "楽天市場でのご注文が確定しました。注文金額：4,780円 獲得予定ポイント：47ポイント", "label": "支払い関係"},
        {"subject": "自動車保険料引き落としのお知らせ", "body": "自動車保険料月額5,240円が口座から引き落とされました。引き落とし日：2025年7月15日", "label": "支払い関係"},
        {"subject": "振込手数料のお知らせ", "body": "銀行振込手数料330円が発生しました。振込先：○○銀行 振込金額：50,000円", "label": "支払い関係"},
        {"subject": "分割払い引き落としのお知らせ", "body": "分割払い第3回目として8,500円が引き落とされました。残り回数：9回 次回引き落とし日：8月15日", "label": "支払い関係"},
        {"subject": "住宅ローン引き落とし完了", "body": "住宅ローン7月分85,000円の引き落としが完了しました。元金：62,000円 利息：23,000円", "label": "支払い関係"},
        {"subject": "LINE Pay決済完了のお知らせ", "body": "LINE Payでの決済が完了しました。決済金額：1,680円 利用店舗：ファミリーマート ポイント獲得：16ポイント", "label": "支払い関係"},
        
        # 既存の他のカテゴリデータも保持
        
        # プロモーション (10件)
        {"subject": "Amazon タイムセール 期間限定", "body": "Amazonタイムセールが開催中です。", "label": "プロモーション"},
        {"subject": "楽天市場 お買い物マラソン ポイント最大", "body": "楽天お買い物マラソンでポイント最大44倍！", "label": "プロモーション"},
        {"subject": "Udemy ビッグセール 90%オフ", "body": "Udemy年末ビッグセールで最大90%オフ！", "label": "プロモーション"},
        {"subject": "セブンマイルプログラム 新着特典", "body": "セブンイレブンの新しい特典のご案内です。", "label": "プロモーション"},
        {"subject": "povo データ追加 トッピング", "body": "povoのデータトッピングキャンペーンのお知らせ。", "label": "プロモーション"},
        {"subject": "Yahoo!ショッピング 5のつく日", "body": "Yahoo!ショッピング5のつく日でポイント5倍！", "label": "プロモーション"},
        {"subject": "メルカリ クーポン配布", "body": "メルカリで使えるクーポンをプレゼント！", "label": "プロモーション"},
        {"subject": "Zozotown セール開催", "body": "Zozotownで大セール開催中です。", "label": "プロモーション"},
        {"subject": "ヨドバシカメラ ポイント還元", "body": "ヨドバシカメラでポイント還元率アップ！", "label": "プロモーション"},
        {"subject": "スターバックス 新商品", "body": "スターバックス新商品のご紹介です。", "label": "プロモーション"},
        
        # 重要 (12件)
        {"subject": "緊急 システム障害 サーバーエラー", "body": "システムに緊急事態が発生しました。", "label": "重要"},
        {"subject": "セキュリティアラート 不正アクセス", "body": "不正アクセスの可能性があります。", "label": "重要"},
        {"subject": "パスワード変更 セキュリティ向上", "body": "セキュリティ向上のためパスワード変更をお願いします。", "label": "重要"},
        {"subject": "GitHub セキュリティアラート", "body": "GitHubリポジトリでセキュリティ脆弱性が検出されました。", "label": "重要"},
        {"subject": "システムメンテナンス緊急", "body": "緊急システムメンテナンスを実施します。", "label": "重要"},
        {"subject": "データベース障害復旧", "body": "データベース障害から復旧しました。", "label": "重要"},
        {"subject": "ネットワーク接続エラー", "body": "ネットワーク接続に問題が発生しています。", "label": "重要"},
        {"subject": "バックアップ失敗通知", "body": "自動バックアップが失敗しました。", "label": "重要"},
        {"subject": "SSL証明書期限切れ", "body": "SSL証明書の期限が近づいています。", "label": "重要"},
        {"subject": "サーバー負荷異常", "body": "サーバーの負荷が異常値を示しています。", "label": "重要"},
        {"subject": "API制限超過", "body": "API使用量が制限を超過しました。", "label": "重要"},
        {"subject": "ディスク容量不足", "body": "サーバーのディスク容量が不足しています。", "label": "重要"},
        
        # 仕事・学習 (11件)
        {"subject": "Indeed 新着求人 エンジニア職", "body": "あなたに合うエンジニア求人が見つかりました。", "label": "仕事・学習"},
        {"subject": "GitHub アクティビティサマリー コミット", "body": "今週のGitHubアクティビティサマリーです。", "label": "仕事・学習"},
        {"subject": "Udemy 学習進捗 Python入門コース", "body": "Python入門コースの学習進捗レポートです。", "label": "仕事・学習"},
        {"subject": "Indeed プレミアム会員 求人情報", "body": "プレミアム会員限定の求人情報をお届けします。", "label": "仕事・学習"},
        {"subject": "Udemy コース修了証明書", "body": "コース修了おめでとうございます。証明書を発行しました。", "label": "仕事・学習"},
        {"subject": "LinkedIn 新しいつながり", "body": "LinkedInで新しいプロフェッショナルとつながりました。", "label": "仕事・学習"},
        {"subject": "Stack Overflow 週間サマリー", "body": "Stack Overflowの週間人気質問をお届けします。", "label": "仕事・学習"},
        {"subject": "Coursera 新コース推奨", "body": "あなたにおすすめの新しいコースのご紹介です。", "label": "仕事・学習"},
        {"subject": "Qiita トレンド記事", "body": "今週のQiitaトレンド記事をお届けします。", "label": "仕事・学習"},
        {"subject": "プログラミング学習進捗", "body": "プログラミング学習の進捗をお知らせします。", "label": "仕事・学習"},
        {"subject": "転職活動サポート", "body": "転職活動のサポート情報をお送りします。", "label": "仕事・学習"}
    ]
    
    return pd.DataFrame(extended_data)

def train_model(df):
    """拡張版モデルの学習（特徴量エンジニアリング適用）"""
    print("拡張版モデル学習を開始します...")
    
    # 特徴量エンジニアリング適用
    print("特徴量エンジニアリングを適用中...")
    df['enhanced_text'] = df.apply(lambda row: create_enhanced_features(f"{row['subject']} {row['body']}"), axis=1)
    
    # 拡張テキストを使用
    X = df['enhanced_text']
    y = df['label']
    
    print(f"学習データ数: {len(X)}")
    print(f"分類クラス: {y.value_counts()}")
    
    # データ分割（小データセット対応）
    if len(X) < 20:
        # 小データセットの場合、stratifyを無効化
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    
    # 拡張TF-IDF ベクトル化（PayPay問題に対応）
    vectorizer = TfidfVectorizer(
        max_features=3000,      # 特徴量数を増加
        ngram_range=(1, 2),     # 1-gramと2-gramを使用
        min_df=1,               # 最小文書頻度を下げて細かい特徴も捉える
        max_df=0.95,            # 最大文書頻度
        sublinear_tf=True,      # TF値の対数スケーリング
        stop_words=None         # 日本語対応のため
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # 拡張SVM モデル学習（PayPay問題に対応）
    model = LinearSVC(
        C=1.0,                  # 正則化パラメータ
        class_weight='balanced', # クラス不均衡に対応
        random_state=42,
        max_iter=2000
    )
    model.fit(X_train_vec, y_train)
    
    # 評価
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\\n学習完了！")
    print(f"精度: {accuracy:.3f}")
    print(f"\\n分類レポート:")
    print(classification_report(y_test, y_pred))
    
    # PayPay特徴量の重要度確認
    feature_names = vectorizer.get_feature_names_out()
    
    # 支払い関係クラスのインデックスを取得
    class_labels = model.classes_
    payment_idx = list(class_labels).index('支払い関係') if '支払い関係' in class_labels else 0
    feature_importance = model.coef_[payment_idx]
    
    # PayPay関連特徴量を探す
    paypay_features = [(name, importance) for name, importance in zip(feature_names, feature_importance) 
                       if 'paypay' in name.lower() or 'ペイ' in name or 'PAYPAY' in name]
    
    if paypay_features:
        print(f"\\n=== PayPay関連特徴量の重要度 ===\\n")
        for feature, importance in sorted(paypay_features, key=lambda x: x[1], reverse=True)[:10]:
            print(f"{feature}: {importance:.3f}")
    
    return vectorizer, model

def train_extended_model():
    """拡張版モデルの学習（test_model.py用）"""
    df = create_extended_training_data()
    return train_model(df)

def save_model(vectorizer, model, model_path="model.pkl"):
    """モデルの保存"""
    with open(model_path, "wb") as f:
        pickle.dump((vectorizer, model), f)
    print(f"モデルを保存しました: {model_path}")

def main():
    """メイン実行関数"""
    print("=== Gmail分類モデル学習 ===")
    
    # 拡張版データで学習（デフォルト動作を変更）
    print("拡張版データセット（45件、4カテゴリ）で学習を開始します...")
    df = create_extended_training_data()
    
    # モデル学習
    vectorizer, model = train_model(df)
    
    # モデル保存
    save_model(vectorizer, model)
    
    print("\\n拡張版モデル学習完了！")
    print("- データ数: 45件")
    print("- カテゴリ: 4つ（支払い関係、プロモーション、重要、仕事・学習）")
    print("\\nrun.py でAPIサーバーを起動してテストしてください。")

if __name__ == "__main__":
    main()