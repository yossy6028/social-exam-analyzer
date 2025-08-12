"""
拡張版コンテンツ抽出モジュール
設問番号の連続性チェックとPDFレイアウト解析を統合
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .final_content_extractor import FinalContentExtractor
from .question_validator import QuestionValidator
# PDFLayoutAnalyzerを条件付きでインポート
try:
    from .pdf_layout_analyzer import PDFLayoutAnalyzer
    PDF_LAYOUT_AVAILABLE = True
except ImportError:
    PDF_LAYOUT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PDFLayoutAnalyzerが利用できません。PDFレイアウト解析機能が制限されます。")

logger = logging.getLogger(__name__)


class EnhancedContentExtractor(FinalContentExtractor):
    """拡張版コンテンツ抽出クラス"""
    
    def __init__(self):
        """初期化"""
        super().__init__()
        self.validator = QuestionValidator()
        self.pdf_analyzer = None
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDFファイルから直接コンテンツを抽出
        
        Args:
            pdf_path: PDFファイルのパス
            
        Returns:
            抽出された内容
        """
        logger.info(f"PDFファイルを解析: {pdf_path}")
        
        # PDFレイアウト解析
        try:
            if not PDF_LAYOUT_AVAILABLE:
                raise ImportError("PDFLayoutAnalyzerが利用できません")
            
            self.pdf_analyzer = PDFLayoutAnalyzer(pdf_path)
            layout_result = self.pdf_analyzer.analyze()
            
            # レイアウトを考慮したテキスト
            text = layout_result['ordered_text']
            
            # レイアウト情報を保持
            self.layout_info = layout_result
            
            logger.info(f"PDFレイアウト解析完了: {layout_result['total_pages']}ページ、"
                       f"{layout_result['text_blocks']}ブロック")
        except Exception as e:
            logger.warning(f"PDFレイアウト解析に失敗、通常のテキスト抽出を使用: {e}")
            # フォールバック：OCRテキストを使用
            text = self._get_ocr_text(pdf_path)
            self.layout_info = None
        
        # コンテンツ抽出
        result = self.extract_all_content(text)
        
        # PDFレイアウト情報を追加
        if self.layout_info:
            result['layout_info'] = {
                'total_pages': self.layout_info['total_pages'],
                'page_layouts': self.layout_info['page_layouts']
            }
        
        return result
    
    def extract_all_content(self, text: str) -> Dict[str, Any]:
        """
        全文から内容を抽出（拡張版）
        
        Args:
            text: 入試問題の全テキスト
            
        Returns:
            抽出された内容
        """
        # 基本の抽出処理
        result = super().extract_all_content(text)
        
        # 設問の連続性を検証
        validation_result = self.validator.validate_section_questions(result['sections'])
        
        # 検証結果を表示
        self.validator.display_validation_results(validation_result)
        
        # 連続性に基づいてセクションを統合
        if not validation_result['valid']:
            logger.info("設問番号の連続性に基づいてセクションを再構成")
            merged_sections = self.validator.merge_sections_by_continuity(result['sections'])
            
            # 統合前後の比較
            logger.info(f"セクション数: {len(result['sections'])} → {len(merged_sections)}")
            
            # 統合後のセクションで再集計
            result = self._recalculate_with_merged_sections(result, merged_sections)
        
        # 検証結果を追加
        result['validation'] = validation_result
        
        return result
    
    def _recalculate_with_merged_sections(self, original_result: Dict, 
                                         merged_sections: List[Dict]) -> Dict[str, Any]:
        """
        統合されたセクションで結果を再計算
        
        Args:
            original_result: 元の結果
            merged_sections: 統合後のセクション
            
        Returns:
            再計算された結果
        """
        result = {
            'total_characters': original_result['total_characters'],
            'total_questions': 0,
            'sections': [],
            'question_types': {
                '選択': 0,
                '記述': 0,
                '抜き出し': 0,
                '漢字・語句': 0
            }
        }
        
        # 各セクションを処理
        for i, section in enumerate(merged_sections):
            # セクション番号を更新
            section['number'] = i + 1
            
            # 設問数を再集計
            questions = section.get('questions', [])
            result['total_questions'] += len(questions)
            
            # 設問タイプを再分類
            for q in questions:
                q_type = q.get('type', '記述')
                if q_type in result['question_types']:
                    result['question_types'][q_type] += 1
            
            result['sections'].append(section)
        
        # 元の検証情報などを引き継ぐ
        if 'layout_info' in original_result:
            result['layout_info'] = original_result['layout_info']
        
        return result
    
    def _get_ocr_text(self, pdf_path: str) -> str:
        """
        PDFに対応するOCRテキストを取得
        
        Args:
            pdf_path: PDFファイルのパス
            
        Returns:
            OCRテキスト
        """
        # PDFファイル名から対応するテキストファイルを推定
        pdf_path = Path(pdf_path)
        
        # いくつかの可能なテキストファイルパスを試す
        possible_paths = [
            pdf_path.with_suffix('.txt'),
            pdf_path.parent / f"{pdf_path.stem}.txt",
            # 設定から動的にパスを取得
            Path.home() / "Desktop" / "01_仕事 (Work)" / "オンライン家庭教師資料" / "過去問" / "2025過去問" / f"{pdf_path.stem}.txt"
        ]
        
        for text_path in possible_paths:
            if text_path.exists():
                logger.info(f"OCRテキストファイルを使用: {text_path}")
                with open(text_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        logger.warning(f"OCRテキストファイルが見つかりません: {pdf_path}")
        return ""
    
    def analyze_with_validation(self, text: str, school_name: str = None) -> Dict[str, Any]:
        """
        検証付きで分析を実行
        
        Args:
            text: 分析するテキスト
            school_name: 学校名（オプション）
            
        Returns:
            分析結果
        """
        result = self.extract_all_content(text)
        
        # 学校名が指定されている場合は追加
        if school_name:
            result['school_name'] = school_name
        
        # 詳細な分析レポートを生成
        report = self._generate_analysis_report(result)
        result['report'] = report
        
        return result
    
    def _generate_analysis_report(self, result: Dict[str, Any]) -> str:
        """
        分析レポートを生成
        
        Args:
            result: 分析結果
            
        Returns:
            レポート文字列
        """
        lines = []
        lines.append("="*60)
        lines.append("入試問題分析レポート")
        lines.append("="*60)
        
        # 基本情報
        lines.append(f"\n【基本情報】")
        lines.append(f"総文字数: {result.get('total_characters', 0):,}")
        lines.append(f"総設問数: {result.get('total_questions', 0)}")
        lines.append(f"セクション数: {len(result.get('sections', []))}")
        
        # レイアウト情報
        if 'layout_info' in result:
            lines.append(f"\n【PDFレイアウト】")
            lines.append(f"総ページ数: {result['layout_info']['total_pages']}")
            for page_info in result['layout_info']['page_layouts']:
                lines.append(f"  ページ{page_info['page']+1}: "
                           f"{page_info['layout']}レイアウト、"
                           f"{page_info['blocks']}ブロック")
        
        # セクション詳細
        lines.append(f"\n【セクション詳細】")
        for section in result.get('sections', []):
            lines.append(f"\n◆ セクション{section['number']}:")
            
            if section.get('source'):
                lines.append(f"  出典: {section['source']['author']} "
                           f"『{section['source']['work']}』")
            else:
                lines.append(f"  出典: なし")
            
            lines.append(f"  ジャンル: {section.get('genre', '不明')}")
            lines.append(f"  テーマ: {section.get('theme', '不明')}")
            lines.append(f"  文字数: {section.get('characters', 0):,}")
            lines.append(f"  設問数: {len(section.get('questions', []))}")
            
            # 統合情報
            if 'merged_from' in section:
                lines.append(f"  ※ セクション{section['merged_from']}を統合")
            
            # 設問番号
            questions = section.get('questions', [])
            if questions:
                q_numbers = [q.get('number', '?') for q in questions]
                lines.append(f"  設問番号: {', '.join(q_numbers)}")
        
        # 検証結果
        if 'validation' in result:
            validation = result['validation']
            lines.append(f"\n【検証結果】")
            
            if validation['valid']:
                lines.append("✅ 設問番号の連続性: 問題なし")
            else:
                lines.append("⚠️  設問番号の連続性: 問題あり")
                for warning in validation['warnings']:
                    lines.append(f"  - {warning}")
            
            if validation['suggestions']:
                lines.append("\n【改善提案】")
                for suggestion in validation['suggestions']:
                    lines.append(f"  💡 {suggestion}")
        
        # 問題タイプ別統計
        lines.append(f"\n【問題タイプ別統計】")
        for q_type, count in result.get('question_types', {}).items():
            lines.append(f"  {q_type}: {count}問")
        
        lines.append("="*60)
        
        return "\n".join(lines)