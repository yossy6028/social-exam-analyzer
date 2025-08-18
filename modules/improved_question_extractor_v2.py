#!/usr/bin/env python3
"""
改善された問題抽出器 v2
日本工業大学駒場などの四角囲み数字形式に対応
"""

import re
import logging
from typing import List, Tuple, Optional
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from patterns.social_terms import extract_important_terms, get_themes_from_terms

logger = logging.getLogger(__name__)

try:
    # 修正版を優先して使用
    from patterns.hierarchical_extractor_fixed import HierarchicalExtractorFixed as HierarchicalExtractor, Question
    logger.info("修正版階層抽出器を使用します")
except ImportError:
    # フォールバック
    from patterns.hierarchical_extractor import HierarchicalExtractor, Question
    logger.info("従来版階層抽出器を使用します")


class ImprovedQuestionExtractorV2:
    """改善された問題抽出器v2（四角囲み対応）"""
    
    def __init__(self):
        """初期化"""
        self.hierarchical_extractor = HierarchicalExtractor()
        
        # 全角→半角変換テーブル
        self.z2h = str.maketrans({
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9'
        })
        
        logger.info("ImprovedQuestionExtractorV2 初期化完了")
    
    def extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """
        テキストから問題を抽出（四角囲み数字対応）
        
        Args:
            text: OCRされたテキスト
            
        Returns:
            [(問題ID, 問題文), ...] のリスト
        """
        questions = []
        
        try:
            # 階層構造を抽出
            structure = self.hierarchical_extractor.extract_with_themes(text)
            
            # 構造をフラット化して問題リストに変換
            for major in structure:
                major_num = self._normalize_number(major.number)
                
                # 大問レベルの問題（スキップ - 問題数が増える原因）
                # if major.text and len(major.text) > 10:
                #     questions.append((f"大問{major_num}", major.text[:200]))
                
                # 問レベルのみを抽出
                for question in major.children:
                    q_num = self._normalize_number(question.number)
                    q_id = f"大問{major_num}-問{q_num}"
                    q_text = question.text[:500] if question.text else ""
                    
                    # 小問の情報を追加（個別の問題としてはカウントしない）
                    if question.children:
                        sub_info = f" (小問{len(question.children)}個: "
                        sub_nums = [self._normalize_number(sub.number) for sub in question.children[:5]]
                        sub_info += ", ".join(sub_nums)
                        if len(question.children) > 5:
                            sub_info += f"...他{len(question.children)-5}個"
                        sub_info += ")"
                        q_text += sub_info
                    
                    if q_text:
                        questions.append((q_id, q_text))
                    
                    # 小問レベル（スキップ - 問題数が増える原因）
                    # for i, subquestion in enumerate(question.children[:3]):
                    #     sub_num = self._normalize_number(subquestion.number)
                    #     sub_id = f"大問{major_num}-問{q_num}-({sub_num})"
                    #     sub_text = subquestion.text[:200] if subquestion.text else ""
                    #     if sub_text and len(sub_text) > 20:
                    #         questions.append((sub_id, sub_text))
            
            # 問題が少ない場合は追加パターンで補完（無効化）
            # 追加パターンは誤検出の原因となるため無効化
            # if len(questions) < 10:
            #     additional = self._extract_additional_patterns(text, structure)
            #     questions.extend(additional)
            
            logger.info(f"ImprovedQuestionExtractorV2: {len(questions)}問を抽出")
            
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
    
    def _extract_additional_patterns(self, text: str, structure: List[Question]) -> List[Tuple[str, str]]:
        """
        追加パターンで問題を補完
        
        Args:
            text: 元のテキスト
            structure: 既に抽出された構造
            
        Returns:
            追加の問題リスト
        """
        additional = []
        
        # 既に抽出された問題番号を記録
        existing_ids = set()
        for major in structure:
            for question in major.children:
                existing_ids.add(f"{major.number}-{question.number}")
        
        # 追加パターン1: 丸数字の設問
        circle_pattern = re.compile(r'([①-⑳])\s*([^①-⑳]{10,200})')
        for match in circle_pattern.finditer(text):
            num = match.group(1)
            q_text = match.group(2).strip()
            if len(q_text) > 20:
                additional.append((f"設問{num}", q_text))
        
        # 追加パターン2: 「次の」で始まる段落
        next_pattern = re.compile(r'次の[^。]+について[^。]+。')
        for match in next_pattern.finditer(text):
            q_text = match.group(0)
            if len(q_text) > 30:
                additional.append((f"設問", q_text))
                if len(additional) >= 5:  # 最大5個まで
                    break
        
        return additional
    
    def _fallback_extraction(self, text: str) -> List[Tuple[str, str]]:
        """
        フォールバック抽出（従来パターン）
        
        Args:
            text: OCRテキスト
            
        Returns:
            問題リスト
        """
        questions = []
        
        # 従来の「問N」パターン
        pattern = re.compile(
            r'問\s*([０-９0-9]+)[．.\s　]*([^問]{10,500})',
            re.DOTALL
        )
        
        for match in pattern.finditer(text):
            q_num = self._normalize_number(match.group(1))
            q_text = match.group(2).strip()
            
            # 選択肢を除去
            q_text = re.sub(r'[ア-エ][．.\s　].*', '', q_text)
            q_text = re.sub(r'[①-⑩][．.\s　].*', '', q_text)
            
            if len(q_text) > 20:
                questions.append((f"問{q_num}", q_text[:300]))
        
        logger.info(f"フォールバック抽出: {len(questions)}問")
        return questions
    
    def extract_with_themes(self, text: str) -> List[Tuple[str, str, List[str]]]:
        """
        テーマ付きで問題を抽出
        
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
                        else:
                            q_themes = major_themes[:3] if major_themes else []
                    else:
                        q_themes = major_themes[:3] if major_themes else []
                    
                    questions_with_themes.append((q_id, q_text, q_themes))
            
            logger.info(f"テーマ付き抽出: {len(questions_with_themes)}問")
            
        except Exception as e:
            logger.error(f"テーマ付き抽出エラー: {e}")
            # フォールバック
            basic_questions = self.extract_questions(text)
            for q_id, q_text in basic_questions:
                questions_with_themes.append((q_id, q_text, []))
        
        return questions_with_themes