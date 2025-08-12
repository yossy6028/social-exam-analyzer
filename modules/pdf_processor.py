"""
PDF処理モジュール
PDFファイルを画像に変換し、OCR処理の準備を行う
"""
import logging
from pathlib import Path
from typing import List, Tuple
from pdf2image import convert_from_path
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF処理クラス"""
    
    def __init__(self, dpi: int = 300):
        """
        初期化
        
        Args:
            dpi: 画像変換時の解像度
        """
        self.dpi = dpi
        
    def convert_pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """
        PDFを画像に変換
        
        Args:
            pdf_path: PDFファイルのパス
            
        Returns:
            変換された画像のリスト
        """
        try:
            logger.info(f"PDFを画像に変換中: {pdf_path}")
            images = convert_from_path(str(pdf_path), dpi=self.dpi)
            logger.info(f"{len(images)}ページの画像に変換完了")
            return images
        except Exception as e:
            logger.error(f"PDF変換エラー: {e}")
            raise
            
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        画像の前処理（OCR精度向上のため）
        
        Args:
            image: PIL Image
            
        Returns:
            前処理済みの画像
        """
        # グレースケール変換
        if image.mode != 'L':
            image = image.convert('L')
            
        # コントラスト調整
        np_image = np.array(image)
        # 簡単な二値化処理
        threshold = np.mean(np_image)
        np_image = np.where(np_image > threshold, 255, np_image)
        
        return Image.fromarray(np_image)
        
    def detect_orientation(self, image: Image.Image) -> str:
        """
        画像の向き（縦書き/横書き）を検出
        
        Args:
            image: PIL Image
            
        Returns:
            'vertical' or 'horizontal'
        """
        # 簡易的な判定（実際にはOCR結果から判定する方が正確）
        width, height = image.size
        
        # 日本の入試問題は通常縦長の用紙に縦書き
        if height > width * 1.2:
            return 'vertical'
        else:
            return 'horizontal'
            
    def split_double_page(self, image: Image.Image) -> Tuple[Image.Image, Image.Image]:
        """
        見開きページを分割（必要な場合）
        
        Args:
            image: PIL Image
            
        Returns:
            左ページ、右ページのタプル
        """
        width, height = image.size
        
        # 横長の場合は見開きの可能性
        if width > height * 1.5:
            mid_x = width // 2
            left_page = image.crop((0, 0, mid_x, height))
            right_page = image.crop((mid_x, 0, width, height))
            return left_page, right_page
        else:
            return image, None