"""
テーマ分類の精緻化モジュール
汎用的な分類を具体的なテーマに修正
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ThemeRefiner:
    """テーマを精緻化するクラス"""
    
    def __init__(self):
        """初期化"""
        self.keyword_themes = self._initialize_keyword_themes()
    
    def _initialize_keyword_themes(self) -> Dict[str, Dict[str, List[str]]]:
        """キーワードとテーマのマッピングを初期化"""
        return {
            '地理': {
                '農業の特色': ['農業', '促成栽培', '抑制栽培', '近郊農業', '稲作', '畑作', '酪農', '畜産'],
                '工業の特色': ['工業', '工場', '製造業', '重工業', '軽工業', '工業地帯', '工業地域'],
                '地形と気候': ['地形', '山脈', '平野', '川', '気候', '雨温図', '降水量', '気温'],
                '人口と都市': ['人口', '人口密度', '都市', '過疎', '過密', '少子高齢化'],
                '地図の読み取り': ['地形図', '地図記号', '等高線', '尾根', '谷', '縮尺'],
                '日本の地域': ['北海道', '東北', '関東', '中部', '近畿', '中国', '四国', '九州'],
                '世界の地理': ['アジア', 'ヨーロッパ', 'アメリカ', 'アフリカ', 'オセアニア'],
                '資源とエネルギー': ['石油', '石炭', '天然ガス', '原子力', '再生可能エネルギー'],
                '貿易と交通': ['輸出', '輸入', '貿易', '港', '空港', '交通', '物流'],
                '環境問題': ['環境', '公害', '地球温暖化', 'CO2', '循環型社会']
            },
            '歴史': {
                '原始・古代': ['縄文', '弥生', '古墳', '銅鐸', '高床倉庫', '埴輪'],
                '飛鳥・奈良時代': ['聖徳太子', '大化の改新', '遣唐使', '平城京', '東大寺', '正倉院'],
                '平安時代': ['平安京', '藤原氏', '摂関政治', '遣唐使廃止', '国風文化', '源氏物語'],
                '鎌倉時代': ['源頼朝', '北条氏', '執権政治', '御成敗式目', '元寇', '鎌倉幕府'],
                '室町時代': ['足利氏', '南北朝', '勘合貿易', '応仁の乱', '下克上', '室町幕府'],
                '安土桃山時代': ['織田信長', '豊臣秀吉', '楽市楽座', '太閤検地', '刀狩'],
                '江戸時代': ['徳川家康', '参勤交代', '鎖国', '元禄文化', '化政文化', '江戸幕府'],
                '明治時代': ['明治維新', '文明開化', '富国強兵', '殖産興業', '日清戦争', '日露戦争'],
                '大正時代': ['大正デモクラシー', '米騒動', '関東大震災', '普通選挙'],
                '昭和時代': ['満州事変', '太平洋戦争', '高度経済成長', 'オイルショック', 'バブル経済'],
                '平成・令和': ['阪神淡路大震災', '東日本大震災', 'IT革命', 'グローバル化']
            },
            '公民': {
                '日本国憲法': ['憲法', '基本的人権', '国民主権', '平和主義', '三権分立'],
                '政治の仕組み': ['国会', '内閣', '裁判所', '選挙', '政党', '地方自治'],
                '経済の仕組み': ['市場経済', '株式会社', '金融', '財政', '税金', '社会保障'],
                '国際社会': ['国際連合', 'NATO', 'EU', 'ASEAN', 'TPP', 'FTA'],
                '現代社会の課題': ['少子高齢化', '環境問題', '格差社会', '情報化社会'],
                '人権と法律': ['人権', '法律', '裁判', '司法', '刑事裁判', '民事裁判']
            },
            '時事': {
                '国際情勢': ['ウクライナ', 'ロシア', '中国', 'アメリカ', '北朝鮮', 'NATO'],
                'パンデミック': ['コロナ', 'COVID', 'ワクチン', 'パンデミック', '感染症'],
                '環境・エネルギー': ['SDGs', '脱炭素', 'カーボンニュートラル', '再生可能エネルギー'],
                '技術革新': ['AI', 'DX', 'IoT', '5G', 'メタバース', 'ブロックチェーン'],
                '社会問題': ['少子化', '高齢化', '働き方改革', 'ジェンダー', 'LGBTQ'],
                '経済動向': ['インフレ', '円安', '金利', '株価', '景気', '失業率']
            }
        }
    
    def refine_theme(self, current_theme: str, text: str, field: str) -> str:
        """
        テーマを精緻化
        
        Args:
            current_theme: 現在のテーマ
            text: 問題文
            field: 分野
            
        Returns:
            精緻化されたテーマ
        """
        # 汎用的な分類の場合のみ精緻化
        generic_patterns = [
            r'地理/歴史/公民/時事総合問題',
            r'総合問題',
            r'分野不明',
            r'テーマ不明',
            r'混合問題'
        ]
        
        is_generic = False
        for pattern in generic_patterns:
            if re.search(pattern, current_theme):
                is_generic = True
                break
        
        if not is_generic and current_theme and len(current_theme) > 3:
            # すでに具体的なテーマの場合はそのまま返す
            return current_theme
        
        # テキストからキーワードを抽出してテーマを推定
        refined_theme = self._extract_theme_from_keywords(text, field)
        
        if refined_theme:
            logger.info(f"テーマ精緻化: {current_theme} → {refined_theme}")
            return refined_theme
        
        # 精緻化できない場合は分野名を返す
        return f"{field}問題"
    
    def _extract_theme_from_keywords(self, text: str, field: str) -> Optional[str]:
        """
        キーワードからテーマを抽出
        
        Args:
            text: 問題文
            field: 分野
            
        Returns:
            抽出されたテーマ
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # 分野別のキーワードマッチング
        if field in self.keyword_themes:
            themes_dict = self.keyword_themes[field]
            best_theme = None
            best_score = 0
            
            for theme, keywords in themes_dict.items():
                score = 0
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword.lower() in text_lower or keyword in text:
                        score += 1
                        matched_keywords.append(keyword)
                
                if score > best_score:
                    best_score = score
                    best_theme = theme
                    if matched_keywords:
                        # マッチしたキーワードを含めたテーマ
                        best_theme = f"{', '.join(matched_keywords[:3])}"
            
            if best_theme:
                return best_theme
        
        # 全分野から検索
        for field_name, themes_dict in self.keyword_themes.items():
            for theme, keywords in themes_dict.items():
                for keyword in keywords[:3]:  # 最初の3つのキーワードをチェック
                    if keyword.lower() in text_lower or keyword in text:
                        return f"{keyword}関連"
        
        return None
    
    def refine_all_themes(self, questions: List) -> List:
        """
        すべての問題のテーマを精緻化
        
        Args:
            questions: 問題リスト
            
        Returns:
            精緻化された問題リスト
        """
        for q in questions:
            if hasattr(q, 'theme') and hasattr(q, 'text') and hasattr(q, 'field'):
                original_theme = q.theme or ""
                refined = self.refine_theme(
                    original_theme,
                    q.text or "",
                    q.field if isinstance(q.field, str) else q.field.value
                )
                if refined != original_theme:
                    q.theme = refined
        
        return questions