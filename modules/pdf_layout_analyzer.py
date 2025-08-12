"""
PDFレイアウト解析モジュール
PDFの物理的なレイアウト（段組み、配置）を解析して、
OCR結果の正しい読み順を推定する
"""

import os
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.app_config import get_config

# PyMuPDFのインポートを試みる
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    import warnings
    warnings.warn(
        "PyMuPDFがインストールされていません。"
        "PDFレイアウト解析機能を使用するには 'pip install PyMuPDF' を実行してください。"
    )

# PILのインポートを試みる
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    import warnings
    warnings.warn(
        "Pillowがインストールされていません。"
        "画像処理機能を使用するには 'pip install Pillow' を実行してください。"
    )

# numpyのインポートを試みる
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """テキストブロックの情報"""
    text: str
    x0: float  # 左端
    y0: float  # 上端
    x1: float  # 右端
    y1: float  # 下端
    page: int
    block_type: str  # 'text', 'question', 'source', 'title'
    column: int = 0  # 段組みの列番号（0: 左/単一、1: 右）
    
    @property
    def width(self):
        return self.x1 - self.x0
    
    @property
    def height(self):
        return self.y1 - self.y0
    
    @property
    def center_x(self):
        return (self.x0 + self.x1) / 2
    
    @property
    def center_y(self):
        return (self.y0 + self.y1) / 2


class PDFLayoutAnalyzer:
    """PDFのレイアウトを解析するクラス"""
    
    def __init__(self, pdf_path: str):
        """
        初期化
        
        Args:
            pdf_path: PDFファイルのパス
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDFが必要です。'pip install PyMuPDF' を実行してください。"
            )
        
        self.pdf_path = pdf_path
        self.doc = None
        self.text_blocks = []
        self.page_layouts = []
        self.config = get_config()
        
        # ファイルサイズをチェック
        self._check_file_size()
    
    def _check_file_size(self):
        """ファイルサイズをチェック"""
        file_size_mb = os.path.getsize(self.pdf_path) / (1024 * 1024)
        max_size_mb = self.config.get_pdf_max_size_mb()
        
        if file_size_mb > max_size_mb:
            raise ValueError(
                f"PDFファイルサイズが大きすぎます: "
                f"{file_size_mb:.1f}MB (最大: {max_size_mb}MB)"
            )
    
    def analyze(self) -> Dict:
        """
        PDFのレイアウトを解析
        
        Returns:
            解析結果
        """
        try:
            self.doc = fitz.open(self.pdf_path)
            
            # ページ数をチェック
            max_pages = self.config.get('pdf.max_pages', 100)
            if len(self.doc) > max_pages:
                logger.warning(
                    f"PDFのページ数が多いため、最初の{max_pages}ページのみ解析します"
                )
                page_range = range(min(len(self.doc), max_pages))
            else:
                page_range = range(len(self.doc))
            
            # 各ページを解析
            for page_num in page_range:
                page = self.doc[page_num]
                page_blocks = self._analyze_page(page, page_num)
                self.text_blocks.extend(page_blocks)
                
                # ページレイアウトを判定
                layout_type = self._detect_page_layout(page_blocks)
                self.page_layouts.append({
                    'page': page_num,
                    'layout': layout_type,
                    'blocks': len(page_blocks)
                })
            
            # 読み順を決定
            ordered_blocks = self._determine_reading_order(self.text_blocks)
            
            # セクションを識別
            sections = self._identify_sections(ordered_blocks)
            
            return {
                'total_pages': len(self.doc),
                'text_blocks': len(self.text_blocks),
                'page_layouts': self.page_layouts,
                'sections': sections,
                'ordered_text': self._blocks_to_text(ordered_blocks)
            }
            
        except Exception as e:
            logger.error(f"PDF解析エラー: {e}")
            raise
        finally:
            if self.doc:
                self.doc.close()
    
    def _analyze_page(self, page, page_num: int) -> List[TextBlock]:
        """
        1ページを解析
        
        Args:
            page: PyMuPDFのページオブジェクト
            page_num: ページ番号
            
        Returns:
            テキストブロックのリスト
        """
        blocks = []
        
        # ページの高さとヘッダー/フッター領域を定義
        page_height = page.rect.height
        # configからマージンを取得、存在しない場合はデフォルト値を使用
        header_margin = page_height * self.config.get('pdf.layout.header_margin', 0.10)
        footer_margin = page_height * (1 - self.config.get('pdf.layout.footer_margin', 0.10))

        # テキストブロックを抽出
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if block["type"] == 0:  # テキストブロック
                # ブロックのY座標を取得
                y0 = block["bbox"][1]
                y1 = block["bbox"][3]

                # ヘッダー/フッター領域にあるブロックはスキップ
                if y1 < header_margin or y0 > footer_margin:
                    continue

                # ブロック内のテキストを結合
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                
                if block_text.strip():
                    # ブロックタイプを判定
                    block_type = self._classify_block(block_text)
                    
                    text_block = TextBlock(
                        text=block_text,
                        x0=block["bbox"][0],
                        y0=y0,
                        x1=block["bbox"][2],
                        y1=y1,
                        page=page_num,
                        block_type=block_type
                    )
                    
                    blocks.append(text_block)
        
        return blocks
    
    def _classify_block(self, text: str) -> str:
        """
        テキストブロックの種類を分類
        
        Args:
            text: テキスト内容
            
        Returns:
            ブロックタイプ
        """
        import re
        
        # 設問パターン
        if re.search(r'^問[一二三四五六七八九十0-9]', text.strip()):
            return 'question'
        
        # 出典パターン
        if re.search(r'[『「].*[』」].*による', text) or \
           re.search(r'――.*[『「].*[』」]', text):
            return 'source'
        
        # タイトルパターン（大問番号など）
        if re.match(r'^[一二三四五六七八九十]、', text.strip()) or \
           re.match(r'^第[一二三四五六七八九十]問', text.strip()):
            return 'title'
        
        return 'text'
    
    def _detect_page_layout(self, blocks: List[TextBlock]) -> str:
        """
        ページのレイアウトタイプを判定
        
        Args:
            blocks: ページ内のテキストブロック
            
        Returns:
            レイアウトタイプ（'single', 'two_column', 'mixed'）
        """
        if not blocks:
            return 'empty'
        
        # X座標の分布を調べる
        x_positions = [block.center_x for block in blocks]
        
        if not x_positions:
            return 'empty'
        
        # ページ幅を推定
        page_width = max(block.x1 for block in blocks)
        
        # 左右の列に分類
        left_blocks = [b for b in blocks if b.center_x < page_width / 2]
        right_blocks = [b for b in blocks if b.center_x >= page_width / 2]
        
        # 2段組みの判定
        if len(left_blocks) > 3 and len(right_blocks) > 3:
            # 左右のブロックが重なっているか確認
            left_y_range = [min(b.y0 for b in left_blocks), max(b.y1 for b in left_blocks)]
            right_y_range = [min(b.y0 for b in right_blocks), max(b.y1 for b in right_blocks)]
            
            # Y座標が重なっている場合は2段組み
            if left_y_range[0] < right_y_range[1] and right_y_range[0] < left_y_range[1]:
                return 'two_column'
        
        return 'single'
    
    def _determine_reading_order(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        テキストブロックの読み順を決定
        
        Args:
            blocks: すべてのテキストブロック
            
        Returns:
            読み順でソートされたブロック
        """
        if not blocks:
            return []
        
        # ページごとに処理
        pages = defaultdict(list)
        for block in blocks:
            pages[block.page].append(block)
        
        ordered = []
        for page_num in sorted(pages.keys()):
            page_blocks = pages[page_num]
            
            # ページレイアウトを確認
            layout = self._detect_page_layout(page_blocks)
            
            if layout == 'two_column':
                # 2段組みの場合
                ordered_page = self._order_two_column(page_blocks)
            else:
                # 単一列の場合
                ordered_page = self._order_single_column(page_blocks)
            
            ordered.extend(ordered_page)
        
        return ordered
    
    def _order_single_column(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        単一列のブロックを順序付け
        
        Args:
            blocks: ページ内のブロック
            
        Returns:
            順序付けされたブロック
        """
        # Y座標でソート（上から下）
        return sorted(blocks, key=lambda b: (b.y0, b.x0))
    
    def _order_two_column(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """
        2段組みのブロックを順序付け
        
        Args:
            blocks: ページ内のブロック
            
        Returns:
            順序付けされたブロック
        """
        if not blocks:
            return []
        
        # ページ幅を推定
        page_width = max(block.x1 for block in blocks)
        
        # 左右の列に分類
        left_column = []
        right_column = []
        
        for block in blocks:
            if block.center_x < page_width / 2:
                block.column = 0
                left_column.append(block)
            else:
                block.column = 1
                right_column.append(block)
        
        # 各列をY座標でソート
        left_column.sort(key=lambda b: b.y0)
        right_column.sort(key=lambda b: b.y0)
        
        # 特殊ケース：設問が右列に配置されている場合
        # （一部の入試問題では本文が左、設問が右に配置）
        left_has_questions = any(b.block_type == 'question' for b in left_column)
        right_has_questions = any(b.block_type == 'question' for b in right_column)
        
        if not left_has_questions and right_has_questions:
            # 本文（左）→ 設問（右）の順
            return left_column + right_column
        else:
            # 通常の2段組み（左→右）
            return left_column + right_column
    
    def _identify_sections(self, blocks: List[TextBlock]) -> List[Dict]:
        """
        テキストブロックからセクションを識別
        
        Args:
            blocks: 順序付けされたテキストブロック
            
        Returns:
            セクション情報のリスト
        """
        sections = []
        current_section = None
        
        for i, block in enumerate(blocks):
            # 大問の開始を検出
            if block.block_type == 'title':
                # 前のセクションを保存
                if current_section:
                    sections.append(current_section)
                
                # 新しいセクション開始
                current_section = {
                    'title': block.text.strip(),
                    'blocks': [block],
                    'source': None,
                    'questions': []
                }
            
            # 出典を検出
            elif block.block_type == 'source':
                if current_section:
                    current_section['source'] = block.text.strip()
                    current_section['blocks'].append(block)
                else:
                    # セクションがない場合は新規作成
                    current_section = {
                        'title': None,
                        'blocks': [block],
                        'source': block.text.strip(),
                        'questions': []
                    }
            
            # 設問を検出
            elif block.block_type == 'question':
                if current_section:
                    current_section['questions'].append(block.text.strip())
                    current_section['blocks'].append(block)
                else:
                    # セクションがない場合は新規作成
                    current_section = {
                        'title': None,
                        'blocks': [block],
                        'source': None,
                        'questions': [block.text.strip()]
                    }
            
            # 通常のテキスト
            else:
                if current_section:
                    current_section['blocks'].append(block)
                else:
                    # 最初のセクション
                    current_section = {
                        'title': None,
                        'blocks': [block],
                        'source': None,
                        'questions': []
                    }
        
        # 最後のセクションを保存
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _blocks_to_text(self, blocks: List[TextBlock]) -> str:
        """
        テキストブロックを文字列に変換
        
        Args:
            blocks: テキストブロックのリスト
            
        Returns:
            結合されたテキスト
        """
        text_parts = []
        prev_page = -1
        prev_column = -1
        
        for block in blocks:
            # ページが変わった場合
            if block.page != prev_page:
                text_parts.append(f"\n\n=== ページ {block.page + 1} ===\n")
                prev_page = block.page
                prev_column = -1
            
            # 段組みが変わった場合
            if hasattr(block, 'column') and block.column != prev_column:
                if block.column == 1:
                    text_parts.append("\n[右列]\n")
                prev_column = block.column
            
            # ブロックタイプを表示
            if block.block_type != 'text':
                text_parts.append(f"[{block.block_type}] ")
            
            text_parts.append(block.text)
            text_parts.append("\n")
        
        return "".join(text_parts)
    
    def extract_with_layout(self) -> str:
        """
        レイアウトを考慮してテキストを抽出
        
        Returns:
            レイアウトを保持したテキスト
        """
        result = self.analyze()
        return result['ordered_text']