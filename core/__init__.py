# Core module initialization
# CLI temporarily commented out due to remaining legacy dependencies
# from .cli import CLI
from .text_engine import TextEngine
from .config import get_config, MainConfig
from .analyzer_di import AnalyzerFactory, BaseAnalyzer

__all__ = ['TextEngine', 'get_config', 'MainConfig', 'AnalyzerFactory', 'BaseAnalyzer']