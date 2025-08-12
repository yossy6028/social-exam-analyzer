"""
改良版セクション分割モジュール v3
語句問題と文章問題の判別を強化
"""
import re
from typing import List, Dict, Optional, Tuple
from models import Section


class ImprovedSectionSplitterV3:
    """改良版セクション分割クラス v3"""
    
    def __init__(self, min_section_length: int = 500):
        """
        初期化
        
        Args:
            min_section_length: 有効なセクションとみなす最小文字数
        """
        self.min_section_length = min_section_length
        self.kanji_to_int = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
    
    def split_sections(self, text: str) -> List[Section]:
        """
        テキストを大問ごとに分割
        
        Args:
            text: 分割対象のテキスト
            
        Returns:
            Sectionオブジェクトのリスト
        """
        # ステップ1: マーカー候補を検出
        candidates = self._find_marker_candidates(text)
        
        # ステップ2: 真の大問マーカーをフィルタリング
        true_markers = self._filter_true_markers(candidates, text)
        
        # ステップ3: テキストを分割
        sections = self._split_text_by_markers(text, true_markers)
        
        return sections
    
    def _find_marker_candidates(self, text: str) -> List[Dict]:
        """
        大問マーカーの候補を網羅的に検出
        
        Args:
            text: 検索対象のテキスト
            
        Returns:
            マーカー候補のリスト
        """
        # 優先度順にパターンを定義（高い優先度ほど信頼性が高い）
        patterns = [
            # 最高優先度: 明確な大問表記
            ('daimon_explicit', r'(?m)^大問\s*([一二三四五六七八九十])', 10),
            ('dai_mon', r'(?m)^第([一二三四五六七八九十])問', 9),
            
            # 高優先度: 「次の文章」を含む明確なパターン
            ('kanji_next_sentence', r'(?m)^([一二三四五六七八九十])[、，]\s*次の文章を読んで', 8),
            ('kanji_next_text', r'(?m)^([一二三四五六七八九十])[、，]\s*次のテキストを読んで', 8),
            ('kanji_next_general', r'(?m)^([一二三四五六七八九十])[、，]\s*次の', 7),
            
            # 中優先度: 括弧付き番号
            ('bracket_kanji', r'(?m)^[【［]([一二三四五六七八九十])[】］]', 6),
            ('paren_kanji', r'(?m)^[（(]([一二三四五六七八九十])[）)]', 5),
            
            # 低優先度: 単純な番号（他の条件と組み合わせて使用）
            ('simple_kanji', r'(?m)^([一二三四五六七八九十])[、，]', 3),
        ]
        
        candidates = []
        
        for pattern_name, pattern_regex, priority in patterns:
            for match in re.finditer(pattern_regex, text):
                num_str = match.group(1)
                num = self.kanji_to_int.get(num_str, 0)
                
                # マッチした行全体を取得（デバッグ用）
                line_start = text.rfind('\n', 0, match.start()) + 1
                line_end = text.find('\n', match.end())
                if line_end == -1:
                    line_end = len(text)
                full_line = text[line_start:line_end].strip()
                
                candidates.append({
                    'start': match.start(),
                    'end': match.end(),
                    'number': num,
                    'text': match.group(0).strip(),
                    'full_line': full_line[:100],  # 最初の100文字
                    'type': pattern_name,
                    'priority': priority
                })
        
        # 位置順にソート
        candidates.sort(key=lambda x: x['start'])
        
        return candidates
    
    def _filter_true_markers(self, candidates: List[Dict], text: str) -> List[Dict]:
        """
        真の大問マーカーをフィルタリング
        
        Args:
            candidates: マーカー候補のリスト
            text: 元のテキスト
            
        Returns:
            確定した大問マーカーのリスト
        """
        if not candidates:
            return []
        
        # 優先度でソート（高い順）
        candidates.sort(key=lambda x: (-x['priority'], x['start']))
        
        # 最初のマーカーを確定
        final_markers = []
        
        for candidate in candidates:
            # 小問チェック
            if self._is_small_question(candidate, text):
                continue
            
            # 番号が1の場合は最初のマーカーとして採用
            if candidate['number'] == 1:
                final_markers = [candidate]
                break
        
        if not final_markers:
            # 番号1が見つからない場合、最初の有効な候補を採用
            for candidate in candidates:
                if not self._is_small_question(candidate, text):
                    final_markers = [candidate]
                    break
        
        if not final_markers:
            return []
        
        # 連続する番号を追加
        candidates.sort(key=lambda x: x['start'])
        
        for candidate in candidates:
            if candidate == final_markers[0]:
                continue
            
            # 小問チェック
            if self._is_small_question(candidate, text):
                continue
            
            # 位置チェック（前のマーカーより後にある）
            prev_marker = final_markers[-1]
            if candidate['start'] <= prev_marker['start']:
                continue
            
            # 距離チェック（近すぎる場合はスキップ）
            distance = candidate['start'] - prev_marker['start']
            if distance < 100:  # 100文字以内は近すぎる
                # ただし、優先度が高い場合は置き換え
                if candidate['priority'] > prev_marker['priority']:
                    final_markers[-1] = candidate
                continue
            
            # 番号の連続性チェック（緩和版）
            expected_num = prev_marker['number'] + 1
            if candidate['number'] != expected_num:
                # 番号が飛んでいる、または戻っている場合
                # ただし、優先度が高いパターンの場合は許容
                if candidate['priority'] < 6 and candidate['number'] <= prev_marker['number']:
                    # 番号が戻る場合のみスキップ（番号が飛ぶのは許容）
                    continue
            
            final_markers.append(candidate)
        
        return final_markers
    
    def _is_small_question(self, candidate: Dict, text: str) -> bool:
        """
        候補が小問かどうかを判定
        
        Args:
            candidate: マーカー候補
            text: 元のテキスト
            
        Returns:
            小問の場合True
        """
        # 「問一」「問二」などの小問パターンをチェック
        if candidate['type'] == 'simple_kanji':
            # 前後のコンテキストを確認
            context_start = max(0, candidate['start'] - 50)
            context_end = min(len(text), candidate['end'] + 100)
            context = text[context_start:context_end]
            
            # 小問のインジケーター
            small_question_indicators = [
                r'問[一二三四五]',
                r'設問[一二三四五]',
                r'次の問いに答えなさい',
                r'について.*答えなさい',
                r'傍線部',
                r'空欄'
            ]
            
            for indicator in small_question_indicators:
                if re.search(indicator, context):
                    return True
        
        return False
    
    def _split_text_by_markers(self, text: str, markers: List[Dict]) -> List[Section]:
        """
        確定したマーカーに基づいてテキストを分割
        
        Args:
            text: 分割対象のテキスト
            markers: 確定した大問マーカーのリスト
            
        Returns:
            Sectionオブジェクトのリスト
        """
        if not markers:
            # マーカーが見つからない場合は全体を1つのセクションとする
            return [Section(
                number=1,
                title="大問1（全体）",
                content=text[:500],
                text=text,
                question_count=self._count_questions(text)
            )]
        
        sections = []
        
        for i, marker in enumerate(markers):
            start_pos = marker['start']
            end_pos = markers[i + 1]['start'] if i + 1 < len(markers) else len(text)
            
            section_text = text[start_pos:end_pos].strip()
            
            # セクションタイプを判定（改良版）
            section_type, is_text_problem = self._determine_section_type_v2(section_text)
            
            # 文字数カウント（語句問題の場合はNone）
            char_count = len(section_text) if is_text_problem else None
            
            section = Section(
                number=marker['number'],
                title=f"大問{marker['number']}（{section_type}）",
                content=section_text[:500] if len(section_text) > 500 else section_text,
                text=section_text,
                question_count=self._count_questions(section_text),
                section_type=section_type,
                is_text_problem=is_text_problem,
                char_count=char_count
            )
            sections.append(section)
        
        return sections
    
    def _determine_section_type_v2(self, text: str) -> Tuple[str, bool]:
        """
        セクションタイプを判定（改良版）
        
        Returns:
            (セクションタイプ, 文章問題かどうか)
        """
        # 全体の長さで初期判定
        text_length = len(text)
        
        # 最初の500文字で詳細判定
        sample = text[:500]
        
        # 語句・漢字問題の明確な指標
        word_problem_indicators = [
            '漢字の読み',
            '漢字を書き',
            'カタカナ',
            '語句',
            '慣用句',
            'ことわざ',
            '熟語',
            '同音異義語',
            '類義語',
            '対義語',
            '次の①～⑤',
            '次の(1)～(5)',
            '下記の'
        ]
        
        # 文章問題の明確な指標
        text_problem_indicators = [
            '次の文章を読んで',
            '文章を読んで',
            '次の文を読んで',
            '以下の文章',
            '作者',
            '筆者',
            '著者',
            '～による',
            '～より'
        ]
        
        # 語句問題チェック
        for indicator in word_problem_indicators:
            if indicator in sample:
                # 短い問題（2000文字未満）で語句指標がある場合
                if text_length < 2000:
                    return '漢字・語句', False
        
        # 文章問題チェック
        for indicator in text_problem_indicators:
            if indicator in sample:
                return '文章読解', True
        
        # 出典チェック（文末）
        if text_length > 1000:
            last_part = text[-300:]
            if re.search(r'[「『].*[」』].*(?:による|より)', last_part):
                return '文章読解', True
            if re.search(r'（.*出典.*）', last_part):
                return '文章読解', True
        
        # 詩・韻文チェック
        if '詩' in sample or '俳句' in sample or '短歌' in sample:
            return '詩・韻文', True
        
        # 長さベースの最終判定
        if text_length > 3000:
            # 3000文字以上は通常文章問題
            return '文章読解', True
        elif text_length < 1000:
            # 1000文字未満は通常語句問題
            return '語句・知識', False
        else:
            # 中間的な長さの場合、設問パターンで判定
            question_patterns = re.findall(r'問[一二三四五六七八九十0-9]+', text)
            if len(question_patterns) > 5:
                # 設問が多い場合は語句問題の可能性が高い
                return '語句・知識', False
            else:
                return '文章読解', True
    
    def _count_questions(self, text: str) -> int:
        """セクション内の設問数をカウント"""
        # 設問パターン
        patterns = [
            r'問([０-９0-9]+)',
            r'問([一二三四五六七八九十]+)',
            r'設問([０-９0-9]+)',
            r'\(([０-９0-9]+)\)',
            r'([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])',
        ]
        
        max_num = 0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 最大値を取得
                for match in matches:
                    try:
                        if match in '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮':
                            num = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮'.index(match) + 1
                        elif match in self.kanji_to_int:
                            num = self.kanji_to_int[match]
                        else:
                            num = int(match)
                        max_num = max(max_num, num)
                    except:
                        continue
        
        return max(max_num, 1)