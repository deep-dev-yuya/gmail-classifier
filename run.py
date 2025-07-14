#!/usr/bin/env python3
"""
Gmail分類PoC - Flask APIサーバー
メイン実行ファイル
"""

from flask import Flask
from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)