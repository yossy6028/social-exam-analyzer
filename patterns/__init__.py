"""
パターン管理モジュール
正規表現パターンの中央管理とキャッシング
"""

from .registry import PatternRegistry
from .recognition_patterns import (
    YEAR_PATTERNS,
    SECTION_PATTERNS,
    SOURCE_PATTERNS,
    QUESTION_PATTERNS,
    QUESTION_CONFIG,
    SECTION_CONFIG,
    SOURCE_CONFIG,
    YEAR_CONFIG,
    QUESTION_NUMBER_MAP,
    SECTION_NUMBER_MAP
)

__all__ = [
    'PatternRegistry',
    'YEAR_PATTERNS',
    'SECTION_PATTERNS', 
    'SOURCE_PATTERNS',
    'QUESTION_PATTERNS',
    'QUESTION_CONFIG',
    'SECTION_CONFIG',
    'SOURCE_CONFIG',
    'YEAR_CONFIG',
    'QUESTION_NUMBER_MAP',
    'SECTION_NUMBER_MAP'
]