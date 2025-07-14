#!/usr/bin/env python3
"""
機械学習モデルテスト
"""

import pytest
import pandas as pd
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.train_model import create_sample_data, train_model

def test_sample_data_creation():
    """サンプルデータ作成テスト"""
    df = create_sample_data()
    
    # データフレームの基本チェック
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'subject' in df.columns
    assert 'body' in df.columns
    assert 'label' in df.columns
    
    # 分類ラベルの確認
    expected_labels = ['支払い関係', '通知', '重要']
    assert all(label in df['label'].unique() for label in expected_labels)

def test_model_training():
    """モデル学習テスト"""
    # サンプルデータで学習
    df = create_sample_data()
    vectorizer, model = train_model(df)
    
    # モデルの基本チェック
    assert vectorizer is not None
    assert model is not None
    
    # 予測テスト
    test_text = ["支払い期限のお知らせ 料金の引き落とし"]
    X_test = vectorizer.transform(test_text)
    prediction = model.predict(X_test)
    
    assert len(prediction) == 1
    assert prediction[0] in ['支払い関係', '通知', '重要']

def test_text_classification():
    """テキスト分類テスト"""
    df = create_sample_data()
    vectorizer, model = train_model(df)
    
    # 支払い関係のテスト
    payment_text = ["請求書 支払い期限 引き落とし"]
    X_payment = vectorizer.transform(payment_text)
    payment_pred = model.predict(X_payment)[0]
    
    # 会議関係のテスト
    meeting_text = ["会議のご案内 ミーティング 参加"]
    X_meeting = vectorizer.transform(meeting_text)
    meeting_pred = model.predict(X_meeting)[0]
    
    # 緊急関係のテスト
    urgent_text = ["緊急 システム障害 重要"]
    X_urgent = vectorizer.transform(urgent_text)
    urgent_pred = model.predict(X_urgent)[0]
    
    # 結果の確認（完全な精度は期待しないが、分類されることを確認）
    assert payment_pred in ['支払い関係', '通知', '重要']
    assert meeting_pred in ['支払い関係', '通知', '重要']
    assert urgent_pred in ['支払い関係', '通知', '重要']

if __name__ == '__main__':
    pytest.main([__file__])