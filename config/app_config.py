"""
アプリケーション設定管理
環境変数と設定ファイルから設定を読み込む
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AppConfig:
    """アプリケーション設定を管理するクラス"""
    
    # デフォルト設定
    DEFAULTS = {
        'database': {
            'excel_filename': 'entrance_exam_database.xlsx',
            'new_excel_filename': 'entrance_exam_database_new.xlsx',
            'backup_enabled': True,
            'max_backup_count': 5
        },
        'ocr': {
            'text_dir': '2025過去問',
            'timeout_seconds': 300,
            'max_file_size_mb': 100
        },
        'pdf': {
            'max_file_size_mb': 200,
            'max_pages': 100,
            'enable_layout_analysis': True,
            'memory_limit_mb': 500
        },
        'processing': {
            'max_text_length': 1000000,
            'max_sections': 10,
            'enable_validation': True,
            'enable_auto_merge': True
        },
        'paths': {
            'use_relative_paths': True,
            'create_dirs_if_missing': True
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初期化
        
        Args:
            config_file: 設定ファイルのパス
        """
        self.config = self.DEFAULTS.copy()
        self.config_file = config_file or self._find_config_file()
        
        # プロジェクトルートを設定
        self.project_root = self._find_project_root()
        
        # データディレクトリを設定
        self.data_dir = self._setup_data_directory()
        
        # 設定を読み込み
        self._load_config()
        
        # 環境変数で上書き
        self._load_environment_variables()
        
        # パスを解決
        self._resolve_paths()
    
    def _find_project_root(self) -> Path:
        """プロジェクトルートを見つける"""
        current = Path(__file__).resolve().parent.parent
        
        # .gitまたはpyproject.tomlがあるディレクトリを探す
        while current != current.parent:
            if (current / '.git').exists() or \
               (current / 'pyproject.toml').exists() or \
               (current / 'requirements.txt').exists():
                return current
            current = current.parent
        
        # 見つからない場合は現在のディレクトリの親
        return Path(__file__).resolve().parent.parent
    
    def _find_config_file(self) -> Optional[Path]:
        """設定ファイルを探す"""
        # 優先順位で探す
        search_paths = [
            Path.cwd() / 'config.json',
            Path.cwd() / '.entrance_exam_config.json',
            Path.home() / '.entrance_exam' / 'config.json',
            Path(__file__).parent / 'config.json'
        ]
        
        for path in search_paths:
            if path.exists():
                logger.info(f"設定ファイルを使用: {path}")
                return path
        
        return None
    
    def _setup_data_directory(self) -> Path:
        """データディレクトリを設定"""
        # 環境変数から取得
        if os.getenv('ENTRANCE_EXAM_DATA_DIR'):
            data_dir = Path(os.getenv('ENTRANCE_EXAM_DATA_DIR'))
        else:
            # デフォルトはユーザーのDocumentsフォルダ
            data_dir = Path.home() / 'Documents' / 'entrance_exam_data'
            
            # macOSの場合は特別な処理
            if os.name == 'posix' and (Path.home() / 'Desktop' / '01_仕事 (Work)').exists():
                # 既存のディレクトリが存在する場合はそれを使用
                data_dir = Path.home() / 'Desktop' / '01_仕事 (Work)' / 'オンライン家庭教師資料' / '過去問'
        
        # ディレクトリが存在しない場合は作成
        if self.config.get('paths', {}).get('create_dirs_if_missing', True):
            data_dir.mkdir(parents=True, exist_ok=True)
        
        return data_dir
    
    def _load_config(self):
        """設定ファイルから設定を読み込む"""
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self.config, file_config)
                    logger.info(f"設定ファイルを読み込みました: {self.config_file}")
            except Exception as e:
                logger.warning(f"設定ファイルの読み込みに失敗: {e}")
    
    def _load_environment_variables(self):
        """環境変数から設定を読み込む"""
        # Excel データベースパス
        if os.getenv('ENTRANCE_EXAM_DB_PATH'):
            self.config['database']['excel_path'] = os.getenv('ENTRANCE_EXAM_DB_PATH')
        
        # OCR テキストディレクトリ
        if os.getenv('ENTRANCE_EXAM_OCR_DIR'):
            self.config['ocr']['text_dir'] = os.getenv('ENTRANCE_EXAM_OCR_DIR')
        
        # ログレベル
        if os.getenv('ENTRANCE_EXAM_LOG_LEVEL'):
            self.config['logging']['level'] = os.getenv('ENTRANCE_EXAM_LOG_LEVEL')
        
        # メモリ制限
        if os.getenv('ENTRANCE_EXAM_MEMORY_LIMIT_MB'):
            self.config['pdf']['memory_limit_mb'] = int(os.getenv('ENTRANCE_EXAM_MEMORY_LIMIT_MB'))
    
    def _merge_config(self, base: Dict, override: Dict):
        """設定をマージする"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _resolve_paths(self):
        """パスを解決する"""
        # Excel データベースのパス
        if 'excel_path' not in self.config['database']:
            excel_filename = self.config['database']['excel_filename']
            self.config['database']['excel_path'] = self.data_dir / excel_filename
        else:
            # 絶対パスでない場合はdata_dirからの相対パス
            path = Path(self.config['database']['excel_path'])
            if not path.is_absolute():
                self.config['database']['excel_path'] = self.data_dir / path
        
        # 新形式Excelのパス
        new_excel_filename = self.config['database']['new_excel_filename']
        self.config['database']['new_excel_path'] = self.data_dir / new_excel_filename
        
        # OCRテキストディレクトリ
        ocr_dir = self.config['ocr']['text_dir']
        if not Path(ocr_dir).is_absolute():
            self.config['ocr']['text_dir'] = self.data_dir / ocr_dir
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: ドット区切りのキー（例: 'database.excel_path'）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_excel_path(self) -> Path:
        """Excelデータベースのパスを取得（新形式を優先）"""
        # 新形式のExcelファイルを優先
        new_path = self.get('database.new_excel_path')
        if new_path:
            return Path(new_path)
        
        # 新形式のパスがない場合は新形式のファイル名で作成
        return self.data_dir / 'entrance_exam_database_new.xlsx'
    
    def get_new_excel_path(self) -> Path:
        """新形式Excelのパスを取得"""
        path = self.get('database.new_excel_path')
        return Path(path) if path else self.data_dir / 'entrance_exam_database_new.xlsx'
    
    def get_ocr_dir(self) -> Path:
        """OCRテキストディレクトリを取得"""
        path = self.get('ocr.text_dir')
        return Path(path) if path else self.data_dir / '2025過去問'
    
    def get_pdf_max_size_mb(self) -> int:
        """PDFの最大サイズ（MB）を取得"""
        return self.get('pdf.max_file_size_mb', 200)
    
    def get_pdf_memory_limit_mb(self) -> int:
        """PDFメモリ制限（MB）を取得"""
        return self.get('pdf.memory_limit_mb', 500)
    
    def save_config(self, path: Optional[str] = None):
        """
        設定をファイルに保存
        
        Args:
            path: 保存先のパス
        """
        save_path = path or self.config_file or (self.project_root / 'config.json')
        
        try:
            # パスを文字列に変換
            config_to_save = self._serialize_config(self.config)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            
            logger.info(f"設定を保存しました: {save_path}")
        except Exception as e:
            logger.error(f"設定の保存に失敗: {e}")
    
    def _serialize_config(self, config: Dict) -> Dict:
        """設定をシリアライズ可能な形式に変換"""
        result = {}
        for key, value in config.items():
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._serialize_config(value)
            else:
                result[key] = value
        return result


# グローバル設定インスタンス
_config = None


def get_config() -> AppConfig:
    """グローバル設定インスタンスを取得"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reset_config(config_file: Optional[str] = None):
    """設定をリセット"""
    global _config
    _config = AppConfig(config_file)
    return _config