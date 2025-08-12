"""
テーマ抽出システムの基本ルール定義
=======================================

このモジュールは社会科入試問題からテーマを抽出するための
基本的なルールとアルゴリズムを定義します。

設計思想:
1. 明確性: 意味が明確に理解できるテーマのみを抽出
2. 具体性: 抽象的すぎる表現を避け、具体的な内容を示す
3. 2文節原則: 「○○の△△」形式で構造化
4. 文脈独立性: 文脈なしでも理解可能なテーマのみ採用
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum
import re


class ThemeCategory(Enum):
    """テーマのカテゴリー"""
    HISTORY_EVENT = "歴史_事件"
    HISTORY_POLICY = "歴史_政策"
    HISTORY_CULTURE = "歴史_文化"
    HISTORY_PERSON = "歴史_人物"
    HISTORY_ERA = "歴史_時代"
    
    GEOGRAPHY_REGION = "地理_地域"
    GEOGRAPHY_INDUSTRY = "地理_産業"
    GEOGRAPHY_NATURE = "地理_自然"
    GEOGRAPHY_CITY = "地理_都市"
    
    CIVICS_LAW = "公民_法律"
    CIVICS_POLITICS = "公民_政治"
    CIVICS_ECONOMY = "公民_経済"
    CIVICS_INTERNATIONAL = "公民_国際"
    
    ABSTRACT = "抽象"
    INVALID = "無効"


@dataclass
class ExtractionRule:
    """テーマ抽出ルール"""
    pattern: re.Pattern
    theme_template: str
    category: ThemeCategory
    priority: int  # 優先度（高いほど優先）
    
    
class ThemeExtractionRules:
    """
    テーマ抽出の基本ルールセット
    
    改訂版アルゴリズム:
    1. 除外判定（最優先）
    2. 具体的パターンマッチング（優先度順）
    3. 文脈依存チェック
    4. 2文節形式への変換
    5. 最終検証
    """
    
    @staticmethod
    def get_exclusion_rules() -> List[re.Pattern]:
        """
        除外すべきパターンのリスト
        
        原則: 以下の条件に該当するものは即座に除外
        - 文脈依存（下線部、資料、この、その等）
        - 不完全な文（〜にあてはまる等）
        - 非社会科用語（ホームページ、電気機器等）
        - 問題形式の指示（選びなさい、答えなさい等）
        """
        return [
            # === 文脈依存表現 ===
            re.compile(r'^(下線部|資料|グラフ|表|図|写真|地図中)'),
            re.compile(r'^(この|その|同年|当時|以下の|上記の|次の)'),
            
            # === 不完全・無意味な表現 ===
            re.compile(r'にあてはまる(語句|人物名|言葉|もの|内容)'),
            re.compile(r'^【[あ-んア-ン]】'),
            re.compile(r'^\([あ-んア-ン]\)'),
            re.compile(r'(空欄|空らん|穴埋め|補充)'),
            re.compile(r'^.{1,3}の内容$'),  # 短すぎる「〜の内容」
            
            # === 問題形式の指示 ===
            re.compile(r'(選びなさい|答えなさい|述べなさい|説明しなさい)$'),
            re.compile(r'^(正しい|誤って|間違|適切|不適切)'),
            re.compile(r'^\d+字(以内|以上)'),
            
            # === 非社会科用語 ===
            re.compile(r'(ホームページ|ウェブサイト|Web|インターネット)'),
            re.compile(r'(電気機械|電子機器|コンピュータ|スマートフォン)'),
            re.compile(r'(グリーンマーク|エコマーク|リサイクルマーク)'),
            
            # === その他の無効表現 ===
            re.compile(r'^(問\d+|設問|質問)'),
            re.compile(r'新聞記事'),  # 文脈なしでは無意味
            re.compile(r'(河川部|部の内容)$'),
        ]
    
    @staticmethod
    def get_specific_rules() -> List[ExtractionRule]:
        """
        具体的なパターンマッチングルール
        
        優先度:
        100: 固有名詞の完全一致
        90: 歴史的事件・政策
        80: 地理的固有名詞
        70: 公民的制度・法律
        60: 文化・人物
        50: 時代・地域
        """
        rules = []
        
        # === 歴史: 事件・出来事（優先度90） ===
        historical_events = [
            ('大化の改新', '大化の改新の内容'),
            ('建武の新政', '建武の新政の影響'),
            ('鎌倉幕府', '鎌倉幕府の成立'),
            ('室町幕府', '室町幕府の政治'),
            ('江戸幕府', '江戸幕府の体制'),
            ('明治維新', '明治維新の改革'),
            ('日清戦争', '日清戦争の経過'),
            ('日露戦争', '日露戦争の影響'),
            ('第一次世界大戦', '第一次世界大戦の影響'),
            ('第二次世界大戦', '第二次世界大戦の経過'),
            ('太平洋戦争', '太平洋戦争の展開'),
            ('阪神・淡路大震災', '阪神・淡路大震災の被害'),  # 正式名称
            ('東日本大震災', '東日本大震災の影響'),
        ]
        
        for keyword, theme in historical_events:
            rules.append(ExtractionRule(
                pattern=re.compile(keyword),
                theme_template=theme,
                category=ThemeCategory.HISTORY_EVENT,
                priority=90
            ))
        
        # === 歴史: 政策・制度（優先度85） ===
        policies = [
            ('墾田永年私財法', '墾田永年私財法の内容'),
            ('班田収授法', '班田収授法の仕組み'),
            ('太閤検地', '太閤検地の実施'),
            ('刀狩', '刀狩の目的'),
            ('楽市楽座', '楽市楽座の政策'),
            ('鎖国', '鎖国政策の影響'),
            ('参勤交代', '参勤交代の制度'),
            ('廃藩置県', '廃藩置県の実施'),
            ('地租改正', '地租改正の内容'),
            ('殖産興業', '殖産興業の政策'),
        ]
        
        for keyword, theme in policies:
            rules.append(ExtractionRule(
                pattern=re.compile(keyword),
                theme_template=theme,
                category=ThemeCategory.HISTORY_POLICY,
                priority=85
            ))
        
        # === 公民: 憲法・法律（優先度80） ===
        laws = [
            ('日本国憲法', '日本国憲法の三原則'),
            ('大日本帝国憲法', '大日本帝国憲法の特徴'),
            ('教育基本法', '教育基本法の理念'),
            ('公職選挙法', '公職選挙法の仕組み'),
            ('民法', '民法の基本原則'),
            ('刑法', '刑法の基本原則'),
        ]
        
        for keyword, theme in laws:
            rules.append(ExtractionRule(
                pattern=re.compile(keyword),
                theme_template=theme,
                category=ThemeCategory.CIVICS_LAW,
                priority=80
            ))
        
        # === 公民: 政治制度（優先度75） ===
        politics = [
            ('内閣総理大臣', '内閣総理大臣の役割'),
            ('国会', '国会の仕組み'),
            ('内閣', '内閣の役割'),
            ('裁判所', '裁判所の種類'),
            ('最高裁判所', '最高裁判所の権限'),
            ('衆議院', '衆議院の優越'),
            ('参議院', '参議院の役割'),
            ('選挙', '選挙制度の仕組み'),
            ('政党', '政党の役割'),
        ]
        
        for keyword, theme in politics:
            rules.append(ExtractionRule(
                pattern=re.compile(keyword),
                theme_template=theme,
                category=ThemeCategory.CIVICS_POLITICS,
                priority=75
            ))
        
        # === 国際関係（優先度70） ===
        international = [
            ('国際連合', '国際連合の役割'),
            ('国連', '国連の組織'),
            ('WHO', 'WHOの活動'),
            ('UNESCO', 'UNESCOの役割'),
            ('NATO', 'NATOの目的'),
            ('EU', 'EUの統合'),
            ('ASEAN', 'ASEANの協力'),
            ('TPP', 'TPPの内容'),
            ('核兵器禁止条約', '核兵器禁止条約の意義'),
        ]
        
        for keyword, theme in international:
            rules.append(ExtractionRule(
                pattern=re.compile(keyword),
                theme_template=theme,
                category=ThemeCategory.CIVICS_INTERNATIONAL,
                priority=70
            ))
        
        return rules
    
    @staticmethod
    def get_category_patterns() -> dict:
        """
        カテゴリーベースのパターン
        
        時代、地域、都道府県などの一般的なカテゴリー
        """
        return {
            '時代': {
                'keywords': [
                    '縄文時代', '弥生時代', '古墳時代', '飛鳥時代',
                    '奈良時代', '平安時代', '鎌倉時代', '室町時代',
                    '戦国時代', '安土桃山時代', '江戸時代', '明治時代',
                    '大正時代', '昭和時代', '平成時代', '令和時代'
                ],
                'suffix_rules': {
                    '政治': '政治',
                    '文化': '文化',
                    '経済': '経済',
                    '社会': '社会',
                    'default': '特徴'
                }
            },
            '地域': {
                'keywords': [
                    '北海道地方', '東北地方', '関東地方', '中部地方',
                    '近畿地方', '中国地方', '四国地方', '九州地方'
                ],
                'suffix_rules': {
                    '産業': '産業',
                    '農業': '農業',
                    '工業': '工業',
                    '気候': '気候',
                    '地形': '地形',
                    'default': '特徴'
                }
            }
        }
    
    @staticmethod
    def create_two_clause_theme(keyword: str, context: str) -> str:
        """
        2文節形式のテーマを生成
        
        Args:
            keyword: メインキーワード
            context: 文脈情報
            
        Returns:
            「○○の△△」形式のテーマ
        """
        # キーワードの性質を分析
        if any(suffix in keyword for suffix in ['憲法', '法', '条約']):
            default_suffix = '内容'
        elif any(suffix in keyword for suffix in ['時代', '幕府']):
            default_suffix = '特徴'
        elif any(suffix in keyword for suffix in ['戦争', '事件', '改革']):
            default_suffix = '影響'
        elif any(suffix in keyword for suffix in ['県', '市', '地方']):
            default_suffix = '特徴'
        else:
            default_suffix = '内容'
        
        # 文脈から適切な修飾語を選択
        if '影響' in context or '結果' in context:
            suffix = '影響'
        elif '原因' in context or '理由' in context:
            suffix = '原因'
        elif '目的' in context:
            suffix = '目的'
        elif '仕組み' in context or '制度' in context:
            suffix = '仕組み'
        elif '役割' in context or '働き' in context:
            suffix = '役割'
        elif '特徴' in context or '特色' in context:
            suffix = '特徴'
        else:
            suffix = default_suffix
        
        return f"{keyword}の{suffix}"
    
    @staticmethod
    def validate_theme(theme: str) -> bool:
        """
        生成されたテーマの妥当性を検証
        
        Args:
            theme: 検証するテーマ
            
        Returns:
            妥当な場合True
        """
        if not theme:
            return False
        
        # 長さチェック
        if len(theme) < 5 or len(theme) > 30:
            return False
        
        # 2文節形式チェック
        if 'の' not in theme:
            return False
        
        # 無意味な繰り返しチェック
        parts = theme.split('の')
        if len(parts) == 2 and parts[0] == parts[1]:
            return False
        
        # 一般的すぎる語句チェック
        too_generic = ['内容', '仕組み', '特徴', '説明', '理由']
        if parts[0] in too_generic:
            return False
        
        return True