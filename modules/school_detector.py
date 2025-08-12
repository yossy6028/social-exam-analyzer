"""
学校名検出モジュール - テキストから学校名を検出
"""
import re
from typing import Optional, List, Tuple, Dict
from pathlib import Path
from dataclasses import dataclass

from config.settings import Settings
from exceptions import SchoolDetectionError
from utils.text_utils import normalize_text


@dataclass
class SchoolPattern:
    """学校パターンの定義"""
    pattern: str
    full_name: str
    aliases: List[str]
    priority: int = 0


class SchoolDetector:
    """学校名検出クラス"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self._compile_patterns()
    
    def _initialize_patterns(self) -> List[SchoolPattern]:
        """学校パターンを初期化"""
        patterns = []
        
        # Settings.SCHOOL_PATTERNSから自動生成
        for pattern_str, full_name in Settings.SCHOOL_PATTERNS.items():
            # 優先度を設定（より具体的なパターンほど高優先度）
            priority = 10
            if '|' in pattern_str:
                priority = 8  # 複数のエイリアスがある場合
            elif len(pattern_str) <= 2:
                priority = 5  # 短い名前は優先度低
            
            # エイリアスを抽出
            aliases = []
            if '|' in pattern_str:
                aliases = pattern_str.split('|')
            else:
                aliases = [pattern_str]
            
            patterns.append(SchoolPattern(
                pattern=pattern_str,
                full_name=full_name,
                aliases=aliases,
                priority=priority
            ))
        
        return patterns
    
    def _compile_patterns(self):
        """正規表現パターンをコンパイル"""
        for pattern_obj in self.patterns:
            pattern_obj.compiled = re.compile(pattern_obj.pattern, re.IGNORECASE)
    
    def detect_school(self, text: str, file_path: Optional[Path] = None) -> Tuple[str, float]:
        """
        テキストから学校名を検出
        
        Args:
            text: 検出対象のテキスト
            file_path: ファイルパス（ファイル名からも学校名を推測）
        
        Returns:
            (学校名, 信頼度) のタプル
        
        Raises:
            SchoolDetectionError: 学校名が検出できない場合
        """
        candidates = {}
        
        # ファイル名から検出
        if file_path:
            file_candidates = self._detect_from_filename(file_path)
            for school, score in file_candidates.items():
                candidates[school] = candidates.get(school, 0) + score
        
        # テキストから検出
        text_candidates = self._detect_from_text(text)
        for school, score in text_candidates.items():
            candidates[school] = candidates.get(school, 0) + score
        
        if not candidates:
            raise SchoolDetectionError(text[:200])
        
        # 最も信頼度の高い学校を選択
        best_school = max(candidates.items(), key=lambda x: x[1])
        school_name = best_school[0]
        
        # 信頼度を0-1の範囲に正規化
        confidence = min(best_school[1] / 10.0, 1.0)
        
        return school_name, confidence
    
    def _detect_from_filename(self, file_path: Path) -> Dict[str, float]:
        """ファイル名から学校名を検出"""
        candidates = {}
        filename = file_path.name
        
        # ディレクトリ名も考慮
        path_parts = [filename]
        if file_path.parent:
            path_parts.append(file_path.parent.name)
        
        for part in path_parts:
            for pattern_obj in sorted(self.patterns, key=lambda x: x.priority, reverse=True):
                if pattern_obj.compiled.search(part):
                    score = pattern_obj.priority
                    
                    # ディレクトリ名の場合はスコアを少し下げる
                    if part != filename:
                        score *= 0.8
                    
                    candidates[pattern_obj.full_name] = candidates.get(
                        pattern_obj.full_name, 0
                    ) + score
        
        return candidates
    
    def _detect_from_text(self, text: str) -> Dict[str, float]:
        """テキスト本文から学校名を検出"""
        candidates = {}
        
        # 最初の1000文字を重点的に検索
        header_text = text[:1000]
        body_text = text[1000:5000] if len(text) > 1000 else ""
        
        for pattern_obj in sorted(self.patterns, key=lambda x: x.priority, reverse=True):
            # ヘッダー部分での出現
            header_matches = pattern_obj.compiled.findall(header_text)
            if header_matches:
                score = pattern_obj.priority * len(header_matches) * 2  # ヘッダーは重み付け
                candidates[pattern_obj.full_name] = candidates.get(
                    pattern_obj.full_name, 0
                ) + score
            
            # 本文での出現
            if body_text:
                body_matches = pattern_obj.compiled.findall(body_text)
                if body_matches:
                    score = pattern_obj.priority * min(len(body_matches), 3)  # 本文は最大3回まで
                    candidates[pattern_obj.full_name] = candidates.get(
                        pattern_obj.full_name, 0
                    ) + score
        
        return candidates
    
    def get_school_specific_patterns(self, school_name: str) -> Dict[str, any]:
        """
        学校固有のパターンを取得
        
        Args:
            school_name: 学校名
        
        Returns:
            学校固有の設定辞書
        """
        # 学校名を正規化
        school_key = None
        for pattern_obj in self.patterns:
            if pattern_obj.full_name == school_name:
                # 最初のエイリアスをキーとして使用
                school_key = pattern_obj.aliases[0] if pattern_obj.aliases else None
                break
        
        # 学校固有の設定
        specific_patterns = {
            '武蔵': {
                'source_pattern': 'musashi',
                'section_markers': ['一', '二', '三', '四', '五'],
                'question_style': 'traditional',
                'typical_sections': 2,
            },
            '開成': {
                'source_pattern': 'default',
                'section_markers': ['一', '二', '三', '四'],
                'question_style': 'numbered',
                'typical_sections': 3,
            },
            '桜蔭': {
                'source_pattern': 'default',
                'section_markers': ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ'],
                'question_style': 'mixed',
                'typical_sections': 3,
            },
            '麻布': {
                'source_pattern': 'default',
                'section_markers': ['一', '二', '三'],
                'question_style': 'descriptive',
                'typical_sections': 1,
            },
            '渋谷': {
                'source_pattern': 'default',
                'section_markers': ['１', '２', '３', '４'],
                'question_style': 'modern',
                'typical_sections': 3,
            },
        }
        
        # デフォルト設定
        default_patterns = {
            'source_pattern': 'default',
            'section_markers': ['一', '二', '三', '四', '五'],
            'question_style': 'standard',
            'typical_sections': 2,
        }
        
        # 学校固有の設定があれば返す、なければデフォルト
        for key, patterns in specific_patterns.items():
            if school_key and key in school_key:
                return patterns
        
        return default_patterns
    
    def normalize_school_name(self, school_name: str) -> str:
        """
        学校名を正規化（正式名称に統一）
        
        Args:
            school_name: 正規化対象の学校名
        
        Returns:
            正式な学校名
        """
        normalized = normalize_text(school_name)
        
        # パターンマッチングで正式名称を見つける
        for pattern_obj in self.patterns:
            if pattern_obj.compiled.search(normalized):
                return pattern_obj.full_name
        
        # マッチしない場合は入力をそのまま返す
        return school_name
    
    def get_all_school_names(self) -> List[str]:
        """
        登録されているすべての学校名を取得
        
        Returns:
            学校名のリスト
        """
        return [p.full_name for p in self.patterns]
    
    def is_known_school(self, school_name: str) -> bool:
        """
        既知の学校かチェック
        
        Args:
            school_name: チェック対象の学校名
        
        Returns:
            既知の学校の場合True
        """
        normalized = normalize_text(school_name)
        
        for pattern_obj in self.patterns:
            if pattern_obj.compiled.search(normalized):
                return True
            if pattern_obj.full_name == school_name:
                return True
        
        return False