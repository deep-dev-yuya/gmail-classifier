"""
MCP Context Enricher Blueprint
メールの文脈補完・情報抽出
"""

from flask import Blueprint, request, jsonify
import re
from datetime import datetime, timedelta

context_bp = Blueprint('context', __name__)

@context_bp.route('/enrich-context', methods=['POST'])
def enrich_context():
    """文脈補完エンドポイント"""
    try:
        data = request.json
        
        if not data or 'body' not in data:
            return jsonify({
                "error": "Missing required field: body"
            }), 400
        
        body = data.get('body', '')
        subject = data.get('subject', '')
        
        # 文脈分析
        context_info = analyze_context(subject, body)
        
        return jsonify(context_info)
        
    except Exception as e:
        return jsonify({
            "error": f"Context enrichment failed: {str(e)}"
        }), 500

def analyze_context(subject, body):
    """メール内容の文脈分析"""
    context = {
        "enriched_context": "特別な文脈なし",
        "context_summary": "",
        "deadline_info": None,
        "priority_level": "normal",
        "keywords": [],
        "entities": {}
    }
    
    text = f"{subject} {body}".lower()
    
    # 支払い関係の検出
    payment_keywords = ["支払い", "請求", "料金", "引き落とし", "決済", "振込", "入金"]
    if any(keyword in text for keyword in payment_keywords):
        context["enriched_context"] = "支払いに関する文脈あり"
        context["context_summary"] = "支払い・請求関連のメール"
        context["priority_level"] = "high"
        context["keywords"].extend([k for k in payment_keywords if k in text])
    
    # 会議・スケジュール関係
    meeting_keywords = ["会議", "ミーティング", "打ち合わせ", "面談", "スケジュール"]
    if any(keyword in text for keyword in meeting_keywords):
        context["enriched_context"] = "会議・スケジュール関連の文脈あり"
        context["context_summary"] = "会議・スケジュール関連のメール"
        context["keywords"].extend([k for k in meeting_keywords if k in text])
    
    # 緊急度の検出
    urgent_keywords = ["緊急", "至急", "重要", "urgent", "important"]
    if any(keyword in text for keyword in urgent_keywords):
        context["priority_level"] = "urgent"
        context["keywords"].extend([k for k in urgent_keywords if k in text])
    
    # 期限の抽出
    deadline = extract_deadline(text)
    if deadline:
        context["deadline_info"] = deadline
        context["priority_level"] = "high"
    
    # エンティティ抽出
    context["entities"] = extract_entities(text)
    
    # キーワード重複除去
    context["keywords"] = list(set(context["keywords"]))
    
    return context

def extract_deadline(text):
    """期限情報の抽出"""
    deadline_patterns = [
        r'(\d{4})[年-](\d{1,2})[月-](\d{1,2})日?',
        r'(\d{1,2})[月/](\d{1,2})日?',
        r'期限[：:]\s*(\d{4})[年-](\d{1,2})[月-](\d{1,2})',
        r'までに|まで'
    ]
    
    for pattern in deadline_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                if len(matches[0]) == 3:  # 年月日
                    year, month, day = matches[0]
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif len(matches[0]) == 2:  # 月日
                    month, day = matches[0]
                    current_year = datetime.now().year
                    return f"{current_year}-{month.zfill(2)}-{day.zfill(2)}"
            except:
                continue
    
    return None

def extract_entities(text):
    """エンティティ抽出（簡易版）"""
    entities = {
        "amounts": [],
        "dates": [],
        "organizations": []
    }
    
    # 金額の抽出
    amount_pattern = r'[￥¥]\s*[\d,]+|[\d,]+\s*円'
    amounts = re.findall(amount_pattern, text)
    entities["amounts"] = amounts
    
    # 日付の抽出
    date_pattern = r'\d{1,2}[月/]\d{1,2}日?|\d{4}[年-]\d{1,2}[月-]\d{1,2}'
    dates = re.findall(date_pattern, text)
    entities["dates"] = dates
    
    return entities