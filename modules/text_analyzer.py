"""
テキスト分析モジュール
OCR結果から問題構造を分析し、設問タイプを分類する
"""
import re
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """テキスト分析クラス"""
    
    # 定数定義（マジックナンバーの除去）
    MIN_SECTION_DISTANCE = 500  # セクション間の最小文字数
    MIN_SECTION_CONTENT = 50    # 有効なセクションの最小文字数
    MIN_QUESTION_DISTANCE = 30  # 設問間の最小文字数
    MIN_VALID_SECTION_SIZE = 200  # 有効なセクションの最小サイズ
    
    def __init__(self, question_patterns: Dict[str, List[str]]):
        """
        初期化
        
        Args:
            question_patterns: 設問タイプのパターン辞書
        """
        self.question_patterns = question_patterns
        self.compiled_patterns = {}
        
        # パターンをコンパイル
        for q_type, patterns in question_patterns.items():
            self.compiled_patterns[q_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
            
    def analyze_exam_structure(self, text: str) -> Dict[str, Any]:
        """
        試験問題の構造を分析
        
        Args:
            text: OCRで抽出されたテキスト
            
        Returns:
            分析結果の辞書
        """
        result = {
            'total_characters': len(text.replace(' ', '').replace('\n', '')),
            'sections': [],
            'questions': [],
            'question_types': defaultdict(int),
            'theme': None
        }
        
        # 大問の検出
        sections = self._detect_sections(text)
        result['sections'] = sections
        
        # 各大問内の設問を検出
        for section in sections:
            questions = self._detect_questions(section['text'])
            for q in questions:
                q['section'] = section['number']
                result['questions'].append(q)
                
        # 設問タイプの分類
        for question in result['questions']:
            q_type = self._classify_question_type(question['text'])
            question['type'] = q_type
            result['question_types'][q_type] += 1
            
        # テーマの判定
        result['theme'] = self._detect_theme(text)
        
        return result
        
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        大問（セクション）を検出
        
        Args:
            text: 全文テキスト
            
        Returns:
            大問のリスト
        """
        sections = []
        
        # 大問のパターン（改善版）
        section_patterns = [
            # 「一、次の文章を読んで」パターン（最優先）
            (r'([一二三四五六七八九十])、次の文章を読んで', 'main_section_comma'),
            # 「二 次の文章を読んで」パターン（スペース区切り）
            (r'([一二三四五六七八九十])\s+次の文章を読んで', 'main_section_space'),
            # 「次の文章を読んであとの質問に答えなさい。」パターン（武蔵形式）
            (r'次の文章を読んであとの質問に答えなさい', 'musashi_pattern'),
            # 「第一問」などのパターン
            (r'(?:^|\n)\s*第([一二三四五六七八九十]+)問', 'dai_mon'),
        ]
        
        # すべてのマッチを収集
        all_matches = []
        for pattern, p_type in section_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                # 武蔵パターンには漢数字がないため、別途処理
                if p_type == 'musashi_pattern':
                    all_matches.append({
                        'start': match.start(),
                        'end': match.end(),
                        'marker': match.group(0).strip(),
                        'type': p_type,
                        'number_text': None  # 武蔵パターンには番号がない
                    })
                else:
                    all_matches.append({
                        'start': match.start(),
                        'end': match.end(),
                        'marker': match.group(0).strip(),
                        'type': p_type,
                        'number_text': match.group(1)
                    })
        
        # 位置でソート
        all_matches.sort(key=lambda x: x['start'])
        
        # 重複を除去し、妥当な大問だけを選択
        selected_matches = []
        prev_pos = -1
        
        # 漢数字を数値に変換
        kanji_to_num = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        for match in all_matches:
            # 前のマッチと近すぎる場合はスキップ（最初のマッチは除く）
            if prev_pos != -1 and match['start'] - prev_pos < self.MIN_SECTION_DISTANCE:  # 500文字以上離れていること
                continue
                
            # 大問の後に十分なテキストがあることを確認
            remaining_text = text[match['end']:match['end']+self.MIN_SECTION_DISTANCE] if match['end']+self.MIN_SECTION_DISTANCE < len(text) else text[match['end']:]
            if len(remaining_text.strip()) < self.MIN_SECTION_CONTENT:  # 最低50文字のコンテンツ
                continue
                
            # 「次の文章を読んで」タイプを優先（武蔵パターンも含む）
            if match['type'] in ['main_section_comma', 'main_section_space', 'musashi_pattern']:
                selected_matches.append(match)
                prev_pos = match['start']
            # 文章が含まれていることを確認
            elif self._is_valid_section(remaining_text):
                selected_matches.append(match)
                prev_pos = match['start']
        
        # 大問を構築
        for i, match in enumerate(selected_matches):
            section_start = match['start']
            section_end = selected_matches[i + 1]['start'] if i + 1 < len(selected_matches) else len(text)
            
            section_text = text[section_start:section_end]
            
            # 番号の決定（武蔵パターンの場合は連番）
            if match['number_text'] is None:
                number = i + 1
            else:
                number = kanji_to_num.get(match['number_text'], i + 1)
            
            sections.append({
                'number': number,
                'marker': match['marker'],
                'text': section_text,
                'start_pos': section_start,
                'end_pos': section_end
            })
        
        # 大問が見つからない場合は全体を1つの大問とする
        return sections if sections else [{'number': 1, 'marker': '', 'text': text, 'start_pos': 0, 'end_pos': len(text)}]
    
    def _is_valid_section(self, text: str) -> bool:
        """
        有効な大問かどうかを判定
        
        Args:
            text: セクションのテキスト
            
        Returns:
            有効な場合True
        """
        # 最低文字数チェック
        if len(text.strip()) < self.MIN_VALID_SECTION_SIZE:
            return False
            
        # 文章の存在を示すキーワード
        text_indicators = [
            '次の文', '以下の文', '文章を読', '〜より', '出典',
            'という', 'である', 'でした', 'だった', 'ます'
        ]
        
        return any(indicator in text for indicator in text_indicators)
        
    def _detect_questions(self, text: str) -> List[Dict[str, Any]]:
        """
        設問を検出
        
        Args:
            text: セクションのテキスト
            
        Returns:
            設問のリスト
        """
        questions = []
        
        # 設問のパターン（改善版）
        question_patterns = [
            r'(?:^|\n|\s)問([一二三四五六七八九十]+)',  # 問一、問二など（漢数字）
            r'(?:^|\n|\s)間([一二三四五六七八九十]+)',  # OCRの誤認識対応（問→間）
            r'(?:^|\n|\s)問([０-９0-9]+)[^\w]',  # 問1、問2など
            r'(?:^|\n|\s)[（(]([０-９0-9]+)[）)][^\w]',  # (1)、(2)など
            r'(?:^|\n|\s)[［\[]{1}([０-９0-9]+)[］\]]{1}[^\w]',  # [1]、[2]など
            r'(?:^|\n|\s)設問([０-９0-9]+)[^\w]',  # 設問1など
            r'([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])',  # 丸数字
            r'(?:^|\n|\s)[ア-ン]\s*[．。、]',  # ア．イ．など
            # 武蔵特有のパターン
            r'(?:^|\n)\s{0,3}[1-9]\s*[^\d]',  # 行頭の数字（1桁）
            r'(?:^|\n)\s{0,3}1[0-9]\s*[^\d]',  # 行頭の数字（10番台）
        ]
        
        # すべてのマッチを収集
        all_matches = []
        for pattern in question_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                all_matches.append((match.start(), match.end(), match.group().strip()))
        
        # 位置でソート
        all_matches.sort(key=lambda x: x[0])
        
        # 重複を除去し、妥当な設問だけを選択
        selected_matches = []
        prev_pos = -1
        
        for start, end, marker in all_matches:
            # 前のマッチと近すぎる場合はスキップ
            if start - prev_pos < self.MIN_QUESTION_DISTANCE:  # 30文字以上離れていること
                continue
                
            # 「間口は三間一尺」のような文章中の「間」を除外
            if '間' in marker and start > 0:
                context = text[max(0, start-10):min(len(text), end+10)]
                if '間口' in context or '間一尺' in context or '三間' in context:
                    continue
                    
            # ページ4の解答用紙部分の設問番号を除外
            if '解答用紙' in text[max(0, start-100):min(len(text), end+100)]:
                continue
                
            # 設問の後に十分なテキストがあることを確認
            remaining_text = text[end:end+100] if end+100 < len(text) else text[end:]
            if len(remaining_text.strip()) < 10:
                continue
                
            selected_matches.append((start, end, marker))
            prev_pos = start
        
        # 設問を構築
        for i, (start, end, marker) in enumerate(selected_matches):
            question_end = selected_matches[i + 1][0] if i + 1 < len(selected_matches) else len(text)
            
            question_text = text[start:question_end].strip()
            
            # 有効な設問かチェック
            if self._is_valid_question(question_text):
                # 問番号の正規化（間→問）
                normalized_marker = marker.replace('間', '問')
                
                questions.append({
                    'number': len(questions) + 1,
                    'marker': normalized_marker,
                    'text': question_text,
                    'start_pos': start,
                    'end_pos': question_end
                })
        
        return questions
    
    def _is_valid_question(self, text: str) -> bool:
        """
        有効な設問かどうかを判定
        
        Args:
            text: 設問のテキスト
            
        Returns:
            有効な場合True
        """
        # 最低文字数チェック
        if len(text.strip()) < 10:
            return False
            
        # 設問を示すキーワード
        question_keywords = [
            'なさい', 'か。', 'て。', 'を。', 'に。',
            '答え', '説明', '述べ', '書き', '選び',
            'どの', 'なぜ', 'いつ', 'どこ', 'だれ',
            'について', 'とは', 'ですか', 'でしょうか',
            '漢字', '語句', '慣用句', 'から選び', '語群',
            'に入る', '部分を', 'の折れる', 'アもイもなかった'
        ]
        
        return any(keyword in text for keyword in question_keywords)
        
    def _classify_question_type(self, question_text: str) -> str:
        """
        設問タイプを分類
        
        Args:
            question_text: 設問のテキスト
            
        Returns:
            設問タイプ
        """
        # 漢字・語句問題のチェック
        if any(pattern.search(question_text) for pattern in self.compiled_patterns.get('漢字・語句', [])):
            return '漢字・語句'
        
        # 丸数字で慣用句・語句問題の場合
        if re.search(r'^[①②③④⑤⑥⑦⑧⑨⑩]', question_text[:10]) and \
           re.search(r'慣用句|ことわざ|語句|漢字|語群|に入る', question_text):
            return '漢字・語句'
            
        # 選択肢の存在をチェック（記号選択）
        if re.search(r'[ア-ン]\s*[\.。、]', question_text) or \
           re.search(r'[A-H]\s*[\.。、]', question_text) or \
           any(pattern.search(question_text) for pattern in self.compiled_patterns.get('記号選択', [])):
            return '記号選択'
            
        # 抜き出し問題のチェック
        if any(pattern.search(question_text) for pattern in self.compiled_patterns.get('抜き出し', [])):
            return '抜き出し'
            
        # 脱文挿入のチェック
        if any(pattern.search(question_text) for pattern in self.compiled_patterns.get('脱文挿入', [])):
            return '脱文挿入'
            
        # 記述問題の判定（より広範なパターン）
        # 文字数指定がある場合
        if re.search(r'\d+字', question_text):
            return '記述'
            
        # 記述を示唆するキーワード
        description_keywords = [
            '説明し', '述べ', '書き', '答え', 'まとめ',
            '考えを', '理由を', 'どのよう', 'なぜ', 'どうして',
            '〜について', '〜とは', '具体的に', '詳しく'
        ]
        
        # 行末パターン（記述問題によくある）
        if re.search(r'(?:答えなさい|述べなさい|書きなさい|説明しなさい|まとめなさい)[。．]?$', question_text):
            # 文字数制限や選択肢がなければ記述
            if not re.search(r'[ア-ン]\s*[\.。、]', question_text) and \
               not re.search(r'から選び', question_text):
                return '記述'
                
        # キーワードベースの判定
        if any(keyword in question_text for keyword in description_keywords):
            # 選択肢や抜き出し指示がなければ記述とする
            if not re.search(r'[ア-ン]\s*[\.。、]', question_text) and \
               not re.search(r'抜き出し', question_text) and \
               not re.search(r'から選び', question_text):
                return '記述'
                
        return 'その他'
        
    def _detect_theme(self, text: str) -> str:
        """
        文章のテーマを判定
        
        Args:
            text: 全文テキスト
            
        Returns:
            テーマ（説明文、物語文、随筆、詩、古文）
        """
        # キーワードベースの簡易判定
        theme_keywords = {
            '説明文': ['である', 'だろう', 'と考えられる', 'ということ', 'つまり'],
            '物語文': ['だった', 'でした', '彼は', '彼女は', '私は'],
            '随筆': ['思う', '感じる', 'だろうか', '私には'],
            '詩': ['詩', '俳句', '短歌', '季語'],
            '古文': ['けり', 'たり', 'なり', 'べし', 'らむ']
        }
        
        theme_scores = defaultdict(int)
        
        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                count = text.count(keyword)
                theme_scores[theme] += count
                
        # 最も高いスコアのテーマを返す
        if theme_scores:
            return max(theme_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'その他'