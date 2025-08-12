"""
パターン管理モジュール
正規表現パターンの中央管理とキャッシング
"""

from .registry import PatternRegistry
from .year_patterns import YEAR_PATTERNS
from .section_patterns import SECTION_PATTERNS
from .source_patterns import SOURCE_PATTERNS
from .question_patterns import QUESTION_PATTERNS

__all__ = [
    'PatternRegistry',
    'YEAR_PATTERNS',
    'SECTION_PATTERNS', 
    'SOURCE_PATTERNS',
    'QUESTION_PATTERNS'
]