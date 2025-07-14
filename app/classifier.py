"""
Gmail分類API Blueprint
機械学習モデルを使用してメールを分類
"""

from flask import Blueprint, request, jsonify
import pickle
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

classifier_bp = Blueprint('classifier', __name__)

# グローバル変数でモデルをキャッシュ
_model = None
_vectorizer = None

def load_model():
    """機械学習モデルの読み込み"""
    global _model, _vectorizer
    
    if _model is None or _vectorizer is None:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl')
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                _vectorizer, _model = pickle.load(f)
        else:
            # デモ用の簡易分類器
            _vectorizer = TfidfVectorizer(max_features=1000)
            _model = LinearSVC()
            
            # ダミーデータで初期化
            dummy_texts = [
                "支払い期限のお知らせ 料金の引き落とし",
                "会議のご案内 スケジュール調整",
                "重要なお知らせ システムメンテナンス"
            ]
            dummy_labels = ["支払い関係", "通知", "重要"]
            
            X = _vectorizer.fit_transform(dummy_texts)
            _model.fit(X, dummy_labels)
    
    return _vectorizer, _model

@classifier_bp.route('/classify', methods=['POST'])
def classify_email():
    """メール分類エンドポイント"""
    try:
        data = request.json
        
        # 必須フィールドの確認
        if not data or 'subject' not in data or 'body' not in data:
            return jsonify({
                "error": "Missing required fields: subject, body"
            }), 400
        
        subject = data.get('subject', '')
        body = data.get('body', '')
        
        # モデル読み込み
        vectorizer, model = load_model()
        
        # テキスト結合と前処理
        text = f"{subject} {body}"
        
        # 予測実行
        X = vectorizer.transform([text])
        prediction = model.predict(X)[0]
        
        # 信頼度計算（SVMの場合）
        try:
            confidence_scores = model.decision_function(X)[0]
            confidence = float(max(confidence_scores)) if hasattr(confidence_scores, '__iter__') else float(confidence_scores)
        except:
            confidence = 0.8  # デフォルト値
        
        # 結果返却
        result = {
            "classification": prediction,
            "confidence": confidence,
            "text_length": len(text),
            "model_status": "loaded"
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": f"Classification failed: {str(e)}"
        }), 500

@classifier_bp.route('/model/status', methods=['GET'])
def model_status():
    """モデルの状態確認"""
    try:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl')
        model_exists = os.path.exists(model_path)
        
        return jsonify({
            "model_file_exists": model_exists,
            "model_path": model_path,
            "model_loaded": _model is not None
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Status check failed: {str(e)}"
        }), 500