#!/usr/bin/env python3
"""
改善された設問分析モジュール
設問タイプと選択肢数を詳細に分析
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QuestionAnalysis:
    """設問分析結果 - 強化版"""
    total_count: int
    type_counts: Dict[str, int]
    choice_counts: Dict[str, int]  # 3択、4択、5択など
    has_word_limit: int  # 文字数指定ありの記述
    no_word_limit: int  # 文字数指定なしの記述
    word_limit_details: Optional[Dict[str, int]] = None  # 字数制限の詳細
    choice_type_details: Optional[Dict[str, List[str]]] = None  # 選択肢の詳細
    extract_details: Optional[Dict[str, int]] = None  # 抜き出しの詳細
    
    
class ImprovedQuestionAnalyzer:
    """改善された設問分析器"""
    
    def analyze_questions(self, text: str, section_type: str = None) -> QuestionAnalysis:
        """
        テキストから設問を詳細分析
        
        Args:
            text: 分析対象テキスト
            section_type: セクションタイプ（漢字・語句など）
        
        Returns:
            設問分析結果
        """
        # 初期化
        type_counts = {
            '選択': 0,
            '記述': 0,
            '抜き出し': 0,
            '漢字': 0,
            '語句': 0,
        }
        
        choice_counts = {
            '2択': 0,
            '3択': 0,
            '4択': 0,
            '5択': 0,
            '6択': 0,
        }
        
        has_word_limit = 0
        no_word_limit = 0
        
        # セクションタイプが漢字・語句の場合の特別処理
        if section_type and '漢字' in section_type:
            # まず範囲表記（1~8など）を探す
            range_pattern = re.search(r'([1-8１-８])[\s]*[~～][\s]*([1-8１-８])', text)
            if range_pattern:
                # 範囲の開始と終了を取得
                start_str = range_pattern.group(1)
                end_str = range_pattern.group(2)
                
                # 全角数字を半角に変換
                if '１' <= start_str <= '８':
                    start_num = ord(start_str) - ord('０')
                else:
                    start_num = int(start_str)
                    
                if '１' <= end_str <= '８':
                    end_num = ord(end_str) - ord('０')
                else:
                    end_num = int(end_str)
                
                # 範囲内の問題数をカウント
                type_counts['漢字'] = end_num - start_num + 1
                logger.debug(f"漢字問題: 範囲表記 {start_num}~{end_num} から {type_counts['漢字']}問を検出")
            else:
                # 範囲表記がない場合は個別の番号を数える
                kanji_numbers = re.findall(r'[1-8１-８①-⑧]\s*[^\d\s]{1,10}[をの]?(?:漢字に|カタカナ)', text)
                arabic_numbers = re.findall(r'(?:^|\s)([1-8１-８])\s+', text)
                
                if kanji_numbers:
                    type_counts['漢字'] = len(kanji_numbers)
                elif arabic_numbers:
                    # 連続する数字の最大値を取る
                    nums = []
                    for n in arabic_numbers:
                        if '１' <= n <= '８':
                            nums.append(ord(n) - ord('０'))
                        else:
                            nums.append(int(n))
                    if nums:
                        type_counts['漢字'] = max(nums)
        
        # 選択問題の判定
        # 「記号で答えなさい」パターンを検索
        symbol_answer_pattern = re.finditer(r'.{0,800}記号[でを]?答え', text)
        
        for match in symbol_answer_pattern:
            context = match.group()
            
            # 選択肢を検出（カタカナ、アルファベット、数字）
            # より広範囲にカタカナ選択肢を検出
            # 改行後のカタカナや、独立したカタカナを探す
            katakana_all = re.findall(r'[ア-オ]', context)
            
            if katakana_all:
                unique_choices = sorted(set(katakana_all))
                
                # 最大の選択肢で択数を判定
                if 'オ' in unique_choices:
                    num_choices = 5
                elif 'エ' in unique_choices:
                    num_choices = 4
                elif 'ウ' in unique_choices:
                    num_choices = 3
                elif 'イ' in unique_choices:
                    num_choices = 2
                else:
                    num_choices = 1
                
                if num_choices >= 2:  # 2つ以上の選択肢がある場合
                    type_counts['選択'] += 1
                    choice_counts[f'{num_choices}択'] += 1
                else:
                    # 選択肢が1つの場合も選択問題として扱う（デフォルト5択）
                    type_counts['選択'] += 1
                    choice_counts['5択'] += 1
            else:
                # カタカナ選択肢が見つからない場合
                # アルファベットや数字の選択肢を探す
                alphabet_choices = re.findall(r'[A-EＡ-Ｅ]', context)
                number_choices = re.findall(r'[1-5１-５]', context)
                
                if alphabet_choices:
                    unique_alpha = sorted(set(alphabet_choices))
                    if 'E' in unique_alpha or 'Ｅ' in unique_alpha:
                        num_choices = 5
                    elif 'D' in unique_alpha or 'Ｄ' in unique_alpha:
                        num_choices = 4
                    elif 'C' in unique_alpha or 'Ｃ' in unique_alpha:
                        num_choices = 3
                    else:
                        num_choices = 2
                    
                    type_counts['選択'] += 1
                    choice_counts[f'{num_choices}択'] += 1
                elif number_choices:
                    unique_nums = sorted(set(number_choices))
                    if '5' in unique_nums or '５' in unique_nums:
                        num_choices = 5
                    elif '4' in unique_nums or '４' in unique_nums:
                        num_choices = 4
                    elif '3' in unique_nums or '３' in unique_nums:
                        num_choices = 3
                    else:
                        num_choices = 2
                    
                    type_counts['選択'] += 1
                    choice_counts[f'{num_choices}択'] += 1
                else:
                    # 選択肢が検出できない場合もデフォルトで5択
                    type_counts['選択'] += 1
                    choice_counts['5択'] += 1
        
        # より包括的な問題分割パターン
        # 「問一」「問1」「問①」など様々な形式に対応
        question_split_patterns = [
            r'問[一二三四五六七八九十]+',
            r'問[0-9０-９]+',
            r'問[①-⑮]',
            r'設問[0-9０-９一二三四五六七八九十]+',
            r'\([0-9０-９一二三四五六七八九十]+\)'
        ]
        
        # 全パターンを統合した分割
        all_questions = []
        for pattern in question_split_patterns:
            if re.search(pattern, text):
                questions = re.split(pattern, text)
                if len(questions) > 1:
                    all_questions.extend(questions[1:])
                    break  # 最初にマッチしたパターンを使用
        
        # 問題が見つからない場合は全体を1つの問題として扱う
        if not all_questions:
            all_questions = [text]
        
        for question_text in all_questions:
            question_text = question_text[:800]  # 問題の最初の800文字を分析
            
            # この問題が選択問題かどうかをチェック（記号で答えパターン以外）
            has_choice = re.search(r'記号[でを]?答え', question_text) is not None
            
            # 抜き出し問題の判定
            if re.search(r'(抜|ぬ)[きく]出[しせ]', question_text) or \
               re.search(r'書[きく]抜[きけ]', question_text):
                type_counts['抜き出し'] += 1
            
            # 記述問題の判定
            elif not has_choice:
                # 文字数指定ありの記述（算用数字、全角数字、漢数字対応）
                if re.search(r'[０-９0-9]+字(?:以内|程度|まで)', question_text) or \
                   re.search(r'[○●][字]?(?:以内|程度)', question_text) or \
                   re.search(r'[一二三四五六七八九十百千万]+字(?:以内|程度|まで)', question_text):
                    type_counts['記述'] += 1
                    has_word_limit += 1
                # 行数指定の記述（1行、2行など）
                elif re.search(r'[１-９1-9一二三四五][行]で?(?:説明|書[きけ]|答え)', question_text):
                    type_counts['記述'] += 1
                    has_word_limit += 1  # 行数も文字数制限の一種として扱う
                # 文字数指定なしの記述（書きなさい、説明しなさいなど）
                elif re.search(r'書[きけ]なさい', question_text) or \
                     re.search(r'説明[しせ](?:なさい|よ)', question_text) or \
                     re.search(r'述べ(?:なさい|よ)', question_text) or \
                     re.search(r'答え(?:なさい|よ)', question_text):
                    type_counts['記述'] += 1
                    no_word_limit += 1
        
        # 詳細分析の初期化
        word_limit_details = {}
        choice_type_details = {}
        extract_details = {'単語抜き出し': 0, '文章抜き出し': 0, '行抜き出し': 0}
        
        # 文字数制限の詳細分析
        word_limit_patterns = [
            # 算用数字・全角数字
            (r'([0-9０-９]+)字以内', '字以内'),
            (r'([0-9０-９]+)字程度', '字程度'),
            (r'([0-9０-９]+)字以下', '字以下'),
            (r'([0-9０-９]+)字まで', '字まで'),
            # 漢数字パターン
            (r'([一二三四五六七八九十百千万]+)字以内', '字以内'),
            (r'([一二三四五六七八九十百千万]+)字程度', '字程度'),
            (r'([一二三四五六七八九十百千万]+)字以下', '字以下'),
            (r'([一二三四五六七八九十百千万]+)字まで', '字まで'),
            # 行数指定パターン
            (r'([１-９1-9一二三四五])行で?', '行'),
            # 特殊パターン（○、●）
            (r'([○●][0-9０-９]*)字?以内', '字以内'),
            (r'([○●][0-9０-９]*)字?程度', '字程度')
        ]
        
        for pattern, suffix in word_limit_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 数値の変換処理
                if match.startswith('○') or match.startswith('●'):
                    # ○、●の後の数字を抽出
                    num_part = match[1:] if len(match) > 1 else '20'  # デフォルト20
                    if not num_part:
                        num_part = '20'
                else:
                    num_part = match
                
                # 漢数字を算用数字に変換
                if any(c in num_part for c in '一二三四五六七八九十百千万'):
                    converted_num = self._convert_kanji_to_number(num_part)
                else:
                    # 全角数字を半角に変換
                    converted_num = ''
                    for char in num_part:
                        if '０' <= char <= '９':
                            converted_num += str(ord(char) - ord('０'))
                        elif '１' <= char <= '９':
                            converted_num += str(ord(char) - ord('１') + 1)
                        else:
                            converted_num += char
                
                # 行数の場合は約40字として扱う（1行約40字の想定）
                if suffix == '行':
                    approx_chars = int(converted_num) * 40 if converted_num.isdigit() else 40
                    detail_key = f"{approx_chars}字程度（{converted_num}行）"
                else:
                    detail_key = f"{converted_num}{suffix}"
                
                word_limit_details[detail_key] = word_limit_details.get(detail_key, 0) + 1
        
        # 選択肢の詳細分析
        choice_patterns = re.finditer(r'.{0,800}記号[でを]?答え', text)
        for match in choice_patterns:
            context = match.group()
            
            # カタカナ選択肢の検出
            katakana_choices = re.findall(r'[アイウエオカキクケコ]', context)
            if katakana_choices:
                unique_katakana = sorted(set(katakana_choices))
                choice_detail = ''.join(unique_katakana)
                
                num_choices = len(unique_katakana)
                if num_choices >= 2:
                    choice_key = f'{num_choices}択'
                    if choice_key not in choice_type_details:
                        choice_type_details[choice_key] = []
                    choice_type_details[choice_key].append(choice_detail)
            
            # アルファベット選択肢の検出
            alphabet_choices = re.findall(r'[A-ZＡ-Ｚ]', context)
            if alphabet_choices and not katakana_choices:
                unique_alphabet = sorted(set(alphabet_choices))
                choice_detail = ''.join(unique_alphabet)
                
                num_choices = len(unique_alphabet)
                if num_choices >= 2:
                    choice_key = f'{num_choices}択'
                    if choice_key not in choice_type_details:
                        choice_type_details[choice_key] = []
                    choice_type_details[choice_key].append(choice_detail)
        
        # 抜き出しの詳細分析
        extract_patterns = [
            (r'単語を?[^\s]*抜[きく]出[しせ]', '単語抜き出し'),
            (r'一字を?[^\s]*抜[きく]出[しせ]', '単語抜き出し'),
            (r'文章を?[^\s]*抜[きく]出[しせ]', '文章抜き出し'),
            (r'本文から[^\s]*抜[きく]出[しせ]', '文章抜き出し'),
            (r'行を?[^\s]*抜[きく]出[しせ]', '行抜き出し'),
            (r'[^\s]*行[^\s]*抜[きく]出[しせ]', '行抜き出し')
        ]
        
        for pattern, extract_type in extract_patterns:
            matches = len(re.findall(pattern, text))
            if matches > 0:
                extract_details[extract_type] += matches
        
        # 総設問数の計算
        total_count = sum(type_counts.values())
        
        return QuestionAnalysis(
            total_count=total_count,
            type_counts=type_counts,
            choice_counts=choice_counts,
            has_word_limit=has_word_limit,
            no_word_limit=no_word_limit,
            word_limit_details=word_limit_details if word_limit_details else None,
            choice_type_details=choice_type_details if choice_type_details else None,
            extract_details=extract_details if any(extract_details.values()) else None
        )
    
    def _convert_kanji_to_number(self, kanji_str: str) -> str:
        """漢数字を算用数字に変換"""
        # 基本的な変換マップ
        kanji_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '二十': 20, '三十': 30, '四十': 40, '五十': 50,
            '六十': 60, '七十': 70, '八十': 80, '九十': 90,
            '百': 100, '千': 1000, '万': 10000
        }
        
        # 完全マッチの場合
        if kanji_str in kanji_map:
            return str(kanji_map[kanji_str])
        
        # 複合パターンの処理（例：二十五、八十など）
        result = 0
        
        # 十の位の処理
        for kanji, value in [
            ('九十', 90), ('八十', 80), ('七十', 70), ('六十', 60),
            ('五十', 50), ('四十', 40), ('三十', 30), ('二十', 20),
            ('十', 10)
        ]:
            if kanji in kanji_str:
                result += value
                kanji_str = kanji_str.replace(kanji, '')
                break
        
        # 一の位の処理
        for kanji, value in [
            ('九', 9), ('八', 8), ('七', 7), ('六', 6),
            ('五', 5), ('四', 4), ('三', 3), ('二', 2), ('一', 1)
        ]:
            if kanji in kanji_str:
                result += value
                break
        
        return str(result) if result > 0 else '0'
    
    def analyze_sections_with_questions(self, sections: List, full_text: str) -> QuestionAnalysis:
        """
        セクションごとに設問を分析して統合
        
        Args:
            sections: セクションリスト
            full_text: 全体テキスト
        
        Returns:
            統合された設問分析結果
        """
        total_type_counts = {
            '選択': 0,
            '記述': 0,
            '抜き出し': 0,
            '漢字': 0,
            '語句': 0,
        }
        
        total_choice_counts = {
            '2択': 0,
            '3択': 0,
            '4択': 0,
            '5択': 0,
            '6択': 0,
        }
        
        total_has_word_limit = 0
        total_no_word_limit = 0
        total_count = 0
        
        for i, section in enumerate(sections):
            # セクションのテキストを取得
            if hasattr(section, 'content'):
                section_text = section.content
            elif hasattr(section, 'text'):
                section_text = section.text
            else:
                continue
            
            # セクションタイプを判定
            section_type = None
            if hasattr(section, 'title'):
                if '漢字' in section.title or '語句' in section.title:
                    section_type = '漢字・語句'
            
            # セクションを分析
            analysis = self.analyze_questions(section_text, section_type)
            
            # 結果を統合
            for key, value in analysis.type_counts.items():
                total_type_counts[key] += value
            
            for key, value in analysis.choice_counts.items():
                total_choice_counts[key] += value
            
            total_has_word_limit += analysis.has_word_limit
            total_no_word_limit += analysis.no_word_limit
            total_count += analysis.total_count
        
        # 統合した詳細情報を収集
        combined_word_limit_details = {}
        combined_choice_type_details = {}
        combined_extract_details = {'単語抜き出し': 0, '文章抜き出し': 0, '行抜き出し': 0}
        
        # 各セクションの詳細分析を再実行して統合
        for section in sections:
            if hasattr(section, 'content'):
                section_text = section.content
            elif hasattr(section, 'text'):
                section_text = section.text
            else:
                continue
            
            section_analysis = self.analyze_questions(section_text)
            
            # 詳細情報を統合
            if hasattr(section_analysis, 'word_limit_details') and section_analysis.word_limit_details:
                for key, value in section_analysis.word_limit_details.items():
                    combined_word_limit_details[key] = combined_word_limit_details.get(key, 0) + value
            
            if hasattr(section_analysis, 'choice_type_details') and section_analysis.choice_type_details:
                for key, value in section_analysis.choice_type_details.items():
                    if key not in combined_choice_type_details:
                        combined_choice_type_details[key] = []
                    combined_choice_type_details[key].extend(value)
            
            if hasattr(section_analysis, 'extract_details') and section_analysis.extract_details:
                for key, value in section_analysis.extract_details.items():
                    combined_extract_details[key] = combined_extract_details.get(key, 0) + value
        
        return QuestionAnalysis(
            total_count=total_count,
            type_counts=total_type_counts,
            choice_counts=total_choice_counts,
            has_word_limit=total_has_word_limit,
            no_word_limit=total_no_word_limit,
            word_limit_details=combined_word_limit_details if combined_word_limit_details else None,
            choice_type_details=combined_choice_type_details if combined_choice_type_details else None,
            extract_details=combined_extract_details if any(combined_extract_details.values()) else None
        )