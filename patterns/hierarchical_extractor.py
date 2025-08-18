"""
階層的問題構造抽出モジュール
大問→問→小問の3層構造を正確に認識
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class Question:
    """個別の問題を表すデータクラス"""
    level: str  # 'major', 'question', 'subquestion'
    number: str  # 問題番号
    text: str  # 問題文（最初の100文字）
    position: Tuple[int, int]  # テキスト内の位置
    marker_type: str  # マーカーの種類（boxed, plain, paren等）
    children: List['Question'] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)

class HierarchicalExtractor:
    """階層的な問題構造を抽出するクラス"""
    
    def __init__(self):
        """パターンを初期化"""
        # 大問検出パターン（優先度順）
        self.major_patterns = [
            # 日本工業大学駒場中学校形式（最優先）
            (r'^([1-9])\s+次の', 'nitkkoma_number_tsugi'),
            (r'^([１-９])\s+次の', 'nitkkoma_fullwidth_tsugi'),
            # OCRエラー対応：「13」→「3」など
            (r'^1([1-9])\s+次の', 'nitkkoma_ocr_error'),
            # 四角で囲まれた数字
            (r'□\s*([１-９1-9一-九])\s*□', 'boxed_square'),
            (r'■\s*([１-９1-9一-九])\s*■', 'boxed_filled'),
            (r'▢\s*([１-９1-9一-九])\s*▢', 'boxed_white'),
            (r'▣\s*([１-９1-9一-九])\s*▣', 'boxed_pattern'),
            # 括弧系
            (r'\[\s*([１-９1-9一-九])\s*\]', 'bracket'),
            (r'【\s*([一-九])\s*】', 'thick_bracket'),
            (r'〔\s*([１-９1-9一-九])\s*〕', 'round_bracket'),
            # その他の大問マーカー
            (r'^大問\s*([一-九１-９1-9])', 'daimon'),
            (r'^第([一-九１-９1-9])問', 'dai_mon'),
            (r'^([一-九])[、，]\s*次の', 'kanji_next'),
            # 独立した漢数字（行頭）
            (r'^([一-九])\s', 'standalone_kanji'),
        ]
        
        # 問（中レベル）検出パターン
        self.question_patterns = [
            (r'問\s*([１-９0-9]{1,2})', 'mon_number'),
            (r'問\s*([一-九十]{1,3})', 'mon_kanji'),
            (r'^([１-９][０-９]?)[．.、]', 'number_period'),
            (r'設問\s*([１-９0-9]{1,2})', 'setsumon'),
        ]
        
        # 小問検出パターン
        self.subquestion_patterns = [
            (r'\(([1-9][0-9]?)\)', 'paren_number'),
            (r'\(([a-z])\)', 'paren_lower'),
            (r'\(([A-Z])\)', 'paren_upper'),
            (r'\(([ア-ン])\)', 'paren_katakana'),
            (r'([①-⑳])', 'circle_number'),
            (r'([㋐-㋾])', 'circle_katakana'),
            (r'([ａ-ｚ])[．.、]', 'fullwidth_lower'),
            (r'([Ａ-Ｚ])[．.、]', 'fullwidth_upper'),
        ]
        
        # 数字変換マップ
        self.number_map = {
            '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
            '１': '1', '２': '2', '３': '3', '４': '4', '５': '5',
            '６': '6', '７': '7', '８': '8', '９': '9', '０': '0',
            '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
            '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
            '⑪': '11', '⑫': '12', '⑬': '13', '⑭': '14', '⑮': '15',
            '⑯': '16', '⑰': '17', '⑱': '18', '⑲': '19', '⑳': '20'
        }
    
    def extract_structure(self, text: str) -> List[Question]:
        """
        テキストから階層的な問題構造を抽出
        
        Args:
            text: 分析対象のテキスト
            
        Returns:
            大問のリスト（各大問は子要素として問と小問を持つ）
        """
        # Step 1: 大問を検出
        major_questions = self._extract_major_questions(text)
        
        # Step 2: 各大問の範囲内で問を検出
        for i, major in enumerate(major_questions):
            # 大問の範囲を特定
            start = major.position[0]
            end = major_questions[i + 1].position[0] if i + 1 < len(major_questions) else len(text)
            major_text = text[start:end]
            
            # 問を検出
            questions = self._extract_questions(major_text, start)
            major.children = questions
            
            # Step 3: 各問の範囲内で小問を検出
            for j, question in enumerate(questions):
                q_start = question.position[0] - start
                q_end = questions[j + 1].position[0] - start if j + 1 < len(questions) else len(major_text)
                question_text = major_text[q_start:q_end]
                
                # 小問を検出
                subquestions = self._extract_subquestions(question_text, question.position[0])
                question.children = subquestions
        
        return major_questions
    
    def _extract_major_questions(self, text: str) -> List[Question]:
        """大問を抽出"""
        major_questions = []
        
        for pattern, marker_type in self.major_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                number = self._normalize_number(match.group(1))
                major_questions.append(Question(
                    level='major',
                    number=number,
                    text=self._get_preview_text(text, match.end(), 100),
                    position=match.span(),
                    marker_type=marker_type
                ))
        
        # 位置でソート
        major_questions.sort(key=lambda x: x.position[0])
        
        # 重複を除去（位置が近いものは最初のものを採用）
        filtered = []
        for q in major_questions:
            if not filtered or q.position[0] - filtered[-1].position[0] > 50:
                filtered.append(q)
        
        return filtered
    
    def _extract_questions(self, text: str, offset: int) -> List[Question]:
        """問（中レベル）を抽出"""
        questions = []
        
        for pattern, marker_type in self.question_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                number = self._normalize_number(match.group(1))
                questions.append(Question(
                    level='question',
                    number=number,
                    text=self._get_preview_text(text, match.end(), 100),
                    position=(match.start() + offset, match.end() + offset),
                    marker_type=marker_type
                ))
        
        questions.sort(key=lambda x: x.position[0])
        
        # 重複除去
        filtered = []
        for q in questions:
            if not filtered or q.position[0] - filtered[-1].position[0] > 20:
                filtered.append(q)
        
        return filtered
    
    def _extract_subquestions(self, text: str, offset: int) -> List[Question]:
        """小問を抽出"""
        subquestions = []
        
        for pattern, marker_type in self.subquestion_patterns:
            for match in re.finditer(pattern, text):
                number = self._normalize_number(match.group(1))
                subquestions.append(Question(
                    level='subquestion',
                    number=number,
                    text=self._get_preview_text(text, match.end(), 50),
                    position=(match.start() + offset, match.end() + offset),
                    marker_type=marker_type
                ))
        
        subquestions.sort(key=lambda x: x.position[0])
        
        # 重複除去
        filtered = []
        for q in subquestions:
            if not filtered or q.position[0] - filtered[-1].position[0] > 10:
                filtered.append(q)
        
        return filtered
    
    def _normalize_number(self, number_str: str) -> str:
        """数字を正規化"""
        # 単一文字の変換
        if number_str in self.number_map:
            return self.number_map[number_str]
        
        # 漢数字の複雑な変換（十一、二十三など）
        if '十' in number_str:
            return self._convert_complex_kanji(number_str)
        
        # OCRエラー対応：「13」→「3」など（日工大駒場用）
        if len(number_str) == 2 and number_str.startswith('1') and number_str[1] in '123456789':
            return number_str[1]  # 2桁目を返す
        
        # 全角数字を半角に変換
        result = ''
        for char in number_str:
            if char in self.number_map:
                result += self.number_map[char]
            else:
                result += char
        
        return result if result else number_str
    
    def _convert_complex_kanji(self, kanji: str) -> str:
        """複雑な漢数字を変換"""
        if kanji == '十':
            return '10'
        
        # 十X形式（十一、十二など）
        if kanji.startswith('十'):
            ones = self.number_map.get(kanji[1], '0') if len(kanji) > 1 else '0'
            return f"1{ones}"
        
        # X十形式（二十、三十など）
        if kanji.endswith('十'):
            tens = self.number_map.get(kanji[0], '1')
            return f"{tens}0"
        
        # X十Y形式（二十三など）
        if '十' in kanji:
            parts = kanji.split('十')
            tens = self.number_map.get(parts[0], '1') if parts[0] else '1'
            ones = self.number_map.get(parts[1], '0') if len(parts) > 1 and parts[1] else '0'
            return f"{tens}{ones}"
        
        return kanji
    
    def _get_preview_text(self, text: str, start: int, length: int) -> str:
        """プレビューテキストを取得"""
        preview = text[start:start + length].strip()
        # 改行を空白に置換
        preview = re.sub(r'\s+', ' ', preview)
        if len(preview) == length:
            preview += '...'
        return preview
    
    def count_all_questions(self, structure: List[Question]) -> Dict[str, int]:
        """
        全問題数をカウント
        
        Args:
            structure: extract_structure()の結果
            
        Returns:
            レベル別の問題数
        """
        counts = {
            'major': len(structure),
            'question': 0,
            'subquestion': 0,
            'total': len(structure)
        }
        
        for major in structure:
            counts['question'] += len(major.children)
            counts['total'] += len(major.children)
            
            for question in major.children:
                counts['subquestion'] += len(question.children)
                counts['total'] += len(question.children)
        
        return counts
    
    def format_structure(self, structure: List[Question]) -> str:
        """
        構造を見やすく整形
        
        Args:
            structure: extract_structure()の結果
            
        Returns:
            整形された文字列
        """
        lines = []
        
        for major in structure:
            lines.append(f"【大問{major.number}】 ({major.marker_type})")
            lines.append(f"  {major.text[:50]}...")
            
            for question in major.children:
                lines.append(f"  問{question.number} ({question.marker_type})")
                lines.append(f"    {question.text[:40]}...")
                
                if question.children:
                    sub_numbers = [f"({sub.number})" for sub in question.children]
                    lines.append(f"    小問: {', '.join(sub_numbers[:10])}")
                    if len(sub_numbers) > 10:
                        lines.append(f"         他{len(sub_numbers) - 10}問")
        
        return '\n'.join(lines)
    
    def extract_with_themes(self, text: str) -> List[Question]:
        """
        テーマ抽出も含めた構造抽出
        
        Args:
            text: 分析対象のテキスト
            
        Returns:
            テーマ付きの問題構造
        """
        # まず通常の構造抽出
        structure = self.extract_structure(text)
        
        # social_termsをインポート
        try:
            from .social_terms import extract_important_terms, get_themes_from_terms
            
            # 各大問でテーマを抽出
            for major in structure:
                # 大問の範囲のテキストを取得
                start = major.position[0]
                end_pos = major.position[0] + 2000  # 大問の最初の2000文字
                major_text = text[start:min(end_pos, len(text))]
                
                # 重要語句を抽出
                terms = extract_important_terms(major_text)
                if terms:
                    theme_info = get_themes_from_terms(terms, top_n=5)
                    major.themes = theme_info['key_terms']
        except ImportError:
            pass  # social_termsが使えない場合はスキップ
        
        return structure