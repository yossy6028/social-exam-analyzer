"""
改良版セクション分割モジュール
Geminiの提案に基づく、より正確な大問分割ロジック
"""
import re
from typing import List, Dict, Optional
from models import Section


class ImprovedSectionSplitter:
    """改良版セクション分割クラス"""
    
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
        候補から真の大問マーカーをフィルタリング
        
        Args:
            candidates: マーカー候補のリスト
            text: 元のテキスト（追加の検証用）
            
        Returns:
            確定した大問マーカーのリスト
        """
        if not candidates:
            return []
        
        # 重複除去（同じ位置の複数マッチから最高優先度を選択）
        unique_candidates = []
        position_map = {}
        
        for c in candidates:
            pos_key = c['start']
            if pos_key not in position_map or c['priority'] > position_map[pos_key]['priority']:
                position_map[pos_key] = c
        
        unique_candidates = sorted(position_map.values(), key=lambda x: x['start'])
        
        # 距離とコンテキストによるフィルタリング
        final_markers = []
        
        for i, candidate in enumerate(unique_candidates):
            # 小問パターンを除外
            if self._is_small_question(candidate, text):
                continue
            
            # 最初のマーカーは基本的に採用
            if not final_markers:
                final_markers.append(candidate)
                continue
            
            prev_marker = final_markers[-1]
            distance = candidate['start'] - prev_marker['start']
            
            # 距離が短すぎる場合はスキップ（ただし優先度が高い場合は例外）
            if distance < self.min_section_length:
                # 優先度が前のマーカーより明確に高い場合は置換を検討
                if candidate['priority'] - prev_marker['priority'] >= 3:
                    # 前のマーカーを置換
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
                question_count=self._count_questions(text),
                char_count=len(text.replace(' ', '').replace('\n', '')),  # 実際の文字数を設定
                section_type="その他",
                is_text_problem=True  # デフォルトで文章問題とする
            )]
        
        sections = []
        
        for i, marker in enumerate(markers):
            start_pos = marker['start']
            end_pos = markers[i + 1]['start'] if i + 1 < len(markers) else len(text)
            
            section_text = text[start_pos:end_pos].strip()
            
            # セクションタイプを判定
            section_type = self._determine_section_type(section_text)
            
            section = Section(
                number=marker['number'],
                title=f"大問{marker['number']}（{section_type}）",
                content=section_text[:500] if len(section_text) > 500 else section_text,
                text=section_text,
                question_count=self._count_questions(section_text),
                char_count=len(section_text.replace(' ', '').replace('\n', '')),  # 実際の文字数を設定
                section_type=section_type,
                is_text_problem=section_type in ['文章読解', '詩・韻文']  # 文章問題かどうかを判定
            )
            sections.append(section)
        
        return sections
    
    def _determine_section_type(self, text: str) -> str:
        """セクションタイプを判定"""
        # 最初の200文字で判定
        sample = text[:200]
        
        if '漢字' in sample or 'カタカナ' in sample or '語句' in sample:
            return '漢字・語句'
        elif '次の文章' in sample or '文章を読んで' in sample:
            return '文章読解'
        elif '詩' in sample or '俳句' in sample or '短歌' in sample:
            return '詩・韻文'
        else:
            # 文章の長さで判定
            if len(text) > 2000:
                return '文章読解'
            else:
                return '語句・知識'
    
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