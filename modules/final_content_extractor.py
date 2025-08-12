"""
最終版コンテンツ抽出モジュール
中学入試国語問題から著者名・作品名を確実に抽出する
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class FinalContentExtractor:
    """入試問題テキストから著者・作品情報を確実に抽出する最終版クラス"""
    
    def extract_all_content(self, text: str) -> Dict[str, Any]:
        """
        全文から内容を抽出
        
        Args:
            text: 入試問題の全テキスト
            
        Returns:
            抽出された内容
        """
        # 全ての出典を抽出
        sources = self._extract_all_sources(text)
        
        # 大問を識別して分割（改良版）
        sections = self._identify_and_divide_sections(text, sources)
        
        # 結果の初期化
        result = {
            'total_characters': len(text.replace(' ', '').replace('\n', '')),
            'total_questions': 0,
            'sections': [],
            'question_types': {
                '選択': 0,
                '記述': 0,
                '抜き出し': 0,
                '漢字・語句': 0
            }
        }
        
        # 各セクションを分析
        for i, section in enumerate(sections):
            section_info = {
                'number': i + 1,
                'source': section.get('source'),
                'start_pos': section['start'],
                'end_pos': section['end'],
                'characters': len(section['text'].replace(' ', '').replace('\n', '')),
                'questions': [],
                'genre': self._detect_genre(section['text']) if not section.get('is_kanji') else '漢字・語句',
                'theme': self._detect_theme(section['text']) if not section.get('is_kanji') else '漢字・語句'
            }
            
            # 設問を抽出
            questions = self._extract_questions_from_section(section['text'])
            section_info['questions'] = questions
            result['total_questions'] += len(questions)
            
            # 設問タイプを分類
            for q in questions:
                q_type = self._classify_question(q['text'])
                q['type'] = q_type
                if q_type in result['question_types']:
                    result['question_types'][q_type] += 1
            
            result['sections'].append(section_info)
        
        return result
    
    def _extract_all_sources(self, text: str) -> List[Dict[str, Any]]:
        """
        テキストから全ての出典情報を抽出
        
        Args:
            text: 全テキスト
            
        Returns:
            出典情報のリスト
        """
        sources = []
        
        # パターン1：（著者名『作品名』より）
        pattern1 = re.compile(r'（([^『』（）]+)[『「]([^』」]+)[』」]より）')
        for match in pattern1.finditer(text):
            author = match.group(1).strip()
            work = match.group(2).strip()
            
            # 有効な著者名かチェック
            if self._is_valid_author(author) and len(work) > 1:
                sources.append({
                    'author': author,
                    'work': work,
                    'position': match.start(),
                    'full_text': match.group(0)
                })
        
        # パターン2：（『作品名』著者名より）
        pattern2 = re.compile(r'（[『「]([^』」]+)[』」]\s*([^（）]+)より）')
        for match in pattern2.finditer(text):
            work = match.group(1).strip()
            author = match.group(2).strip()
            
            if self._is_valid_author(author) and len(work) > 1:
                # 既に同じ位置で検出していないかチェック
                if not any(s['position'] == match.start() for s in sources):
                    sources.append({
                        'author': author,
                        'work': work,
                        'position': match.start(),
                        'full_text': match.group(0)
                    })
        
        # パターン3：著者名 『作品名』による（聖光学院形式）
        pattern3 = re.compile(r'([^『』\n\r]+)\s*[『「]([^』」]+)[』」]\s*による')
        for match in pattern3.finditer(text):
            author = match.group(1).strip()
            work = match.group(2).strip()
            
            if self._is_valid_author(author) and len(work) > 1:
                # 既に同じ位置で検出していないかチェック
                if not any(s['position'] == match.start() for s in sources):
                    sources.append({
                        'author': author,
                        'work': work,
                        'position': match.start(),
                        'full_text': match.group(0)
                    })
        
        # パターン4：著者名「作品名」(出版社情報)による（永井佳子形式）
        pattern4 = re.compile(r'([^「」\n\r]+)「([^「」]+)」\([^）]+\)による')
        for match in pattern4.finditer(text):
            author = match.group(1).strip()
            work = match.group(2).strip()
            
            if self._is_valid_author(author) and len(work) > 1:
                # 既に同じ位置で検出していないかチェック
                if not any(s['position'] == match.start() for s in sources):
                    sources.append({
                        'author': author,
                        'work': work,
                        'position': match.start(),
                        'full_text': match.group(0)
                    })
        
        # 位置でソート
        sources.sort(key=lambda x: x['position'])
        
        return sources
    
    def _is_valid_author(self, name: str) -> bool:
        """
        有効な著者名かチェック
        
        Args:
            name: 著者名候補
            
        Returns:
            有効な場合True
        """
        if not name or len(name) < 2 or len(name) > 20:
            return False
        
        # 除外パターン
        exclude_patterns = [
            r'^[0-9\-\s]+$',  # 数字のみ
            r'^――',  # 傍線記号
            r'^問[一二三四五六七八九十0-9]',  # 設問番号
            r'部[アイウエオ]',  # 傍線部記号
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, name):
                return False
        
        return True
    
    def _divide_by_sources(self, text: str, sources: List[Dict]) -> List[Dict]:
        """
        出典情報を基に文章を大問に分割
        
        Args:
            text: 全テキスト
            sources: 出典情報リスト
            
        Returns:
            各大問の情報リスト
        """
        sections = []
        
        # 最初に漢字語句問題があるかチェック
        # 「問一」「問1」などで始まり、出典がない部分を探す
        kanji_pattern = re.compile(r'(問[一二三四五六七八九十１-９1-9]|^[一二三四五六七八九十１-９1-9]\s*[、．\s])', re.MULTILINE)
        first_question = kanji_pattern.search(text[:2000])  # 最初の2000文字をチェック
        
        if first_question and sources:
            # 最初の出典までの間に漢字語句問題がある可能性
            first_source_pos = sources[0]['position']
            
            # 漢字語句問題の終わりを探す（最初の出典の前）
            kanji_section_text = text[:first_source_pos]
            
            # 漢字・語句・慣用句などのキーワードがあるか確認
            if any(keyword in kanji_section_text[:1000] for keyword in ['漢字', '語句', '慣用句', 'ことわざ', '読み', '意味']):
                # 漢字語句問題として最初の大問を追加
                sections.append({
                    'text': kanji_section_text,
                    'source': None,  # 漢字語句問題には出典がない
                    'start': 0,
                    'end': first_source_pos,
                    'is_kanji': True  # 漢字語句問題フラグ
                })
        
        if not sources:
            # 出典が見つからない場合は全体を1つの大問とする
            sections.append({
                'text': text,
                'source': None,
                'start': 0,
                'end': len(text),
                'is_kanji': False
            })
        else:
            # 各出典に基づいて大問を作成
            for i, source in enumerate(sources):
                # この出典の文章の開始位置を決定
                if i == 0:
                    # 最初の出典の場合
                    if sections and sections[0].get('is_kanji'):
                        # 既に漢字語句問題がある場合は、その後から
                        start = sections[0]['end']
                    else:
                        # テキストの最初から（ただし出典より前の部分）
                        # 出典の前1500文字程度を含める
                        start = max(0, source['position'] - 1500)
                else:
                    # 前の出典の位置の少し後から
                    prev_source_end = sources[i-1]['position'] + len(sources[i-1]['full_text'])
                    # 次の文章の開始位置（前の出典の後、適切な改行位置を探す）
                    start = prev_source_end
                    # 改行2つ以上で区切られている位置を探す
                    double_newline = text.find('\n\n', prev_source_end)
                    if double_newline != -1 and double_newline < source['position'] - 500:
                        start = double_newline + 2
                
                # 次の出典までまたは文末まで
                if i + 1 < len(sources):
                    # 次の出典の前まで
                    next_source_start = sources[i + 1]['position']
                    # 次の文章との境界を探す
                    end = source['position'] + len(source['full_text'])
                    # 改行2つで区切られた位置を探す
                    double_newline = text.find('\n\n', end)
                    if double_newline != -1 and double_newline < next_source_start - 500:
                        end = double_newline
                    else:
                        # 次の出典の前1500文字程度まで
                        end = min(next_source_start - 1500, source['position'] + len(source['full_text']) + 5000)
                else:
                    # 最後の出典の場合は文末まで
                    end = len(text)
                
                section_text = text[start:end]
                
                # 有効な文章かチェック（短すぎる場合は除外）
                if len(section_text) > 500:
                    # 既に同じ範囲が追加されていないかチェック
                    if not any(s['start'] == start and s['end'] == end for s in sections):
                        sections.append({
                            'text': section_text,
                            'source': source,
                            'start': start,
                            'end': end,
                            'is_kanji': False
                        })
        
        return sections

    def _identify_and_divide_sections(self, text: str, sources: List[Dict]) -> List[Dict]:
        """
        大問を識別して分割（適切な大問レベルのみ検出）
        
        Args:
            text: 全テキスト
            sources: 出典情報リスト
            
        Returns:
            各大問の情報リスト
        """
        sections = []
        
        # 大問レベルの番号パターンのみ検出（小問レベルは除外）
        # 聖光学院形式: 「一、」「二、」「三、」「四、」の大問番号パターン
        section_patterns = [
            r'[一二三四五六七八九十]、',  # 「一、」「二、」形式（聖光学院）
            r'[１-４1-4][\s　、]',  # アラビア数字（1-4のみ、大問レベル）
            r'第[一二三四五六七八九十]問',  # 「第一問」形式
        ]
        
        # 大問開始位置を検出（行頭のもののみ）
        section_starts = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, text):
                # 行頭または改行直後の場合のみ
                if match.start() == 0 or text[match.start()-1] in '\n\r':
                    # 前後の文脈をチェックして大問レベルかどうか確認
                    context_before = text[max(0, match.start()-50):match.start()]
                    context_after = text[match.start():match.start()+200]
                    
                    # 小問パターンを除外（「問一」「問二」など）
                    if not re.search(r'問[一二三四五六七八九十]', context_before + match.group()):
                        # 「次の文章」「文の」「カタカナ」など大問の典型的なキーワードがあるかチェック
                        if any(keyword in context_after for keyword in [
                            '次の文章', '文の', 'カタカナ', '漢字', '語句', 'ひらがな', 
                            '読んで', '答えなさい', 'について', '～について'
                        ]):
                            section_starts.append({
                                'position': match.start(),
                                'match': match.group(),
                                'pattern': pattern,
                                'context': context_after[:100]
                            })
        
        # 位置でソート
        section_starts.sort(key=lambda x: x['position'])
        
        # 検出された大問開始位置が少ない場合は出典ベースの分割を使用
        if len(section_starts) < 3 and sources:
            print(f"大問番号の検出が不十分（{len(section_starts)}個）、出典ベースの分割を使用")
            return self._divide_by_sources(text, sources)
        
        # 語句問題のキーワード
        kanji_keywords = ['漢字', '語句', 'カタカナ', 'ひらがな', '慣用句', 'ことわざ']
        
        # 各大問の範囲を決定
        for i, start_info in enumerate(section_starts):
            start = start_info['position']
            
            # 次の大問開始位置または文末を終点とする
            if i + 1 < len(section_starts):
                end = section_starts[i + 1]['position']
            else:
                end = len(text)
            
            # セクションテキスト
            section_text = text[start:end]
            
            # この範囲内の出典を探す
            section_sources = [s for s in sources if start <= s['position'] < end]
            
            # 語句問題かどうか判定（最初の300文字で判定）
            check_text = section_text[:300] if len(section_text) > 300 else section_text
            is_kanji = any(keyword in check_text for keyword in kanji_keywords)
            
            # セクション情報を構築
            if section_sources:
                # 出典がある場合は最初の出典を使用
                main_source = section_sources[0]
                sections.append({
                    'text': section_text,
                    'source': main_source,
                    'start': start,
                    'end': end,
                    'is_kanji': False
                })
            elif is_kanji:
                # 語句問題
                sections.append({
                    'text': section_text,
                    'source': None,
                    'start': start,
                    'end': end,
                    'is_kanji': True
                })
            elif len(section_text) > 500:
                # その他の文章問題
                sections.append({
                    'text': section_text,
                    'source': None,
                    'start': start,
                    'end': end,
                    'is_kanji': False
                })
        
        # フィルタリング: 短すぎるセクションを除外
        sections = [s for s in sections if len(s['text']) > 200]
        
        # デバッグ出力
        print(f"検出された大問数: {len(sections)}")
        for i, section in enumerate(sections):
            if section.get('source'):
                print(f"  大問{i+1}: {section['source']['author']} 『{section['source']['work']}』")
            elif section.get('is_kanji'):
                print(f"  大問{i+1}: 漢字・語句問題")
            else:
                print(f"  大問{i+1}: 文章問題（出典なし）")
        
        # 大問が見つからない場合の処理
        if not sections:
            if sources:
                return self._divide_by_sources(text, sources)
            else:
                sections.append({
                    'text': text,
                    'source': None,
                    'start': 0,
                    'end': len(text),
                    'is_kanji': False
                })
        
        return sections
    
    def _extract_questions_from_section(self, section_text: str) -> List[Dict[str, Any]]:
        """
        セクションから設問を抽出
        
        Args:
            section_text: セクションのテキスト
            
        Returns:
            設問のリスト
        """
        questions = []
        
        # 設問のパターン
        patterns = [
            (r'問([一二三四五六七八九十])', 'kanji_num'),
            (r'問([０-９0-9]+)', 'arabic_num'),
            (r'設問([０-９0-9]+)', 'setsumon'),
        ]
        
        all_matches = []
        for pattern_str, q_type in patterns:
            pattern = re.compile(pattern_str)
            for match in pattern.finditer(section_text):
                all_matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'number': match.group(1),
                    'type': q_type,
                    'full_match': match.group(0)
                })
        
        # 位置でソート
        all_matches.sort(key=lambda x: x['start'])
        
        # 各設問のテキストを抽出
        for i, match in enumerate(all_matches):
            # 次の設問または文末までをこの設問のテキストとする
            text_start = match['start']
            if i + 1 < len(all_matches):
                text_end = all_matches[i + 1]['start']
            else:
                text_end = len(section_text)
            
            question_text = section_text[text_start:text_end].strip()
            
            # 有効な設問かチェック
            if self._is_valid_question(question_text):
                questions.append({
                    'number': match['number'],
                    'text': question_text[:300],  # 最初の300文字
                    'full_text': question_text,
                    'position': text_start
                })
        
        return questions
    
    def _is_valid_question(self, text: str) -> bool:
        """
        有効な設問かチェック
        
        Args:
            text: 設問テキスト
            
        Returns:
            有効な場合True
        """
        if len(text) < 20:
            return False
        
        # 設問を示すキーワード
        keywords = [
            'なさい', '答え', '説明', '述べ', '選び',
            'について', 'とは', 'ですか', 'ありますが',
            'どのような', 'なぜ', 'どういうこと',
            '意味を', '理由を'
        ]
        
        # 最初の200文字に設問キーワードが含まれているか
        search_area = text[:200] if len(text) > 200 else text
        return any(keyword in search_area for keyword in keywords)
    
    def _classify_question(self, text: str) -> str:
        """
        設問のタイプを分類
        
        Args:
            text: 設問テキスト
            
        Returns:
            設問タイプ
        """
        # 漢字・語句問題
        if any(keyword in text for keyword in ['漢字', '語句', '慣用句', 'ことわざ', '語群']):
            return '漢字・語句'
        
        # 抜き出し問題
        if any(keyword in text for keyword in ['抜き出し', '書き抜き', 'そのまま抜き出']):
            return '抜き出し'
        
        # 選択問題（記号がある場合）
        if re.search(r'[ア-ン][。、．\s]', text) or '選び' in text:
            return '選択'
        
        # それ以外は記述問題
        return '記述'
    
    def _detect_genre(self, text: str) -> str:
        """
        文章のジャンルを判定（中学受験用）
        
        Args:
            text: テキスト
            
        Returns:
            ジャンル
        """
        # 会話文の数をカウント
        dialogue_count = text.count('「') + text.count('」')
        
        # 小説・物語の判定（会話文が多い）
        if dialogue_count > 20:
            return '小説・物語'
        
        # 論説文の判定（論理的な展開）
        elif any(keyword in text for keyword in ['である', 'のだ', '考察', '論じる', '主張', 'べきだ']):
            return '論説文'
        
        # 説明文の判定（客観的な説明）
        elif any(keyword in text for keyword in ['について説明', 'とは', '定義', '仕組み', 'つまり']):
            return '説明文'
        
        # それ以外は随筆（エッセイ）
        else:
            return '随筆'
    
    def _detect_theme(self, text: str) -> str:
        """
        文章のテーマを判定
        
        Args:
            text: テキスト
            
        Returns:
            テーマ
        """
        theme_keywords = {
            '人間関係・成長': ['友', '家族', '成長', '大人', '子ども', '親', '兄弟'],
            '社会・文化': ['社会', '文化', '歴史', '戦争', '平和', '日本', '世界'],
            '自然・環境': ['自然', '環境', '動物', '植物', '森', '海', '山'],
            '科学・技術': ['科学', '技術', '実験', '研究', 'データ'],
            '哲学・思想': ['考え', '思', '意味', '価値', '存在']
        }
        
        scores = {}
        for theme, keywords in theme_keywords.items():
            score = sum(text.count(keyword) for keyword in keywords)
            scores[theme] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return '不明'