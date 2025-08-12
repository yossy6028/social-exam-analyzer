"""
構造化されたテーマ抽出器
問題文をリード文・設問・選択肢に分解してテーマを抽出
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ProblemStructure:
    """問題の構造"""
    lead_text: Optional[str] = None  # リード文（本文）
    question: Optional[str] = None   # 設問
    choices: List[str] = None        # 選択肢
    reference_content: Optional[str] = None  # 参照内容（下線部など）


@dataclass 
class StructuredTheme:
    """構造化されたテーマ"""
    theme: Optional[str]
    confidence: float
    source: str  # 'lead', 'question', 'choices', 'reference'
    category: Optional[str]


class StructuredThemeExtractor:
    """構造化アプローチによるテーマ抽出"""
    
    def __init__(self):
        self.question_end_patterns = self._init_question_end_patterns()
        self.choice_patterns = self._init_choice_patterns()
        self.reference_patterns = self._init_reference_patterns()
        self.theme_keywords = self._init_theme_keywords()
    
    def _init_question_end_patterns(self) -> List[re.Pattern]:
        """設問の終わりを示すパターン"""
        return [
            re.compile(r'答えなさい[。．]?'),
            re.compile(r'選びなさい[。．]?'),
            re.compile(r'書きなさい[。．]?'),
            re.compile(r'述べなさい[。．]?'),
            re.compile(r'説明しなさい[。．]?'),
            re.compile(r'選び記号で答えなさい[。．]?'),
            re.compile(r'答えよ[。．]?'),
        ]
    
    def _init_choice_patterns(self) -> List[re.Pattern]:
        """選択肢のパターン"""
        return [
            re.compile(r'[①②③④⑤⑥⑦⑧⑨⑩]\s*([^①②③④⑤⑥⑦⑧⑨⑩。]+)'),
            re.compile(r'[ア-ン][．.]\s*([^ア-ン。]+)'),
            re.compile(r'[ABCD][．.]\s*([^ABCD。]+)'),
        ]
    
    def _init_reference_patterns(self) -> Dict[str, re.Pattern]:
        """参照パターン"""
        return {
            'underline': re.compile(r'下線([①②③④⑤⑥⑦⑧⑨⑩\d]+)'),
            'blank': re.compile(r'空(?:らん|欄|所)\s*[\(（]([①②③④⑤⑥⑦⑧⑨⑩\d]+)[\)）]'),
            'figure': re.compile(r'(?:次の)?図([①②③④⑤⑥⑦⑧⑨⑩\d]*)'),
            'document': re.compile(r'(?:次の)?(?:文章|資料)([①②③④⑤⑥⑦⑧⑨⑩\d]*)'),
        }
    
    def _init_theme_keywords(self) -> Dict[str, List[str]]:
        """テーマ候補となるキーワード"""
        return {
            '歴史': [
                '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
                '平安時代', '鎌倉時代', '室町時代', '戦国時代', '江戸時代',
                '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代',
                '聖徳太子', '織田信長', '豊臣秀吉', '徳川家康',
                '大化の改新', '応仁の乱', '明治維新', '太平洋戦争'
            ],
            '地理': [
                '関東地方', '近畿地方', '東北地方', '九州地方',
                '東京', '大阪', '名古屋', '三大都市圏',
                '人口', '産業', '気候', '地形', '資源'
            ],
            '公民': [
                '日本国憲法', '三権分立', '国会', '内閣', '裁判所',
                '選挙', '参議院', '衆議院', '地方自治',
                '少子高齢化', '社会保障', 'SDGs'
            ]
        }
    
    def parse_problem_structure(self, text: str) -> ProblemStructure:
        """問題文を構造的に分解"""
        structure = ProblemStructure()
        
        # 設問の終わりを探す
        question_end_pos = -1
        for pattern in self.question_end_patterns:
            match = pattern.search(text)
            if match:
                question_end_pos = match.end()
                break
        
        if question_end_pos > 0:
            # 設問部分
            structure.question = text[:question_end_pos].strip()
            
            # 選択肢を抽出
            remaining = text[question_end_pos:].strip()
            choices = []
            for pattern in self.choice_patterns:
                matches = pattern.findall(remaining)
                choices.extend(matches)
            structure.choices = choices if choices else None
            
            # リード文を推測（「について」の前など）
            about_match = re.search(r'^(.+?)(について|に関して)', structure.question)
            if about_match:
                structure.lead_text = about_match.group(1)
        else:
            # 設問パターンが見つからない場合
            structure.question = text
        
        return structure
    
    def extract_theme_from_structure(self, structure: ProblemStructure) -> StructuredTheme:
        """構造化された問題からテーマを抽出"""
        
        # 1. リード文からテーマを探す
        if structure.lead_text:
            theme = self._extract_from_lead(structure.lead_text)
            if theme:
                return StructuredTheme(theme, 0.9, 'lead', self._categorize(theme))
        
        # 2. 設問からテーマを探す
        if structure.question:
            theme = self._extract_from_question(structure.question)
            if theme and theme not in ['空欄補充', '正しい文章を', 'まちがっている文章を']:
                return StructuredTheme(theme, 0.7, 'question', self._categorize(theme))
        
        # 3. 選択肢からテーマを推測
        if structure.choices:
            theme = self._infer_from_choices(structure.choices)
            if theme:
                return StructuredTheme(theme, 0.5, 'choices', self._categorize(theme))
        
        # 4. テーマが見つからない場合はNone
        return StructuredTheme(None, 0.0, 'none', None)
    
    def _extract_from_lead(self, text: str) -> Optional[str]:
        """リード文からテーマを抽出"""
        # 参照表現を除去
        text = re.sub(r'下線[①②③④⑤⑥⑦⑧⑨⑩\d]+', '', text)
        text = re.sub(r'空(?:らん|欄)[（(][①②③④⑤⑥⑦⑧⑨⑩\d]+[）)]', '', text)
        
        # キーワードを探す
        for category, keywords in self.theme_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return keyword
        
        # 固有名詞を抽出
        proper_noun = re.search(r'([ぁ-んァ-ヴー一-龥]{2,10}(?:時代|天皇|将軍|の乱|の戦い|地方|憲法))', text)
        if proper_noun:
            return proper_noun.group(1)
        
        return None
    
    def _extract_from_question(self, text: str) -> Optional[str]:
        """設問からテーマを抽出"""
        # 問題形式の表現を除去
        text = re.sub(r'(?:正しい|まちがっている|適切な)(?:文章|もの)を', '', text)
        text = re.sub(r'次の[ア-ン①-⑩].*?から.*?選', '', text)
        text = re.sub(r'答えなさい|選びなさい|書きなさい', '', text)
        
        # 「〜について」の前の部分を抽出
        about_match = re.search(r'([^。、]{3,20}?)(?:について|に関して)', text)
        if about_match:
            candidate = about_match.group(1)
            # 参照表現でない場合
            if not re.match(r'^(?:下線|空らん|次の図|この)', candidate):
                return candidate
        
        return None
    
    def _infer_from_choices(self, choices: List[str]) -> Optional[str]:
        """選択肢からテーマを推測"""
        if not choices:
            return None
        
        # 共通するカテゴリを探す
        if all('時代' in c for c in choices[:3]):
            return '歴史時代'
        if all(any(p in c for p in ['県', '地方', '市']) for c in choices[:3]):
            return '地域・地名'
        
        # 最初の選択肢から固有名詞を抽出
        for choice in choices[:2]:
            for category, keywords in self.theme_keywords.items():
                for keyword in keywords:
                    if keyword in choice:
                        return keyword
        
        return None
    
    def _categorize(self, theme: str) -> Optional[str]:
        """テーマのカテゴリを判定"""
        if not theme:
            return None
        
        for category, keywords in self.theme_keywords.items():
            for keyword in keywords:
                if keyword in theme:
                    return category
        
        if '時代' in theme:
            return '歴史'
        if '地方' in theme or '都市' in theme:
            return '地理'
        if '憲法' in theme or '選挙' in theme:
            return '公民'
        
        return None
    
    def extract_theme(self, text: str) -> StructuredTheme:
        """メインのテーマ抽出メソッド"""
        # 問題文を構造的に分解
        structure = self.parse_problem_structure(text)
        
        # 構造からテーマを抽出
        return self.extract_theme_from_structure(structure)