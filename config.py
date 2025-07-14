"""
Flask設定ファイル
"""

import os
from pathlib import Path

class Config:
    """基本設定クラス"""
    
    # Flask設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API設定
    API_TITLE = "Gmail分類PoC API"
    API_VERSION = "1.0.0"
    
    # モデル設定
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'model.pkl')
    
    # LINE API設定
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
    
    # Google Sheets API設定
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE')
    GOOGLE_SHEETS_SPREADSHEET_ID = os.environ.get('GOOGLE_SHEETS_SPREADSHEET_ID')
    
    # ログ設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
    
    # n8n Webhook設定
    N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook')
    
    @staticmethod
    def init_app(app):
        """アプリケーション初期化"""
        # ログディレクトリ作成
        log_dir = os.path.dirname(Config.LOG_FILE)
        Path(log_dir).mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    """開発環境設定"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """本番環境設定"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """テスト環境設定"""
    DEBUG = True
    TESTING = True

# 設定マッピング
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}