#!/usr/bin/env python3
"""
強化版テーマ抽出器
subject_index.mdとの照合を徹底的に行い、正確なテーマを抽出
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from modules.subject_index_loader import SubjectIndexLoader
from modules.theme_knowledge_base import ThemeKnowledgeBase

logger = logging.getLogger(__name__)


class EnhancedThemeExtractor:
    """subject_index.mdを最大限活用する強化版テーマ抽出器"""
    
    def __init__(self):
        """初期化"""
        self.subject_loader = SubjectIndexLoader()
        self.knowledge_base = ThemeKnowledgeBase()
        
        # 除外すべき無意味なパターン
        self.invalid_patterns = [
            r'受験番号.*氏名',
            r'氏名.*受験番号',
            r'得点.*採点',
            r'解答.*用紙',
            r'漢字四字',
            r'総合総合',
            r'業績$',  # 末尾が「業績」だけのもの
        ]
        
        logger.info("EnhancedThemeExtractor 初期化完了")
    
    def extract_theme(self, question_text: str, question_num: str = "", field: str = "") -> Dict:
        """
        問題文から正確なテーマを抽出
        
        Args:
            question_text: 問題文
            question_num: 問題番号
            field: 分野（地理/歴史/公民/時事）
            
        Returns:
            抽出結果の辞書
        """
        
        # 無効なテキストを除外
        if self._is_invalid_text(question_text):
            logger.debug(f"無効なテキストを除外: {question_text[:50]}")
            return {
                'theme': '分析対象外',
                'keywords': [],
                'field': field or '総合',
                'confidence': 0
            }
        
        # subject_indexから重要語句を検出
        found_terms = self.subject_loader.find_important_terms(question_text)
        
        # 優先テーマがある場合はそれを採用
        if found_terms['priority_themes']:
            theme = found_terms['priority_themes'][0]
            logger.info(f"優先テーマ採用: {theme}")
            
            # 関連語句を収集
            all_keywords = (found_terms['history'] + 
                          found_terms['geography'] + 
                          found_terms['civics'])[:5]
            
            # 分野を自動判定
            if not field:
                field = self.subject_loader.get_field_from_terms(all_keywords)
            
            return {
                'theme': theme,
                'keywords': all_keywords,
                'field': field,
                'confidence': 1.0
            }
        
        # 通常の重要語句から テーマを構築
        all_found = (found_terms['history'] + 
                    found_terms['geography'] + 
                    found_terms['civics'])
        
        if all_found:
            # 最も重要な語句をテーマとする
            theme = self._build_theme_from_terms(all_found, question_text, field)
            
            # 分野を自動判定
            if not field:
                field = self.subject_loader.get_field_from_terms(all_found)
            
            return {
                'theme': theme,
                'keywords': all_found[:5],
                'field': field,
                'confidence': 0.8
            }
        
        # ThemeKnowledgeBaseでフォールバック
        try:
            theme = self.knowledge_base.determine_theme(question_text[:500], field)
            keywords = self.knowledge_base.extract_important_terms(question_text, field, limit=5)
            
            # 無意味なテーマを修正
            if self._is_invalid_theme(theme):
                theme = self._fix_invalid_theme(theme, question_text, field)
            
            return {
                'theme': theme,
                'keywords': keywords,
                'field': field or '総合',
                'confidence': 0.5
            }
        except:
            # 最終フォールバック
            return {
                'theme': f"{field}問題" if field else "総合問題",
                'keywords': [],
                'field': field or '総合',
                'confidence': 0.1
            }
    
    def _is_invalid_text(self, text: str) -> bool:
        """無効なテキストかチェック"""
        if not text or len(text.strip()) < 5:
            return True
        
        # 除外パターンにマッチするか
        for pattern in self.invalid_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # 解答欄のみの場合
        if re.match(r'^[\s\d\(\)（）ア-ンァ-ヶ]+$', text):
            return True
        
        return False
    
    def _is_invalid_theme(self, theme: str) -> bool:
        """無効なテーマかチェック（OCRフラグメント含む）"""
        if not theme:
            return True
            
        # OCRフラグメントパターン
        ocr_fragments = [
            r'^記号\s+\w+$',  # "記号 文武"
            r'^\w{2,4}県\w{1,2}$',  # "兵庫県明"
            r'^.+以外$',  # "朱子学以外"
            r'^下線部',  # "下線部"で始まる
            r'^記号\s+下線部$',  # "記号 下線部"
            r'^\w+\s+下線部$',  # "核兵器 下線部"
            r'^新詳',  # "新詳日本史"
            r'^第\d+[条項]$',  # "第78条"
            r'^\w{1,3}$',  # 3文字以下
        ]
        
        import re
        for pattern in ocr_fragments:
            if re.match(pattern, theme):
                return True
        
        # 「〜の業績」パターンをチェック
        if 'の業績' in theme:
            return True
            
        # その他の無効パターン
        invalid_themes = [
            '受験番号氏名',
            '総合総合問題',
            '漢字四字',
            '業績',  # 単体の「業績」
            '氏名',
            '受験番号'
        ]
        
        for invalid in invalid_themes:
            if invalid in theme:
                return True
        
        return False
    
    def _fix_invalid_theme(self, theme: str, text: str, field: str) -> str:
        """無効なテーマを修正"""
        
        # 「〜の業績」を適切に変換
        if '業績' in theme:
            # テーマから人名・地名・語句を抽出
            theme_parts = theme.replace('の業績', '').strip()
            
            # 人名パターン（「氏」が含まれる場合）
            if '氏' in theme_parts:
                return f"{theme_parts}の功績"
            
            # 地名パターン（県・市・国など）
            elif any(suffix in theme_parts for suffix in ['県', '市', '国', '地域']):
                return f"{theme_parts}の発展"
            
            # 歴史的事項パターン
            elif any(keyword in theme_parts for keyword in ['貿易', '戦争', '条約', '改革', '制度']):
                return theme_parts  # 「業績」を削除してそのまま返す
            
            # その他の場合、文脈から判断
            elif field == '歴史':
                # 歴史の場合は「〜の意義」や「〜の影響」にする
                if '朱子学' in theme_parts or '仏教' in theme_parts:
                    return f"{theme_parts}の影響"
                else:
                    return f"{theme_parts}の意義"
            elif field == '地理':
                return f"{theme_parts}の特色"
            elif field == '公民':
                return f"{theme_parts}の役割"
            else:
                # フィールドが不明な場合
                return theme_parts if theme_parts else f"{field}の重要事項"
        
        # 「総合総合問題」を修正
        if '総合総合' in theme:
            return f"{field}総合問題" if field else "総合問題"
        
        # 不完全なテーマの修正（例：「兵庫県明」）
        if theme and len(theme) <= 5 and not any(suffix in theme for suffix in ['問題', '特徴', '特色', '役割']):
            # 短すぎるテーマは「〜の特徴」を付ける
            return f"{theme}の特徴"
        
        return theme
    
    def _build_theme_from_terms(self, terms: List[str], text: str, field: str) -> str:
        """検出された語句からテーマを構築"""
        
        if not terms:
            return f"{field}問題"
        
        # 最も重要な語句を選定
        primary_term = terms[0]
        
        # 特定のパターンに基づいてテーマを構築
        theme_patterns = {
            '促成栽培': '促成栽培と農業',
            '四大工業地帯': '日本の工業地帯',
            '三権分立': '三権分立の仕組み',
            '鎌倉幕府': '鎌倉幕府の成立',
            '明治維新': '明治維新の改革',
            '大日本帝国憲法': '大日本帝国憲法の特徴',
            '日本国憲法': '日本国憲法の原則',
        }
        
        # パターンにマッチする場合
        for key, theme in theme_patterns.items():
            if key in primary_term or key in terms:
                return theme
        
        # 文脈から判断
        if '特徴' in text or '特色' in text:
            return f"{primary_term}の特徴"
        elif '役割' in text or '働き' in text:
            return f"{primary_term}の役割"
        elif '原因' in text or '理由' in text:
            return f"{primary_term}の原因"
        elif '影響' in text or '結果' in text:
            return f"{primary_term}の影響"
        else:
            return primary_term
    
    def analyze_questions(self, questions: List) -> List[Dict]:
        """
        複数の問題を一括分析
        
        Args:
            questions: 問題リスト
            
        Returns:
            分析結果のリスト
        """
        results = []
        
        for q in questions:
            # 問題テキストと番号を取得
            if hasattr(q, 'text'):
                text = q.text
            else:
                text = str(q)
            
            if hasattr(q, 'number'):
                num = q.number
            else:
                num = ""
            
            if hasattr(q, 'field'):
                field = q.field.value if hasattr(q.field, 'value') else str(q.field)
            else:
                field = ""
            
            # テーマを抽出
            result = self.extract_theme(text, num, field)
            result['question_number'] = num
            results.append(result)
        
        return results