"""
基底アナライザークラス
すべてのアナライザーの共通機能を提供
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
import time
from functools import wraps

from patterns.registry import PatternRegistry
from processors.text_preprocessor import TextPreprocessor
from core.config_validator import ConfigValidator


def timing_decorator(func):
    """実行時間を計測するデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger = logging.getLogger(func.__module__)
        logger.debug(f"{func.__name__} took {end_time - start_time:.3f} seconds")
        
        return result
    return wrapper


class BaseAnalyzer(ABC):
    """
    すべてのアナライザーの基底クラス
    共通機能とインターフェースを定義
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            config: 設定辞書（オプション）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 設定の検証とデフォルト値の適用
        validator = ConfigValidator()
        base_config = config or {}
        
        # base_analyzer用の設定を検証
        if 'base_analyzer' in validator.schema:
            validated_config = validator.validate(
                base_config, 
                component='base_analyzer'
            )
            self.config = validated_config
        else:
            self.config = base_config
        
        # 共通コンポーネントの初期化
        self.pattern_registry = PatternRegistry()
        self.text_preprocessor = TextPreprocessor()
        
        # キャッシュ
        self._cache = {}
        
        # 初期化フック
        self._initialize()
    
    def _initialize(self):
        """
        サブクラス固有の初期化
        オーバーライド可能
        """
        pass
    
    @abstractmethod
    def analyze(self, text: str, **kwargs) -> Any:
        """
        分析を実行（サブクラスで実装必須）
        
        Args:
            text: 分析対象のテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            分析結果
        """
        pass
    
    def preprocess_text(self, text: str) -> str:
        """
        テキストの前処理
        
        Args:
            text: 元のテキスト
            
        Returns:
            前処理済みテキスト
        """
        # キャッシュチェック
        cache_key = f"preprocessed_{hash(text)}"
        if cache_key in self._cache:
            self.logger.debug("Using cached preprocessed text")
            return self._cache[cache_key]
        
        # 前処理実行
        processed = self.text_preprocessor.clean_for_analysis(text)
        
        # キャッシュ保存
        self._cache[cache_key] = processed
        
        return processed
    
    def get_pattern(self, pattern_name: str, flags: int = 0):
        """
        パターンレジストリからパターンを取得
        
        Args:
            pattern_name: パターン名
            flags: 正規表現フラグ
            
        Returns:
            コンパイル済みパターン
        """
        return self.pattern_registry.get_pattern(pattern_name, flags)
    
    def find_all_matches(self, pattern_name: str, text: str, flags: int = 0) -> list:
        """
        パターンですべての一致を検索
        
        Args:
            pattern_name: パターン名
            text: 検索対象テキスト
            flags: 正規表現フラグ
            
        Returns:
            一致のリスト
        """
        return self.pattern_registry.findall(pattern_name, text, flags)
    
    def validate_input(self, text: str) -> bool:
        """
        入力テキストのバリデーション
        
        Args:
            text: 検証対象のテキスト
            
        Returns:
            有効な場合True
            
        Raises:
            ValidationError: 無効な入力の場合
        """
        if not text:
            raise ValidationError("Empty text provided")
        
        if len(text) < self.config.get('min_text_length', 100):
            raise ValidationError(f"Text too short: {len(text)} characters")
        
        if len(text) > self.config.get('max_text_length', 1000000):
            raise ValidationError(f"Text too long: {len(text)} characters")
        
        return True
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._cache.clear()
        self.logger.debug("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """キャッシュ統計を取得"""
        return {
            'entries': len(self._cache),
            'size_bytes': sum(len(str(v)) for v in self._cache.values())
        }
    
    @timing_decorator
    def analyze_with_timing(self, text: str, **kwargs) -> Any:
        """
        タイミング計測付きで分析を実行
        
        Args:
            text: 分析対象のテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            分析結果
        """
        return self.analyze(text, **kwargs)
    
    def log_analysis_start(self, text_length: int, **kwargs):
        """分析開始をログ出力"""
        self.logger.info(f"Starting analysis: {text_length} characters")
        if kwargs:
            self.logger.debug(f"Parameters: {kwargs}")
    
    def log_analysis_complete(self, result: Any):
        """分析完了をログ出力"""
        result_summary = self._get_result_summary(result)
        self.logger.info(f"Analysis complete: {result_summary}")
    
    def _get_result_summary(self, result: Any) -> str:
        """
        結果のサマリーを生成（オーバーライド可能）
        
        Args:
            result: 分析結果
            
        Returns:
            サマリー文字列
        """
        if hasattr(result, '__dict__'):
            return f"{type(result).__name__} object"
        elif isinstance(result, dict):
            return f"dict with {len(result)} keys"
        elif isinstance(result, list):
            return f"list with {len(result)} items"
        else:
            return str(type(result))
    
    def handle_error(self, error: Exception, context: str = ""):
        """
        エラーハンドリング
        
        Args:
            error: 発生した例外
            context: エラーコンテキスト
        """
        error_msg = f"Error in {self.__class__.__name__}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {error}"
        
        self.logger.error(error_msg, exc_info=True)
        
        # エラーを再発生させるか、カスタムエラーに変換
        if self.config.get('propagate_errors', True):
            raise
        else:
            return self._get_error_result(error, context)
    
    def _get_error_result(self, error: Exception, context: str) -> Any:
        """
        エラー時のデフォルト結果を生成（オーバーライド可能）
        
        Args:
            error: 発生した例外
            context: エラーコンテキスト
            
        Returns:
            エラー結果
        """
        return {
            'success': False,
            'error': str(error),
            'context': context
        }


# カスタム例外クラス
class AnalyzerError(Exception):
    """アナライザーの基底例外クラス"""
    pass


class ValidationError(AnalyzerError):
    """バリデーションエラー"""
    pass