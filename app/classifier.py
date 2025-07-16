"""
Gmail分類API Blueprint
機械学習モデルを使用してメールを分類
"""

from flask import Blueprint, request, jsonify
import pickle
import joblib
import os
import pandas as pd
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

classifier_bp = Blueprint('classifier', __name__)

# グローバル変数でPipelineモデルをキャッシュ
_pipeline = None

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
        features.append(f"PAYPAY_STRENGTH_{min(paypay_strength, 5)}")  # 上镐5で正規化
    
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

def load_pipeline():
    """Pipeline化されたモデルの読み込み"""
    global _pipeline
    
    if _pipeline is None:
        # Pipeline化されたモデルを優先的に読み込み
        pipeline_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'paypay_specialized_v1.pkl')
        old_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl')
        
        if os.path.exists(pipeline_path):
            # Pipeline化されたモデルを読み込み
            loaded_data = joblib.load(pipeline_path)
            _pipeline = loaded_data['pipeline']
        elif os.path.exists(old_model_path):
            # 旧形式のモデルを読み込み（fallback）
            with open(old_model_path, 'rb') as f:
                vectorizer, model = pickle.load(f)
            # 旧形式をPipelineに変換
            from sklearn.pipeline import make_pipeline
            _pipeline = make_pipeline(vectorizer, model)
        else:
            # デモ用の簡易分類器
            vectorizer = TfidfVectorizer(max_features=1000)
            model = LinearSVC()
            
            # ダミーデータで初期化
            dummy_texts = [
                "支払い期限のお知らせ 料金の引き落とし",
                "会議のご案内 スケジュール調整",
                "重要なお知らせ システムメンテナンス"
            ]
            dummy_labels = ["支払い関係", "通知", "重要"]
            
            X = vectorizer.fit_transform(dummy_texts)
            model.fit(X, dummy_labels)
            
            from sklearn.pipeline import make_pipeline
            _pipeline = make_pipeline(vectorizer, model)
    
    return _pipeline

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
        
        # Pipeline読み込み
        pipeline = load_pipeline()
        
        # テキスト結合とPayPay特化特徴量エンジニアリング
        text = f"{subject} {body}"
        enhanced_text = create_paypay_specialized_features(text)
        
        # 予測実行（Pipeline）
        prediction = pipeline.predict([enhanced_text])[0]
        
        # 信頼度計算（CalibratedClassifierCVで確率化）
        try:
            probabilities = pipeline.predict_proba([enhanced_text])[0]
            confidence = float(max(probabilities))
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
        pipeline_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'paypay_specialized_v1.pkl')
        old_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl')
        
        return jsonify({
            "pipeline_file_exists": os.path.exists(pipeline_path),
            "pipeline_path": pipeline_path,
            "old_model_file_exists": os.path.exists(old_model_path),
            "old_model_path": old_model_path,
            "pipeline_loaded": _pipeline is not None
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Status check failed: {str(e)}"
        }), 500

@classifier_bp.route('/model/reload', methods=['POST'])
def reload_model():
    """モデルの再読み込み"""
    try:
        global _pipeline
        _pipeline = None  # キャッシュクリア
        
        # 新しいPipelineを読み込み
        pipeline = load_pipeline()
        
        return jsonify({
            "status": "success",
            "message": "Pipeline model reloaded successfully",
            "pipeline_loaded": _pipeline is not None
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Reload failed: {str(e)}"
        }), 500