"""
問題番号の重複・欠番を自動修正するモジュール
Gemini APIが利用できない場合のフォールバック処理
"""

import re
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)


class QuestionNumberFixer:
    """問題番号を自動修正するクラス"""
    
    def fix_output_text(self, text: str) -> str:
        """
        出力テキストの問題番号を修正
        
        Args:
            text: 修正対象のテキスト
            
        Returns:
            修正後のテキスト
        """
        lines = text.split('\n')
        fixed_lines = []
        
        current_major = None
        seen_questions = {}  # {大問番号: {問題番号のセット}}
        question_counters = {}  # {大問番号: 次の問題番号}
        
        for line in lines:
            # 大問の開始を検出
            major_match = re.match(r'^▼\s*大問\s*(\d+)', line)
            if major_match:
                current_major = major_match.group(1)
                if current_major not in seen_questions:
                    seen_questions[current_major] = set()
                    question_counters[current_major] = 1
                fixed_lines.append(line)
                continue
            
            # 問題行を検出
            question_match = re.match(r'^  (大問(\d+)-問(\d+)):(.*)', line)
            if question_match and current_major:
                full_id = question_match.group(1)
                major_num = question_match.group(2)
                question_num = question_match.group(3)
                rest_of_line = question_match.group(4)
                
                # 大問番号が一致しない場合は修正
                if major_num != current_major:
                    logger.info(f"大問番号を修正: 大問{major_num} → 大問{current_major}")
                    major_num = current_major
                
                # 問題番号の重複をチェック
                if question_num in seen_questions[current_major]:
                    # 重複している場合は新しい番号を割り当て
                    new_num = str(question_counters[current_major])
                    logger.info(f"重複問題番号を修正: 大問{major_num}-問{question_num} → 問{new_num}")
                    question_num = new_num
                    question_counters[current_major] += 1
                else:
                    # 重複していない場合はそのまま使用
                    seen_questions[current_major].add(question_num)
                    # カウンターを更新
                    try:
                        num_val = int(question_num)
                        if num_val >= question_counters[current_major]:
                            question_counters[current_major] = num_val + 1
                    except ValueError:
                        pass
                
                # 修正した行を作成
                fixed_line = f"  大問{major_num}-問{question_num}:{rest_of_line}"
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def fix_question_list(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        問題リストの番号を修正
        
        Args:
            questions: [(問題ID, 問題テキスト), ...] のリスト
            
        Returns:
            修正後のリスト
        """
        fixed_questions = []
        seen_ids = {}  # {問題ID: 出現回数}
        major_question_counts = {}  # {大問番号: {問題番号: 出現回数}}
        
        for q_id, q_text in questions:
            # 大問と問題番号を抽出
            match = re.match(r'大問(\d+)-問(\d+)', q_id)
            if match:
                major_num = match.group(1)
                question_num = match.group(2)
                
                # 大問ごとの問題番号カウント
                if major_num not in major_question_counts:
                    major_question_counts[major_num] = {}
                
                if question_num in major_question_counts[major_num]:
                    # 重複を検出
                    occurrence = major_question_counts[major_num][question_num] + 1
                    major_question_counts[major_num][question_num] = occurrence
                    
                    # 次の大問に移動すべきか判断
                    next_major = str(int(major_num) + 1)
                    if occurrence == 2 and next_major in ['2', '3', '4']:
                        # 2回目の出現は次の大問へ
                        new_id = f"大問{next_major}-問{question_num}"
                        logger.info(f"問題を次の大問へ移動: {q_id} → {new_id}")
                        fixed_questions.append((new_id, q_text))
                    else:
                        # 番号を振り直し
                        new_num = str(len(major_question_counts[major_num]) + 1)
                        new_id = f"大問{major_num}-問{new_num}"
                        logger.info(f"問題番号を振り直し: {q_id} → {new_id}")
                        fixed_questions.append((new_id, q_text))
                else:
                    # 初回出現
                    major_question_counts[major_num][question_num] = 1
                    fixed_questions.append((q_id, q_text))
            else:
                # パターンに一致しない場合はそのまま
                fixed_questions.append((q_id, q_text))
        
        return fixed_questions
    
    def validate_and_report(self, text: str) -> Dict[str, List[str]]:
        """
        テキストの問題番号を検証してレポート
        
        Args:
            text: 検証対象のテキスト
            
        Returns:
            エラー情報の辞書
        """
        errors = {
            'duplicates': [],
            'missing': [],
            'wrong_major': []
        }
        
        lines = text.split('\n')
        current_major = None
        seen_questions = {}
        
        for line in lines:
            # 大問の開始
            major_match = re.match(r'^▼\s*大問\s*(\d+)', line)
            if major_match:
                current_major = major_match.group(1)
                if current_major not in seen_questions:
                    seen_questions[current_major] = []
                continue
            
            # 問題行
            question_match = re.match(r'^  大問(\d+)-問(\d+):', line)
            if question_match and current_major:
                major_num = question_match.group(1)
                question_num = question_match.group(2)
                
                # 大問番号の不一致
                if major_num != current_major:
                    errors['wrong_major'].append(f"大問{major_num}-問{question_num} (現在の大問: {current_major})")
                
                # 重複チェック
                q_id = f"大問{major_num}-問{question_num}"
                if q_id in seen_questions.get(major_num, []):
                    errors['duplicates'].append(q_id)
                else:
                    if major_num not in seen_questions:
                        seen_questions[major_num] = []
                    seen_questions[major_num].append(q_id)
        
        # 欠番チェック
        for major_num, questions in seen_questions.items():
            if questions:
                # 問題番号を整数に変換してソート
                q_nums = []
                for q_id in questions:
                    match = re.match(r'大問\d+-問(\d+)', q_id)
                    if match:
                        try:
                            q_nums.append(int(match.group(1)))
                        except ValueError:
                            pass
                
                if q_nums:
                    q_nums.sort()
                    # 1から最大値までの連続性をチェック
                    for i in range(1, max(q_nums)):
                        if i not in q_nums:
                            errors['missing'].append(f"大問{major_num}-問{i}")
        
        return errors