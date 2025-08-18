"""
データモデル定義 - アプリケーション全体で使用される型定義
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum


class ProcessingStatus(Enum):
    """処理ステータス"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class YearDetectionResult:
    """年度検出結果"""
    years: List[str]
    detection_patterns: Dict[str, List[tuple]]
    confidence: float


@dataclass
class FileSelectionResult:
    """ファイル選択結果"""
    selected_files: List[Path]
    cancelled: bool = False


@dataclass
class ExamDocument:
    """入試問題ドキュメント"""
    file_path: Path
    content: str
    detected_years: List[str]
    detected_school: Optional[str] = None
    encoding: str = "utf-8"
    file_type: str = "unknown"


@dataclass
class AnalysisResult:
    """分析結果"""
    year: str
    school: str
    content: str
    questions: List[Any]  # Question オブジェクトのリスト
    themes: List[str]
    sections: List[Dict[str, Any]]
    source_file: Path
    confidence: float = 0.0


@dataclass
class ExcelExportConfig:
    """Excel出力設定"""
    output_path: Path
    include_themes: bool = True
    include_questions: bool = True
    include_sources: bool = True


@dataclass
class Question:
    """設問データクラス"""
    number: str
    text: str
    field: str
    theme: str = ""
    question_type: str = "その他"
    choices: Optional[List[str]] = None
    answer: Optional[str] = None
    difficulty: int = 1
    source_section: str = ""