"""
パターン抽出モジュール
出典情報や特定のパターンを抽出する
"""
import re
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class PatternExtractor:
    """パターン抽出クラス"""
    
    def __init__(self, source_patterns: List[str]):
        """
        初期化
        
        Args:
            source_patterns: 出典パターンのリスト
        """
        self.source_patterns = [re.compile(pattern) for pattern in source_patterns]
        
    def extract_source_info(self, text: str) -> Dict[str, Optional[str]]:
        """
        出典情報を抽出
        
        Args:
            text: 全文テキスト
            
        Returns:
            出典情報の辞書
        """
        result = {
            'author': None,
            'title': None,
            'publisher': None,
            'year': None,
            'raw_source': None
        }
        
        # 各パターンで検索
        for i, pattern in enumerate(self.source_patterns):
            match = pattern.search(text)
            if match:
                groups = match.groups()
                matched_text = match.group(0)
                
                # 武蔵特有のパターン処理
                if 'の文による' in matched_text:
                    # （新美南吉の文による）形式
                    result['author'] = groups[0].strip() if groups else None
                    result['raw_source'] = matched_text
                elif '『' in matched_text and '』' in matched_text:
                    # 作品名が含まれる場合
                    if len(groups) >= 2:
                        result['title'] = groups[0].strip()
                        result['author'] = groups[1].strip()
                    elif len(groups) >= 1:
                        result['title'] = groups[0].strip()
                    result['raw_source'] = matched_text
                elif len(groups) >= 2:
                    # 標準的な2要素パターン
                    result['author'] = groups[0].strip()
                    result['title'] = groups[1].strip()
                    result['raw_source'] = matched_text
                elif len(groups) >= 1:
                    # 1要素のみの場合
                    result['author'] = groups[0].strip()
                    result['raw_source'] = matched_text
                    
                # 有効な情報が抽出できた場合は終了
                if result['author'] or result['title']:
                    break
                    
        # 追加の情報抽出
        if result['raw_source']:
            # 出版社の抽出
            pub_match = re.search(r'（([^）]+社)）', result['raw_source'])
            if pub_match:
                result['publisher'] = pub_match.group(1)
                
            # 年の抽出
            year_match = re.search(r'(19|20)\d{2}年', result['raw_source'])
            if year_match:
                result['year'] = year_match.group(0)
                
        return result
        
    def extract_choice_count(self, question_text: str) -> Optional[int]:
        """
        選択肢の数を抽出
        
        Args:
            question_text: 設問テキスト
            
        Returns:
            選択肢数（4択、5択など）
        """
        # カタカナの選択肢
        katakana_choices = re.findall(r'[ア-ン]\s*[\.。、]', question_text)
        if katakana_choices:
            return len(katakana_choices)
            
        # アルファベットの選択肢
        alphabet_choices = re.findall(r'[A-H]\s*[\.。、]', question_text)
        if alphabet_choices:
            return len(alphabet_choices)
            
        # 数字の選択肢
        number_choices = re.findall(r'[①②③④⑤⑥⑦⑧⑨⑩]', question_text)
        if number_choices:
            return len(number_choices)
            
        return None
        
    def extract_character_limit(self, question_text: str) -> Optional[Tuple[int, int]]:
        """
        記述問題の文字数制限を抽出
        
        Args:
            question_text: 設問テキスト
            
        Returns:
            (最小文字数, 最大文字数)のタプル
        """
        # パターン: XX字以内、XX字程度、XX字〜YY字
        patterns = [
            (r'(\d+)字以内', lambda m: (0, int(m.group(1)))),
            (r'(\d+)字程度', lambda m: (int(int(m.group(1)) * 0.8), int(int(m.group(1)) * 1.2))),
            (r'(\d+)字〜(\d+)字', lambda m: (int(m.group(1)), int(m.group(2)))),
            (r'(\d+)字から(\d+)字', lambda m: (int(m.group(1)), int(m.group(2))))
        ]
        
        for pattern, extractor in patterns:
            match = re.search(pattern, question_text)
            if match:
                return extractor(match)
                
        return None
        
    def extract_answer_sheet_info(self, text: str) -> Dict[str, Any]:
        """
        解答用紙から情報を抽出
        
        Args:
            text: 解答用紙のOCRテキスト
            
        Returns:
            解答用紙情報の辞書
        """
        result = {
            'total_points': None,
            'question_points': {},
            'answer_formats': {}
        }
        
        # 総得点の抽出
        total_match = re.search(r'(\d+)点満点', text)
        if total_match:
            result['total_points'] = int(total_match.group(1))
            
        # 各問の配点抽出
        point_patterns = [
            r'問(\d+)[^\d]*(\d+)点',
            r'[（(](\d+)[）)][^\d]*(\d+)点',
            r'設問(\d+)[^\d]*(\d+)点'
        ]
        
        for pattern in point_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                q_num = match.group(1)
                points = int(match.group(2))
                result['question_points'][f'問{q_num}'] = points
                
        # 解答形式の検出
        # 記号欄の検出
        if re.search(r'[ア-ン]\s*○', text) or re.search(r'記号.*欄', text):
            result['answer_formats']['記号欄'] = True
            
        # 記述欄の検出（マス目の行数など）
        grid_match = re.search(r'(\d+)行', text)
        if grid_match:
            result['answer_formats']['記述行数'] = int(grid_match.group(1))
            
        return result