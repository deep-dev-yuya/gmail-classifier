"""
Flask アプリケーションファクトリー
"""

from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    
    # CORS設定（n8nからのアクセス用）
    CORS(app)
    
    # 設定読み込み
    app.config.from_object('config.Config')
    
    # Blueprint登録
    from app.classifier import classifier_bp
    from app.context_enricher import context_bp
    
    app.register_blueprint(classifier_bp, url_prefix='/api')
    app.register_blueprint(context_bp, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        return {"status": "healthy", "service": "gmail-classifier"}
    
    return app