"""
Brave Search API クライアント
================================

実際のBrave Search APIを使用して
社会科用語の正確な情報を取得します。
"""

import os
import json
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import urllib.request
import urllib.parse
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class BraveSearchResult:
    """Brave検索結果"""
    title: str
    description: str
    url: str
    score: float = 0.0
    
    
class BraveSearchClient:
    """
    Brave Search APIクライアント
    
    社会科用語の検索に特化した実装
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Brave Search APIキー
        """
        self.api_key = api_key or os.environ.get('BRAVE_API_KEY')
        if not self.api_key:
            logger.warning("Brave Search APIキーが設定されていません")
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.cache = {}
        
    def search(self, query: str, count: int = 5, lang: str = "ja") -> List[BraveSearchResult]:
        """
        Brave Search APIで検索
        
        Args:
            query: 検索クエリ
            count: 取得する結果数（最大20）
            lang: 言語（ja=日本語）
            
        Returns:
            検索結果のリスト
        """
        if not self.api_key:
            logger.error("APIキーが設定されていないため検索できません")
            return []
        
        # キャッシュチェック
        cache_key = f"{query}:{count}:{lang}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # クエリパラメータ
            params = {
                'q': query,
                'count': min(count, 20),
                'lang': lang,
                'country': 'JP',
                'search_lang': 'ja',
                'safesearch': 'moderate'
            }
            
            # URLエンコード
            query_string = urllib.parse.urlencode(params)
            url = f"{self.base_url}?{query_string}"
            
            # リクエスト作成
            request = urllib.request.Request(
                url,
                headers={
                    'Accept': 'application/json',
                    'X-Subscription-Token': self.api_key
                }
            )
            
            # API呼び出し
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 結果を解析
            results = self._parse_results(data)
            
            # キャッシュに保存
            self.cache[cache_key] = results
            
            return results
            
        except urllib.error.HTTPError as e:
            logger.error(f"Brave Search APIエラー: {e.code} - {e.reason}")
            return []
        except Exception as e:
            logger.error(f"検索中にエラーが発生: {e}")
            return []
    
    def _parse_results(self, data: Dict) -> List[BraveSearchResult]:
        """
        API応答を解析
        """
        results = []
        
        if 'web' not in data or 'results' not in data['web']:
            return results
        
        for item in data['web']['results']:
            result = BraveSearchResult(
                title=item.get('title', ''),
                description=item.get('description', ''),
                url=item.get('url', ''),
                score=item.get('relevance_score', 0.0)
            )
            results.append(result)
        
        return results
    
    def search_social_term(self, term: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        社会科用語を検索して正確な情報を取得
        
        Args:
            term: 検索する用語
            context: 文脈（追加のキーワード）
            
        Returns:
            用語の正確な情報
        """
        # 社会科向けの検索クエリを構築
        query_parts = [term]
        
        # コンテキストから追加キーワードを抽出
        if context:
            if '震災' in context or '地震' in context:
                query_parts.extend(['日本', '災害', '正式名称'])
            elif '時代' in context or '歴史' in context:
                query_parts.extend(['日本史', '歴史'])
            elif '地理' in context or '産業' in context:
                query_parts.extend(['日本地理', '地理'])
            elif '憲法' in context or '法律' in context:
                query_parts.extend(['公民', '法律'])
            else:
                query_parts.extend(['社会科', '中学受験'])
        
        query = ' '.join(query_parts)
        
        # 検索実行
        results = self.search(query, count=3)
        
        if not results:
            return None
        
        # 最も関連性の高い結果から情報を抽出
        return self._extract_term_info(term, results)
    
    def _extract_term_info(self, original_term: str, results: List[BraveSearchResult]) -> Dict[str, Any]:
        """
        検索結果から用語情報を抽出
        """
        if not results:
            return None
        
        # 最初の結果を主に使用
        first = results[0]
        
        # 正式名称の推定
        formal_name = self._extract_formal_name(first.title, first.description, original_term)
        
        # カテゴリーの判定
        category = self._determine_category(first.title + ' ' + first.description)
        
        # 時代の抽出（歴史の場合）
        era = None
        if category == '歴史':
            era = self._extract_era(first.description)
        
        return {
            'original_term': original_term,
            'formal_name': formal_name,
            'category': category,
            'era': era,
            'description': first.description[:200],
            'source_url': first.url,
            'confidence': min(0.9, 0.5 + first.score)
        }
    
    def _extract_formal_name(self, title: str, description: str, original: str) -> str:
        """
        タイトルと説明から正式名称を抽出
        """
        # よくある修正パターン
        corrections = {
            '阪神淡路': '阪神・淡路大震災',
            '青地大震災': '阪神・淡路大震災',
            '東日本': '東日本大震災',
            '関東': '関東大震災',
            '上げ米': '上米の制',
            '建武の改革': '建武の新政',
            '大東亜戦争': '太平洋戦争',
        }
        
        # 直接的な修正
        for key, correct in corrections.items():
            if key in original:
                return correct
        
        # Wikipediaタイトルから抽出
        if 'Wikipedia' in title:
            # 「○○ - Wikipedia」形式から抽出
            if ' - ' in title:
                name = title.split(' - ')[0].strip()
                if len(name) > 2 and '検索結果' not in name:
                    return name
        
        # 説明文から「○○とは」形式を探す
        import re
        match = re.match(r'^([^、。\s]+?)(?:とは|は|が|を)', description)
        if match:
            candidate = match.group(1)
            if len(candidate) > 2 and len(candidate) < 20:
                return candidate
        
        return original
    
    def _determine_category(self, text: str) -> str:
        """
        テキストから社会科のカテゴリーを判定
        """
        # キーワードベースの判定
        history_keywords = ['時代', '幕府', '戦争', '天皇', '将軍', '改革', '維新', '事件']
        geography_keywords = ['県', '地方', '産業', '地形', '気候', '人口', '資源', '震災']
        civics_keywords = ['憲法', '法律', '選挙', '国会', '内閣', '裁判', '条約', '国連']
        
        history_score = sum(1 for k in history_keywords if k in text)
        geography_score = sum(1 for k in geography_keywords if k in text)
        civics_score = sum(1 for k in civics_keywords if k in text)
        
        if history_score >= geography_score and history_score >= civics_score:
            return '歴史'
        elif geography_score >= civics_score:
            return '地理'
        else:
            return '公民'
    
    def _extract_era(self, text: str) -> Optional[str]:
        """
        テキストから時代を抽出
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
        import re
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


# グローバルインスタンス（APIキー付き）
_global_client = None

def get_brave_client(api_key: Optional[str] = None) -> BraveSearchClient:
    """
    Braveクライアントのシングルトンを取得
    """
    global _global_client
    if _global_client is None:
        # 提供されたAPIキーを使用
        _global_client = BraveSearchClient(
            api_key=api_key or "BSAE5HSjUtrfzSj18mUUNZJxjSnspgC"
        )
    return _global_client