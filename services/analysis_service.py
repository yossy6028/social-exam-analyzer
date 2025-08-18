"""
分析サービス - ビジネスロジックの中心
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from config.unified_settings import settings, AnalysisOptions
from modules.ocr_handler import OCRHandler
from modules.social_analyzer import SocialAnalyzer
from modules.gemini_bridge import GeminiBridge


logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """分析リクエスト"""
    pdf_path: str
    school_name: str
    year: str
    options: AnalysisOptions
    progress_callback: Optional[Callable[[str], None]] = None


@dataclass
class AnalysisResult:
    """分析結果"""
    questions: list
    statistics: Dict[str, Any]
    total_questions: int
    school_name: str
    year: str
    source: str = "standard"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'questions': self.questions,
            'statistics': self.statistics,
            'total_questions': self.total_questions,
            'school_name': self.school_name,
            'year': self.year,
            'source': self.source
        }


class AnalysisService:
    """分析サービス"""
    
    def __init__(self):
        """初期化"""
        self.ocr_handler = OCRHandler()
        self.social_analyzer = SocialAnalyzer()
        self.gemini_bridge = None
        
        # Gemini Bridgeの初期化
        if settings.api.gemini_api_key:
            try:
                self.gemini_bridge = GeminiBridge()
                logger.info("Gemini Bridge initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Bridge: {e}")
    
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        PDFファイルを分析
        
        Args:
            request: 分析リクエスト
            
        Returns:
            分析結果
        """
        try:
            # プログレス通知
            if request.progress_callback:
                request.progress_callback("分析を開始します...")
            
            # Gemini詳細分析を使用する場合
            if request.options.use_gemini_detailed and self.gemini_bridge:
                return self._analyze_with_gemini(request)
            
            # 標準分析
            return self._analyze_standard(request)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
    
    def _analyze_with_gemini(self, request: AnalysisRequest) -> AnalysisResult:
        """Gemini APIを使用した詳細分析"""
        if request.progress_callback:
            request.progress_callback("Gemini APIによる詳細分析を実行中...")
        
        # Gemini分析実行
        result = self.gemini_bridge.analyze_pdf(
            request.pdf_path,
            request.progress_callback
        )
        
        # 結果を構造化
        return AnalysisResult(
            questions=result.get('questions', []),
            statistics=result.get('statistics', {}),
            total_questions=result.get('total_questions', 0),
            school_name=request.school_name,
            year=request.year,
            source='gemini_detailed'
        )
    
    def _analyze_standard(self, request: AnalysisRequest) -> AnalysisResult:
        """標準パターンマッチング分析"""
        if request.progress_callback:
            request.progress_callback("PDFからテキストを抽出中...")
        
        # OCR処理
        text = self.ocr_handler.process_pdf(request.pdf_path)
        
        if not text:
            raise ValueError("PDFからテキストを抽出できませんでした")
        
        if request.progress_callback:
            request.progress_callback("問題を分析中...")
        
        # 分析実行
        self.social_analyzer.analyze_text(text)
        
        # オプションに基づいてフィルタリング
        questions = self._filter_questions(
            self.social_analyzer.questions,
            request.options
        )
        
        # 統計情報の計算
        statistics = self._calculate_statistics(questions)
        
        return AnalysisResult(
            questions=questions,
            statistics=statistics,
            total_questions=len(questions),
            school_name=request.school_name,
            year=request.year,
            source='standard'
        )
    
    def _filter_questions(self, questions: list, options: AnalysisOptions) -> list:
        """オプションに基づいて問題をフィルタリング"""
        filtered = []
        
        for q in questions:
            field = getattr(q, 'field', None)
            if not field:
                continue
            
            # フィールドに基づいてフィルタリング
            field_value = field.value if hasattr(field, 'value') else str(field)
            
            if field_value == '地理' and not options.analyze_geography:
                continue
            if field_value == '歴史' and not options.analyze_history:
                continue
            if field_value == '公民' and not options.analyze_civics:
                continue
            if field_value == '時事問題' and not options.analyze_current_affairs:
                continue
            
            filtered.append(q)
        
        return filtered
    
    def _calculate_statistics(self, questions: list) -> Dict[str, Any]:
        """統計情報の計算"""
        if not questions:
            return {}
        
        # 分野別集計
        field_counts = {}
        format_counts = {}
        
        for q in questions:
            # 分野
            field = getattr(q, 'field', None)
            if field:
                field_str = field.value if hasattr(field, 'value') else str(field)
                field_counts[field_str] = field_counts.get(field_str, 0) + 1
            
            # 出題形式
            q_format = getattr(q, 'question_format', None)
            if q_format:
                format_str = q_format.value if hasattr(q_format, 'value') else str(q_format)
                format_counts[format_str] = format_counts.get(format_str, 0) + 1
        
        return {
            'field_distribution': field_counts,
            'format_distribution': format_counts,
            'total_questions': len(questions)
        }