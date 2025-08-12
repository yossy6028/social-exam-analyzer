"""
パターンレジストリ - 正規表現パターンの中央管理とキャッシング
"""
import re
import threading
from typing import Dict, Optional, Pattern, Any
import logging

logger = logging.getLogger(__name__)


class PatternRegistry:
    """
    シングルトンパターンレジストリ
    すべての正規表現パターンを中央管理し、コンパイル済みパターンをキャッシュ
    """
    
    _instance = None
    _lock = threading.Lock()  # スレッドセーフ用のロック
    _compiled_patterns: Dict[str, Pattern] = {}
    _pattern_definitions: Dict[str, str] = {}
    _pattern_flags: Dict[str, int] = {}
    
    def __new__(cls):
        # ダブルチェックロッキングパターンでスレッドセーフを保証
        if cls._instance is None:
            with cls._lock:
                # ロック取得後に再度チェック
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_all_patterns()
    
    def _load_all_patterns(self):
        """すべてのパターン定義を読み込み"""
        from . import year_patterns, section_patterns, source_patterns, question_patterns
        
        # 年度パターン
        self._register_patterns('year', year_patterns.YEAR_PATTERNS)
        
        # セクションパターン
        self._register_patterns('section', section_patterns.SECTION_PATTERNS)
        
        # 出典パターン
        self._register_patterns('source', source_patterns.SOURCE_PATTERNS)
        
        # 設問パターン
        self._register_patterns('question', question_patterns.QUESTION_PATTERNS)
        
        logger.info(f"Loaded {len(self._pattern_definitions)} pattern definitions")
    
    def _register_patterns(self, category: str, patterns: Dict[str, Any]):
        """カテゴリごとのパターンを登録"""
        for name, pattern_def in patterns.items():
            full_name = f"{category}.{name}"
            
            if isinstance(pattern_def, dict):
                # 辞書形式の場合（pattern, flags）
                self._pattern_definitions[full_name] = pattern_def['pattern']
                self._pattern_flags[full_name] = pattern_def.get('flags', 0)
            else:
                # 文字列形式の場合
                self._pattern_definitions[full_name] = pattern_def
                self._pattern_flags[full_name] = 0
    
    def get_pattern(self, pattern_name: str, flags: int = 0) -> Pattern:
        """
        コンパイル済みパターンを取得（キャッシュ付き）
        
        Args:
            pattern_name: パターン名（例: 'year.kanji', 'section.major_marker'）
            flags: 追加の正規表現フラグ
            
        Returns:
            コンパイル済みのPatternオブジェクト
        """
        cache_key = f"{pattern_name}:{flags}"
        
        if cache_key not in self._compiled_patterns:
            if pattern_name not in self._pattern_definitions:
                raise ValueError(f"Pattern '{pattern_name}' not found in registry")
            
            pattern_str = self._pattern_definitions[pattern_name]
            combined_flags = self._pattern_flags.get(pattern_name, 0) | flags
            
            try:
                self._compiled_patterns[cache_key] = re.compile(pattern_str, combined_flags)
                logger.debug(f"Compiled pattern '{pattern_name}' with flags {combined_flags}")
            except re.error as e:
                logger.error(f"Failed to compile pattern '{pattern_name}': {e}")
                # 重要なパターンの場合はフォールバックを試みる
                if self._is_critical_pattern(pattern_name):
                    fallback = self._get_fallback_pattern(pattern_name)
                    if fallback:
                        try:
                            self._compiled_patterns[cache_key] = re.compile(fallback, 0)
                            logger.warning(f"Using fallback pattern for '{pattern_name}'")
                        except re.error:
                            raise ValueError(f"Critical pattern '{pattern_name}' failed to compile")
                    else:
                        raise ValueError(f"No fallback for critical pattern '{pattern_name}'")
                else:
                    # 非重要パターンは元のエラーを再発生
                    raise
        
        return self._compiled_patterns[cache_key]
    
    def get_raw_pattern(self, pattern_name: str) -> str:
        """
        生のパターン文字列を取得
        
        Args:
            pattern_name: パターン名
            
        Returns:
            パターン文字列
        """
        if pattern_name not in self._pattern_definitions:
            raise ValueError(f"Pattern '{pattern_name}' not found in registry")
        return self._pattern_definitions[pattern_name]
    
    def search(self, pattern_name: str, text: str, flags: int = 0) -> Optional[re.Match]:
        """
        パターンで検索を実行
        
        Args:
            pattern_name: パターン名
            text: 検索対象テキスト
            flags: 追加の正規表現フラグ
            
        Returns:
            Matchオブジェクトまたはなし
        """
        pattern = self.get_pattern(pattern_name, flags)
        return pattern.search(text)
    
    def findall(self, pattern_name: str, text: str, flags: int = 0) -> list:
        """
        パターンですべての一致を検索
        
        Args:
            pattern_name: パターン名
            text: 検索対象テキスト
            flags: 追加の正規表現フラグ
            
        Returns:
            一致のリスト
        """
        pattern = self.get_pattern(pattern_name, flags)
        return pattern.findall(text)
    
    def finditer(self, pattern_name: str, text: str, flags: int = 0):
        """
        パターンですべての一致をイテレータで取得
        
        Args:
            pattern_name: パターン名
            text: 検索対象テキスト
            flags: 追加の正規表現フラグ
            
        Returns:
            Matchオブジェクトのイテレータ
        """
        pattern = self.get_pattern(pattern_name, flags)
        return pattern.finditer(text)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._compiled_patterns.clear()
        logger.info("Pattern cache cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """統計情報を取得"""
        return {
            'definitions': len(self._pattern_definitions),
            'cached': len(self._compiled_patterns),
            'categories': len(set(name.split('.')[0] for name in self._pattern_definitions))
        }
    
    def _is_critical_pattern(self, pattern_name: str) -> bool:
        """
        重要なパターンかどうかを判定
        
        Args:
            pattern_name: パターン名
            
        Returns:
            重要なパターンの場合True
        """
        # 重要なパターンのリスト
        critical_patterns = [
            'year.year_4digit',  # 4桁年度
            'year.kanji',  # 漢数字年度
            'section.kanji_comma_next',  # セクションマーカー
            'source.author_title_niyoru',  # 基本的な出典パターン
        ]
        return pattern_name in critical_patterns
    
    def _get_fallback_pattern(self, pattern_name: str) -> Optional[str]:
        """
        フォールバックパターンを取得
        
        Args:
            pattern_name: パターン名
            
        Returns:
            フォールバックパターン文字列、または None
        """
        # フォールバックパターンの定義
        fallback_patterns = {
            'year.year_4digit': r'20\d\d',  # シンプルな4桁
            'year.kanji': r'[一二三四五六七八九〇]{4}',  # 基本的な漢数字
            'section.kanji_comma_next': r'[一二三四五]',  # 単純な漢数字
            'source.author_title_niyoru': r'.+『.+』',  # 最小限のパターン
        }
        return fallback_patterns.get(pattern_name)