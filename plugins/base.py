"""
プラグインベースクラス - 学校別解析プラグインの基底クラス
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import re

from models import AnalysisResult, Question, Section, ExamSource
from config.settings import Settings


@dataclass
class PluginInfo:
    """プラグイン情報"""
    name: str
    version: str
    school_names: List[str]  # サポートする学校名のリスト
    description: str
    author: str = "Entrance Exam Analyzer Team"
    priority: int = 0  # 優先度（高い値が優先）


class SchoolAnalyzerPlugin(ABC):
    """学校別解析プラグインの基底クラス"""
    
    def __init__(self):
        self.info = self.get_plugin_info()
        self._compile_patterns()
    
    @abstractmethod
    def get_plugin_info(self) -> PluginInfo:
        """プラグイン情報を取得"""
        pass
    
    @abstractmethod
    def get_section_markers(self) -> List[str]:
        """大問マーカーのリストを取得"""
        pass
    
    @abstractmethod
    def get_question_patterns(self) -> Dict[str, List[str]]:
        """設問パターンを取得"""
        pass
    
    @abstractmethod
    def get_source_patterns(self) -> List[str]:
        """出典パターンを取得"""
        pass
    
    def _compile_patterns(self):
        """正規表現パターンをコンパイル"""
        # セクションマーカーをコンパイル
        self.section_pattern = self._create_section_pattern()
        
        # 設問パターンをコンパイル
        self.question_patterns_compiled = {}
        for q_type, patterns in self.get_question_patterns().items():
            self.question_patterns_compiled[q_type] = [
                re.compile(p, re.MULTILINE | re.DOTALL) for p in patterns
            ]
        
        # 出典パターンをコンパイル
        self.source_patterns_compiled = [
            re.compile(p, re.MULTILINE) for p in self.get_source_patterns()
        ]
    
    def _create_section_pattern(self) -> re.Pattern:
        """セクションマーカーの正規表現パターンを作成"""
        markers = self.get_section_markers()
        if not markers:
            return re.compile(r'(?!)')  # マッチしないパターン
        
        # マーカーをエスケープして結合
        escaped_markers = [re.escape(marker) for marker in markers]
        pattern = r'^\s*(' + '|'.join(escaped_markers) + r')\s*$'
        return re.compile(pattern, re.MULTILINE)
    
    def analyze(self, text: str, school_name: str, year: str) -> AnalysisResult:
        """
        テキストを解析
        
        Args:
            text: 解析対象のテキスト
            school_name: 学校名
            year: 年度
        
        Returns:
            解析結果
        """
        # セクションを検出
        sections = self.detect_sections(text)
        
        # 各セクションの設問を検出
        all_questions = []
        for section in sections:
            questions = self.detect_questions(section)
            section.questions = questions
            all_questions.extend(questions)
        
        # 設問タイプを集計
        question_types = self.aggregate_question_types(all_questions)
        
        # 出典を検出
        sources = self.detect_sources(text)
        
        # テーマとジャンルを推定
        theme = self.estimate_theme(text)
        genre = self.estimate_genre(text)
        
        return AnalysisResult(
            school_name=school_name,
            year=year,
            total_characters=len(text),
            sections=sections,
            questions=all_questions,
            question_types=question_types,
            sources=sources,
            theme=theme,
            genre=genre
        )
    
    def detect_sections(self, text: str) -> List[Section]:
        """
        セクション（大問）を検出
        
        Args:
            text: 解析対象のテキスト
        
        Returns:
            セクションのリスト
        """
        sections = []
        matches = list(self.section_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            marker = match.group(1)
            start_pos = match.end()
            
            # 次のセクションマーカーまでをセクションとする
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            # セクションテキストを抽出
            section_text = text[start_pos:end_pos].strip()
            
            # 最小文字数チェック
            if len(section_text) >= Settings.MIN_SECTION_CONTENT:
                section = Section(
                    number=i + 1,
                    marker=marker,
                    text=section_text,
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                sections.append(section)
        
        # セクションが見つからない場合は全体を1つのセクションとする
        if not sections:
            sections.append(Section(
                number=1,
                marker="",
                text=text,
                start_pos=0,
                end_pos=len(text)
            ))
        
        return sections
    
    def detect_questions(self, section: Section) -> List[Question]:
        """
        セクション内の設問を検出
        
        Args:
            section: セクション
        
        Returns:
            設問のリスト
        """
        questions = []
        question_number = 1
        
        # 設問パターンでテキストを検索
        for q_type, patterns in self.question_patterns_compiled.items():
            for pattern in patterns:
                matches = pattern.finditer(section.text or "")
                
                for match in matches:
                    # 文字数制限を抽出
                    char_limit = self._extract_character_limit(match.group())
                    
                    # 選択肢数を抽出
                    choice_count = self._extract_choice_count(match.group())
                    
                    question = Question(
                        number=question_number,
                        text=match.group()[:200],  # 最初の200文字
                        type=q_type,
                        section=section.number,
                        character_limit=char_limit,
                        choice_count=choice_count
                    )
                    questions.append(question)
                    question_number += 1
        
        # 設問番号でソート
        questions.sort(key=lambda q: q.number)
        
        return questions
    
    def detect_sources(self, text: str) -> List[ExamSource]:
        """
        出典を検出
        
        Args:
            text: 解析対象のテキスト
        
        Returns:
            出典のリスト
        """
        sources = []
        
        for pattern in self.source_patterns_compiled:
            matches = pattern.finditer(text)
            
            for match in matches:
                source = self._parse_source(match)
                if source:
                    sources.append(source)
        
        return sources
    
    def _parse_source(self, match: re.Match) -> Optional[ExamSource]:
        """
        マッチから出典情報を解析
        
        Args:
            match: 正規表現マッチ
        
        Returns:
            出典情報、解析失敗時はNone
        """
        try:
            groups = match.groups()
            raw_source = match.group()
            
            # デフォルトの解析（サブクラスでオーバーライド可能）
            source = ExamSource(raw_source=raw_source)
            
            # グループから情報を抽出
            if len(groups) >= 1:
                source.author = groups[0]
            if len(groups) >= 2:
                source.title = groups[1]
            if len(groups) >= 3:
                source.publisher = groups[2]
            
            return source
        except Exception:
            return None
    
    def aggregate_question_types(self, questions: List[Question]) -> Dict[str, int]:
        """
        設問タイプを集計
        
        Args:
            questions: 設問のリスト
        
        Returns:
            タイプ別の設問数
        """
        type_counts = {}
        
        for question in questions:
            if question.type not in type_counts:
                type_counts[question.type] = 0
            type_counts[question.type] += 1
        
        # デフォルトタイプを0で初期化
        for q_type in ['記述', '選択', '漢字・語句', '抜き出し']:
            if q_type not in type_counts:
                type_counts[q_type] = 0
        
        return type_counts
    
    def estimate_theme(self, text: str) -> Optional[str]:
        """
        テーマを推定
        
        Args:
            text: 解析対象のテキスト
        
        Returns:
            推定されたテーマ
        """
        themes = {
            '人間関係・成長': ['友情', '家族', '成長', '青春', '恋愛'],
            '自然・環境': ['自然', '環境', '地球', '生態', '気候'],
            '社会・文化': ['社会', '文化', '歴史', '伝統', '現代'],
            '科学・技術': ['科学', '技術', 'AI', 'ロボット', '宇宙'],
            '哲学・思想': ['哲学', '思想', '生き方', '価値観', '倫理'],
        }
        
        # キーワードマッチングでテーマを推定
        max_count = 0
        estimated_theme = None
        
        for theme, keywords in themes.items():
            count = sum(1 for keyword in keywords if keyword in text)
            if count > max_count:
                max_count = count
                estimated_theme = theme
        
        return estimated_theme
    
    def estimate_genre(self, text: str) -> Optional[str]:
        """
        ジャンルを推定
        
        Args:
            text: 解析対象のテキスト
        
        Returns:
            推定されたジャンル
        """
        genres = {
            '小説・物語': ['物語', '小説', '登場人物', '場面', 'セリフ'],
            '評論・論説': ['論じ', '考察', '主張', '論理', '分析'],
            '随筆・エッセイ': ['随筆', 'エッセイ', '体験', '感想', '日常'],
            '詩・韻文': ['詩', '韻', '比喩', '象徴', 'リズム'],
        }
        
        # キーワードマッチングでジャンルを推定
        max_count = 0
        estimated_genre = None
        
        for genre, keywords in genres.items():
            count = sum(1 for keyword in keywords if keyword in text)
            if count > max_count:
                max_count = count
                estimated_genre = genre
        
        return estimated_genre
    
    def _extract_character_limit(self, text: str) -> Optional[Tuple[int, int]]:
        """設問から文字数制限を抽出"""
        patterns = [
            r'(\d+)字以上(\d+)字以内',
            r'(\d+)〜(\d+)字',
            r'(\d+)字以内',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return (int(groups[0]), int(groups[1]))
                elif len(groups) == 1:
                    limit = int(groups[0])
                    return (0, limit)
        
        return None
    
    def _extract_choice_count(self, text: str) -> Optional[int]:
        """設問から選択肢数を抽出"""
        # ア〜オ形式
        katakana_choices = re.findall(r'[ア-オ]', text)
        if katakana_choices:
            return len(set(katakana_choices))
        
        # A〜E形式
        alpha_choices = re.findall(r'[A-E]', text)
        if alpha_choices:
            return len(set(alpha_choices))
        
        # 1〜5形式
        num_choices = re.findall(r'[1-5]', text)
        if len(num_choices) >= 3:
            return len(set(num_choices))
        
        return None
    
    def supports_school(self, school_name: str) -> bool:
        """
        指定された学校をサポートしているかチェック
        
        Args:
            school_name: 学校名
        
        Returns:
            サポートしている場合True
        """
        return school_name in self.info.school_names