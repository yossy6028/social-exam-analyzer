"""
改善された問題抽出モジュール
大問・小問の階層構造を正確に認識
"""

import re
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImprovedQuestionExtractor:
    """改善された問題抽出器"""
    
    def __init__(self):
        # 大問パターン
        self.major_patterns = [
            re.compile(r'^(\d+)[\.。]\s*(.+?)$', re.MULTILINE),  # 1. 次の〜
            re.compile(r'^[一二三四五六七八九十]+[\.。]\s*(.+?)$', re.MULTILINE),  # 一. 次の〜
            re.compile(r'^第(\d+)問\s*(.+?)$', re.MULTILINE),  # 第1問
            re.compile(r'^大問(\d+)\s*(.+?)$', re.MULTILINE),  # 大問1
            re.compile(r'^\[(\d+)\]\s*(.+?)$', re.MULTILINE),  # [1] 次の〜
            re.compile(r'^【(\d+)】\s*(.+?)$', re.MULTILINE),  # 【1】次の〜
        ]
        
        # 小問パターン（優先順位順）
        self.minor_patterns = [
            re.compile(r'問\s*([０-９\d]+)[\s\.\:：　]*(.+?)(?=問\s*[０-９\d]+|$)', re.DOTALL),
            re.compile(r'\(([０-９\d]+)\)\s*(.+?)(?=\([０-９\d]+\)|$)', re.DOTALL),
            re.compile(r'設問\s*([０-９\d]+)[\s\.\:：　]*(.+?)(?=設問\s*[０-９\d]+|$)', re.DOTALL),
        ]
        
        # クリーニングパターン
        self.cleaning_patterns = [
            # 試験の注意事項
            re.compile(r'【注意】[\s\S]*?問題は次のページから始まります。'),
            re.compile(r'令和\d+年度[\s\S]*?\(問題用紙\)'),
            re.compile(r'注意[\s\S]*?(?=\d+\.|$)'),
            re.compile(r'\d+\.\s*指示があるまで[\s\S]*?(?=\d+\.|$)'),
            re.compile(r'\d+\.\s*問題は\d+[\s\S]*?(?=\d+\.|$)'),
            re.compile(r'答えはすべて解答用紙[\s\S]*?(?=\d+\.|$)'),
            # ページ番号など
            re.compile(r'^\d+\s*$', re.MULTILINE),
            re.compile(r'^-\s*\d+\s*-\s*$', re.MULTILINE),
        ]
    
    def clean_text(self, text: str) -> str:
        """テキストのクリーニング"""
        cleaned = text
        for pattern in self.cleaning_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # 連続する空行を削除
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """問題を階層的に抽出"""
        questions = []
        cleaned_text = self.clean_text(text)
        
        # まず大問を探す
        major_sections = self._find_major_sections(cleaned_text)
        
        if major_sections:
            # 大問ごとに小問を抽出
            for major_num, section_text in major_sections:
                minor_questions = self._extract_minor_questions(section_text)
                
                if minor_questions:
                    for minor_num, q_text in minor_questions:
                        # 全角数字を半角に変換
                        minor_num = self._normalize_number(minor_num)
                        questions.append((f"大問{major_num}-問{minor_num}", q_text))
                else:
                    # 小問が見つからない場合は大問全体を1つの問題として扱う
                    if len(section_text.strip()) > 20:
                        questions.append((f"大問{major_num}", section_text[:500]))
        else:
            # 大問構造がない場合は全体から小問を探す
            logger.info("大問構造が見つかりません。全体から問題を抽出します。")
            minor_questions = self._extract_minor_questions(cleaned_text)
            
            # 問題番号のリセットを検出して大問を推定
            questions = self._detect_resets_and_assign_major(minor_questions)
        
        # 重複を除去
        questions = self._remove_duplicates(questions)
        
        logger.info(f"抽出された問題数: {len(questions)}")
        return questions
    
    def _find_major_sections(self, text: str) -> List[Tuple[str, str]]:
        """大問セクションを見つける"""
        major_sections = []
        
        for pattern in self.major_patterns:
            matches = list(pattern.finditer(text))
            if matches:
                logger.debug(f"大問パターンマッチ: {len(matches)}件")
                
                for i, match in enumerate(matches):
                    major_num = match.group(1) if match.lastindex >= 1 else str(i + 1)
                    start = match.start()
                    end = matches[i + 1].start() if i < len(matches) - 1 else len(text)
                    
                    section_text = text[start:end]
                    major_sections.append((major_num, section_text))
                
                break  # 最初にマッチしたパターンを使用
        
        return major_sections
    
    def _extract_minor_questions(self, text: str) -> List[Tuple[str, str]]:
        """小問を抽出"""
        minor_questions = []
        
        for pattern in self.minor_patterns:
            matches = pattern.findall(text)
            if matches:
                for num, q_text in matches:
                    q_text = self._clean_question_text(q_text)
                    if self._is_valid_question(q_text):
                        minor_questions.append((num, q_text))
                
                if minor_questions:
                    break  # 最初にマッチしたパターンを使用
        
        return minor_questions
    
    def _detect_resets_and_assign_major(self, minor_questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """問題番号のリセットを検出して大問を割り当て"""
        if not minor_questions:
            return []
        
        result = []
        current_major = 1
        previous_num = 0
        
        for num_str, q_text in minor_questions:
            num = int(self._normalize_number(num_str))
            
            # リセット検出
            if num == 1 and previous_num >= 2:
                current_major += 1
                logger.debug(f"問題番号リセット検出: 大問{current_major}へ")
            
            result.append((f"大問{current_major}-問{num}", q_text))
            previous_num = num
        
        return result
    
    def _normalize_number(self, num_str: str) -> str:
        """全角数字を半角に変換"""
        trans_table = str.maketrans('０１２３４５６７８９', '0123456789')
        return num_str.translate(trans_table)
    
    def _clean_question_text(self, text: str) -> str:
        """問題文をクリーニング"""
        # 選択肢の整形
        text = re.sub(r'([アイウエ])\s*\.\s*', r'\1. ', text)
        
        # 改行の整理
        text = re.sub(r'\n+', '\n', text)
        
        # 余分な空白の削除
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def _is_valid_question(self, text: str) -> bool:
        """有効な問題文かどうか判定"""
        # 短すぎるテキストは無効
        if len(text.strip()) < 10:
            return False
        
        # 数値データのみの場合は無効
        if re.match(r'^[\d\s\.\,\%]+$', text.strip()):
            return False
        
        # 問題文らしいキーワードがあるか
        question_keywords = [
            '答えなさい', '選びなさい', '説明しなさい', '述べなさい',
            '次の', '空らん', '下線', '適切な', '正しい', 'まちがって',
            '地図', '表', 'グラフ', '図', '資料', '文章',
            'あてはまる', 'について', 'に関して'
        ]
        
        has_keywords = any(keyword in text for keyword in question_keywords)
        is_long_enough = len(text.strip()) >= 30
        
        return has_keywords or is_long_enough
    
    def _remove_duplicates(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """重複を除去"""
        seen = set()
        unique_questions = []
        
        for q_num, q_text in questions:
            # 問題文の最初の50文字をキーとして使用
            key = q_text[:50] if len(q_text) > 50 else q_text
            if key not in seen:
                seen.add(key)
                unique_questions.append((q_num, q_text))
            else:
                logger.debug(f"重複除去: {q_num}")
        
        return unique_questions