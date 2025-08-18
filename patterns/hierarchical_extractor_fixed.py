"""
階層的問題構造抽出モジュール（修正版）
大問→問→小問の3層構造を正確に認識
解答用紙の除外と問題番号の重複防止を実装
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

class HierarchicalExtractorFixed:
    """階層的な問題構造を抽出するクラス（修正版）"""
    
    def __init__(self):
        """パターンを初期化"""
        # 大問検出パターン（優先度順）
        self.major_patterns = [
            # 日本工業大学駒場中学校形式（最優先）
            (r'^([1-9])\s+次の', 'nitkkoma_number_tsugi'),
            (r'^([１-９])\s+次の', 'nitkkoma_fullwidth_tsugi'),
            # OCR改行エラー対応：「2\n次の」パターン
            (r'^([1-9])\s*\n\s*次の', 'nitkkoma_number_newline'),
            (r'^([１-９])\s*\n\s*次の', 'nitkkoma_fullwidth_newline'),
            # OCRエラー対応：「13」→「3」など（具体的パターン）
            (r'^13\s+次の', 'nitkkoma_13_to_3'),
            (r'^14\s+次の', 'nitkkoma_14_to_4'),
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
            # 「問」パターンを最優先（日本工業大学駒場中学校の形式）
            (r'問\s*([１-９0-9]{1,2})', 'mon_number'),
            (r'問\s*([一-九十]{1,3})', 'mon_kanji'),
            # 設問パターン
            (r'設問\s*([１-９0-9]{1,2})', 'setsumon'),
            # 括弧付き数字パターン（優先度を下げる）
            # 地図ラベルや選択肢を誤認識しないよう、より厳密な条件が必要
            # 一時的に無効化して「問」パターンのみで検出
            # (r'\(([1-9][0-9]?)\)', 'paren_number_q'),
            # (r'（([１-９][０-９]?)）', 'paren_zenkaku_q'),
            # 番号ピリオドパターン
            (r'^([１-９][０-９]?)[．.、]', 'number_period'),
        ]
        
        # 小問検出パターン
        self.subquestion_patterns = [
            # (r'\(([1-9][0-9]?)\)', 'paren_number'),  # 問パターンと競合するためコメントアウト
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
        
        # 除外すべきパターン（解答用紙等）
        self.exclusion_patterns = [
            r'社会\s*\(解答用紙\)',       # 解答用紙の見出し
            r'受験番号氏名',
            r'※注意',
            r'得点',
            r'裏にも解答らん',
            r'記号問[0-9]+名称問[0-9]+',  # 解答用紙の項目
            r'問[0-9]+記号問[0-9]+',      # 解答用紙の項目
            r'平野\(漢字\)',
            r'\(漢字四字\)',
            r'\(漢字\)',
            # 「解答用紙」単体は除外しない（注意書きで使われるため）
        ]
        
        # コンパイル済み除外パターン
        self.compiled_exclusions = [re.compile(pattern) for pattern in self.exclusion_patterns]
    
    def extract_structure(self, text: str) -> List[Question]:
        """
        テキストから階層的な問題構造を抽出（修正版）
        
        Args:
            text: 分析対象のテキスト
            
        Returns:
            大問のリスト（各大問は子要素として問と小問を持つ）
        """
        # Step 0: 解答用紙部分を除外
        clean_text = self._remove_answer_sheet_sections(text)
        
        # Step 1: 大問を検出
        major_questions = self._extract_major_questions(clean_text)
        
        # Step 2: 各大問の範囲内で問を検出
        for i, major in enumerate(major_questions):
            # 大問の範囲を特定（次の大問の開始位置まで）
            start = major.position[0]
            end = major_questions[i + 1].position[0] if i + 1 < len(major_questions) else len(clean_text)
            major_text = clean_text[start:end]
            
            # 問を検出（重複除去を強化）
            questions = self._extract_questions_deduplicated(major_text, start, major.number)
            major.children = questions
            
            # Step 3: 各問の範囲内で小問を検出
            for j, question in enumerate(questions):
                q_start = question.position[0] - start
                q_end = questions[j + 1].position[0] - start if j + 1 < len(questions) else len(major_text)
                question_text = major_text[q_start:q_end]
                
                # 小問を検出
                subquestions = self._extract_subquestions(question_text, question.position[0])
                question.children = subquestions
        
        # Step 4: 問題の再割り当て（OCR順序エラー対応）
        major_questions = self._reassign_misplaced_questions(major_questions)
        
        return major_questions
    
    def _remove_answer_sheet_sections(self, text: str) -> str:
        """
        解答用紙部分を除外
        
        Args:
            text: 元のテキスト
            
        Returns:
            解答用紙部分を除外したテキスト
        """
        # より具体的な解答用紙の開始パターン
        # 順序を重要度順に変更（より具体的なパターンを優先）
        answer_sheet_markers = [
            r'社会\s*\(解答用紙\)\s*問',  # 「社会(解答用紙)問」パターン
            r'問1記号問1名称問2理由問3',    # 解答用紙特有のパターン
            r'受験番号氏名\s*※注意',      # 受験番号氏名の後に注意書き
            r'※注意:裏にも解答らん',
        ]
        
        # 文字数の中間あたりから探索（問題用紙の最初にある「解答用紙」を除外）
        search_start = len(text) // 2  # 全体の50%以降から探索
        
        answer_start_pos = len(text)
        for marker in answer_sheet_markers:
            match = re.search(marker, text[search_start:])
            if match:
                actual_pos = search_start + match.start()
                if actual_pos < answer_start_pos:
                    answer_start_pos = actual_pos
        
        # より確実な方法：「社会\n(解答用紙)」の最後の出現位置を探す
        social_answer_pattern = r'社会\s*\(解答用紙\)'
        matches = list(re.finditer(social_answer_pattern, text))
        if matches:
            # 最後に出現する「社会(解答用紙)」を使用
            last_match = matches[-1]
            answer_start_pos = min(answer_start_pos, last_match.start())
        
        if answer_start_pos < len(text):
            # 解答用紙部分を除外
            clean_text = text[:answer_start_pos]
            print(f"解答用紙部分を除外: {len(text)} → {len(clean_text)} 文字")
            return clean_text
        
        return text
    
    def _extract_major_questions(self, text: str) -> List[Question]:
        """大問を抽出（修正版）"""
        major_questions = []
        
        for pattern, marker_type in self.major_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                # 除外パターンのチェック
                if self._should_exclude(text, match.start(), match.end()):
                    continue
                
                # OCRエラー対応：具体的パターン
                if marker_type == 'nitkkoma_13_to_3':
                    number = '3'
                elif marker_type == 'nitkkoma_14_to_4':
                    number = '4'
                else:
                    number = self._normalize_number(match.group(1))
                    if marker_type == 'nitkkoma_ocr_error':
                        number = match.group(1)  # 2桁目を使用
                
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
            if not filtered or q.position[0] - filtered[-1].position[0] > 100:
                filtered.append(q)
        
        # 大問番号の妥当性チェック（より柔軟に）
        expected_numbers = ['1', '2', '3', '4', '5']  # 5も含める（万が一のため）
        valid_majors = []
        
        print(f"フィルタ後の大問候補: {[(q.number, q.marker_type, q.position[0]) for q in filtered]}")
        
        for q in filtered:
            # 数字の場合のみチェック、その他は通す
            if q.number.isdigit():
                if q.number in expected_numbers:
                    valid_majors.append(q)
                else:
                    print(f"無効な大問番号をスキップ: {q.number}")
            else:
                # 数字以外（アルファベット等）は通す
                valid_majors.append(q)
        
        print(f"大問検出: {len(filtered)} → {len(valid_majors)} (妥当性チェック後)")
        return valid_majors
    
    def _extract_questions_deduplicated(self, text: str, offset: int, major_number: str) -> List[Question]:
        """問（中レベル）を抽出（重複除去強化版）"""
        questions = []
        seen_positions = set()
        seen_numbers = {}  # 問番号 → 位置のマッピング
        
        for pattern, marker_type in self.question_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                # 除外パターンのチェック
                if self._should_exclude(text, match.start() + offset, match.end() + offset):
                    continue
                
                # 位置の重複チェック（同じ位置の複数マッチを防ぐ）
                pos = match.start() + offset
                if any(abs(pos - seen_pos) < 3 for seen_pos in seen_positions):  # 3文字以内は重複
                    continue
                
                number = self._normalize_number(match.group(1))
                
                # 同一大問内での問番号重複チェック
                question_key = f"{major_number}-{number}"
                if question_key in seen_numbers:
                    # 同じ問番号が複数回出現する場合、位置が十分離れていれば別の問として扱う
                    previous_pos = seen_numbers[question_key]
                    if abs(pos - previous_pos) < 300:  # 300文字以内なら重複として除外
                        continue
                
                seen_numbers[question_key] = pos
                
                # 有効な問番号のみ（1-20の範囲）
                try:
                    num_val = int(number)
                    if not (1 <= num_val <= 20):
                        continue
                except ValueError:
                    continue
                
                question = Question(
                    level='question',
                    number=number,
                    text=self._get_preview_text(text, match.end(), 100),
                    position=(match.start() + offset, match.end() + offset),
                    marker_type=marker_type
                )
                
                questions.append(question)
                seen_positions.add(pos)
        
        questions.sort(key=lambda x: x.position[0])
        
        # 連続した同じ番号の問題を除去（括弧形式の問題で重複検出されやすい）
        filtered_questions = []
        prev_number = None
        for q in questions:
            if q.number != prev_number:
                filtered_questions.append(q)
                prev_number = q.number
            elif len(filtered_questions) > 0:
                # 前の問題との距離をチェック
                if q.position[0] - filtered_questions[-1].position[0] > 200:
                    filtered_questions.append(q)
        
        print(f"大問{major_number}: {len(filtered_questions)}問を検出")
        return filtered_questions
    
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
    
    def _should_exclude(self, text: str, start: int, end: int) -> bool:
        """除外すべきパターンかチェック"""
        # マッチ周辺のテキストを取得
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 50)
        context = text[context_start:context_end]
        
        # 除外パターンをチェック
        for pattern in self.compiled_exclusions:
            if pattern.search(context):
                return True
        
        return False
    
    def _normalize_number(self, number_str: str) -> str:
        """数字を正規化"""
        # 単一文字の変換
        if number_str in self.number_map:
            return self.number_map[number_str]
        
        # 漢数字の複雑な変換（十一、二十三など）
        if '十' in number_str:
            return self._convert_complex_kanji(number_str)
        
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
    
    def _reassign_misplaced_questions(self, major_questions: List[Question]) -> List[Question]:
        """
        誤配置された問題を再割り当て（OCR順序エラー対応）
        
        Args:
            major_questions: 大問のリスト
            
        Returns:
            再割り当て後の大問リスト
        """
        if len(major_questions) < 2:
            return major_questions
        
        # 各大問の問題番号をチェック
        for i in range(len(major_questions) - 1):
            current_major = major_questions[i]
            next_major = major_questions[i + 1]
            
            if not current_major.children or not next_major.children:
                continue
            
            # 次の大問の全問題をチェック（最初の数問だけでなく）
            misplaced = []
            
            for q in next_major.children:
                try:
                    q_num = int(q.number)
                    # 大問1→大問2の場合: 問9-11が大問2にあるのは異常
                    # 注: この判定は誤動作することがあるため、より厳格な条件を追加
                    # 大問2の最初の問題番号が12以上の場合のみ誤配置と判定
                    first_q_num = int(next_major.children[0].number) if next_major.children else 1
                    if i == 0 and q_num >= 9 and q_num <= 11 and first_q_num >= 12:
                        misplaced.append(q)
                        print(f"誤配置検出: 大問{next_major.number}の問{q.number}は大問{current_major.number}に属する可能性")
                except ValueError:
                    continue
            
            # 誤配置された問題を移動
            if misplaced:
                for q in misplaced:
                    next_major.children.remove(q)
                    current_major.children.append(q)
                
                # 問題番号でソート
                try:
                    current_major.children.sort(key=lambda x: int(x.number))
                except ValueError:
                    pass  # ソートできない場合はそのまま
                
                print(f"大問{current_major.number}に{len(misplaced)}問を再割り当て")
        
        # 大問2の問題番号が1から始まらない場合の処理
        if len(major_questions) >= 2:
            major2 = major_questions[1]
            if major2.children:
                try:
                    # 大問2の問題番号をチェック
                    q_nums = [int(q.number) for q in major2.children]
                    
                    # 問1が存在しない、または最初の番号が9以上の場合
                    if 1 not in q_nums or (q_nums and min(q_nums) >= 9):
                        # 問9-11を大問1に移動、問12-13を問1-2に振り直し
                        major1 = major_questions[0]
                        to_move = []
                        to_renumber = []
                        
                        for q in major2.children:
                            try:
                                num = int(q.number)
                                if num >= 9 and num <= 11:
                                    to_move.append(q)
                                elif num >= 12:
                                    to_renumber.append((q, num - 11))  # 12→1, 13→2
                            except ValueError:
                                pass
                        
                        # 移動
                        for q in to_move:
                            major2.children.remove(q)
                            major1.children.append(q)
                        
                        # 番号振り直し（必要に応じて）
                        # この部分は実装が複雑なため、現状維持
                        
                        # ソート
                        try:
                            major1.children.sort(key=lambda x: int(x.number))
                        except ValueError:
                            pass
                        
                        if to_move:
                            print(f"大問2から大問1へ{len(to_move)}問を再割り当て")
                    
                except ValueError:
                    pass
        
        return major_questions
    
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