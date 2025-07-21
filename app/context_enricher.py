"""
Gmail分類システム用 高度文脈補完モジュール
コンテキストガイドの高度化を参考に実装
"""

from flask import Blueprint, request, jsonify
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

context_bp = Blueprint('context', __name__)

class AdvancedContextEnricher:
    """高度な文脈補完クラス（Gmail特化）"""
    
    def __init__(self):
        # 金額抽出パターン（Gmail特化）
        self.amount_patterns = [
            r'(\d{1,3}(?:,\d{3})*|\d+)円',
            r'(\d{1,3}(?:,\d{3})*|\d+)¥',
            r'¥(\d{1,3}(?:,\d{3})*|\d+)',
            r'金額[：:]\s*(\d{1,3}(?:,\d{3})*|\d+)円?',
            r'利用金額[：:]\s*(\d{1,3}(?:,\d{3})*|\d+)円?',
            r'請求金額[：:]\s*(\d{1,3}(?:,\d{3})*|\d+)円?',
            r'(\d+\.\d{2})',  # 3360.00形式
        ]
        
        # 日付抽出パターン（拡張版）
        self.date_patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?',
            r'(\d{1,2})[月/-](\d{1,2})日?',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'期限[：:]\s*(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日?',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{2}:\d{2}:\d{2})',  # 時刻パターン
        ]
        
        # 決済サービス名（PayPay特化拡張）
        self.payment_services = {
            'major_payment': ['PayPay', 'LINE Pay', 'Apple Pay', 'Google Pay', 'Amazon Pay'],
            'credit_service': ['ペイディ', 'Paidy', 'メルペイ', '楽天ペイ', 'PayPal'],
            'card_service': ['デビットカード', 'クレジットカード', 'VISA', 'MasterCard', 'JCB'],
            'bank_service': ['銀行振込', '口座振替', '引き落とし', '振替'],
            'store_service': ['セブンイレブン', 'ローソン', 'ファミマ', 'イオン', 'Amazon', '楽天']
        }
        
        # 緊急度キーワード（Gmail特化）
        self.urgency_keywords = {
            'high': ['緊急', '至急', '重要', 'urgent', 'emergency', '障害', '停止', 'セキュリティ', '不正'],
            'medium': ['お知らせ', 'notification', '通知', '案内', 'ご連絡', '確認', '手続き'],
            'low': ['プロモーション', 'キャンペーン', 'セール', 'お得', 'タイムセール', '特典']
        }
        
        # 支払い関連キーワード（詳細化）
        self.payment_keywords = {
            'charge': ['チャージ', 'charge', '入金', '残高追加', '補充'],
            'debit': ['引き落とし', '決済', '利用完了', '支払い完了', '購入', '課金'],
            'billing': ['請求', '料金', 'お支払い', '請求書', '明細'],
            'transfer': ['送金', '振込', '受取', '送付'],
            'general': ['支払い', '決済', '入金', '残高', '利用', '購入']
        }

    def extract_entities(self, text: str) -> Dict:
        """エンティティ抽出（Gmail特化）"""
        entities = {
            'amounts': [],
            'dates': [],
            'payment_services': {},
            'urgency_level': 'low',
            'paypay_strength': 0,
            'payment_type': None
        }
        
        # 金額抽出
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text)
            entities['amounts'].extend(matches)
        
        # 日付抽出
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            entities['dates'].extend(matches)
        
        # 決済サービス分類
        for service_type, services in self.payment_services.items():
            found_services = [s for s in services if s in text]
            if found_services:
                entities['payment_services'][service_type] = found_services
        
        # PayPay強度計算
        paypay_variants = ['PayPay', 'paypay', 'ペイペイ', 'ペイ', 'PAYPAY']
        for variant in paypay_variants:
            entities['paypay_strength'] += text.count(variant)
        
        # 緊急度判定
        for level, keywords in self.urgency_keywords.items():
            if any(keyword in text for keyword in keywords):
                entities['urgency_level'] = level
                break
        
        # 支払いタイプ判定
        for pay_type, keywords in self.payment_keywords.items():
            if any(keyword in text for keyword in keywords):
                entities['payment_type'] = pay_type
                break
        
        return entities

    def analyze_payment_context(self, text: str) -> Dict:
        """支払い関連文脈の詳細分析（PayPay特化）"""
        payment_context = {
            'is_payment_related': False,
            'payment_type': None,
            'action_required': False,
            'keywords_found': [],
            'paypay_specific': False,
            'context_strength': 0,
            'completion_indicators': [],
            'amount_context': False
        }
        
        # 全支払いキーワード検索
        all_keywords = []
        for category, keywords in self.payment_keywords.items():
            found = [kw for kw in keywords if kw in text]
            all_keywords.extend(found)
            if found and category != 'general':
                payment_context['payment_type'] = category
        
        payment_context['keywords_found'] = all_keywords
        
        if all_keywords:
            payment_context['is_payment_related'] = True
            payment_context['context_strength'] = len(all_keywords)
        
        # PayPay特化判定
        paypay_indicators = ['PayPay', 'paypay', 'ペイペイ', 'ペイ']
        if any(indicator in text for indicator in paypay_indicators):
            payment_context['paypay_specific'] = True
            payment_context['context_strength'] += 2
        
        # 完了指標検出
        completion_words = ['完了', '終了', 'しました', 'されました', '確定']
        payment_context['completion_indicators'] = [
            word for word in completion_words if word in text
        ]
        
        # 金額文脈判定
        if any(pattern in text for pattern in ['金額', '料金', '¥', '円']):
            payment_context['amount_context'] = True
            payment_context['context_strength'] += 1
        
        # アクション要求判定
        action_words = ['期限', '確認', '手続き', 'お支払い', '変更']
        if any(word in text for word in action_words):
            payment_context['action_required'] = True
        
        return payment_context

    def calculate_priority(self, entities: Dict, payment_context: Dict) -> str:
        """優先度計算の高度化（Gmail特化）"""
        score = 0
        
        # 緊急度による加点
        urgency_scores = {'high': 40, 'medium': 20, 'low': 0}
        score += urgency_scores.get(entities['urgency_level'], 0)
        
        # PayPay特化による加点
        if payment_context['paypay_specific']:
            score += 25
        
        # 支払い関連による加点
        if payment_context['is_payment_related']:
            score += 20
            if payment_context['action_required']:
                score += 15
        
        # 文脈強度による加点
        score += min(payment_context['context_strength'] * 5, 20)
        
        # 金額による加点
        if entities['amounts']:
            score += 15
        
        # 日付による加点
        if entities['dates']:
            score += 10
        
        # PayPay強度による加点
        if entities['paypay_strength'] > 0:
            score += min(entities['paypay_strength'] * 10, 30)
        
        # 優先度判定（Gmail特化）
        if score >= 50:
            return 'high'
        elif score >= 25:
            return 'medium'
        else:
            return 'low'

    def enrich_context(self, subject: str, body: str) -> Dict:
        """統合文脈補完（Gmail特化）"""
        full_text = f"{subject} {body}"
        
        # エンティティ抽出
        entities = self.extract_entities(full_text)
        
        # 支払い文脈分析
        payment_context = self.analyze_payment_context(full_text)
        
        # 優先度計算
        priority = self.calculate_priority(entities, payment_context)
        
        # 文脈要約生成
        context_summary = self._generate_context_summary(
            entities, payment_context, priority
        )
        
        return {
            'enriched_context': context_summary,
            'priority_level': priority,
            'entities': entities,
            'payment_analysis': payment_context,
            'keywords': payment_context['keywords_found'],
            'deadline_info': entities['dates'][0] if entities['dates'] else None,
            'amount_info': entities['amounts'][0] if entities['amounts'] else None,
            'paypay_strength': entities['paypay_strength'],
            'context_strength': payment_context['context_strength']
        }

    def _generate_context_summary(self, entities: Dict, payment_context: Dict, priority: str) -> str:
        """文脈要約の生成（Gmail特化）"""
        summary_parts = []
        
        # 優先度情報
        priority_labels = {'high': '高優先度', 'medium': '中優先度', 'low': '低優先度'}
        summary_parts.append(f"{priority_labels[priority]}のメール")
        
        # PayPay特化情報
        if payment_context['paypay_specific']:
            summary_parts.append("PayPay関連")
            if entities['paypay_strength'] > 1:
                summary_parts.append(f"(強度: {entities['paypay_strength']})")
        
        # 支払い関連情報
        if payment_context['is_payment_related']:
            if payment_context['payment_type'] == 'charge':
                summary_parts.append("チャージ・入金に関する通知")
            elif payment_context['payment_type'] == 'debit':
                summary_parts.append("決済・利用完了の通知")
            elif payment_context['payment_type'] == 'billing':
                summary_parts.append("請求・料金に関する通知")
            elif payment_context['payment_type'] == 'transfer':
                summary_parts.append("送金・振込に関する通知")
            else:
                summary_parts.append("支払い関連の通知")
        
        # 完了状態情報
        if payment_context['completion_indicators']:
            summary_parts.append("処理完了済み")
        
        # 金額情報
        if entities['amounts']:
            summary_parts.append(f"金額: {entities['amounts'][0]}円")
        
        # サービス情報
        for service_type, services in entities['payment_services'].items():
            if services:
                summary_parts.append(f"{service_type}: {', '.join(services)}")
        
        # 緊急度情報
        if entities['urgency_level'] == 'high':
            summary_parts.append("緊急対応が必要")
        elif payment_context['action_required']:
            summary_parts.append("アクションが必要")
        
        return "、".join(summary_parts)

# グローバルインスタンス
advanced_enricher = AdvancedContextEnricher()

@context_bp.route('/enrich-context', methods=['POST'])
def enrich_context():
    """高度文脈補完エンドポイント"""
    try:
        data = request.json
        
        if not data or 'body' not in data:
            return jsonify({
                "error": "Missing required field: body"
            }), 400
        
        body = data.get('body', '')
        subject = data.get('subject', '')
        
        # 高度文脈分析
        context_info = advanced_enricher.enrich_context(subject, body)
        
        return jsonify(context_info)
        
    except Exception as e:
        logging.error(f"Context enrichment failed: {str(e)}")
        return jsonify({
            "error": f"Context enrichment failed: {str(e)}"
        }), 500

@context_bp.route('/analyze-payment', methods=['POST'])
def analyze_payment():
    """支払い分析専用エンドポイント"""
    try:
        data = request.json
        text = f"{data.get('subject', '')} {data.get('body', '')}"
        
        payment_analysis = advanced_enricher.analyze_payment_context(text)
        entities = advanced_enricher.extract_entities(text)
        
        return jsonify({
            'payment_analysis': payment_analysis,
            'extracted_amounts': entities['amounts'],
            'extracted_dates': entities['dates'],
            'payment_services': entities['payment_services'],
            'paypay_strength': entities['paypay_strength']
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Payment analysis failed: {str(e)}"
        }), 500

# 下位互換性のための古い関数
def analyze_context(subject, body):
    """メール内容の文脈分析（下位互換）"""
    # 新しい高度文脈補完を使用
    result = advanced_enricher.enrich_context(subject, body)
    
    # 古い形式に変換
    return {
        "enriched_context": result['enriched_context'],
        "context_summary": result['enriched_context'],
        "deadline_info": result['deadline_info'],
        "priority_level": result['priority_level'],
        "keywords": result['keywords'],
        "entities": {
            "amounts": result['entities']['amounts'],
            "dates": result['entities']['dates'],
            "organizations": list(result['entities']['payment_services'].keys())
        }
    }

def extract_deadline(text):
    """期限情報の抽出（高度版使用）"""
    entities = advanced_enricher.extract_entities(text)
    return entities['dates'][0] if entities['dates'] else None

def extract_entities(text):
    """エンティティ抽出（高度版使用）"""
    entities = advanced_enricher.extract_entities(text)
    return {
        "amounts": entities['amounts'],
        "dates": entities['dates'],
        "organizations": list(entities['payment_services'].keys())
    }