"""
依存性注入版アナライザー
テスタビリティと拡張性を向上させた設計
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
import logging
import time
from functools import wraps
from dataclasses import dataclass

from core.config import MainConfig, get_config
from core.text_engine import TextEngine


# プロトコル定義（インターフェース）
class PatternRegistryProtocol(Protocol):
    """パターンレジストリのプロトコル"""
    def get_all_patterns(self) -> Dict[str, Any]: ...
    def extract_all(self, text: str, filename: str = '') -> Dict[str, Any]: ...


class TextPreprocessorProtocol(Protocol):
    """テキスト前処理のプロトコル"""
    def preprocess(self, text: str) -> str: ...
    def normalize(self, text: str) -> str: ...


class ConfigValidatorProtocol(Protocol):
    """設定検証のプロトコル"""
    def validate(self, config: Dict, component: str = '') -> Dict: ...


# 依存性コンテナ
@dataclass
class Dependencies:
    """依存性を管理するコンテナ"""
    config: MainConfig
    pattern_registry: Optional[PatternRegistryProtocol] = None
    text_preprocessor: Optional[TextPreprocessorProtocol] = None
    config_validator: Optional[ConfigValidatorProtocol] = None
    text_engine: Optional[TextEngine] = None
    logger: Optional[logging.Logger] = None


def timing_decorator(func):
    """実行時間を計測するデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # selfがある場合はそのloggerを使用
        if args and hasattr(args[0], 'logger'):
            logger = args[0].logger
        else:
            logger = logging.getLogger(func.__module__)
        
        logger.debug(f"{func.__name__} took {end_time - start_time:.3f} seconds")
        
        return result
    return wrapper


class BaseAnalyzer(ABC):
    """
    依存性注入に対応した基底アナライザークラス
    """
    
    def __init__(self, dependencies: Optional[Dependencies] = None):
        """
        依存性注入による初期化
        
        Args:
            dependencies: 依存性コンテナ
        """
        # 依存性の注入または デフォルト作成
        if dependencies is None:
            dependencies = self._create_default_dependencies()
        
        self.dependencies = dependencies
        self.config = dependencies.config
        self.logger = dependencies.logger or logging.getLogger(self.__class__.__name__)
        
        # 依存コンポーネント
        self.pattern_registry = dependencies.pattern_registry
        self.text_preprocessor = dependencies.text_preprocessor
        self.config_validator = dependencies.config_validator
        self.text_engine = dependencies.text_engine or TextEngine(self.config)
        
        # キャッシュ
        self._cache = {}
        
        # 初期化フック
        self._initialize()
    
    def _create_default_dependencies(self) -> Dependencies:
        """デフォルトの依存性を作成"""
        from patterns.registry import PatternRegistry
        from processors.text_preprocessor import TextPreprocessor
        from core.config_validator import ConfigValidator
        
        config = get_config()
        
        return Dependencies(
            config=config,
            pattern_registry=PatternRegistry(),
            text_preprocessor=TextPreprocessor(),
            config_validator=ConfigValidator(),
            text_engine=TextEngine(config),
            logger=logging.getLogger(self.__class__.__name__)
        )
    
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
        if self.text_preprocessor:
            return self.text_preprocessor.preprocess(text)
        return text
    
    def validate_config(self, config: Dict[str, Any], component: str = '') -> Dict[str, Any]:
        """
        設定を検証
        
        Args:
            config: 検証する設定
            component: コンポーネント名
            
        Returns:
            検証済み設定
        """
        if self.config_validator:
            return self.config_validator.validate(config, component)
        return config
    
    @timing_decorator
    def analyze_with_cache(self, text: str, cache_key: Optional[str] = None, **kwargs) -> Any:
        """
        キャッシュ付き分析
        
        Args:
            text: 分析対象のテキスト
            cache_key: キャッシュキー（省略時は自動生成）
            **kwargs: 追加パラメータ
            
        Returns:
            分析結果
        """
        # キャッシュキーの生成
        if cache_key is None:
            import hashlib
            cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # キャッシュチェック
        if self.config.processing.cache_enabled and cache_key in self._cache:
            self.logger.debug(f"Cache hit for key: {cache_key[:8]}...")
            return self._cache[cache_key]
        
        # 分析実行
        result = self.analyze(text, **kwargs)
        
        # キャッシュ保存
        if self.config.processing.cache_enabled:
            self._cache[cache_key] = result
        
        return result
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._cache.clear()
        self.logger.info("Cache cleared")


class TextAnalyzer(BaseAnalyzer):
    """
    テキスト分析の具体的実装
    """
    
    def analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        テキストを分析
        
        Args:
            text: 分析対象のテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            分析結果
        """
        # 前処理
        preprocessed = self.preprocess_text(text)
        
        # TextEngineを使用して分析
        processed_text = self.text_engine.process_text(
            preprocessed,
            filename=kwargs.get('filename'),
            school=kwargs.get('school'),
            year=kwargs.get('year')
        )
        
        # 結果を辞書形式で返す
        return self.text_engine.export_to_dict(processed_text)


class QuestionAnalyzer(BaseAnalyzer):
    """
    設問分析の具体的実装
    """
    
    def analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        設問を分析
        
        Args:
            text: 分析対象のテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            設問分析結果
        """
        # パターンレジストリを使用して設問を抽出
        if self.pattern_registry:
            patterns = self.pattern_registry.extract_all(text, kwargs.get('filename', ''))
            questions = patterns.get('questions', [])
        else:
            questions = []
        
        # 設問タイプ別に分類
        question_types = {}
        for q in questions:
            q_type = q.get('type', 'other')
            if q_type not in question_types:
                question_types[q_type] = []
            question_types[q_type].append(q)
        
        return {
            'total_questions': len(questions),
            'question_types': question_types,
            'questions': questions
        }


class SectionAnalyzer(BaseAnalyzer):
    """
    セクション分析の具体的実装
    """
    
    def analyze(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        セクションを分析
        
        Args:
            text: 分析対象のテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            セクション分析結果
        """
        # パターンレジストリを使用してセクションを抽出
        if self.pattern_registry:
            patterns = self.pattern_registry.extract_all(text, kwargs.get('filename', ''))
            sections = patterns.get('sections', [])
        else:
            sections = []
        
        # セクション情報を整理
        section_info = []
        for i, section in enumerate(sections):
            info = {
                'number': section.get('section_number', i + 1),
                'position': section.get('position'),
                'title': section.get('raw_text', ''),
                'pattern': section.get('pattern')
            }
            section_info.append(info)
        
        return {
            'total_sections': len(sections),
            'sections': section_info
        }


# ファクトリークラス
class AnalyzerFactory:
    """
    アナライザーのファクトリークラス
    依存性注入を管理
    """
    
    def __init__(self, dependencies: Optional[Dependencies] = None):
        """
        初期化
        
        Args:
            dependencies: 共有する依存性コンテナ
        """
        self.dependencies = dependencies
    
    def create_text_analyzer(self) -> TextAnalyzer:
        """テキストアナライザーを作成"""
        return TextAnalyzer(self.dependencies)
    
    def create_question_analyzer(self) -> QuestionAnalyzer:
        """設問アナライザーを作成"""
        return QuestionAnalyzer(self.dependencies)
    
    def create_section_analyzer(self) -> SectionAnalyzer:
        """セクションアナライザーを作成"""
        return SectionAnalyzer(self.dependencies)
    
    def create_custom_analyzer(self, analyzer_class: type, **kwargs) -> BaseAnalyzer:
        """
        カスタムアナライザーを作成
        
        Args:
            analyzer_class: アナライザークラス
            **kwargs: 追加の依存性
            
        Returns:
            アナライザーインスタンス
        """
        # 依存性のコピーを作成
        if self.dependencies:
            import copy
            deps = copy.copy(self.dependencies)
            # 追加の依存性を設定
            for key, value in kwargs.items():
                setattr(deps, key, value)
        else:
            deps = None
        
        return analyzer_class(deps)


# 後方互換性のためのエイリアス
def create_analyzer(analyzer_type: str = 'text', config: Optional[Dict] = None) -> BaseAnalyzer:
    """
    後方互換性のためのファクトリー関数
    
    Args:
        analyzer_type: アナライザーのタイプ
        config: 設定辞書
        
    Returns:
        アナライザーインスタンス
    """
    # 設定から依存性を構築
    if config:
        from core.config import MainConfig
        main_config = MainConfig.from_dict(config)
    else:
        main_config = get_config()
    
    deps = Dependencies(config=main_config)
    factory = AnalyzerFactory(deps)
    
    analyzer_map = {
        'text': factory.create_text_analyzer,
        'question': factory.create_question_analyzer,
        'section': factory.create_section_analyzer,
    }
    
    creator = analyzer_map.get(analyzer_type, factory.create_text_analyzer)
    return creator()