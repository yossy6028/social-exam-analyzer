"""
PDF OCR処理モジュール
PDFファイルをGoogle Cloud Vision APIを使用してOCR処理し、テキストを抽出する
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import os

from .pdf_processor import PDFProcessor
from .ocr_handler import OCRHandler

logger = logging.getLogger(__name__)


class PDFOCRProcessor:
    """PDF OCR処理クラス"""
    
    def __init__(self, dpi: int = 300, credentials_path: Optional[str] = None):
        """
        初期化
        
        Args:
            dpi: PDF変換時の解像度
            credentials_path: Google Cloud認証情報のパス（省略時はADCを使用）
        """
        self.pdf_processor = PDFProcessor(dpi=dpi)
        self.ocr_handler = OCRHandler(credentials_path=credentials_path)
        self.dpi = dpi
        
    def process_pdf(self, pdf_path: Path, 
                   save_images: bool = False,
                   output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        PDFファイルをOCR処理してテキストを抽出
        
        Args:
            pdf_path: PDFファイルのパス
            save_images: 変換した画像を保存するか
            output_dir: 画像保存先ディレクトリ（save_images=Trueの場合）
            
        Returns:
            OCR結果の辞書
        """
        try:
            logger.info(f"PDF OCR処理開始: {pdf_path}")
            
            # PDFを画像に変換
            images = self.pdf_processor.convert_pdf_to_images(pdf_path)
            
            # 画像を保存（オプション）
            if save_images and output_dir:
                self._save_images(images, output_dir, pdf_path.stem)
            
            # 各ページをOCR処理
            results = {
                'file_path': str(pdf_path),
                'file_name': pdf_path.name,
                'total_pages': len(images),
                'pages': [],
                'full_text': ''
            }
            
            all_text = []
            
            for i, image in enumerate(images, 1):
                logger.info(f"ページ {i}/{len(images)} をOCR処理中...")
                
                # 画像の前処理
                processed_image = self.pdf_processor.preprocess_image(image)
                
                # OCR実行
                ocr_result = self.ocr_handler.extract_text_from_image(
                    processed_image,
                    language_hints=['ja']
                )
                
                # ページ結果を保存
                page_result = {
                    'page_number': i,
                    'text': ocr_result['full_text'],
                    'confidence': self._calculate_average_confidence(ocr_result),
                    'is_vertical': self.ocr_handler.detect_vertical_text(ocr_result),
                    'blocks': ocr_result.get('blocks', [])
                }
                
                results['pages'].append(page_result)
                all_text.append(f"=== ページ {i} ===\n{ocr_result['full_text']}")
                
            # 全ページのテキストを結合
            results['full_text'] = '\n\n'.join(all_text)
            
            logger.info(f"PDF OCR処理完了: 総文字数 {len(results['full_text'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"PDF OCR処理エラー: {e}")
            raise
            
    def process_pdf_to_text(self, pdf_path: Path) -> str:
        """
        PDFファイルをテキストに変換（シンプル版）
        
        Args:
            pdf_path: PDFファイルのパス
            
        Returns:
            抽出されたテキスト
        """
        results = self.process_pdf(pdf_path)
        return results['full_text']
        
    def _save_images(self, images: List[Image.Image], output_dir: Path, prefix: str):
        """
        画像を保存
        
        Args:
            images: 画像リスト
            output_dir: 保存先ディレクトリ
            prefix: ファイル名のプレフィックス
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, image in enumerate(images, 1):
            output_path = output_dir / f"{prefix}_page_{i:02d}.png"
            image.save(output_path)
            logger.info(f"画像を保存: {output_path}")
            
    def _calculate_average_confidence(self, ocr_result: Dict[str, Any]) -> float:
        """
        OCR結果の平均信頼度を計算
        
        Args:
            ocr_result: OCR結果
            
        Returns:
            平均信頼度（0.0-1.0）
        """
        confidences = []
        
        for block in ocr_result.get('blocks', []):
            if 'confidence' in block and block['confidence'] is not None:
                confidences.append(block['confidence'])
                
        if confidences:
            return sum(confidences) / len(confidences)
        else:
            return 0.0
            
    def detect_exam_structure(self, text: str) -> Dict[str, Any]:
        """
        入試問題の構造を検出
        
        Args:
            text: OCR抽出されたテキスト
            
        Returns:
            検出された構造情報
        """
        structure = {
            'has_multiple_sections': False,
            'sections': [],
            'question_count': 0,
            'has_answer_choices': False
        }
        
        # 大問の検出（一、二、三 または 1、2、3）
        import re
        
        # 漢数字の大問
        kanji_sections = re.findall(r'[一二三四五六七八九十]\s*[、。\s]', text)
        if kanji_sections:
            structure['has_multiple_sections'] = True
            structure['sections'] = kanji_sections
            
        # アラビア数字の大問
        arabic_sections = re.findall(r'^\s*\d+\s*[、。\s]', text, re.MULTILINE)
        if arabic_sections and not kanji_sections:
            structure['has_multiple_sections'] = True
            structure['sections'] = arabic_sections
            
        # 問題番号の検出
        question_patterns = [
            r'問\s*\d+',
            r'問\s*[一二三四五六七八九十]',
            r'\(\s*\d+\s*\)',
            r'【\s*\d+\s*】'
        ]
        
        for pattern in question_patterns:
            questions = re.findall(pattern, text)
            structure['question_count'] += len(questions)
            
        # 選択肢の検出
        choice_patterns = [
            r'[ア-オ]\s*[、。\s]',
            r'[A-E]\s*[、。\s]',
            r'[①-⑤]'
        ]
        
        for pattern in choice_patterns:
            if re.search(pattern, text):
                structure['has_answer_choices'] = True
                break
                
        return structure