"""
改良版コンテンツ抽出モジュール
中学入試国語問題から著者名・作品名を正確に抽出する
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ImprovedContentExtractor:
    """入試問題テキストから著者・作品情報を正確に抽出するクラス"""
    
    def extract_sources_from_exam(self, text: str) -> Dict[str, Any]:
        """
        入試問題から出典情報を抽出
        
        中学入試国語の特徴：
        - 各文章（大問）は3000-5000字程度
        - 文章の末尾に「（著者名『作品名』より）」の形式で出典が記載
        - 複数の文章がある場合は各文章ごとに出典がある
        
        Args:
            text: OCR結果のテキスト
            
        Returns:
            抽出結果の辞書
        """
        result = {
            'sections': [],  # 各大問の情報
            'total_questions': 0,
            'total_characters': len(text.replace(' ', '').replace('\n', ''))
        }
        
        # 大問を分割
        sections = self._split_into_sections(text)
        
        for i, section_text in enumerate(sections, 1):
            section_info = {
                'number': i,
                'source': None,
                'questions': [],
                'characters': len(section_text.replace(' ', '').replace('\n', ''))
            }
            
            # 出典を抽出（文章の最後の部分を重点的に探索）
            source = self._extract_source_from_section(section_text)
            if source:
                section_info['source'] = source
            
            # 設問を検出
            questions = self._extract_questions(section_text)
            section_info['questions'] = questions
            result['total_questions'] += len(questions)
            
            result['sections'].append(section_info)
        
        return result
    
    def _split_into_sections(self, text: str) -> List[str]:
        """
        テキストを大問ごとに分割
        
        Args:
            text: 全体のテキスト
            
        Returns:
            各大問のテキストリスト
        """
        sections = []
        
        # 大問の開始パターン
        section_patterns = [
            r'([一二三四五六七八九十])[、\s]+次の文章を読[みん]',
            r'次の文章を読[みん](?:、|\s)*(?:後|あと)の',
            r'これを読[みん](?:、|\s)*(?:後|あと)の問[いひ]'
        ]
        
        # パターンで分割点を見つける
        split_points = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, text):
                split_points.append(match.start())
        
        # 分割点でテキストを分ける
        if split_points:
            split_points.sort()
            split_points.append(len(text))  # 最後を追加
            
            for i in range(len(split_points) - 1):
                section = text[split_points[i]:split_points[i+1]]
                if len(section) > 100:  # 短すぎるセクションは除外
                    sections.append(section)
        
        # 分割できなかった場合は全体を1つのセクションとする
        if not sections:
            sections = [text]
        
        return sections
    
    def _extract_source_from_section(self, section_text: str) -> Optional[Dict[str, str]]:
        """
        セクションから出典情報を抽出
        優先順位：
        1. 文末の「（著者名『作品名』より）」形式
        2. 文末の「（『作品名』著者名）」形式
        3. その他のパターン
        
        Args:
            section_text: セクションのテキスト
            
        Returns:
            出典情報の辞書、見つからない場合はNone
        """
        # テキストの最後の500文字を重点的に探索
        search_area = section_text[-500:] if len(section_text) > 500 else section_text
        
        # パターン1: （著者名『作品名』より）
        pattern1 = re.compile(r'[（(]\s*([^『』（）\n]+?)[『「]([^』」\n]+?)[』」](?:より|から)\s*[）)]')
        match = pattern1.search(search_area)
        if match:
            author = match.group(1).strip()
            work = match.group(2).strip()
            # 著者名の妥当性チェック
            if self._is_valid_author_name(author):
                return {'author': author, 'work': work}
        
        # パターン2: （『作品名』著者名より）
        pattern2 = re.compile(r'[（(]\s*[『「]([^』」\n]+?)[』」]\s*([^（）\n]+?)(?:より|から)?\s*[）)]')
        match = pattern2.search(search_area)
        if match:
            work = match.group(1).strip()
            author = match.group(2).strip()
            if self._is_valid_author_name(author):
                return {'author': author, 'work': work}
        
        # パターン3: 文中の「次の文章は○○による」など
        pattern3 = re.compile(r'(?:次の文章は|以下は|これは)\s*([^によるの\n]{2,10})(?:による|の|が書いた)')
        match = pattern3.search(section_text[:500])  # 冒頭部分を探索
        if match:
            author = match.group(1).strip()
            if self._is_valid_author_name(author):
                # 作品名も探す
                work_pattern = re.compile(r'[『「]([^』」]+)[』」]')
                work_match = work_pattern.search(section_text[:500])
                work = work_match.group(1) if work_match else None
                return {'author': author, 'work': work}
        
        return None
    
    def _is_valid_author_name(self, name: str) -> bool:
        """
        有効な著者名かチェック
        
        Args:
            name: チェック対象の名前
            
        Returns:
            有効な場合True
        """
        if not name or len(name) < 2:
            return False
        
        # 明らかに著者名ではないパターンを除外
        invalid_patterns = [
            r'^[0-9\-\s]+$',  # 数字のみ
            r'^[ぁ-ん]{1}$',  # ひらがな1文字
            r'^――',  # 傍線
            r'^問[一二三四五六七八九十0-9]',  # 設問番号
            r'^[ア-ン][．。、]',  # 記号
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, name):
                return False
        
        # 日本人名パターン（漢字・ひらがな・カタカナの組み合わせ）
        japanese_name = re.compile(r'^[一-龥ぁ-んァ-ヴー\s　]+$')
        # 外国人名パターン（カタカナまたはアルファベット）
        foreign_name = re.compile(r'^[ァ-ヴー・\s　A-Za-z]+$')
        
        return bool(japanese_name.match(name) or foreign_name.match(name))
    
    def _extract_questions(self, section_text: str) -> List[Dict[str, Any]]:
        """
        セクションから設問を抽出
        
        Args:
            section_text: セクションのテキスト
            
        Returns:
            設問のリスト
        """
        questions = []
        
        # 設問パターン
        patterns = [
            (r'問([一二三四五六七八九十])', 'kanji'),
            (r'問([０-９0-9]+)', 'number'),
            (r'設問([０-９0-9]+)', 'setsumon'),
        ]
        
        for pattern_str, q_type in patterns:
            pattern = re.compile(pattern_str)
            for match in pattern.finditer(section_text):
                # 設問の開始位置から次の設問または終端までを取得
                start = match.start()
                end = len(section_text)
                
                # 次の設問を探す
                next_match = pattern.search(section_text, match.end())
                if next_match:
                    end = next_match.start()
                
                question_text = section_text[start:end]
                
                # 設問として妥当かチェック
                if self._is_valid_question(question_text):
                    questions.append({
                        'number': match.group(1),
                        'type': q_type,
                        'text': question_text[:200],  # 最初の200文字
                        'position': start
                    })
        
        # 位置でソート
        questions.sort(key=lambda x: x['position'])
        
        return questions
    
    def _is_valid_question(self, text: str) -> bool:
        """
        有効な設問かチェック
        
        Args:
            text: 設問テキスト
            
        Returns:
            有効な場合True
        """
        if len(text) < 10:
            return False
        
        # 設問を示すキーワード
        keywords = [
            'なさい', '答え', '説明', '述べ', '選び',
            'について', 'とは', 'ですか', 'ありますが',
            'どのような', 'なぜ', 'どういうこと'
        ]
        
        return any(keyword in text[:100] for keyword in keywords)