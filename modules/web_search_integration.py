"""
Web検索統合モジュール
======================

Brave Search APIやMCPツールを使用して
社会科用語の正確な表現を取得します。
"""

import re
import json
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SocialTermInfo:
    """社会科用語の情報"""
    term: str                    # 用語
    formal_name: str             # 正式名称
    reading: Optional[str]       # 読み方
    category: str               # カテゴリー（歴史/地理/公民）
    era: Optional[str]          # 時代（歴史の場合）
    description: str            # 説明
    related_terms: List[str]    # 関連用語
    confidence: float           # 信頼度


class SocialTermWebSearcher:
    """
    社会科用語のWeb検索を行うクラス
    
    使用可能な検索方法：
    1. Brave Search API（brave_web_search）
    2. MCP o3検索（mcp__o3__o3-search）
    3. 一般的なWeb検索
    """
    
    def __init__(self, use_brave: bool = True, use_mcp_o3: bool = False):
        self.use_brave = use_brave
        self.use_mcp_o3 = use_mcp_o3
        self.cache = {}
        
    async def search_term(self, term: str, context: str = "") -> Optional[SocialTermInfo]:
        """
        用語をWeb検索して正確な情報を取得
        
        Args:
            term: 検索する用語
            context: 文脈（問題文の一部など）
            
        Returns:
            正確な用語情報
        """
        # キャッシュチェック
        cache_key = f"{term}:{context[:30]}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 検索クエリ構築
            query = self._build_query(term, context)
            
            # 検索実行
            if self.use_brave:
                result = await self._search_with_brave(query)
            elif self.use_mcp_o3:
                result = await self._search_with_mcp_o3(query)
            else:
                result = await self._search_general(query)
            
            # 結果を解析
            term_info = self._parse_result(result, term)
            
            # キャッシュに保存
            self.cache[cache_key] = term_info
            
            return term_info
            
        except Exception as e:
            logger.error(f"Web検索エラー: {e}")
            return None
    
    def _build_query(self, term: str, context: str) -> str:
        """
        効果的な検索クエリを構築
        """
        # 基本クエリ
        query_parts = [term]
        
        # カテゴリー推定
        if any(word in context for word in ['時代', '幕府', '戦争', '改革']):
            query_parts.append("日本史")
        elif any(word in context for word in ['地方', '県', '産業', '気候']):
            query_parts.append("日本地理")
        elif any(word in context for word in ['憲法', '法律', '選挙', '国会']):
            query_parts.append("公民")
        
        # 追加キーワード
        query_parts.extend([
            "正式名称",
            "社会科",
            "中学受験"
        ])
        
        return " ".join(query_parts)
    
    async def _search_with_brave(self, query: str) -> Dict:
        """
        Brave Search APIを使用した検索
        
        実際の実装では brave_web_search ツールを呼び出す
        """
        # ここでは仮の実装
        # 実際には: result = await brave_web_search(query=query, count=5)
        
        logger.info(f"Brave検索: {query}")
        
        # モック結果
        return {
            'web': {
                'results': [
                    {
                        'title': '阪神・淡路大震災 - Wikipedia',
                        'description': '阪神・淡路大震災は1995年1月17日に発生した...',
                        'url': 'https://ja.wikipedia.org/wiki/阪神・淡路大震災'
                    }
                ]
            }
        }
    
    async def _search_with_mcp_o3(self, query: str) -> Dict:
        """
        MCP o3検索を使用
        """
        # 実際には: result = await mcp__o3__o3-search(input=query)
        
        logger.info(f"MCP o3検索: {query}")
        
        return {
            'response': '検索結果のテキスト'
        }
    
    async def _search_general(self, query: str) -> Dict:
        """
        一般的なWeb検索（フォールバック）
        """
        logger.info(f"一般検索: {query}")
        return {}
    
    def _parse_result(self, result: Dict, original_term: str) -> Optional[SocialTermInfo]:
        """
        検索結果を解析して用語情報を抽出
        """
        if not result:
            return None
        
        # Brave検索結果の解析
        if 'web' in result and 'results' in result['web']:
            return self._parse_brave_result(result['web']['results'], original_term)
        
        # MCP o3結果の解析
        if 'response' in result:
            return self._parse_mcp_result(result['response'], original_term)
        
        return None
    
    def _parse_brave_result(self, results: List[Dict], original_term: str) -> Optional[SocialTermInfo]:
        """
        Brave検索結果から用語情報を抽出
        """
        if not results:
            return None
        
        # 最初の結果から情報抽出
        first_result = results[0]
        title = first_result.get('title', '')
        description = first_result.get('description', '')
        
        # 正式名称の抽出
        formal_name = self._extract_formal_name(title, description, original_term)
        
        # カテゴリー判定
        category = self._determine_category(formal_name, description)
        
        return SocialTermInfo(
            term=original_term,
            formal_name=formal_name,
            reading=None,
            category=category,
            era=self._extract_era(description),
            description=description[:200],
            related_terms=[],
            confidence=0.8
        )
    
    def _extract_formal_name(self, title: str, description: str, original: str) -> str:
        """
        正式名称を抽出
        """
        # よくある修正パターン
        corrections = {
            '阪神淡路': '阪神・淡路大震災',
            '東日本': '東日本大震災',
            '上げ米': '上米の制',
            '建武': '建武の新政',
        }
        
        for key, correct in corrections.items():
            if key in original:
                return correct
        
        # タイトルから抽出
        if ' - ' in title:
            name = title.split(' - ')[0].strip()
            if len(name) > 2:
                return name
        
        return original
    
    def _determine_category(self, term: str, description: str) -> str:
        """
        カテゴリーを判定
        """
        text = f"{term} {description}"
        
        if any(word in text for word in ['時代', '幕府', '戦争', '天皇', '将軍']):
            return '歴史'
        elif any(word in text for word in ['県', '地方', '産業', '地形', '気候']):
            return '地理'
        elif any(word in text for word in ['憲法', '法律', '選挙', '国会', '裁判']):
            return '公民'
        else:
            return '総合'
    
    def _extract_era(self, text: str) -> Optional[str]:
        """
        時代を抽出
        """
        eras = [
            '縄文時代', '弥生時代', '古墳時代', '飛鳥時代',
            '奈良時代', '平安時代', '鎌倉時代', '室町時代',
            '戦国時代', '安土桃山時代', '江戸時代',
            '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
        ]
        
        for era in eras:
            if era in text:
                return era
        
        # 年号から推定
        year_match = re.search(r'(\d{3,4})年', text)
        if year_match:
            year = int(year_match.group(1))
            if year < 710:
                return '飛鳥時代以前'
            elif year < 794:
                return '奈良時代'
            elif year < 1185:
                return '平安時代'
            elif year < 1333:
                return '鎌倉時代'
            elif year < 1573:
                return '室町時代'
            elif year < 1603:
                return '安土桃山時代'
            elif year < 1868:
                return '江戸時代'
            elif year < 1912:
                return '明治時代'
            elif year < 1926:
                return '大正時代'
            elif year < 1989:
                return '昭和時代'
            elif year < 2019:
                return '平成時代'
            else:
                return '令和時代'
        
        return None
    
    def _parse_mcp_result(self, response: str, original_term: str) -> Optional[SocialTermInfo]:
        """
        MCP o3検索結果から用語情報を抽出
        """
        # レスポンステキストから情報抽出
        # 実装は検索結果の形式に依存
        
        return SocialTermInfo(
            term=original_term,
            formal_name=original_term,
            reading=None,
            category='総合',
            era=None,
            description=response[:200],
            related_terms=[],
            confidence=0.7
        )


def integrate_web_search_with_extractor():
    """
    Web検索をテーマ抽出器に統合
    """
    from .theme_extractor_with_web import ThemeExtractorWithWeb
    
    # Web検索機能を有効にした抽出器を作成
    extractor = ThemeExtractorWithWeb(enable_web_search=True)
    
    # 検索プロバイダーを設定
    searcher = SocialTermWebSearcher(use_brave=True)
    
    # 統合（実装が必要）
    # extractor.set_search_provider(searcher)
    
    return extractor