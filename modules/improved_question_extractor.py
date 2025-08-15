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
        # 大問パターン（優先順位順）
        self.major_patterns = [
            # 明示的な大問表記
            re.compile(r'^大問\s*(\d+)', re.MULTILINE),  # 大問1
            re.compile(r'^第\s*(\d+)\s*問', re.MULTILINE),  # 第1問
            re.compile(r'^【\s*(\d+)\s*】', re.MULTILINE),  # 【1】
            re.compile(r'^\[\s*(\d+)\s*\]', re.MULTILINE),  # [1]
            # 数字のみの大問パターン（行頭の数字）
            re.compile(r'^(\d+)\s*[\.。]\s*(?:次の|下記の|以下の)', re.MULTILINE),  # 1. 次の〜
            re.compile(r'^[一二三四五六七八九十]+[\.。]\s*(?:次の|下記の|以下の)', re.MULTILINE),  # 一. 次の〜
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
            # 大問番号を1から順番に振り直す
            for idx, (original_major_num, section_text) in enumerate(major_sections, 1):
                minor_questions = self._extract_minor_questions(section_text)
                
                if minor_questions:
                    for minor_num, q_text in minor_questions:
                        # 全角数字を半角に変換
                        minor_num = self._normalize_number(minor_num)
                        questions.append((f"大問{idx}-問{minor_num}", q_text))
                else:
                    # 小問が見つからない場合は大問全体を1つの問題として扱う
                    if len(section_text.strip()) > 20:
                        questions.append((f"大問{idx}", section_text[:500]))
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
        """大問セクションを見つける（改良版）"""
        major_sections = []
        
        # まず明示的な大問マーカーを探す
        for pattern in self.major_patterns:
            matches = list(pattern.finditer(text))
            if matches:
                logger.debug(f"大問パターンマッチ: {len(matches)}件")
                
                # マッチ数が異常に多い場合（10以上）は誤検出の可能性
                if len(matches) > 10:
                    logger.warning(f"大問マッチ数が異常: {len(matches)}件 → スキップ")
                    continue
                
                for i, match in enumerate(matches):
                    major_num = match.group(1) if match.lastindex >= 1 else str(i + 1)
                    
                    # 異常な大問番号をチェック
                    try:
                        if major_num.isdigit() and int(major_num) > 10:
                            logger.warning(f"異常な大問番号: {major_num} → スキップ")
                            continue
                    except:
                        pass
                    
                    start = match.start()
                    end = matches[i + 1].start() if i < len(matches) - 1 else len(text)
                    
                    section_text = text[start:end]
                    
                    # セクションが短すぎる場合はスキップ
                    if len(section_text.strip()) < 50:
                        continue
                        
                    major_sections.append((major_num, section_text))
                
                # 有効な大問が見つかった場合のみbreak
                if major_sections:
                    break
        
        # 大問が見つからない、または少なすぎる場合の補正
        if not major_sections or len(major_sections) > 8:
            logger.info("大問構造が不明確なため、問題番号リセットから推定します")
            return []  # 空を返して、後続の処理で問題番号リセットから推定
        
        return major_sections
    
    def _extract_minor_questions(self, text: str) -> List[Tuple[str, str]]:
        """小問を抽出（大問の説明文も含める）"""
        minor_questions = []
        
        # 大問の説明文（本文）を抽出し、選択肢・資料と分離
        context = ""
        # 問1以前の本文（最大300文字）
        first_question_pos = text.find("問")
        if first_question_pos > 0:
            pre = text[:min(first_question_pos, 300)]
            # 選択肢先頭（ア./イ./①…）が混入していたらそこまでを本文とみなす
            m = re.search(r'(\n|^)[\s　]*([ア-ン]|[①-⑩])[\．\.\s　]', pre)
            if m:
                pre = pre[:m.start()]
            context = pre.strip()
            if context:
                context = context + "\n"
        
        for pattern in self.minor_patterns:
            matches = pattern.findall(text)
            if matches:
                for num, q_text in matches:
                    # 本文・選択肢・資料のスコープ分離
                    main_part = q_text
                    # 選択肢以降を切り落とし、本文の地の文を強調
                    m2 = re.search(r'(\n|^)[\s　]*([ア-ン]|[①-⑩])[\．\.\s　]', main_part)
                    if m2:
                        main_part = main_part[:m2.start()]
                    # 問1の場合は大問本文も前置
                    if num in ['1', '１'] and context:
                        main_part = context + main_part
                    
                    main_part = self._clean_question_text(main_part)
                    if self._is_valid_question(main_part):
                        minor_questions.append((num, main_part))
                
                if minor_questions:
                    break  # 最初にマッチしたパターンを使用
        
        return minor_questions
    
    def _detect_resets_and_assign_major(self, minor_questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """問題番号のリセットを検出して大問を割り当て（改良版）"""
        if not minor_questions:
            return []
        
        result = []
        current_major = 1
        previous_num = 0
        max_major = 5  # 中学入試の社会は通常3-5大問
        question_count_in_major = 0
        
        for num_str, q_text in minor_questions:
            try:
                num = int(self._normalize_number(num_str))
            except (ValueError, TypeError):
                # 数値に変換できない場合はスキップ
                logger.warning(f"問題番号の変換に失敗: {num_str}")
                continue
            
            # より厳密なリセット検出
            # 条件1: 問1に戻った場合（前の問題が3以上）
            # 条件2: 現在の大問内で既に5問以上あり、問1に戻った
            if num == 1 and (previous_num >= 3 or question_count_in_major >= 5):
                if current_major < max_major:
                    current_major += 1
                    question_count_in_major = 0
                    logger.debug(f"問題番号リセット検出: 問{previous_num}→問1, 大問{current_major}へ")
            
            # 通常の問題番号の連続性チェック
            # 問題番号が10以上離れて小さくなった場合はリセットの可能性
            elif previous_num > 0 and num < previous_num and (previous_num - num) >= 10:
                if current_major < max_major:
                    current_major += 1
                    question_count_in_major = 0
                    logger.debug(f"大幅な番号逆行検出: 問{previous_num}→問{num}, 大問{current_major}へ")
            
            result.append((f"大問{current_major}-問{num}", q_text))
            previous_num = num
            question_count_in_major += 1
        
        # 結果の妥当性チェック
        major_counts = {}
        for q_id, _ in result:
            major_part = q_id.split('-')[0]
            major_counts[major_part] = major_counts.get(major_part, 0) + 1
        
        # 異常な大問数の検出と修正
        if len(major_counts) > max_major:
            logger.warning(f"異常な大問数を検出: {len(major_counts)}個 → 再割り当て")
            # 問題を均等に再配分
            total_questions = len(result)
            questions_per_major = max(5, total_questions // 4)  # 1大問あたり最低5問
            
            corrected_result = []
            for idx, (old_id, q_text) in enumerate(result):
                # 新しい大問番号を計算
                new_major = min((idx // questions_per_major) + 1, 4)
                # 問題番号を抽出
                q_num = old_id.split('問')[-1] if '問' in old_id else str(idx + 1)
                corrected_result.append((f"大問{new_major}-問{q_num}", q_text))
            
            result = corrected_result
            
            # 修正後の大問構造を再計算
            major_counts = {}
            for q_id, _ in result:
                major_part = q_id.split('-')[0]
                major_counts[major_part] = major_counts.get(major_part, 0) + 1
        
        logger.info(f"検出された大問構造: {dict(major_counts)}")
        
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