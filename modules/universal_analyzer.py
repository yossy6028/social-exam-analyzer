"""
汎用入試問題分析モジュール
すべての学校に対応する統一された分析ロジック
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from models import AnalysisResult, Section, ExamSource as Source
from config.settings import Settings
from modules.improved_question_analyzer import ImprovedQuestionAnalyzer, QuestionAnalysis
from modules.section_splitter_v2 import ImprovedSectionSplitter
import logging

logger = logging.getLogger(__name__)


class UniversalAnalyzer:
    """すべての学校に対応する汎用分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.question_patterns = Settings.QUESTION_PATTERNS
        self.compiled_patterns = self._compile_patterns()
        self.improved_analyzer = ImprovedQuestionAnalyzer()
        self.section_splitter = ImprovedSectionSplitter(min_section_length=500)
        
    def _compile_patterns(self) -> Dict[str, List]:
        """パターンをコンパイル"""
        compiled = {}
        for q_type, patterns in self.question_patterns.items():
            compiled[q_type] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in patterns
            ]
        return compiled
    
    def analyze(self, text: str, school_name: str, year: str) -> AnalysisResult:
        """
        入試問題テキストを分析
        
        Args:
            text: 分析対象のテキスト
            school_name: 学校名
            year: 年度
            
        Returns:
            分析結果
        """
        logger.info(f"分析開始: {school_name} {year}年")
        
        # 基本分析
        sections = self._analyze_sections(text)
        
        # 各セクションから出典を抽出して直接関連付け
        for i, section in enumerate(sections):
            section_text = section.text if hasattr(section, 'text') else section.content
            
            # セクション内から出典を抽出
            section_sources = self._extract_sources_from_text(section_text)
            if section_sources:
                # 最初の出典をセクションに直接設定
                section.source = section_sources[0]
                # ジャンルとテーマも個別に検出
                section.genre = self._detect_genre(section_text)
                section.theme = self._detect_theme(section_text)
            
            # セクションごとの設問分析
            section_analysis = self.improved_analyzer.analyze_questions(
                section_text, 
                section_type=section.section_type if hasattr(section, 'section_type') else None
            )
            
            # セクションに詳細な設問分析を追加
            section.question_details = {
                '選択': {
                    'count': section_analysis.type_counts.get('選択', 0),
                    'details': section_analysis.choice_counts
                },
                '記述': {
                    'count': section_analysis.type_counts.get('記述', 0),
                    'with_limit': section_analysis.has_word_limit,
                    'without_limit': section_analysis.no_word_limit,
                    'word_limit_details': section_analysis.word_limit_details
                },
                '抜き出し': {
                    'count': section_analysis.type_counts.get('抜き出し', 0),
                    'details': section_analysis.extract_details
                },
                '漢字': {
                    'count': section_analysis.type_counts.get('漢字', 0)
                },
                '語句': {
                    'count': section_analysis.type_counts.get('語句', 0)
                }
            }
            
            # 選択肢の詳細を設定
            if section_analysis.choice_type_details:
                section.choice_type_details = section_analysis.choice_type_details
        
        # 全体の統合分析も実行
        detailed_analysis = self.improved_analyzer.analyze_sections_with_questions(sections, text)
        
        # 設問タイプを詳細分析から取得
        question_types = detailed_analysis.type_counts
        
        # 全体の出典リストを作成
        sources = []
        for section in sections:
            if hasattr(section, 'source') and section.source:
                if not any(s.title == section.source.title and s.author == section.source.author for s in sources):
                    sources.append(section.source)
        
        # 全体のテーマとジャンル（最初の文章セクションから取得）
        theme = None
        genre = None
        for section in sections:
            if hasattr(section, 'is_text_problem') and section.is_text_problem:
                if hasattr(section, 'theme') and section.theme:
                    theme = section.theme
                if hasattr(section, 'genre') and section.genre:
                    genre = section.genre
                if theme and genre:
                    break
        
        # テーマ・ジャンルが取得できない場合は全体から検出
        if not theme:
            theme = self._detect_theme(text)
        if not genre:
            genre = self._detect_genre(text)
        
        # 結果を作成
        result = AnalysisResult(
            school_name=school_name,
            year=year,
            total_characters=len(text.replace(' ', '').replace('\n', '')),
            sections=sections,
            questions=[],  # 空のリストを設定
            question_types=question_types,
            sources=sources,
            theme=theme,
            genre=genre
        )
        
        # 詳細分析結果を追加属性として保存
        result.choice_distribution = detailed_analysis.choice_counts if hasattr(detailed_analysis, 'choice_counts') else {}
        result.written_answer_details = {
            'has_word_limit': detailed_analysis.has_word_limit if hasattr(detailed_analysis, 'has_word_limit') else 0,
            'no_word_limit': detailed_analysis.no_word_limit if hasattr(detailed_analysis, 'no_word_limit') else 0
        }
        
        # 詳細分析情報を追加
        if hasattr(detailed_analysis, 'word_limit_details') and detailed_analysis.word_limit_details:
            result.word_limit_details = detailed_analysis.word_limit_details
        
        if hasattr(detailed_analysis, 'choice_type_details') and detailed_analysis.choice_type_details:
            result.choice_type_details = detailed_analysis.choice_type_details
        
        if hasattr(detailed_analysis, 'extract_details') and detailed_analysis.extract_details:
            result.extract_details = detailed_analysis.extract_details
        
        logger.info(f"分析完了: 大問{len(sections)}個、設問{result.get_question_count()}問")
        
        return result
    
    def _analyze_sections(self, text: str) -> List[Section]:
        """セクション（大問）を分析 - 改善版"""
        
        # 新しい改良版セクション分割を使用
        sections = self.section_splitter.split_sections(text)
        
        # セクションが見つからない場合のフォールバック
        if not sections:
            sections = [Section(
                number=1,
                title="全体",
                content=text[:500],
                text=text,
                question_count=self._count_questions_in_section(text),
                char_count=len(text.replace(' ', '').replace('\n', '')),  # 実際の文字数を設定
                section_type="その他",
                is_text_problem=True  # デフォルトで文章問題とする
            )]
        
        return sections
    
    def _split_by_major_markers(self, text: str) -> List[Section]:
        """構造的な大問マーカーで確実に分割する新メソッド"""
        sections = []
        
        # 大問マーカーのパターン（優先度順）
        major_patterns = [
            # 漢数字 + 読点 + 「次の」（最も一般的）
            (r'^([一二三四五六七八九十])[、，]\s*次の', 'kanji_comma_next'),
            # 「大問」+ 漢数字
            (r'^大問\s*([一二三四五六七八九十])', 'daimon_kanji'),
            # 「第」+ 漢数字 + 「問」
            (r'^第([一二三四五六七八九十])問', 'dai_kanji_mon'),
            # 「問」+ 漢数字（問一、問二など）
            (r'^問([一二三四五六七八九十])(?:[^\d]|$)', 'mon_kanji'),
            # 算用数字 + 読点/句点
            (r'^([１２３４５６７８９])[、．.]', 'number_punct'),
        ]
        
        # すべてのマーカーの位置を収集
        markers = []
        for line_num, line in enumerate(text.split('\n')):
            line_stripped = line.strip()
            
            # 「問一」「問二」などの小問を除外するためのチェック
            # ただし「三、次の漢字」のような場合は大問として扱う
            if line_stripped.startswith('問') and not re.match(r'^問\s*[一二三四五]', line_stripped):
                # 「問1」「問2」などの小問は除外（「問一」のような大問番号は許可）
                if re.match(r'^問\s*\d+', line_stripped) or re.match(r'^問\s*[①-⑮]', line_stripped):
                    continue
                
            for pattern, pattern_type in major_patterns:
                match = re.match(pattern, line_stripped)
                if match:
                    # 大問として認識する条件を改善
                    # 「一、」「二、」「三、」などは基本的に大問として扱う
                    # ただし、明らかに小問の場合は除外
                    is_major_section = False
                    
                    if pattern_type == 'kanji_comma_next':
                        # 漢数字+読点パターンは常に大問
                        is_major_section = True
                    elif '次の' in line:
                        # 「次の」が含まれる場合は大問
                        is_major_section = True
                    elif pattern_type in ['daimon_kanji', 'dai_kanji_mon']:
                        # 「大問」「第X問」は常に大問
                        is_major_section = True
                    elif re.match(r'^[一二三四五六七八九十][、，]', line_stripped):
                        # 漢数字+読点で始まる場合は大問の可能性が高い
                        is_major_section = True
                    
                    if is_major_section:
                        # テキスト内での実際の位置を計算
                        position = sum(len(l) + 1 for l in text.split('\n')[:line_num])
                        markers.append({
                            'position': position,
                            'marker': match.group(0),
                            'number': match.group(1) if match.groups() else str(len(markers) + 1),
                            'type': pattern_type,
                            'line': line_num,
                            'full_line': line_stripped[:50]  # デバッグ用
                        })
                        break  # 最初にマッチしたパターンのみ使用
        
        # 位置でソート
        markers.sort(key=lambda x: x['position'])
        
        # マーカーが2つ以上ある場合のみ分割
        if len(markers) >= 2:
            for i, marker in enumerate(markers):
                start_pos = marker['position']
                end_pos = markers[i + 1]['position'] if i + 1 < len(markers) else len(text)
                
                section_text = text[start_pos:end_pos].strip()
                
                # 最小文字数チェック（緩和: 100 -> 20）
                # 短い大問（漢字問題など）も考慮
                if len(section_text) > 20:
                    # セクションタイプを判定
                    section_type = self._determine_section_type(section_text)
                    
                    section = Section(
                        number=i + 1,
                        title=f"大問{self._convert_to_arabic(marker['number'])}（{section_type}）",
                        content=section_text[:500] if len(section_text) > 500 else section_text,
                        text=section_text,
                        question_count=self._count_questions_in_section(section_text),
                        char_count=len(section_text.replace(' ', '').replace('\n', '')),  # 実際の文字数を設定
                        section_type=section_type,
                        is_text_problem=section_type in ['文章読解', '詩・韻文']  # 文章問題かどうかを判定
                    )
                    sections.append(section)
        
        return sections
    
    def _convert_to_arabic(self, num_str: str) -> str:
        """漢数字やその他の数字を算用数字に変換"""
        kanji_map = {
            '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
        }
        
        # 全角数字を半角に
        if '１' <= num_str[0] <= '９':
            return str(ord(num_str[0]) - ord('１') + 1)
        
        # 漢数字を変換
        return kanji_map.get(num_str, num_str)
    
    def _detect_sections_by_question_reset(self, text: str) -> List[Section]:
        """設問番号のリセットを検出して大問を区切る"""
        sections = []
        
        # 設問番号のパターン
        question_patterns = [
            r'問([１-９0-9]+)',  # 問1, 問１など
            r'問([一二三四五六七八九十]+)',  # 問一, 問二など
            r'\(([１-９0-9]+)\)',  # (1), (１)など
            r'([①-⑮])',  # ①, ②など
        ]
        
        # すべての設問番号を位置と共に収集
        all_questions = []
        for pattern in question_patterns:
            for match in re.finditer(pattern, text):
                # 番号を数値に変換
                num_str = match.group(1)
                num = self._convert_to_number(num_str)
                if num > 0:
                    all_questions.append({
                        'position': match.start(),
                        'number': num,
                        'text': match.group(0),
                        'pattern': pattern
                    })
        
        # 位置でソート
        all_questions.sort(key=lambda x: x['position'])
        
        # 番号がリセットされる位置を検出
        section_starts = []
        prev_num = 0
        prev_pattern = None
        prev_position = 0
        
        for q in all_questions:
            # 問1に戻った場合（番号リセット）
            # ただし、位置が近すぎる場合（500文字以内）は無視
            if q['number'] == 1 and prev_num > 1 and q['position'] - prev_position > 500:
                section_starts.append(q['position'])
            
            # 異なるパターンで1から始まる場合も検出
            if q['number'] == 1 and prev_pattern and q['pattern'] != prev_pattern:
                if not section_starts or q['position'] - section_starts[-1] > 500:
                    section_starts.append(q['position'])
            
            prev_num = q['number']
            prev_pattern = q['pattern']
            prev_position = q['position']
        
        # 最初のセクションの開始位置を追加（テキストの先頭）
        if section_starts:
            section_starts.insert(0, 0)
        elif all_questions:
            # セクションリセットが検出されない場合は全体を1つとする
            section_starts = [0]
        
        # セクションを作成
        for i, start_pos in enumerate(section_starts):
            end_pos = section_starts[i + 1] if i + 1 < len(section_starts) else len(text)
            section_text = text[start_pos:end_pos]
            
            if len(section_text) > Settings.MIN_SECTION_CONTENT:
                # セクションタイプを判定
                section_type = self._determine_section_type(section_text)
                
                section = Section(
                    number=i + 1,
                    title=f"大問{i + 1}（{section_type}）",
                    content=section_text,  # 全文を保存
                    text=section_text,
                    question_count=self._count_questions_in_section(section_text),
                    char_count=len(section_text.replace(' ', '').replace('\n', '')),  # 実際の文字数を設定
                    section_type=section_type,
                    is_text_problem=section_type in ['文章読解', '詩・韻文']  # 文章問題かどうかを判定
                )
                sections.append(section)
        
        return sections
    
    def _convert_to_number(self, num_str: str) -> int:
        """漢数字や丸数字を数値に変換"""
        # 漢数字
        kanji_to_num = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15
        }
        
        # 丸数字
        circle_to_num = {
            '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
            '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
            '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15
        }
        
        # 全角数字を半角に変換
        if '０' <= num_str[0] <= '９':
            num_str = ''.join(str(ord(c) - ord('０')) for c in num_str)
        
        # 変換
        if num_str in kanji_to_num:
            return kanji_to_num[num_str]
        elif num_str in circle_to_num:
            return circle_to_num[num_str]
        elif num_str.isdigit():
            return int(num_str)
        else:
            return 0
    
    def _determine_section_type(self, text: str) -> str:
        """セクションタイプを判定"""
        # 漢字・語句の判定
        if '漢字' in text[:200] or 'カタカナ' in text[:200] or '語句' in text[:200]:
            return '漢字・語句'
        # 文章読解の判定
        elif '次の文章' in text[:200] or '文章を読んで' in text[:200]:
            return '文章読解'
        # 詩・韻文の判定
        elif '詩' in text[:200] or '俳句' in text[:200] or '短歌' in text[:200]:
            return '詩・韻文'
        else:
            # 文章の長さで判定
            if len(text) > 2000:
                return '文章読解'
            else:
                return '語句・知識'
    
    def _handle_special_section_pattern(self, text: str) -> List[Section]:
        """早稲田実業のような特殊なセクションパターンを処理"""
        sections = []
        
        # 特定のパターンを検索
        patterns_with_positions = []
        
        # すべての大問パターンを一度に検索して重複を避ける
        # パターン1: 最初の文章（「- 次の文章」「一 次の文章」など）
        # 「二」で始まらない「次の文章」を探す
        all_next_patterns = list(re.finditer(r'[-|一二三]\s*次の', text))
        
        for match in all_next_patterns:
            match_text = text[match.start():match.start() + 20]
            
            # 第一の文章（「- 次の文章」または「一 次の文章」）
            if re.match(r'[-|一]\s*次の文章', match_text):
                if not any(pos for pos, _ in patterns_with_positions if abs(pos - match.start()) < 10):
                    patterns_with_positions.append((match.start(), '文章読解1'))
            
            # 第二の文章（「二 次の文章」）
            elif re.match(r'二\s*次の文章', match_text):
                if not any(pos for pos, _ in patterns_with_positions if abs(pos - match.start()) < 10):
                    patterns_with_positions.append((match.start(), '文章読解2'))
            
            # 第三の問題（「三次の問い」「三次の1~8」など）
            elif re.match(r'三\s*次の', match_text):
                if '問い' in match_text or '漢字' in text[match.start():match.start() + 100]:
                    if not any(pos for pos, _ in patterns_with_positions if abs(pos - match.start()) < 10):
                        patterns_with_positions.append((match.start(), '漢字・語句'))
        
        # 位置でソート
        patterns_with_positions.sort(key=lambda x: x[0])
        
        # セクションを作成
        for i, (start_pos, section_type) in enumerate(patterns_with_positions):
            end_pos = patterns_with_positions[i+1][0] if i+1 < len(patterns_with_positions) else len(text)
            
            section_text = text[start_pos:end_pos]
            if len(section_text) > 20:  # 最低20文字以上（短い大問も考慮）
                section = Section(
                    number=i + 1,
                    title=f"大問{i+1}（{section_type}）",
                    content=section_text,  # 全文を保存
                    text=section_text,  # textフィールドにも保存
                    question_count=self._count_questions_in_section(section_text),
                    char_count=len(section_text.replace(' ', '').replace('\n', '')),  # 実際の文字数を設定
                    section_type=section_type,
                    is_text_problem=section_type in ['文章読解', '詩・韻文']  # 文章問題かどうかを判定
                )
                sections.append(section)
        
        return sections
    
    def _count_questions_in_section(self, text: str) -> int:
        """セクション内の設問数をカウント"""
        # 設問パターン（優先度順）
        question_patterns = [
            (r'問([０-９0-9]+)', 'number'),  # 問1, 問2など
            (r'問([一二三四五六七八九十]+)', 'kanji'),  # 問一, 問二など
            (r'設問([０-９0-9]+)', 'number'),  # 設問1, 設問2など
            (r'\(([０-９0-9]+)\)', 'number'),  # (1), (2)など
            (r'\(([一二三四五六七八九十]+)\)', 'kanji'),  # (一), (二)など
            (r'([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])', 'circle'),  # ①, ②など
        ]
        
        max_question_num = 0
        
        for pattern, pattern_type in question_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if pattern_type == 'number':
                    # 数字の場合は最大値を取る
                    nums = [int(m) for m in matches if m.isdigit()]
                    if nums:
                        max_question_num = max(max_question_num, max(nums))
                elif pattern_type == 'kanji':
                    # 漢数字の場合は変換して最大値を取る
                    kanji_to_num = {
                        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15
                    }
                    nums = [kanji_to_num.get(m, 0) for m in matches]
                    if nums:
                        max_question_num = max(max_question_num, max(nums))
                elif pattern_type == 'circle':
                    # 丸数字の場合は個数を数える
                    max_question_num = max(max_question_num, len(set(matches)))
        
        # 最低1問はあるとする
        return max(max_question_num, 1)
    
    def _analyze_question_types(self, text: str) -> Dict[str, int]:
        """設問タイプを分析（互換性のために残す）"""
        # 改善された分析器を使用
        analysis = self.improved_analyzer.analyze_questions(text)
        return analysis.type_counts
    
    def _extract_sources(self, text: str) -> List[Source]:
        """出典を抽出（セクションごとに冒頭と末尾から検出）"""
        sources = []
        
        # まずセクションを取得
        sections = self._analyze_sections(text) if not hasattr(self, '_current_sections') else self._current_sections
        
        # 各セクションから出典を抽出
        for section in sections:
            if hasattr(section, 'text'):
                section_text = section.text
            elif hasattr(section, 'content'):
                section_text = section.content
            else:
                continue
            
            # セクションの末尾（最後の2000文字）を重点的に検索
            # 出典は通常、文章の最後に記載されることが多い
            end_text = section_text[-2000:] if len(section_text) > 2000 else section_text
            
            # セクション内のすべての出典を抽出
            section_sources = self._extract_sources_from_text(end_text)
            
            # 重複を避けて追加
            for source in section_sources:
                if source and not any(s.title == source.title and s.author == source.author for s in sources):
                    sources.append(source)
        
        # 見つからない場合は全体から検索（フォールバック）
        if not sources:
            # 全体テキストから「による」「より」を含む部分を探す
            sources = self._extract_sources_from_text(text)
        
        return sources[:10]  # 最大10個まで
    
    def _extract_sources_from_text(self, text: str) -> List[Source]:
        """テキストから出典を抽出 - 拡充版"""
        sources = []
        
        # 包括的な出典パターン（優先度順）
        source_patterns = [
            # OCR特化: 括弧内の標準形式
            (r'\(([^\(\)]+)『([^』]+)』\)', 'ocr_paren_author_title'),
            (r'\(([^\(\)]+)「([^」]+)」『([^』]+)』\)', 'ocr_paren_author_quote_title'),
            # 最優先: 「による」を含む明確なパターン
            (r'([^\s『「（）]+)\s*『([^』]+)』\s*による', 'author_title_niyoru'),
            (r'([^\s『「（）]+)\s*「([^」]+)」\s*による', 'author_quote_niyoru'),
            # 雑誌掲載作品パターン（全角括弧・半角括弧両対応）
            (r'([^\s『「（）\(\)]+)\s*「([^」]+)」\s*（\s*『([^』]+)』\s*(?:第[^）]*号\s*)?所収\s*）\s*による', 'author_quote_magazine_full_zen'),
            (r'([^\s『「（）\(\)]+)\s*「([^」]+)」\s*\(\s*『([^』]+)』\s*(?:第[^\)]*号\s*)?所収\s*\)\s*による', 'author_quote_magazine_full_han'),
            (r'([^\s『「（）]+)\s*「([^」]+)」\s*［\s*『([^』]+)』\s*所収\s*］\s*による', 'author_quote_magazine_bracket'),
            
            # 「より」パターン
            (r'（([^\s『「）]+)\s*『([^』]+)』\s*より）', 'paren_author_title_yori'),
            (r'（([^\s『「）]+)\s*「([^」]+)」\s*より）', 'paren_author_quote_yori'),
            (r'([^\s『「（）]+)\s*『([^』]+)』\s*より', 'author_title_yori'),
            
            # 「から」パターン
            (r'([^\s『「（）]+)\s*『([^』]+)』\s*から', 'author_title_kara'),
            (r'『([^』]+)』\s*（([^）]+)）\s*から', 'title_author_kara'),
            
            # 出典ラベル付き
            (r'出典\s*[：:]\s*([^\s『「（）]+)\s*『([^』]+)』', 'source_label_author_title'),
            (r'出典\s*[：:]\s*『([^』]+)』\s*（([^）]+)）', 'source_label_title_author'),
            (r'※\s*([^\s『「（）]+)\s*『([^』]+)』', 'asterisk_author_title'),
            
            # 説明文付き
            (r'次の文章は[、，]\s*([^\s『「（）]+)の『([^』]+)』', 'description_author_title'),
            (r'([^\s『「（）]+)『([^』]+)』の一節', 'author_title_excerpt'),
            
            # 古典・無著者パターン
            (r'『([^』]+)』\s*による', 'title_only_niyoru'),
            (r'『([^』]+)』\s*より', 'title_only_yori'),
            
            # 括弧内の補足情報
            (r'([^\s『「（）]+)の文\s*による', 'author_text_niyoru'),
            (r'([^\s『「（）]+)の文章\s*による', 'author_text_niyoru'),
        ]
        
        # パターンマッチングを実行
        for pattern, pattern_type in source_patterns:
            # 各行で検索（行末の出典を優先）
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                matches = re.findall(pattern, line)
                for match in matches:
                    source = self._parse_source_match(match, pattern_type)
                    if source and source.author and source.title:
                        # 重複チェック
                        if not any(s.title == source.title and s.author == source.author for s in sources):
                            sources.append(source)
                            # 最初の有効な出典を見つけたら次のパターンへ
                            if len(sources) >= 2:  # 通常2つまで
                                return sources
        
        return sources[:5]  # 最大5つまで
    
    def _parse_source_match(self, match, pattern_type: str) -> Optional[Source]:
        """出典マッチをパースしてSourceオブジェクトを作成"""
        author = None
        title = None
        extra = None
        
        if not match:
            return None
            
        # パターンタイプに応じて解析
        if isinstance(match, tuple):
            if len(match) >= 3:
                # 3要素の場合（著者、タイトル、追加情報）
                if 'ocr_paren_author_quote_title' in pattern_type:
                    # OCR特化: (著者「作品名」『雑誌名』) 形式
                    author = match[0].strip()
                    title = match[1].strip()  # 作品名
                    extra = match[2].strip()   # 雑誌名
                elif 'magazine' in pattern_type or 'bracket' in pattern_type:
                    author = match[0].strip()
                    title = match[1].strip()
                    extra = match[2].strip() if match[2] else None
                else:
                    # その他のパターン
                    author = match[0].strip()
                    title = match[1].strip()
                    extra = match[2].strip() if len(match) > 2 else None
            elif len(match) == 2:
                # 2要素の場合
                if 'ocr_paren_author_title' in pattern_type:
                    # OCR特化: (著者『タイトル』) 形式
                    author = match[0].strip()
                    title = match[1].strip()
                elif 'title_author' in pattern_type:
                    title = match[0].strip()
                    author = match[1].strip()
                else:
                    author = match[0].strip()
                    title = match[1].strip()
            elif len(match) == 1:
                # 1要素の場合
                if 'title_only' in pattern_type:
                    title = match[0].strip()
                elif 'author_text' in pattern_type:
                    author = match[0].strip()
                else:
                    # 文字列として処理
                    text = match[0].strip()
                    if '『' in text and '』' in text:
                        # タイトルを抽出
                        title_match = re.search(r'『([^』]+)』', text)
                        if title_match:
                            title = title_match.group(1)
                        # 著者を抽出
                        author_part = text.split('『')[0].strip()
                        if author_part:
                            author = author_part
        elif isinstance(match, str):
            # 単一文字列の場合
            text = match.strip()
            if '『' in text and '』' in text:
                title_match = re.search(r'『([^』]+)』', text)
                if title_match:
                    title = title_match.group(1)
                author_part = text.split('『')[0].strip()
                if author_part:
                    author = author_part
            else:
                author = text
        
        # Sourceオブジェクトを作成
        if title or author:
            source = Source(
                author=author,
                title=title
            )
            # 追加情報があれば属性として保存
            if extra:
                source.extra_info = extra
            return source
        
        return None
    
    def _detect_theme(self, text: str) -> Optional[str]:
        """テーマを検出 - 詳細版（複合テーマ対応）"""
        # より詳細なテーマカテゴリ
        theme_keywords = {
            '本・読書・文学': {
                'primary': ['本', '読書', '図書', '書籍', '文学', '物語', '小説', '作品', '著者', '作家'],
                'secondary': ['読む', '書く', '文章', 'ページ', '出版', '印刷'],
                'weight': 3
            },
            '友情・人間関係': {
                'primary': ['友情', '友達', '友人', '仲間', '親友', '友', '仲良し'],
                'secondary': ['一緒', '共に', '助け合い', '協力', '信頼'],
                'weight': 3
            },
            '家族・親子': {
                'primary': ['家族', '親子', '母', '父', '兄弟', '姉妹', '祖父母', '家庭'],
                'secondary': ['親', '子', '息子', '娘', '家'],
                'weight': 3
            },
            '成長・自己発見': {
                'primary': ['成長', '大人', '変化', '発見', '気づき', '理解', '学び'],
                'secondary': ['変わる', '成る', '分かる', '知る'],
                'weight': 3
            },
            '自然・生命': {
                'primary': ['自然', '生命', '生き物', '動物', '植物', '生態', '環境'],
                'secondary': ['木', '森', '川', '山', '海', '空', '鳥', '虫', '花'],
                'weight': 2
            },
            '社会・現代': {
                'primary': ['社会', '現代', '時代', '世界', '日本', '国', '都市', '地方'],
                'secondary': ['人々', '暮らし', '生活', '仕事', '学校'],
                'weight': 2
            },
            '科学・知識': {
                'primary': ['科学', '研究', '実験', '発見', '技術', '知識', '学問'],
                'secondary': ['データ', '分析', '観察', '原理', '法則'],
                'weight': 2
            },
            '哲学・価値観': {
                'primary': ['哲学', '思想', '価値', '意味', '本質', '真理', '道徳'],
                'secondary': ['考える', '問い', '答え', 'なぜ', '理由'],
                'weight': 2
            },
            '冒険・挑戦': {
                'primary': ['冒険', '挑戦', '旅', '探検', '未知', '新しい'],
                'secondary': ['挑む', '進む', '向かう', '目指す'],
                'weight': 2
            },
            '感情・心理': {
                'primary': ['感情', '気持ち', '心', '思い', '感じ', '愛', '喜び', '悲しみ'],
                'secondary': ['嬉しい', '悲しい', '楽しい', '辛い', '苦しい'],
                'weight': 2
            }
        }
        
        # サンプルテキスト（冒頭2000文字）
        sample_text = text[:2000] if len(text) > 2000 else text
        
        theme_scores = {}
        for theme, keywords_dict in theme_keywords.items():
            score = 0
            weight = keywords_dict.get('weight', 1)
            
            # 主キーワードは基本3点×重み
            for keyword in keywords_dict.get('primary', []):
                count = sample_text.count(keyword)
                score += count * 3 * weight
            
            # 副キーワードは基本1点×重み
            for keyword in keywords_dict.get('secondary', []):
                count = sample_text.count(keyword)
                score += count * 1 * weight
            
            # 最小閾値：3点以上でないとテーマとして認識しない
            if score >= 3:
                theme_scores[theme] = score
        
        # 複数のテーマを検出して結合
        if theme_scores:
            # スコアの高い順に最大2つまで選択
            sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
            
            # 最高スコアの80%以上のテーマを選択（最大2つ）
            top_score = sorted_themes[0][1]
            selected_themes = []
            
            for theme, score in sorted_themes[:3]:  # 最大3つまでチェック
                if score >= top_score * 0.8:
                    selected_themes.append(theme)
                    if len(selected_themes) >= 2:
                        break
            
            # テーマを結合して返す
            if len(selected_themes) > 1:
                return '・'.join(selected_themes)
            else:
                return selected_themes[0]
        
        # デフォルトテーマ
        return '人間と社会'
    
    def _detect_genre(self, text: str) -> Optional[str]:
        """ジャンルを検出 - 強化版（重み付きスコアリング）"""
        genre_patterns = {
            '小説・物語': {
                'primary': ['「', '」', '会話', '物語', '小説', 'だった', 'と思った'],
                'secondary': ['私', '彼', '彼女', 'さん', 'くん', 'ちゃん'],
                'negative': ['論じる', '考察', '研究', '実験']
            },
            '評論・論説': {
                'primary': ['論じる', '考察', '問題', '主張', '理由', '結論', 'について'],
                'secondary': ['しかし', 'したがって', 'つまり', 'ところで', 'なぜなら'],
                'negative': ['物語', '小説', '「']
            },
            '随筆・エッセイ': {
                'primary': ['随筆', 'エッセイ', '私は', '体験', '思い出', '感じる'],
                'secondary': ['思う', '考える', '日々', '日常', '暮らし'],
                'negative': ['実験', '研究', '論証']
            },
            '詩・韻文': {
                'primary': ['詩', '俳句', '短歌', '韻', '季語'],
                'secondary': ['句', '音', '調べ'],
                'negative': ['論じる', '物語']
            }
        }
        
        genre_scores = {}
        # ジャンル判定は冒頭1000文字で行う
        sample_text = text[:1000] if len(text) > 1000 else text
        
        for genre, keywords_dict in genre_patterns.items():
            score = 0
            
            # 主キーワードは3点
            for keyword in keywords_dict.get('primary', []):
                count = sample_text.count(keyword)
                score += count * 3
            
            # 副キーワードは1点
            for keyword in keywords_dict.get('secondary', []):
                count = sample_text.count(keyword)
                score += count * 1
            
            # ネガティブキーワードは-2点
            for keyword in keywords_dict.get('negative', []):
                count = sample_text.count(keyword)
                score -= count * 2
            
            # 最小閾値：3点以上でないとジャンルとして認識しない
            if score >= 3:
                genre_scores[genre] = score
        
        if genre_scores:
            # スコアが最も高いジャンルを返す
            return max(genre_scores, key=genre_scores.get)
        
        # デフォルト判定（フォールバック）
        if '「' in sample_text and '」' in sample_text:
            return '小説・物語'
        elif '私' in sample_text[:200]:
            return '随筆・エッセイ'
        else:
            return '評論・論説'