"""
統合テキスト処理エンジン
全てのテキスト処理機能を一元化
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from patterns.recognition_patterns import (
    extract_sections,
    extract_questions,
    extract_source_info,
    extract_year,
    QUESTION_CONFIG,
    SECTION_CONFIG
)
from core.config import get_config

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """設問タイプの列挙型"""
    CHOICE = "選択"
    DESCRIPTION = "記述"
    EXTRACT = "抜き出し"
    KANJI = "漢字・語句"
    BLANK = "空欄補充"
    OTHER = "その他"


@dataclass
class Question:
    """設問情報"""
    number: int
    type: QuestionType
    text: str
    position: Tuple[int, int]
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Section:
    """セクション（大問）情報"""
    number: int
    title: Optional[str]
    source: Optional[Dict[str, str]]
    questions: List[Question]
    text: str
    position: Tuple[int, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedText:
    """処理済みテキスト"""
    original_text: str
    sections: List[Section]
    total_characters: int
    total_questions: int
    question_type_counts: Dict[QuestionType, int]
    year: Optional[int]
    school: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextEngine:
    """統合テキスト処理エンジン"""
    
    def __init__(self, config=None):
        """
        初期化
        
        Args:
            config: 設定オブジェクト（省略時はグローバル設定を使用）
        """
        self.config = config or get_config()
        self._compiled_patterns = {}
        self._cache = {}
        
    def process_text(
        self,
        text: str,
        filename: Optional[str] = None,
        school: Optional[str] = None,
        year: Optional[int] = None
    ) -> ProcessedText:
        """
        テキストを処理して構造化データを生成
        
        Args:
            text: 処理対象のテキスト
            filename: ファイル名（年度抽出に使用）
            school: 学校名（省略時は自動検出）
            year: 年度（省略時は自動検出）
            
        Returns:
            処理済みテキスト
        """
        # キャッシュチェック
        cache_key = self._generate_cache_key(text, filename, school, year)
        if self.config.processing.cache_enabled and cache_key in self._cache:
            logger.debug(f"キャッシュヒット: {cache_key[:20]}...")
            return self._cache[cache_key]
        
        # 基本情報の抽出
        if year is None:
            year = extract_year(text, filename or '')
        
        if school is None:
            school = self._detect_school(text, filename)
        
        # セクション分割
        sections_data = extract_sections(text)
        sections = []
        
        # 各セクションを処理
        for i, section_data in enumerate(sections_data):
            section_text = self._extract_section_text(text, section_data)
            
            # 出典情報抽出
            source_info = self._extract_source_for_section(section_text)
            
            # 設問抽出
            questions = self._extract_questions_for_section(section_text, section_data['position'][0])
            
            section = Section(
                number=section_data.get('section_number', i + 1),
                title=self._generate_section_title(section_data, source_info),
                source=source_info,
                questions=questions,
                text=section_text,
                position=section_data['position'],
                metadata=section_data
            )
            sections.append(section)
        
        # セクションが見つからない場合は全体を1セクションとして扱う
        if not sections:
            questions = self._extract_questions_for_section(text, 0)
            source_info = self._extract_source_for_section(text)
            
            sections.append(Section(
                number=1,
                title="本文",
                source=source_info,
                questions=questions,
                text=text,
                position=(0, len(text)),
                metadata={}
            ))
        
        # 統計情報の計算
        total_questions = sum(len(s.questions) for s in sections)
        question_type_counts = self._count_question_types(sections)
        total_characters = len(text.replace(' ', '').replace('\n', ''))
        
        result = ProcessedText(
            original_text=text,
            sections=sections,
            total_characters=total_characters,
            total_questions=total_questions,
            question_type_counts=question_type_counts,
            year=year,
            school=school,
            metadata={
                'filename': filename,
                'processing_version': '2.0'
            }
        )
        
        # キャッシュに保存
        if self.config.processing.cache_enabled:
            self._cache[cache_key] = result
        
        return result
    
    def _detect_school(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """学校名を検出"""
        # ファイル名から検出
        if filename:
            for pattern, school_name in self.config.school.patterns.items():
                if re.search(pattern, filename, re.IGNORECASE):
                    return school_name
        
        # テキストから検出
        for pattern, school_name in self.config.school.patterns.items():
            if re.search(pattern, text[:1000], re.IGNORECASE):  # 最初の1000文字をチェック
                return school_name
        
        return None
    
    def _extract_section_text(self, text: str, section_data: Dict) -> str:
        """セクションのテキストを抽出"""
        start, end = section_data['position']
        
        # 次のセクションまでのテキストを取得
        if end > len(text):
            end = len(text)
        
        return text[start:end].strip()
    
    def _extract_source_for_section(self, section_text: str) -> Optional[Dict[str, str]]:
        """セクションの出典情報を抽出"""
        sources = extract_source_info(section_text)
        
        if sources:
            # 最も優先度の高い出典を選択
            best_source = sources[0]
            result = {
                'raw_text': best_source.get('raw_text', ''),
                'pattern': best_source.get('pattern', '')
            }
            
            # 著者・タイトル・雑誌情報を追加
            for key in ['author', 'title', 'magazine']:
                if key in best_source:
                    result[key] = best_source[key]
            
            return result
        
        return None
    
    def _extract_questions_for_section(self, section_text: str, base_position: int) -> List[Question]:
        """セクション内の設問を抽出"""
        questions_data = extract_questions(section_text)
        questions = []
        
        for i, q_data in enumerate(questions_data):
            # 設問タイプを判定
            q_type = self._determine_question_type(q_data)
            
            # 設問番号を取得
            q_number = q_data.get('question_number', i + 1)
            if isinstance(q_number, str):
                try:
                    q_number = int(q_number)
                except ValueError:
                    q_number = i + 1
            
            # 位置を調整（セクションの開始位置を加算）
            position = (
                q_data['position'][0] + base_position,
                q_data['position'][1] + base_position
            )
            
            question = Question(
                number=q_number,
                type=q_type,
                text=q_data.get('raw_text', ''),
                position=position,
                confidence=self._calculate_confidence(q_data),
                metadata=q_data
            )
            questions.append(question)
        
        return questions
    
    def _determine_question_type(self, question_data: Dict) -> QuestionType:
        """設問タイプを判定"""
        q_type = question_data.get('type', 'other')
        
        type_mapping = {
            'choice': QuestionType.CHOICE,
            'description': QuestionType.DESCRIPTION,
            'extract': QuestionType.EXTRACT,
            'kanji': QuestionType.KANJI,
            'blank': QuestionType.BLANK,
            'vocabulary': QuestionType.KANJI,
        }
        
        return type_mapping.get(q_type, QuestionType.OTHER)
    
    def _calculate_confidence(self, data: Dict) -> float:
        """信頼度を計算"""
        # 優先度やパターンマッチの強さから信頼度を計算
        priority = data.get('priority', 0)
        if priority >= 10:
            return 1.0
        elif priority >= 7:
            return 0.9
        elif priority >= 5:
            return 0.8
        else:
            return 0.7
    
    def _generate_section_title(self, section_data: Dict, source_info: Optional[Dict]) -> str:
        """セクションタイトルを生成"""
        # セクション番号
        section_number = section_data.get('section_number', '')
        
        # 出典情報からタイトル生成
        if source_info:
            if 'title' in source_info:
                title = source_info['title']
                if 'author' in source_info:
                    return f"第{section_number}問 - {source_info['author']}『{title}』"
                return f"第{section_number}問 - 『{title}』"
        
        # デフォルトタイトル
        if section_number:
            return f"第{section_number}問"
        
        return "本文"
    
    def _count_question_types(self, sections: List[Section]) -> Dict[QuestionType, int]:
        """設問タイプごとの数を集計"""
        counts = {q_type: 0 for q_type in QuestionType}
        
        for section in sections:
            for question in section.questions:
                counts[question.type] += 1
        
        return counts
    
    def _generate_cache_key(self, text: str, filename: Optional[str], school: Optional[str], year: Optional[int]) -> str:
        """キャッシュキーを生成"""
        import hashlib
        
        key_parts = [
            text[:100],  # テキストの先頭100文字
            filename or '',
            school or '',
            str(year) if year else ''
        ]
        key_str = '|'.join(key_parts)
        
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def format_for_display(self, processed_text: ProcessedText) -> str:
        """処理済みテキストを表示用にフォーマット"""
        lines = []
        
        # ヘッダー情報
        lines.append("=" * 60)
        if processed_text.school:
            lines.append(f"学校: {processed_text.school}")
        if processed_text.year:
            lines.append(f"年度: {processed_text.year}年")
        lines.append(f"総文字数: {processed_text.total_characters:,}文字")
        lines.append(f"総設問数: {processed_text.total_questions}問")
        lines.append("")
        
        # 設問タイプ別集計
        lines.append("【設問タイプ別集計】")
        for q_type, count in processed_text.question_type_counts.items():
            if count > 0:
                lines.append(f"  {q_type.value}: {count}問")
        lines.append("")
        
        # セクション情報
        lines.append("【セクション構成】")
        for section in processed_text.sections:
            lines.append(f"\n{section.title}")
            lines.append("-" * 40)
            
            # 出典情報
            if section.source:
                if 'author' in section.source and 'title' in section.source:
                    lines.append(f"出典: {section.source['author']}『{section.source['title']}』")
                elif 'title' in section.source:
                    lines.append(f"出典: 『{section.source['title']}』")
            
            # 設問情報
            lines.append(f"設問数: {len(section.questions)}問")
            
            # 設問タイプの内訳
            type_counts = {}
            for q in section.questions:
                type_counts[q.type.value] = type_counts.get(q.type.value, 0) + 1
            
            if type_counts:
                lines.append("内訳: " + ", ".join(f"{t}: {c}問" for t, c in type_counts.items()))
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def export_to_dict(self, processed_text: ProcessedText) -> Dict[str, Any]:
        """処理済みテキストを辞書形式でエクスポート"""
        return {
            'school': processed_text.school,
            'year': processed_text.year,
            'total_characters': processed_text.total_characters,
            'total_questions': processed_text.total_questions,
            'question_types': {
                q_type.value: count 
                for q_type, count in processed_text.question_type_counts.items()
            },
            'sections': [
                {
                    'number': section.number,
                    'title': section.title,
                    'source': section.source,
                    'question_count': len(section.questions),
                    'questions': [
                        {
                            'number': q.number,
                            'type': q.type.value,
                            'confidence': q.confidence
                        }
                        for q in section.questions
                    ]
                }
                for section in processed_text.sections
            ],
            'metadata': processed_text.metadata
        }


# 後方互換性のためのエイリアス
class TextAnalyzer(TextEngine):
    """後方互換性のためのエイリアス"""
    pass


class FinalContentExtractor(TextEngine):
    """後方互換性のためのエイリアス"""
    
    def extract_all_content(self, text: str) -> Dict[str, Any]:
        """後方互換性のためのメソッド"""
        processed = self.process_text(text)
        return self.export_to_dict(processed)


class ContentExtractor(TextEngine):
    """後方互換性のためのエイリアス"""
    
    def extract_content(self, text: str) -> Dict[str, Any]:
        """後方互換性のためのメソッド"""
        processed = self.process_text(text)
        return self.export_to_dict(processed)