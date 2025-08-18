#!/usr/bin/env python3
"""
改善された問題抽出器 v3（修正版）
解答用紙除外と問題番号重複防止を実装
"""

import re
import logging
from typing import List, Tuple, Optional
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from patterns.hierarchical_extractor_fixed import HierarchicalExtractorFixed, Question
from patterns.social_terms import extract_important_terms, get_themes_from_terms

logger = logging.getLogger(__name__)


class ImprovedQuestionExtractorV3:
    """改善された問題抽出器v3（修正版）"""
    
    def __init__(self):
        """初期化"""
        self.hierarchical_extractor = HierarchicalExtractorFixed()
        
        # 全角→半角変換テーブル
        self.z2h = str.maketrans({
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9'
        })
        
        # 無効なテーマパターン
        self.invalid_theme_patterns = [
            r'受験番号氏名',
            r'漢字四字',
            r'総合総合',
            r'解答用紙',
            r'記号問\d+',
            r'名称問\d+',
            r'平野\(漢字\)',
            r'\(漢字四字\)',
            r'の業績$',  # 「〜の業績」で終わるもの
        ]
        
        self.compiled_invalid_patterns = [re.compile(pattern) for pattern in self.invalid_theme_patterns]
        
        logger.info("ImprovedQuestionExtractorV3 初期化完了")
    
    def extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """
        テキストから問題を抽出（修正版）
        
        Args:
            text: OCRされたテキスト
            
        Returns:
            [(問題ID, 問題文), ...] のリスト
        """
        questions = []
        
        try:
            # 階層構造を抽出（修正版）
            structure = self.hierarchical_extractor.extract_structure(text)
            
            # 構造をフラット化して問題リストに変換
            for major in structure:
                major_num = self._normalize_number(major.number)
                
                # 大問レベルの問題（長い場合のみ）
                if major.text and len(major.text) > 20:
                    questions.append((f"大問{major_num}", major.text[:200]))
                
                # 問レベル
                for question in major.children:
                    q_num = self._normalize_number(question.number)
                    q_id = f"大問{major_num}-問{q_num}"
                    q_text = question.text[:500] if question.text else ""
                    
                    # 小問がある場合は小問も含める
                    if question.children:
                        sub_info = f" (小問{len(question.children)}個: "
                        sub_nums = [self._normalize_number(sub.number) for sub in question.children[:5]]
                        sub_info += ", ".join(sub_nums)
                        if len(question.children) > 5:
                            sub_info += f"...他{len(question.children)-5}個"
                        sub_info += ")"
                        q_text += sub_info
                    
                    if q_text and len(q_text) > 10:
                        questions.append((q_id, q_text))
                    
                    # 小問レベル（重要なものだけ）
                    for i, subquestion in enumerate(question.children[:3]):
                        sub_num = self._normalize_number(subquestion.number)
                        sub_id = f"大問{major_num}-問{q_num}-({sub_num})"
                        sub_text = subquestion.text[:200] if subquestion.text else ""
                        if sub_text and len(sub_text) > 15:
                            questions.append((sub_id, sub_text))
            
            logger.info(f"ImprovedQuestionExtractorV3: {len(questions)}問を抽出")
            
            # デバッグ用：検出した問題の詳細
            if logger.isEnabledFor(logging.DEBUG):
                counts = self.hierarchical_extractor.count_all_questions(structure)
                logger.debug(f"階層別: 大問{counts['major']}、問{counts['question']}、小問{counts['subquestion']}")
            
        except Exception as e:
            logger.error(f"問題抽出エラー: {e}", exc_info=True)
            # フォールバック：従来パターン
            questions = self._fallback_extraction(text)
        
        return questions
    
    def _normalize_number(self, number_str: str) -> str:
        """数字を正規化（全角→半角、漢数字→算用数字）"""
        if not number_str:
            return "0"
        
        # 全角を半角に
        normalized = number_str.translate(self.z2h)
        
        # 漢数字の変換
        kanji_map = {
            '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
        }
        
        for kanji, num in kanji_map.items():
            normalized = normalized.replace(kanji, num)
        
        # アルファベットはそのまま
        if normalized.isalpha():
            return normalized
        
        # 数字以外を除去
        import re
        nums = re.findall(r'\d+', normalized)
        if nums:
            return nums[0]
        
        return normalized if normalized else "0"
    
    def _fallback_extraction(self, text: str) -> List[Tuple[str, str]]:
        """
        フォールバック抽出（従来パターン）
        
        Args:
            text: OCRテキスト
            
        Returns:
            問題リスト
        """
        questions = []
        
        # 解答用紙部分を除外
        clean_text = self._remove_answer_sheet_from_text(text)
        
        # 従来の「問N」パターン
        pattern = re.compile(
            r'問\s*([０-９0-9]+)[．.\s　]*([^問]{10,500})',
            re.DOTALL
        )
        
        seen_positions = set()
        for match in pattern.finditer(clean_text):
            # 位置の重複チェック
            if any(abs(match.start() - pos) < 30 for pos in seen_positions):
                continue
            
            q_num = self._normalize_number(match.group(1))
            q_text = match.group(2).strip()
            
            # 選択肢を除去
            q_text = re.sub(r'[ア-エ][．.\s　].*', '', q_text)
            q_text = re.sub(r'[①-⑩][．.\s　].*', '', q_text)
            
            if len(q_text) > 20:
                questions.append((f"問{q_num}", q_text[:300]))
                seen_positions.add(match.start())
        
        logger.info(f"フォールバック抽出: {len(questions)}問")
        return questions
    
    def _remove_answer_sheet_from_text(self, text: str) -> str:
        """テキストから解答用紙部分を除外"""
        # 解答用紙の開始位置を特定
        answer_sheet_markers = [
            r'社会\s*\(解答用紙\)',
            r'解答用紙',
            r'受験番号氏名',
            r'※注意:裏にも解答らん'
        ]
        
        earliest_pos = len(text)
        for marker in answer_sheet_markers:
            match = re.search(marker, text)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
        
        if earliest_pos < len(text):
            return text[:earliest_pos]
        
        return text
    
    def extract_with_themes(self, text: str) -> List[Tuple[str, str, List[str]]]:
        """
        テーマ付きで問題を抽出（修正版）
        
        Args:
            text: OCRテキスト
            
        Returns:
            [(問題ID, 問題文, [テーマリスト]), ...] のリスト
        """
        questions_with_themes = []
        
        try:
            # 階層構造とテーマを抽出
            structure = self.hierarchical_extractor.extract_with_themes(text)
            
            for major in structure:
                major_num = self._normalize_number(major.number)
                
                # 大問のテーマ
                major_themes = major.themes if major.themes else []
                
                for question in major.children:
                    q_num = self._normalize_number(question.number)
                    q_id = f"大問{major_num}-問{q_num}"
                    q_text = question.text[:500] if question.text else ""
                    
                    # 問題固有のテーマも抽出
                    if q_text:
                        terms = extract_important_terms(q_text)
                        if terms:
                            q_themes = [t['term'] for t in terms[:3]]
                            # 無効なテーマを除外
                            q_themes = self._filter_invalid_themes(q_themes)
                        else:
                            q_themes = self._filter_invalid_themes(major_themes[:3])
                    else:
                        q_themes = self._filter_invalid_themes(major_themes[:3])
                    
                    questions_with_themes.append((q_id, q_text, q_themes))
            
            logger.info(f"テーマ付き抽出: {len(questions_with_themes)}問")
            
        except Exception as e:
            logger.error(f"テーマ付き抽出エラー: {e}")
            # フォールバック
            basic_questions = self.extract_questions(text)
            for q_id, q_text in basic_questions:
                questions_with_themes.append((q_id, q_text, []))
        
        return questions_with_themes
    
    def _filter_invalid_themes(self, themes: List[str]) -> List[str]:
        """無効なテーマを除外"""
        valid_themes = []
        
        for theme in themes:
            if not theme:
                continue
            
            # 無効パターンをチェック
            is_invalid = False
            for pattern in self.compiled_invalid_patterns:
                if pattern.search(theme):
                    is_invalid = True
                    break
            
            if not is_invalid:
                valid_themes.append(theme)
        
        return valid_themes
    
    def get_expected_structure_for_nitkkoma(self) -> dict:
        """日本工業大学駒場中学校の期待される構造を返す"""
        return {
            'expected_majors': 4,
            'expected_total_questions': 42,
            'major_distribution': {
                '1': {'questions': 11, 'field': '地理'},
                '2': {'questions': 13, 'field': '歴史'},
                '3': {'questions': 13, 'field': '公民'},
                '4': {'questions': 5, 'field': '時事・総合'}
            }
        }
    
    def validate_structure(self, structure: List[Question]) -> dict:
        """抽出された構造を検証"""
        expected = self.get_expected_structure_for_nitkkoma()
        counts = self.hierarchical_extractor.count_all_questions(structure)
        
        validation = {
            'is_valid': True,
            'issues': [],
            'actual_counts': counts,
            'expected_counts': expected
        }
        
        # 大問数チェック
        if counts['major'] != expected['expected_majors']:
            validation['is_valid'] = False
            validation['issues'].append(f"大問数不正: 期待{expected['expected_majors']}、実際{counts['major']}")
        
        # 総問題数チェック（許容範囲±5）
        total_questions = counts['question']
        expected_total = expected['expected_total_questions']
        if abs(total_questions - expected_total) > 5:
            validation['is_valid'] = False
            validation['issues'].append(f"総問題数不正: 期待{expected_total}、実際{total_questions}")
        
        return validation