#!/usr/bin/env python3
"""
Gmail分類PoC APIテスト
"""

import pytest
import json
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

@pytest.fixture
def client():
    """テスト用Flaskクライアント"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """ヘルスチェックテスト"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'gmail-classifier'

def test_classify_api(client):
    """メール分類APIテスト"""
    test_data = {
        "subject": "支払い期限のお知らせ",
        "body": "クレジットカード料金の引き落とし日が近づいています"
    }
    
    response = client.post('/api/classify',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'classification' in data
    assert 'confidence' in data
    assert 'text_length' in data

def test_classify_api_missing_data(client):
    """メール分類API - データ不足テスト"""
    test_data = {
        "subject": "テスト件名"
        # body が不足
    }
    
    response = client.post('/api/classify',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data

def test_enrich_context_api(client):
    """文脈補完APIテスト"""
    test_data = {
        "subject": "会議のご案内",
        "body": "来週の定例ミーティングについてご連絡します"
    }
    
    response = client.post('/api/enrich-context',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'enriched_context' in data
    assert 'context_summary' in data
    assert 'keywords' in data
    assert 'entities' in data

def test_payment_context_detection(client):
    """支払い関係の文脈検出テスト"""
    test_data = {
        "subject": "請求書発行のお知らせ",
        "body": "支払い期限は今月末です。振込をお願いします。"
    }
    
    response = client.post('/api/enrich-context',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "支払い" in data['enriched_context']
    assert data['priority_level'] == 'high'

def test_model_status_api(client):
    """モデル状態APIテスト"""
    response = client.get('/api/model/status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'model_loaded' in data
    assert 'model_path' in data

if __name__ == '__main__':
    pytest.main([__file__])