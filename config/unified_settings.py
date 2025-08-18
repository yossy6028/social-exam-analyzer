"""
統一設定管理
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass
class AnalysisOptions:
    """分析オプション"""
    analyze_geography: bool = True
    analyze_history: bool = True
    analyze_civics: bool = True
    analyze_current_affairs: bool = True
    use_gemini: bool = False
    use_gemini_detailed: bool = True  # デフォルトでON


@dataclass
class UISettings:
    """UI設定"""
    window_width: int = 900
    window_height: int = 700
    font_family: str = "メイリオ"
    font_size: int = 10


@dataclass
class APISettings:
    """API設定"""
    gemini_api_key: Optional[str] = None
    vision_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None
    
    def validate(self) -> bool:
        """API設定の検証"""
        return bool(self.gemini_api_key)


class UnifiedSettings:
    """統一設定クラス"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初期化"""
        # 環境変数を読み込み
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # 各設定を初期化
        self.analysis = AnalysisOptions()
        self.ui = UISettings()
        self.api = APISettings(
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            vision_api_key=os.getenv('GOOGLE_CLOUD_API_KEY'),
            brave_api_key=os.getenv('BRAVE_API_KEY')
        )
        
        # パス設定
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / 'data'
        self.logs_dir = self.project_root / 'logs'
        self.output_dir = self.project_root / 'output'
        
        # ディレクトリ作成
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def reload(self):
        """設定の再読み込み"""
        self._initialize()
    
    def to_dict(self) -> dict:
        """辞書形式で出力"""
        return {
            'analysis': {
                'analyze_geography': self.analysis.analyze_geography,
                'analyze_history': self.analysis.analyze_history,
                'analyze_civics': self.analysis.analyze_civics,
                'analyze_current_affairs': self.analysis.analyze_current_affairs,
                'use_gemini': self.analysis.use_gemini,
                'use_gemini_detailed': self.analysis.use_gemini_detailed
            },
            'ui': {
                'window_width': self.ui.window_width,
                'window_height': self.ui.window_height,
                'font_family': self.ui.font_family,
                'font_size': self.ui.font_size
            },
            'api': {
                'has_gemini_key': bool(self.api.gemini_api_key),
                'has_vision_key': bool(self.api.vision_api_key),
                'has_brave_key': bool(self.api.brave_api_key)
            }
        }


# シングルトンインスタンス
settings = UnifiedSettings()