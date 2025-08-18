"""
統合社会科問題分析モジュール
social_analyzer.py, social_analyzer_fixed.py, social_analyzer_improved.pyを統合
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class SocialField(Enum):
    """社会科分野"""
    GEOGRAPHY = "地理"
    HISTORY = "歴史"
    CIVICS = "公民"
    CURRENT_AFFAIRS = "時事問題"
    MIXED = "総合"


class ResourceType(Enum):
    """資料タイプ"""
    MAP = "地図"
    GRAPH = "グラフ"
    TIMELINE = "年表"
    TABLE = "表"
    PHOTO = "写真"
    DOCUMENT = "文書"
    OTHER = "その他"


class QuestionFormat(Enum):
    """出題形式"""
    SHORT_ANSWER = "短答式"
    MULTIPLE_CHOICE = "記号選択"
    DESCRIPTIVE = "記述式"
    FILL_IN_BLANK = "穴埋め"
    TRUE_FALSE = "正誤判定"
    COMBINATION = "組み合わせ"
    OTHER = "その他"


@dataclass
class SocialQuestion:
    """社会科問題"""
    number: str
    text: str
    field: SocialField
    resource_types: List[ResourceType] = field(default_factory=list)
    question_format: QuestionFormat = QuestionFormat.OTHER
    is_current_affairs: bool = False
    time_period: Optional[str] = None
    region: Optional[str] = None
    topic: Optional[str] = None
    theme: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    hierarchy_id: Optional[str] = None
    original_text: Optional[str] = None


class UnifiedSocialAnalyzer:
    """統合社会科問題分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.questions: List[SocialQuestion] = []
        self.raw_text = ""
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """パターンの初期化（統合版）"""
        # 分野パターン
        self.field_patterns = {
            SocialField.GEOGRAPHY: [
                r'地図', r'地形', r'気候', r'産業', r'人口', r'都市',
                r'農業', r'工業', r'貿易', r'資源', r'環境', r'地域',
                r'都道府県', r'国土', r'自然', r'災害', r'交通'
            ],
            SocialField.HISTORY: [
                r'時代', r'歴史', r'年号', r'人物', r'事件', r'戦争',
                r'条約', r'改革', r'文化', r'江戸', r'明治', r'昭和',
                r'平成', r'令和', r'幕府', r'朝廷', r'武士'
            ],
            SocialField.CIVICS: [
                r'憲法', r'法律', r'政治', r'選挙', r'国会', r'内閣',
                r'裁判', r'権利', r'義務', r'民主', r'自由', r'平等',
                r'経済', r'税金', r'社会保障', r'国際'
            ],
            SocialField.CURRENT_AFFAIRS: [
                r'SDGs', r'コロナ', r'パンデミック', r'温暖化', r'AI',
                r'デジタル', r'少子高齢', r'働き方', r'ウクライナ',
                r'環境問題', r'再生可能エネルギー'
            ]
        }
        
        # 問題パターン（改善版）
        self.question_patterns = [
            # 大問パターン
            (r'(?:^|\n)\s*([1-9]|[一二三四五六七八九十])\s*[．.]', 'major'),
            (r'(?:^|\n)\s*第\s*([1-9]|[一二三四五六七八九十])\s*問', 'major'),
            (r'(?:^|\n)\s*大問\s*([1-9])', 'major'),
            # 小問パターン
            (r'問\s*([1-9]\d*|[一二三四五六七八九十]+)', 'minor'),
            (r'\(([1-9]\d*)\)', 'minor'),
            (r'［([1-9]\d*)］', 'minor')
        ]
    
    def analyze_text(self, text: str) -> List[SocialQuestion]:
        """
        テキストを分析
        
        Args:
            text: 分析対象のテキスト
            
        Returns:
            分析された問題のリスト
        """
        self.raw_text = text
        self.questions = []
        
        # 問題を抽出
        questions_data = self._extract_questions(text)
        
        # 各問題を分析
        for q_data in questions_data:
            question = self._analyze_question(q_data)
            if question:
                self.questions.append(question)
        
        # 重複除去と正規化
        self._normalize_questions()
        
        return self.questions
    
    def _extract_questions(self, text: str) -> List[Dict[str, Any]]:
        """問題を抽出"""
        questions = []
        lines = text.split('\n')
        
        current_major = None
        current_text = []
        
        for i, line in enumerate(lines):
            # 大問の検出
            for pattern, q_type in self.question_patterns:
                if q_type == 'major':
                    match = re.search(pattern, line)
                    if match:
                        if current_text and current_major:
                            # 前の大問を保存
                            questions.append({
                                'number': current_major,
                                'text': '\n'.join(current_text),
                                'type': 'major'
                            })
                        current_major = f"大問{match.group(1)}"
                        current_text = [line]
                        break
            else:
                # 小問の検出
                if current_major:
                    for pattern, q_type in self.question_patterns:
                        if q_type == 'minor':
                            match = re.search(pattern, line)
                            if match:
                                questions.append({
                                    'number': f"{current_major}-問{match.group(1)}",
                                    'text': line,
                                    'type': 'minor'
                                })
                                break
                    else:
                        current_text.append(line)
        
        # 最後の大問を保存
        if current_text and current_major:
            questions.append({
                'number': current_major,
                'text': '\n'.join(current_text),
                'type': 'major'
            })
        
        return questions
    
    def _analyze_question(self, q_data: Dict[str, Any]) -> Optional[SocialQuestion]:
        """個別の問題を分析"""
        try:
            # 分野を判定
            field = self._determine_field(q_data['text'])
            
            # 資料タイプを判定
            resource_types = self._detect_resources(q_data['text'])
            
            # 出題形式を判定
            question_format = self._detect_format(q_data['text'])
            
            # キーワード抽出
            keywords = self._extract_keywords(q_data['text'], field)
            
            # テーマ抽出
            theme = self._extract_theme(q_data['text'], field)
            
            return SocialQuestion(
                number=q_data['number'],
                text=q_data['text'][:500],  # 最初の500文字
                field=field,
                resource_types=resource_types,
                question_format=question_format,
                keywords=keywords[:5],  # 最大5個
                theme=theme,
                original_text=q_data['text']
            )
            
        except Exception as e:
            logger.warning(f"問題分析エラー: {e}")
            return None
    
    def _determine_field(self, text: str) -> SocialField:
        """分野を判定"""
        scores = {}
        
        for field, patterns in self.field_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            scores[field] = score
        
        # 最高スコアの分野を返す
        if scores:
            max_field = max(scores.items(), key=lambda x: x[1])
            if max_field[1] > 0:
                return max_field[0]
        
        return SocialField.MIXED
    
    def _detect_resources(self, text: str) -> List[ResourceType]:
        """資料タイプを検出"""
        resources = []
        
        resource_patterns = {
            ResourceType.MAP: r'地図|地形図',
            ResourceType.GRAPH: r'グラフ|図表',
            ResourceType.TIMELINE: r'年表|年代',
            ResourceType.TABLE: r'表\d+|資料.?表',
            ResourceType.PHOTO: r'写真|画像',
            ResourceType.DOCUMENT: r'文書|資料.?文'
        }
        
        for resource_type, pattern in resource_patterns.items():
            if re.search(pattern, text):
                resources.append(resource_type)
        
        return resources
    
    def _detect_format(self, text: str) -> QuestionFormat:
        """出題形式を検出"""
        format_patterns = {
            QuestionFormat.SHORT_ANSWER: r'答えなさい|書きなさい|何ですか',
            QuestionFormat.MULTIPLE_CHOICE: r'選びなさい|選択|ア\s*イ\s*ウ',
            QuestionFormat.DESCRIPTIVE: r'説明しなさい|述べなさい|論じなさい',
            QuestionFormat.FILL_IN_BLANK: r'空欄|［\s*］|（\s*）に',
            QuestionFormat.TRUE_FALSE: r'正しい|誤り|正誤',
            QuestionFormat.COMBINATION: r'組み合わせ|結びつけ'
        }
        
        for q_format, pattern in format_patterns.items():
            if re.search(pattern, text):
                return q_format
        
        return QuestionFormat.OTHER
    
    def _extract_keywords(self, text: str, field: SocialField) -> List[str]:
        """キーワードを抽出"""
        keywords = []
        
        # 分野別の重要語句パターン
        if field == SocialField.GEOGRAPHY:
            patterns = [r'[東西南北]?[ァ-ヴー]+平野', r'[ァ-ヴー]+山脈', r'[ァ-ヴー]+川']
        elif field == SocialField.HISTORY:
            patterns = [r'\d+年', r'[ァ-ヴー]+時代', r'[ァ-ヴー]+の乱']
        elif field == SocialField.CIVICS:
            patterns = [r'第\d+条', r'基本的[ァ-ヴー]+', r'[ァ-ヴー]+権']
        else:
            patterns = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        # 重複を除去
        return list(dict.fromkeys(keywords))
    
    def _extract_theme(self, text: str, field: SocialField) -> Optional[str]:
        """テーマを抽出"""
        # 簡易的なテーマ抽出
        if field == SocialField.GEOGRAPHY:
            if '農業' in text:
                return '日本の農業'
            elif '工業' in text:
                return '日本の工業'
            elif '気候' in text:
                return '日本の気候'
        elif field == SocialField.HISTORY:
            if '江戸' in text:
                return '江戸時代'
            elif '明治' in text:
                return '明治時代'
            elif '戦争' in text:
                return '戦争と平和'
        elif field == SocialField.CIVICS:
            if '憲法' in text:
                return '日本国憲法'
            elif '選挙' in text:
                return '選挙制度'
            elif '国会' in text:
                return '国会のしくみ'
        
        return None
    
    def _normalize_questions(self):
        """問題番号の正規化と重複除去"""
        # 番号でソート
        self.questions.sort(key=lambda q: (
            self._extract_major_number(q.number),
            self._extract_minor_number(q.number)
        ))
        
        # 重複除去
        seen = set()
        unique_questions = []
        
        for q in self.questions:
            if q.number not in seen:
                seen.add(q.number)
                unique_questions.append(q)
        
        self.questions = unique_questions
    
    def _extract_major_number(self, number: str) -> int:
        """大問番号を抽出"""
        match = re.search(r'大問(\d+)', number)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_minor_number(self, number: str) -> int:
        """小問番号を抽出"""
        match = re.search(r'問(\d+)', number)
        if match:
            return int(match.group(1))
        return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        if not self.questions:
            return {}
        
        field_counts = {}
        format_counts = {}
        resource_counts = {}
        
        for q in self.questions:
            # 分野
            field_counts[q.field.value] = field_counts.get(q.field.value, 0) + 1
            
            # 形式
            format_counts[q.question_format.value] = format_counts.get(q.question_format.value, 0) + 1
            
            # 資料
            for resource in q.resource_types:
                resource_counts[resource.value] = resource_counts.get(resource.value, 0) + 1
        
        return {
            'total_questions': len(self.questions),
            'field_distribution': field_counts,
            'format_distribution': format_counts,
            'resource_distribution': resource_counts
        }