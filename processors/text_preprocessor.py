"""
テキスト前処理モジュール
すべてのアナライザーで共通のテキスト前処理を提供
"""
import re
import unicodedata
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """
    テキスト前処理クラス
    OCRテキストのクリーニング、正規化、セグメント化を担当
    """
    
    def __init__(self):
        """初期化"""
        self._init_patterns()
    
    def _init_patterns(self):
        """前処理用パターンの初期化"""
        # OCRアーティファクトパターン
        self.page_marker_pattern = re.compile(r'={3,}\s*ページ\s*\d+\s*={3,}')
        self.ocr_noise_pattern = re.compile(r'[〔〕｜│┃┌┐└┘├┤┬┴┼]')
        self.excessive_spaces = re.compile(r'\s{3,}')
        self.control_chars = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]')
        
        # 正規化パターン
        self.multiple_newlines = re.compile(r'\n{3,}')
        self.trailing_spaces = re.compile(r'[ \t]+$', re.MULTILINE)
        self.leading_spaces = re.compile(r'^[ \t]+', re.MULTILINE)
    
    def preprocess(self, text: str, 
                  remove_ocr_artifacts: bool = True,
                  normalize_unicode: bool = True,
                  fix_line_breaks: bool = True,
                  remove_page_markers: bool = True) -> str:
        """
        テキストの前処理を実行
        
        Args:
            text: 処理対象のテキスト
            remove_ocr_artifacts: OCRアーティファクトを除去
            normalize_unicode: Unicode正規化を実行
            fix_line_breaks: 改行を修正
            remove_page_markers: ページマーカーを除去
            
        Returns:
            前処理済みテキスト
        """
        if not text:
            return ""
        
        original_length = len(text)
        
        # Unicode正規化
        if normalize_unicode:
            text = self.normalize_unicode(text)
        
        # 制御文字の除去
        text = self.remove_control_characters(text)
        
        # OCRアーティファクトの除去
        if remove_ocr_artifacts:
            text = self.remove_ocr_artifacts(text)
        
        # ページマーカーの除去
        if remove_page_markers:
            text = self.remove_page_markers(text)
        
        # 改行の修正
        if fix_line_breaks:
            text = self.fix_line_breaks(text)
        
        # 空白の正規化
        text = self.normalize_whitespace(text)
        
        processed_length = len(text)
        reduction_rate = (1 - processed_length / original_length) * 100 if original_length > 0 else 0
        
        logger.debug(f"Text preprocessing: {original_length} -> {processed_length} chars "
                    f"({reduction_rate:.1f}% reduction)")
        
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """
        Unicode正規化（NFKC）
        全角英数字を半角に、半角カナを全角に変換
        """
        # NFKC正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 追加の文字正規化
        replacements = {
            '～': '〜',  # 波ダッシュ
            '－': 'ー',  # 長音記号
            '｢': '「',   # 括弧
            '｣': '」',
            '（': '（',  # 全角括弧の統一
            '）': '）',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def remove_control_characters(self, text: str) -> str:
        """制御文字を除去（改行・タブは保持）"""
        return self.control_chars.sub('', text)
    
    def remove_ocr_artifacts(self, text: str) -> str:
        """OCR特有のノイズを除去"""
        # 罫線文字の除去
        text = self.ocr_noise_pattern.sub('', text)
        
        # 孤立した記号の除去
        text = re.sub(r'(?<!\S)[・。、](?!\S)', '', text)
        
        # 不自然な記号の連続を除去
        text = re.sub(r'[^\w\s]{5,}', '', text)
        
        return text
    
    def remove_page_markers(self, text: str) -> str:
        """ページマーカーを除去"""
        # === ページ X === 形式
        text = self.page_marker_pattern.sub('', text)
        
        # ページ番号のみの行
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # ヘッダー・フッター（よくあるパターン）
        text = re.sub(r'^.{0,10}ページ.{0,10}$', '', text, flags=re.MULTILINE)
        
        return text
    
    def fix_line_breaks(self, text: str) -> str:
        """不適切な改行を修正"""
        # 文中の不自然な改行を除去（句読点で終わらない改行）
        text = re.sub(r'([^。、！？\n])\n([^「『（\[【])', r'\1\2', text)
        
        # 連続する改行を2つまでに制限
        text = self.multiple_newlines.sub('\n\n', text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """空白文字を正規化"""
        # 行末の空白を除去
        text = self.trailing_spaces.sub('', text)
        
        # 行頭の空白を除去（インデントは保持）
        text = self.leading_spaces.sub('', text)
        
        # 連続する空白を1つに
        text = self.excessive_spaces.sub(' ', text)
        
        # 全角スペースを統一
        text = re.sub(r'　+', '　', text)
        
        return text.strip()
    
    def segment_text(self, text: str, max_length: int = 1000) -> List[str]:
        """
        テキストを適切な長さのセグメントに分割
        
        Args:
            text: 分割対象のテキスト
            max_length: セグメントの最大文字数
            
        Returns:
            テキストセグメントのリスト
        """
        if len(text) <= max_length:
            return [text]
        
        segments = []
        
        # 段落で分割を試みる
        paragraphs = text.split('\n\n')
        current_segment = ""
        
        for paragraph in paragraphs:
            if len(current_segment) + len(paragraph) + 2 <= max_length:
                if current_segment:
                    current_segment += "\n\n"
                current_segment += paragraph
            else:
                if current_segment:
                    segments.append(current_segment)
                
                # 段落が長すぎる場合は句点で分割
                if len(paragraph) > max_length:
                    sentences = self.split_by_sentence(paragraph)
                    current_segment = ""
                    
                    for sentence in sentences:
                        if len(current_segment) + len(sentence) <= max_length:
                            current_segment += sentence
                        else:
                            if current_segment:
                                segments.append(current_segment)
                            current_segment = sentence
                else:
                    current_segment = paragraph
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def split_by_sentence(self, text: str) -> List[str]:
        """テキストを文単位で分割"""
        # 句点での分割（ただし、括弧内の句点は除外）
        sentences = []
        current = ""
        paren_depth = 0
        
        for char in text:
            current += char
            
            if char in '「『（［【':
                paren_depth += 1
            elif char in '」』）］】':
                paren_depth = max(0, paren_depth - 1)
            elif char in '。！？' and paren_depth == 0:
                sentences.append(current)
                current = ""
        
        if current:
            sentences.append(current)
        
        return sentences
    
    def extract_metadata(self, text: str) -> dict:
        """
        テキストからメタデータを抽出
        
        Returns:
            メタデータ辞書（学校名、年度、科目など）
        """
        metadata = {}
        
        # 最初の数行からメタデータを抽出
        first_lines = '\n'.join(text.split('\n')[:10])
        
        # 学校名パターン
        school_patterns = [
            r'([\w]+)中学校',
            r'([\w]+)中学',
            r'([\w]+)学園',
            r'([\w]+)学院'
        ]
        
        for pattern in school_patterns:
            match = re.search(pattern, first_lines)
            if match:
                metadata['school'] = match.group(1)
                break
        
        # 科目パターン
        subject_match = re.search(r'(国語|算数|理科|社会|英語)', first_lines)
        if subject_match:
            metadata['subject'] = subject_match.group(1)
        
        # 試験タイプ
        if '入学試験' in first_lines or '入試' in first_lines:
            metadata['exam_type'] = '入学試験'
        elif '模試' in first_lines:
            metadata['exam_type'] = '模擬試験'
        
        return metadata
    
    def clean_for_analysis(self, text: str) -> str:
        """
        分析用のクリーンなテキストを生成
        すべての前処理を適用
        """
        return self.preprocess(
            text,
            remove_ocr_artifacts=True,
            normalize_unicode=True,
            fix_line_breaks=True,
            remove_page_markers=True
        )