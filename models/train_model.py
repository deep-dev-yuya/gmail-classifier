#!/usr/bin/env python3
"""
Gmail分類モデル学習スクリプト
CSVデータから機械学習モデルを作成
"""

import pandas as pd
import pickle
import os
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

def train_model(df):
    """モデルの学習"""
    print("モデル学習を開始します...")
    
    # テキスト結合
    X = df["subject"] + " " + df["body"]
    y = df["label"]
    
    print(f"学習データ数: {len(X)}")
    print(f"分類クラス: {y.unique()}")
    
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # TF-IDF ベクトル化
    vectorizer = TfidfVectorizer(
        max_features=2000,
        ngram_range=(1, 2),
        stop_words=None  # 日本語対応のため
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # SVM モデル学習
    model = LinearSVC(random_state=42)
    model.fit(X_train_vec, y_train)
    
    # 評価
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\\n学習完了！")
    print(f"精度: {accuracy:.2f}")
    print(f"\\n分類レポート:")
    print(classification_report(y_test, y_pred))
    
    return vectorizer, model

def save_model(vectorizer, model, model_path="model.pkl"):
    """モデルの保存"""
    with open(model_path, "wb") as f:
        pickle.dump((vectorizer, model), f)
    print(f"モデルを保存しました: {model_path}")

def main():
    """メイン実行関数"""
    print("=== Gmail分類モデル学習 ===")
    
    # データ読み込み
    df = load_training_data()
    
    # モデル学習
    vectorizer, model = train_model(df)
    
    # モデル保存
    save_model(vectorizer, model)
    
    print("\\n学習完了！run.py でAPIサーバーを起動してテストしてください。")

if __name__ == "__main__":
    main()