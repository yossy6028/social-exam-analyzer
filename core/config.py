"""
中央集権的設定管理モジュール
全ての設定を一元管理し、環境変数やファイルからの設定読み込みをサポート
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class FileConfig:
    """ファイル関連の設定"""
    max_files_to_display: int = 50
    max_files_per_school: int = 5
    min_path_display_length: int = 60
    default_encoding_list: List[str] = field(default_factory=lambda: [
        'utf-8', 'shift-jis', 'euc-jp', 'cp932', 'iso-2022-jp', 'utf-16'
    ])
    max_file_size_mb: int = 200


@dataclass
class YearConfig:
    """年度検出関連の設定"""
    min_year_2digit: int = 14  # 2014年
    max_year_2digit: int = 25  # 2025年
    min_valid_year: int = 1990
    max_valid_year: int = 2030
    default_century: int = 2000
    kanji_digit_map: Dict[str, str] = field(default_factory=lambda: {
        '〇': '0', '零': '0', '０': '0',
        '一': '1', '壱': '1', '１': '1',
        '二': '2', '弐': '2', '２': '2',
        '三': '3', '参': '3', '３': '3',
        '四': '4', '肆': '4', '４': '4',
        '五': '5', '伍': '5', '５': '5',
        '六': '6', '陸': '6', '６': '6',
        '七': '7', '柒': '7', '７': '7',
        '八': '8', '捌': '8', '８': '8',
        '九': '9', '玖': '9', '９': '9'
    })
    era_conversion: Dict[str, int] = field(default_factory=lambda: {
        'reiwa_base': 2018,   # 令和元年 = 2019
        'heisei_base': 1988,  # 平成元年 = 1989
        'showa_base': 1925    # 昭和元年 = 1926
    })


@dataclass
class TextAnalysisConfig:
    """テキスト分析関連の設定"""
    min_section_distance: int = 500
    min_section_content: int = 50
    min_question_distance: int = 30
    min_valid_section_size: int = 200
    max_sections: int = 10
    max_text_length: int = 1000000
    min_text_length: int = 100
    merge_threshold: int = 200
    title_max_length: int = 150
    max_questions_per_section: int = 30
    min_question_length: int = 10


@dataclass
class OCRConfig:
    """OCR関連の設定"""
    text_dir: str = '2025過去問'
    timeout_seconds: int = 300
    max_file_size_mb: int = 100
    enable_layout_analysis: bool = True
    confidence_threshold: float = 0.8
    language: str = 'jpn'


@dataclass
class PDFConfig:
    """PDF処理関連の設定"""
    max_file_size_mb: int = 200
    max_pages: int = 100
    enable_layout_analysis: bool = True
    memory_limit_mb: int = 500
    dpi: int = 300
    image_format: str = 'png'


@dataclass
class DatabaseConfig:
    """データベース（Excel）関連の設定"""
    excel_filename: str = 'entrance_exam_database.xlsx'
    new_excel_filename: str = 'entrance_exam_database_new.xlsx'
    backup_enabled: bool = True
    max_backup_count: int = 5
    excel_engine: str = 'openpyxl'
    sheet_name_format: str = '{school}_{year}'
    max_sheet_name_length: int = 31  # Excel制限


@dataclass
class ProcessingConfig:
    """処理関連の設定"""
    enable_validation: bool = True
    enable_auto_merge: bool = True
    parallel_processing: bool = False  # 将来の並列処理対応
    max_workers: int = 4
    batch_size: int = 10
    cache_enabled: bool = False  # 将来のキャッシュ対応
    cache_ttl_seconds: int = 3600


@dataclass
class PathConfig:
    """パス関連の設定"""
    use_relative_paths: bool = True
    create_dirs_if_missing: bool = True
    output_dir: Path = field(default_factory=lambda: Path("data/output"))
    backup_dir: Path = field(default_factory=lambda: Path("data/backups"))
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    cache_dir: Path = field(default_factory=lambda: Path("data/cache"))


@dataclass
class LoggingConfig:
    """ロギング関連の設定"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    log_filename: str = 'social_analyzer.log'


@dataclass
class SchoolConfig:
    """学校名認識の設定"""
    patterns: Dict[str, str] = field(default_factory=lambda: {
        r'開成': '開成中学校',
        r'桜蔭|桜陰': '桜蔭中学校',
        r'麻布': '麻布中学校',
        r'武蔵': '武蔵中学校',
        r'女子学院|JG': '女子学院中学校',
        r'雙葉|双葉': '雙葉中学校',
        r'筑駒|筑波大.*駒場': '筑波大学附属駒場中学校',
        r'渋(?:谷)?教?(?:育)?(?:学園)?渋谷?|渋渋|渋幕': '渋谷教育学園渋谷中学校',
        r'聖光(?:学院)?': '聖光学院中学校',
        r'栄光(?:学園)?': '栄光学園中学校',
        r'慶應|慶応': '慶應義塾中等部',
        r'早稲田実業|早実': '早稲田実業学校中等部',
        r'豊島岡|豊島': '豊島岡女子学園中学校',
        r'海城': '海城中学校',
        r'駒場東邦|駒東': '駒場東邦中学校',
        r'灘': '灘中学校',
    })
    year_patterns: List[str] = field(default_factory=lambda: [
        r'武蔵(\d{2})',
        r'開成(\d{2})',
        r'麻布(\d{2})',
        r'桜蔭(\d{2})',
        r'女子学院(\d{2})',
        r'雙葉(\d{2})',
        r'渋渋(\d{2})',
        r'渋谷(\d{2})',
        r'慶應(\d{2})',
        r'早実(\d{2})',
    ])


@dataclass
class MainConfig:
    """メイン設定クラス - 全ての設定を統合"""
    file: FileConfig = field(default_factory=FileConfig)
    year: YearConfig = field(default_factory=YearConfig)
    text_analysis: TextAnalysisConfig = field(default_factory=TextAnalysisConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    pdf: PDFConfig = field(default_factory=PDFConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    school: SchoolConfig = field(default_factory=SchoolConfig)
    
    # 動的に設定されるパス
    project_root: Optional[Path] = None
    data_dir: Optional[Path] = None
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.project_root is None:
            self.project_root = self._find_project_root()
        if self.data_dir is None:
            self.data_dir = self._setup_data_directory()
        self._resolve_paths()
    
    def _find_project_root(self) -> Path:
        """プロジェクトルートを見つける"""
        current = Path(__file__).resolve().parent.parent
        
        while current != current.parent:
            if any((current / marker).exists() for marker in ['.git', 'pyproject.toml', 'requirements.txt']):
                return current
            current = current.parent
        
        return Path(__file__).resolve().parent.parent
    
    def _setup_data_directory(self) -> Path:
        """データディレクトリを設定"""
        if os.getenv('ENTRANCE_EXAM_DATA_DIR'):
            data_dir = Path(os.getenv('ENTRANCE_EXAM_DATA_DIR'))
        else:
            data_dir = Path.home() / 'Documents' / 'entrance_exam_data'
            
            # macOSの既存ディレクトリチェック
            if os.name == 'posix':
                legacy_path = Path.home() / 'Desktop' / '01_仕事 (Work)' / 'オンライン家庭教師資料' / '過去問'
                if legacy_path.exists():
                    data_dir = legacy_path
        
        if self.paths.create_dirs_if_missing:
            data_dir.mkdir(parents=True, exist_ok=True)
        
        return data_dir
    
    def _resolve_paths(self):
        """相対パスを絶対パスに解決"""
        # パス設定の解決
        for attr_name in ['output_dir', 'backup_dir', 'log_dir', 'cache_dir']:
            path = getattr(self.paths, attr_name)
            if not path.is_absolute():
                setattr(self.paths, attr_name, self.project_root / path)
        
        # OCRディレクトリの解決
        if not Path(self.ocr.text_dir).is_absolute():
            self.ocr.text_dir = str(self.data_dir / self.ocr.text_dir)
    
    def get_excel_path(self) -> Path:
        """Excelデータベースのパスを取得"""
        return self.data_dir / self.database.new_excel_filename
    
    def get_ocr_dir(self) -> Path:
        """OCRテキストディレクトリを取得"""
        return Path(self.ocr.text_dir)
    
    def get_search_directories(self) -> List[Path]:
        """検索対象ディレクトリのリストを返す"""
        directories = [
            Path.cwd(),
            Path.home() / "Desktop",
        ]
        
        if os.getenv('ENTRANCE_EXAM_SEARCH_DIRS'):
            for dir_str in os.getenv('ENTRANCE_EXAM_SEARCH_DIRS').split(':'):
                directories.append(Path(dir_str))
        else:
            # デフォルトの検索パス
            directories.extend([
                Path.home() / "Desktop" / "01_仕事 (Work)" / "オンライン家庭教師資料" / "過去問",
                Path.home() / "Desktop" / "過去問のエイリアス",
            ])
        
        return directories
    
    def get_allowed_directories(self) -> List[Path]:
        """セキュリティ: アクセス許可ディレクトリのリストを返す"""
        allowed = [
            Path.home().resolve(),
            Path.cwd().resolve(),
        ]
        if os.name == 'posix':
            allowed.append(Path("/tmp").resolve())
        else:
            temp_dir = os.environ.get('TEMP', '')
            if temp_dir:
                allowed.append(Path(temp_dir).resolve())
        return allowed
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式に変換"""
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if hasattr(value, '__dataclass_fields__'):
                result[field_name] = asdict(value)
            elif isinstance(value, Path):
                result[field_name] = str(value)
            elif value is not None:
                result[field_name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainConfig':
        """辞書から設定を作成"""
        config_classes = {
            'file': FileConfig,
            'year': YearConfig,
            'text_analysis': TextAnalysisConfig,
            'ocr': OCRConfig,
            'pdf': PDFConfig,
            'database': DatabaseConfig,
            'processing': ProcessingConfig,
            'paths': PathConfig,
            'logging': LoggingConfig,
            'school': SchoolConfig,
        }
        
        kwargs = {}
        for key, config_class in config_classes.items():
            if key in data and isinstance(data[key], dict):
                kwargs[key] = config_class(**data[key])
        
        # その他のフィールド
        for key in ['project_root', 'data_dir']:
            if key in data:
                value = data[key]
                kwargs[key] = Path(value) if value else None
        
        return cls(**kwargs)
    
    def save(self, path: Optional[Path] = None):
        """設定をファイルに保存"""
        save_path = path or self.project_root / 'config.json'
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"設定を保存しました: {save_path}")
        except Exception as e:
            logger.error(f"設定の保存に失敗: {e}")
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'MainConfig':
        """ファイルから設定を読み込む"""
        if path and path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception as e:
                logger.warning(f"設定ファイルの読み込みに失敗: {e}")
        
        return cls()
    
    def load_environment_variables(self):
        """環境変数から設定を読み込む"""
        # データディレクトリ
        if os.getenv('ENTRANCE_EXAM_DATA_DIR'):
            self.data_dir = Path(os.getenv('ENTRANCE_EXAM_DATA_DIR'))
        
        # OCRディレクトリ
        if os.getenv('ENTRANCE_EXAM_OCR_DIR'):
            self.ocr.text_dir = os.getenv('ENTRANCE_EXAM_OCR_DIR')
        
        # ログレベル
        if os.getenv('ENTRANCE_EXAM_LOG_LEVEL'):
            self.logging.level = os.getenv('ENTRANCE_EXAM_LOG_LEVEL')
        
        # メモリ制限
        if os.getenv('ENTRANCE_EXAM_MEMORY_LIMIT_MB'):
            self.pdf.memory_limit_mb = int(os.getenv('ENTRANCE_EXAM_MEMORY_LIMIT_MB'))
        
        # 並列処理
        if os.getenv('ENTRANCE_EXAM_PARALLEL'):
            self.processing.parallel_processing = os.getenv('ENTRANCE_EXAM_PARALLEL').lower() == 'true'
        
        # キャッシュ
        if os.getenv('ENTRANCE_EXAM_CACHE'):
            self.processing.cache_enabled = os.getenv('ENTRANCE_EXAM_CACHE').lower() == 'true'


# グローバル設定インスタンス
_config: Optional[MainConfig] = None


def get_config() -> MainConfig:
    """グローバル設定インスタンスを取得"""
    global _config
    if _config is None:
        _config = MainConfig()
        _config.load_environment_variables()
    return _config


def reset_config(config_file: Optional[Path] = None) -> MainConfig:
    """設定をリセット"""
    global _config
    if config_file:
        _config = MainConfig.load(config_file)
    else:
        _config = MainConfig()
    _config.load_environment_variables()
    return _config


def set_config(config: MainConfig):
    """設定を設定"""
    global _config
    _config = config


# 後方互換性のためのエイリアス
class Settings:
    """後方互換性のための設定クラス"""
    
    def __init__(self):
        self._config = get_config()
    
    def __getattr__(self, name):
        # 旧設定名から新設定へのマッピング
        mappings = {
            'MAX_FILES_TO_DISPLAY': lambda: self._config.file.max_files_to_display,
            'MAX_FILES_PER_SCHOOL': lambda: self._config.file.max_files_per_school,
            'MIN_PATH_DISPLAY_LENGTH': lambda: self._config.file.min_path_display_length,
            'DEFAULT_ENCODING_LIST': lambda: self._config.file.default_encoding_list,
            'MIN_YEAR_2DIGIT': lambda: self._config.year.min_year_2digit,
            'MAX_YEAR_2DIGIT': lambda: self._config.year.max_year_2digit,
            'MIN_VALID_YEAR': lambda: self._config.year.min_valid_year,
            'MAX_VALID_YEAR': lambda: self._config.year.max_valid_year,
            'MIN_SECTION_DISTANCE': lambda: self._config.text_analysis.min_section_distance,
            'MIN_SECTION_CONTENT': lambda: self._config.text_analysis.min_section_content,
            'MIN_QUESTION_DISTANCE': lambda: self._config.text_analysis.min_question_distance,
            'MIN_VALID_SECTION_SIZE': lambda: self._config.text_analysis.min_valid_section_size,
            'SCHOOL_PATTERNS': lambda: self._config.school.patterns,
            'OUTPUT_DIR': lambda: self._config.paths.output_dir,
            'BACKUP_DIR': lambda: self._config.paths.backup_dir,
            'LOG_DIR': lambda: self._config.paths.log_dir,
            'EXCEL_ENGINE': lambda: self._config.database.excel_engine,
            'get_search_directories': lambda: self._config.get_search_directories,
            'get_allowed_directories': lambda: self._config.get_allowed_directories,
        }
        
        if name in mappings:
            return mappings[name]()
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


class AppConfig:
    """後方互換性のためのAppConfigクラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        if config_file:
            self._config = MainConfig.load(Path(config_file))
        else:
            self._config = get_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """ドット記法でネストされた設定値を取得"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_excel_path(self) -> Path:
        return self._config.get_excel_path()
    
    def get_new_excel_path(self) -> Path:
        return self._config.get_excel_path()
    
    def get_ocr_dir(self) -> Path:
        return self._config.get_ocr_dir()
    
    def get_pdf_max_size_mb(self) -> int:
        return self._config.pdf.max_file_size_mb
    
    def get_pdf_memory_limit_mb(self) -> int:
        return self._config.pdf.memory_limit_mb