"""
コンテンツ抽出モジュール
OCR結果から著者名、作品名、出典情報を正確に抽出する
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ContentExtractor:
    """入試問題テキストから著者・作品情報を抽出するクラス"""
    
    def __init__(self):
        """初期化"""
        # 出典パターンのコンパイル
        self.source_patterns = [
            # 「（著者名『作品名』より）」パターン
            re.compile(r'[（(]([^『』（）]+)[『「]([^』」]+)[』」](?:より|から)[）)]'),
            # 「（『作品名』著者名）」パターン
            re.compile(r'[（(][『「]([^』」]+)[』」]\s*([^（）]+)[）)]'),
            # 「著者名『作品名』」パターン（括弧なし）
            re.compile(r'([^『』\s]{2,10})[『「]([^』」]+)[』」]'),
            # 「作者名「作品名」」パターン
            re.compile(r'([^「」\s]{2,10})「([^」]+)」'),
        ]
        
        # 設問に含まれる作品・著者への言及パターン
        self.reference_patterns = [
            # 「戸塚治虫から」「佐野三津彦を紹介」など
            re.compile(r'([^、。\s]{2,8})(?:から|を|が|は|の|より)'),
            # 「君嶋織子は」「三津彦は」など
            re.compile(r'([^、。\s]{2,8})(?:は|が|も|を|に|と|の)'),
        ]
        
    def extract_all_sources(self, text: str) -> List[Dict[str, Any]]:
        """
        テキストから全ての出典情報を抽出
        
        Args:
            text: OCR結果のテキスト
            
        Returns:
            出典情報のリスト
        """
        sources = []
        
        # 1. まず明確な出典表記を探す（文末の括弧内など）
        direct_sources = self._extract_direct_sources(text)
        sources.extend(direct_sources)
        
        # 2. 文章中の作品・著者への言及を探す
        references = self._extract_references(text)
        sources.extend(references)
        
        # 3. 設問文から情報を抽出
        question_sources = self._extract_from_questions(text)
        sources.extend(question_sources)
        
        # 重複を除去
        unique_sources = self._deduplicate_sources(sources)
        
        return unique_sources
    
    def _extract_direct_sources(self, text: str) -> List[Dict[str, Any]]:
        """
        明確な出典表記を抽出（括弧内の著者名・作品名など）
        
        Args:
            text: テキスト
            
        Returns:
            出典情報のリスト
        """
        sources = []
        
        # テキストの最後の部分を重点的に検索（出典は通常最後にある）
        text_sections = text.split('\n')
        
        for i, line in enumerate(text_sections):
            # 各パターンでマッチを試みる
            for pattern in self.source_patterns:
                matches = pattern.findall(line)
                for match in matches:
                    if len(match) >= 2:
                        # パターンによって著者と作品の順序が異なる
                        if '『' in match[0] or '「' in match[0]:
                            # 作品名が先の場合
                            work = match[0].strip()
                            author = match[1].strip()
                        else:
                            # 著者名が先の場合
                            author = match[0].strip()
                            work = match[1].strip()
                        
                        # 有効な出典情報かチェック
                        if self._is_valid_source(author, work):
                            sources.append({
                                'author': author,
                                'work': work,
                                'line_number': i + 1,
                                'type': 'direct',
                                'confidence': 0.9
                            })
        
        return sources
    
    def _extract_references(self, text: str) -> List[Dict[str, Any]]:
        """
        文章中の作品・著者への言及を抽出
        
        Args:
            text: テキスト
            
        Returns:
            参照情報のリスト
        """
        sources = []
        
        # 特定のキーワードと組み合わせて人名を探す
        author_indicators = [
            '作家', '著者', '児童文学作家', '漫画家', 'さん', '氏', '先生',
            'から', 'より', 'による', 'の作品', 'が書いた', 'が描いた'
        ]
        
        work_indicators = [
            '『', '」', 'という作品', 'という小説', 'という物語', 'という本',
            'ラジオドラマ', '映画', '作品', '小説', '物語'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # 人名の可能性がある部分を抽出
            potential_names = re.findall(r'([一-龥ぁ-ん]{2,5}[一-龥]{1,3})', line)
            
            for name in potential_names:
                # 周辺のコンテキストをチェック
                context = line
                if any(indicator in context for indicator in author_indicators):
                    # 関連する作品名を探す
                    work_match = re.search(r'[『「]([^』」]+)[』」]', context)
                    if work_match:
                        sources.append({
                            'author': name,
                            'work': work_match.group(1),
                            'line_number': i + 1,
                            'type': 'reference',
                            'confidence': 0.7
                        })
                    else:
                        sources.append({
                            'author': name,
                            'work': None,
                            'line_number': i + 1,
                            'type': 'reference',
                            'confidence': 0.5
                        })
        
        return sources
    
    def _extract_from_questions(self, text: str) -> List[Dict[str, Any]]:
        """
        設問文から著者・作品情報を抽出
        
        Args:
            text: テキスト
            
        Returns:
            出典情報のリスト
        """
        sources = []
        
        # 設問パターン
        question_patterns = [
            r'問[一二三四五六七八九十0-9]+',
            r'設問[0-9]+',
        ]
        
        # 設問部分を特定
        for pattern in question_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 設問の後の200文字を確認
                start = match.end()
                end = min(start + 200, len(text))
                question_text = text[start:end]
                
                # 設問文に含まれる人名・作品名を探す
                if '三津彦' in question_text or '君嶋' in question_text or '児童文学' in question_text:
                    # これらは本文中の登場人物の可能性が高い
                    continue
                
                # 「〜について」「〜とは」などの文脈で出てくる固有名詞を探す
                name_matches = re.findall(r'([^、。\s]{2,8})(?:について|とは|という)', question_text)
                for name in name_matches:
                    if self._is_likely_author_name(name):
                        sources.append({
                            'author': name,
                            'work': None,
                            'line_number': 0,
                            'type': 'question',
                            'confidence': 0.4
                        })
        
        return sources
    
    def _is_valid_source(self, author: str, work: str) -> bool:
        """
        有効な出典情報かチェック
        
        Args:
            author: 著者名
            work: 作品名
            
        Returns:
            有効な場合True
        """
        # 著者名の妥当性チェック
        if author and len(author) > 0:
            # 数字のみ、記号のみは除外
            if re.match(r'^[0-9\-\s]+$', author):
                return False
            # 1文字は除外
            if len(author) == 1:
                return False
        
        # 作品名の妥当性チェック
        if work and len(work) > 0:
            # あまりに短い作品名は除外
            if len(work) < 2:
                return False
            # ページ番号っぽいものは除外
            if re.match(r'^[0-9\-\s]+$', work):
                return False
        
        # 少なくとも著者か作品のどちらかは必要
        return bool(author or work)
    
    def _is_likely_author_name(self, text: str) -> bool:
        """
        著者名の可能性が高いかチェック
        
        Args:
            text: チェック対象のテキスト
            
        Returns:
            著者名の可能性が高い場合True
        """
        # 日本人の名前パターン
        japanese_name_pattern = re.compile(r'^[一-龥ぁ-ん]{2,4}[\s　]?[一-龥ぁ-ん]{2,4}$')
        
        # カタカナの外国人名
        foreign_name_pattern = re.compile(r'^[ァ-ヴー・]+$')
        
        return bool(japanese_name_pattern.match(text) or foreign_name_pattern.match(text))
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重複する出典情報を除去
        
        Args:
            sources: 出典情報のリスト
            
        Returns:
            重複を除去したリスト
        """
        unique = {}
        
        for source in sources:
            # キーを作成（著者と作品の組み合わせ）
            key = f"{source.get('author', '')}_{source.get('work', '')}"
            
            # 既存のエントリーがない、または信頼度が高い場合は更新
            if key not in unique or source['confidence'] > unique[key]['confidence']:
                unique[key] = source
        
        return list(unique.values())
    
    def extract_exam_content(self, text: str) -> Dict[str, Any]:
        """
        入試問題から主要な内容を抽出
        
        Args:
            text: OCR結果のテキスト
            
        Returns:
            抽出された内容情報
        """
        # 出典情報を抽出
        sources = self.extract_all_sources(text)
        
        # 最も信頼度の高い出典を選択
        primary_source = None
        if sources:
            primary_source = max(sources, key=lambda x: x['confidence'])
        
        # ジャンルを判定
        genre = self._detect_genre(text)
        
        # テーマを判定
        theme = self._detect_theme(text)
        
        return {
            'primary_source': primary_source,
            'all_sources': sources,
            'genre': genre,
            'theme': theme,
            'total_characters': len(text.replace(' ', '').replace('\n', ''))
        }
    
    def _detect_genre(self, text: str) -> str:
        """
        文章のジャンルを判定
        
        Args:
            text: テキスト
            
        Returns:
            ジャンル
        """
        genre_keywords = {
            '小説・物語': ['物語', '小説', 'ストーリー', '会話', '「', '」', 'と言った', 'と思った'],
            '評論・論説': ['論じ', '考察', '分析', '主張', 'である', 'ではない', 'について'],
            '随筆・エッセイ': ['思う', '感じ', 'だろう', 'かもしれない', '私は', '筆者は'],
            '詩': ['詩', '韻', '節', 'リズム'],
            '古文': ['けり', 'なり', 'たり', 'べし', 'む', 'らむ']
        }
        
        scores = {}
        for genre, keywords in genre_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[genre] = score
        
        # 最も高いスコアのジャンルを返す
        if scores:
            return max(scores, key=scores.get)
        
        return '不明'
    
    def _detect_theme(self, text: str) -> str:
        """
        文章のテーマを判定
        
        Args:
            text: テキスト
            
        Returns:
            テーマ
        """
        theme_keywords = {
            '人間関係・成長': ['友達', '友情', '家族', '成長', '大人', '子ども', '親子', '兄弟'],
            '自然・環境': ['自然', '環境', '動物', '植物', '森', '海', '山', '川', '地球'],
            '社会・文化': ['社会', '文化', '歴史', '伝統', '現代', '日本', '世界', '国'],
            '科学・技術': ['科学', '技術', '実験', '研究', 'データ', '発見', '発明'],
            '哲学・思想': ['哲学', '思想', '考え', '真理', '存在', '意味', '価値'],
            '戦争・平和': ['戦争', '平和', '戦い', '戦後', '戦中', '戦災', '孤児']
        }
        
        scores = {}
        for theme, keywords in theme_keywords.items():
            score = sum(text.count(keyword) for keyword in keywords)
            scores[theme] = score
        
        # 最も高いスコアのテーマを返す
        if scores:
            return max(scores, key=scores.get)
        
        return '不明'