"""
Web検索を活用した高度なテーマ抽出システム
========================================

判定が難しいケースでWeb検索を使用して
正確な表現や用語を取得します。
"""

import re
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import json

from .theme_extractor_v2 import ThemeExtractorV2, ExtractedTheme

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    """Web検索結果"""
    original_query: str
    verified_term: Optional[str]
    correct_expression: Optional[str]
    field: Optional[str]
    confidence: float


class ThemeExtractorWithWeb(ThemeExtractorV2):
    """
    Web検索を活用したテーマ抽出器
    
    基本のテーマ抽出に加えて、以下の場合にWeb検索を活用：
    1. 固有名詞の正式名称確認
    2. 歴史的事件の正確な表現
    3. 専門用語の適切な2文節形式
    4. 時事問題の最新情報
    """
    
    def __init__(self, enable_web_search: bool = True):
        super().__init__()
        self.enable_web_search = enable_web_search
        self._search_cache = {}  # 検索結果のキャッシュ
        
    def extract(self, text: str) -> ExtractedTheme:
        """
        テーマを抽出（Web検索を活用）
        """
        # まず基本の抽出を試みる
        base_result = super().extract(text)
        
        # Web検索が無効、または既に高信頼度の結果がある場合
        if not self.enable_web_search or (base_result.theme and base_result.confidence > 0.9):
            return base_result
        
        # 判定が難しいケースを検出
        if self._needs_web_verification(text, base_result):
            web_result = self._search_and_verify(text, base_result)
            if web_result and web_result.verified_term:
                return ExtractedTheme(
                    theme=web_result.correct_expression,
                    category=web_result.field,
                    confidence=web_result.confidence
                )
        
        return base_result
    
    def _needs_web_verification(self, text: str, result: ExtractedTheme) -> bool:
        """
        Web検証が必要かどうか判定
        
        以下のケースで必要と判定：
        1. 結果の信頼度が低い（< 0.7）
        2. 固有名詞が含まれるが不完全
        3. 時事的な内容
        4. 専門用語で曖昧さがある
        """
        # 信頼度が低い
        if result.theme and result.confidence < 0.7:
            return True
        
        # 固有名詞の可能性があるパターン
        proper_noun_patterns = [
            r'[A-Z]{2,}',  # 略語（WHO, NATOなど）
            r'\d{4}年',     # 年号
            r'第\d+回',     # 回数
            r'○○大震災',   # 災害名の一部
        ]
        
        for pattern in proper_noun_patterns:
            if re.search(pattern, text):
                return True
        
        # 時事的キーワード
        current_keywords = ['最近', '現在', '今年', '昨年', '新しい', '最新']
        if any(keyword in text for keyword in current_keywords):
            return True
        
        # 不完全な表現
        if result.theme is None and len(text) > 10:
            # 意味のある内容がありそうだが抽出できていない
            return True
        
        return False
    
    def _search_and_verify(self, text: str, base_result: ExtractedTheme) -> Optional[WebSearchResult]:
        """
        Web検索を使って用語を検証・改善
        """
        # キャッシュチェック
        cache_key = text[:50]  # 最初の50文字でキャッシュキー
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]
        
        try:
            # 検索クエリを構築
            query = self._build_search_query(text, base_result)
            
            # Web検索の実行（実際の実装では適切なAPIを使用）
            search_result = self._perform_web_search(query)
            
            # 結果を解析して正式名称を抽出
            verified_result = self._parse_search_result(search_result, text)
            
            # キャッシュに保存
            self._search_cache[cache_key] = verified_result
            
            return verified_result
            
        except Exception as e:
            logger.warning(f"Web検索中にエラー: {e}")
            return None
    
    def _build_search_query(self, text: str, base_result: ExtractedTheme) -> str:
        """
        効果的な検索クエリを構築
        """
        # キーワード抽出
        keywords = self._extract_key_terms(text)
        
        # 社会科コンテキストを追加
        context_terms = []
        if '震災' in text or '地震' in text:
            context_terms.append('日本 災害 正式名称')
        elif '戦争' in text or '事件' in text:
            context_terms.append('日本史 歴史 事件')
        elif '憲法' in text or '法律' in text:
            context_terms.append('日本 法律 公民')
        elif '条約' in text or '協定' in text:
            context_terms.append('国際条約 正式名称')
        else:
            context_terms.append('社会科 用語')
        
        # クエリ構築
        query_parts = keywords[:3]  # 主要キーワード3つまで
        query_parts.extend(context_terms)
        
        return ' '.join(query_parts)
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        テキストから主要な用語を抽出
        """
        # 名詞を抽出（3文字以上）
        nouns = re.findall(r'[一-龥ァ-ヴー]{3,}', text)
        
        # 除外語
        exclude_words = {
            'について', '答えなさい', '説明しなさい', '述べなさい',
            'ください', 'として', '次の', 'うち'
        }
        
        # フィルタリング
        filtered = [n for n in nouns if n not in exclude_words]
        
        # 重要度でソート（長い語句を優先）
        filtered.sort(key=len, reverse=True)
        
        return filtered[:5]  # 上位5つ
    
    def _perform_web_search(self, query: str) -> Dict:
        """
        実際のWeb検索を実行
        
        注：この実装例では、モックデータを返します。
        実際の実装では、適切なWeb検索APIを使用してください。
        """
        logger.info(f"Web検索クエリ: {query}")
        
        # ここでは一般的な修正パターンを返す
        # 実際の実装では、Brave Search APIやGoogle Search APIを使用
        
        corrections = {
            '阪神淡路': '阪神・淡路大震災',
            '東日本': '東日本大震災',
            '関東': '関東大震災',
            '上げ米': '上米の制',
            '建武': '建武の新政',
            '大化': '大化の改新',
        }
        
        # クエリに含まれるキーワードをチェック
        for key, correct in corrections.items():
            if key in query:
                return {
                    'verified_term': correct,
                    'confidence': 0.95
                }
        
        return {'verified_term': None, 'confidence': 0.0}
    
    def _parse_search_result(self, search_result: Dict, original_text: str) -> WebSearchResult:
        """
        検索結果を解析して正式名称を抽出
        """
        if not search_result.get('verified_term'):
            return WebSearchResult(
                original_query=original_text,
                verified_term=None,
                correct_expression=None,
                field=None,
                confidence=0.0
            )
        
        verified_term = search_result['verified_term']
        
        # 分野を判定
        field = self._determine_field_from_term(verified_term)
        
        # 2文節形式を生成
        if '大震災' in verified_term:
            expression = f"{verified_term}の被害"
        elif '戦争' in verified_term:
            expression = f"{verified_term}の影響"
        elif '事件' in verified_term:
            expression = f"{verified_term}の背景"
        elif '条約' in verified_term or '協定' in verified_term:
            expression = f"{verified_term}の内容"
        elif '憲法' in verified_term or '法' in verified_term:
            expression = f"{verified_term}の仕組み"
        else:
            expression = f"{verified_term}の特徴"
        
        return WebSearchResult(
            original_query=original_text,
            verified_term=verified_term,
            correct_expression=expression,
            field=field,
            confidence=search_result.get('confidence', 0.9)
        )
    
    def _determine_field_from_term(self, term: str) -> str:
        """
        用語から分野を判定
        """
        if any(word in term for word in ['時代', '戦争', '事件', '改革', '幕府']):
            return '歴史'
        elif any(word in term for word in ['震災', '地方', '県', '市', '産業']):
            return '地理'
        elif any(word in term for word in ['憲法', '法律', '条約', '国会', '内閣']):
            return '公民'
        else:
            return '総合'


class WebSearchProvider:
    """
    Web検索プロバイダーのインターフェース
    
    実際の実装では、以下のいずれかを使用：
    - Brave Search API
    - Google Custom Search API
    - Bing Search API
    - MCP経由のWeb検索ツール
    """
    
    def search(self, query: str, context: str = "社会科") -> Dict:
        """
        Web検索を実行
        
        Args:
            query: 検索クエリ
            context: 検索コンテキスト（社会科、歴史、地理など）
            
        Returns:
            検索結果の辞書
        """
        raise NotImplementedError("実装が必要です")


class BraveSearchProvider(WebSearchProvider):
    """
    Brave Search APIを使用した検索プロバイダー
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
    def search(self, query: str, context: str = "社会科") -> Dict:
        """
        Brave Search APIを使用して検索
        """
        # 実際の実装では、brave_web_searchツールを使用
        # ここではモック実装
        full_query = f"{query} {context} 正式名称 日本"
        
        # モックレスポンス
        return {
            'query': full_query,
            'results': [],
            'verified_term': None,
            'confidence': 0.0
        }


def create_extractor_with_web_search(provider: Optional[WebSearchProvider] = None) -> ThemeExtractorWithWeb:
    """
    Web検索機能付きのテーマ抽出器を作成
    
    Args:
        provider: 使用するWeb検索プロバイダー
        
    Returns:
        設定済みのテーマ抽出器
    """
    extractor = ThemeExtractorWithWeb(enable_web_search=True)
    
    if provider:
        # プロバイダーを設定（実装が必要）
        pass
    
    return extractor