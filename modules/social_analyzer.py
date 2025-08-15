"""
社会科目入試問題分析モジュール
地理・歴史・公民の三分野、資料読み取り、時事問題、出題形式を分析
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
import logging

# 改善されたテーマ抽出システムをインポート
try:
    from .theme_extractor_v2 import ThemeExtractorV2, ExtractedTheme
    USE_V2_EXTRACTOR = True
except ImportError:
    try:
        from .improved_theme_extractor import ImprovedThemeExtractor, ThemeExtractionResult
        USE_IMPROVED_EXTRACTOR = True
        USE_V2_EXTRACTOR = False
    except ImportError:
        USE_IMPROVED_EXTRACTOR = False
        USE_V2_EXTRACTOR = False

logger = logging.getLogger(__name__)


class SocialField(Enum):
    """社会科目の分野"""
    GEOGRAPHY = "地理"
    HISTORY = "歴史"
    CIVICS = "公民"
    CURRENT_AFFAIRS = "時事問題"
    MIXED = "総合"


class ResourceType(Enum):
    """資料の種類"""
    MAP = "地図"
    GRAPH = "グラフ"
    TIMELINE = "年表"
    TABLE = "表"
    PHOTO = "写真"
    DOCUMENT = "文書資料"
    OTHER = "その他資料"
    NONE = "資料なし"


class QuestionFormat(Enum):
    """出題形式"""
    SHORT_ANSWER = "短答式"
    MULTIPLE_CHOICE = "選択式"
    DESCRIPTIVE = "記述式"
    FILL_IN_BLANK = "穴埋め"
    TRUE_FALSE = "正誤判定"
    COMBINATION = "組み合わせ"
    OTHER = "その他"


@dataclass
class SocialQuestion:
    """社会科目の問題情報"""
    number: str
    text: str
    field: SocialField = SocialField.MIXED
    resource_types: List[ResourceType] = dataclass_field(default_factory=list)
    question_format: QuestionFormat = QuestionFormat.OTHER
    is_current_affairs: bool = False
    keywords: List[str] = dataclass_field(default_factory=list)
    time_period: Optional[str] = None  # 歴史の時代
    region: Optional[str] = None  # 地理の地域
    topic: Optional[str] = None  # 主題


class SocialAnalyzer:
    """社会科目問題の分析器"""
    
    def __init__(self):
        self.field_patterns = self._initialize_field_patterns()
        self.resource_patterns = self._initialize_resource_patterns()
        self.format_patterns = self._initialize_format_patterns()
        self.current_affairs_keywords = self._initialize_current_affairs_keywords()
        
        # 改善されたテーマ抽出器を初期化
        if USE_V2_EXTRACTOR:
            self.theme_extractor_v2 = ThemeExtractorV2()
            self.improved_extractor = None
        elif USE_IMPROVED_EXTRACTOR:
            self.improved_extractor = ImprovedThemeExtractor()
            self.theme_extractor_v2 = None
        else:
            self.improved_extractor = None
            self.theme_extractor_v2 = None
        
    def _initialize_field_patterns(self) -> Dict[SocialField, List[re.Pattern]]:
        """分野判定パターンの初期化（詳細版）"""
        return {
            SocialField.GEOGRAPHY: [
                re.compile(r'(地図|地形|気候|産業|人口|都市|農業|工業|貿易|資源|環境)'),
                re.compile(r'(北海道|東北|関東|中部|近畿|中国|四国|九州|沖縄)'),
                re.compile(r'(アジア|ヨーロッパ|アフリカ|北アメリカ|南アメリカ|オセアニア)'),
                re.compile(r'(緯度|経度|標高|平野|山地|川|湖|海)'),
                # 特産品・産業
                re.compile(r'(米|野菜|果物|畜産|漁業|林業|鉱業|製造業|サービス業)'),
                re.compile(r'(自動車|電子機器|鉄鋼|石油|化学|繊維|食品)'),
                re.compile(r'(港|空港|新幹線|高速道路|物流|観光)'),
            ],
            SocialField.HISTORY: [
                re.compile(r'(縄文|弥生|古墳|飛鳥|奈良|平安|鎌倉|室町|戦国|安土桃山|江戸|明治|大正|昭和|平成|令和)'),
                re.compile(r'(時代|世紀|年代|歴史|文化|政治|経済|社会|戦争|条約)'),
                re.compile(r'(\d{3,4}年)'),
                re.compile(r'(天皇|将軍|幕府|藩|武士|貴族|農民|町人)'),
                # 歴史的事件
                re.compile(r'(の乱|の変|の役|の戦い|革命|維新|改革|開国|鎖国)'),
                re.compile(r'(遣唐使|遣隋使|日米|日中|日露|太平洋戦争|世界大戦)'),
                re.compile(r'(織田信長|豊臣秀吉|徳川家康|源頼朝|足利|北条|藤原)'),
            ],
            SocialField.CIVICS: [
                re.compile(r'(憲法|法律|政治|選挙|国会|内閣|裁判|司法|立法|行政)'),
                re.compile(r'(権利|義務|自由|平等|民主|主権|国民|市民)'),
                re.compile(r'(経済|財政|税金|予算|金融|貿易|為替|株式)'),
                re.compile(r'(国際|国連|条約|協定|外交|安全保障)'),
                # 政治機構
                re.compile(r'(衆議院|参議院|最高裁判所|地方自治|都道府県|市町村)'),
                re.compile(r'(首相|大臣|知事|市長|議員|裁判官)'),
                re.compile(r'(政党|与党|野党|連立|解散|施政方針)'),
            ],
        }
    
    def _initialize_resource_patterns(self) -> Dict[ResourceType, List[re.Pattern]]:
        """資料種別判定パターンの初期化"""
        return {
            ResourceType.MAP: [
                re.compile(r'(地図|地形図|分布図|白地図|路線図)'),
                re.compile(r'図\d+.*地図'),
            ],
            ResourceType.GRAPH: [
                re.compile(r'(グラフ|折れ線|棒グラフ|円グラフ|帯グラフ)'),
                re.compile(r'図\d+.*グラフ'),
            ],
            ResourceType.TIMELINE: [
                re.compile(r'(年表|年代|時系列|歴史年表)'),
                re.compile(r'表\d+.*年表'),
            ],
            ResourceType.TABLE: [
                re.compile(r'(表\d+|データ|統計|一覧)'),
            ],
            ResourceType.PHOTO: [
                re.compile(r'(写真|画像|図版)'),
            ],
            ResourceType.DOCUMENT: [
                re.compile(r'(文書|史料|資料\d+|条文|憲章)'),
            ],
        }
    
    def _initialize_format_patterns(self) -> Dict[QuestionFormat, List[re.Pattern]]:
        """出題形式判定パターンの初期化"""
        return {
            QuestionFormat.SHORT_ANSWER: [
                re.compile(r'(答えなさい|書きなさい|述べなさい)'),
                re.compile(r'(何|誰|いつ|どこ|なぜ|どのように)'),
            ],
            QuestionFormat.MULTIPLE_CHOICE: [
                re.compile(r'(選びなさい|選択肢|ア\s*イ\s*ウ|①\s*②\s*③)'),
                re.compile(r'次の.+から.+選'),
            ],
            QuestionFormat.DESCRIPTIVE: [
                re.compile(r'(説明しなさい|論じなさい|述べなさい|理由を.+書)'),
                re.compile(r'\d+字(以内|程度)で'),
            ],
            QuestionFormat.FILL_IN_BLANK: [
                re.compile(r'(空欄|空所|（\s*）|〔\s*〕|［\s*］)'),
                re.compile(r'に当てはまる'),
            ],
            QuestionFormat.TRUE_FALSE: [
                re.compile(r'(正しい|誤り|○×|正誤)'),
            ],
            QuestionFormat.COMBINATION: [
                re.compile(r'(組み合わせ|対応|関係)'),
            ],
        }
    
    def _initialize_current_affairs_keywords(self) -> List[str]:
        """時事問題キーワードの初期化"""
        return [
            'SDGs', '持続可能', '気候変動', '温暖化', 'カーボンニュートラル',
            'コロナ', 'パンデミック', 'ワクチン', 'オリンピック', 'パラリンピック',
            'AI', '人工知能', 'DX', 'デジタル', 'SNS', 'インターネット',
            '少子高齢化', '人口減少', '働き方改革', 'ジェンダー', '多様性',
            'ウクライナ', 'ロシア', '台湾', '中国', '北朝鮮', 'ミサイル',
            '選挙', '政権', '内閣', '法改正', '憲法改正',
            '災害', '地震', '台風', '豪雨', '防災', '復興',
        ]
    
    def analyze_question(self, question_text: str, question_number: str = "") -> SocialQuestion:
        """問題文を分析して社会科目の問題情報を生成"""
        question = SocialQuestion(
            number=question_number,
            text=question_text,
            field=self._detect_field(question_text),
            resource_types=self._detect_resources(question_text),
            question_format=self._detect_format(question_text),
            is_current_affairs=self._is_current_affairs(question_text),
            keywords=self._extract_keywords(question_text),
        )
        
        # 分野別の追加情報を抽出
        if question.field == SocialField.HISTORY:
            question.time_period = self._extract_time_period(question_text)
        elif question.field == SocialField.GEOGRAPHY:
            question.region = self._extract_region(question_text)
        
        question.topic = self._extract_topic(question_text)
        
        return question
    
    def _detect_field(self, text: str) -> SocialField:
        """問題文から分野を判定（重み付けスコアリングシステム）"""
        field_scores = {}
        
        # 各分野の重み付きスコア計算
        for field, patterns in self.field_patterns.items():
            field_scores[field] = self._calculate_field_score(text, field, patterns)
        
        # 分野特有の強力キーワードによる追加判定
        field_scores = self._apply_strong_keywords(text, field_scores)
        
        # スコアがない場合
        total_score = sum(field_scores.values())
        if total_score == 0:
            if self._is_current_affairs(text):
                return SocialField.CURRENT_AFFAIRS
            return SocialField.MIXED
        
        # 最高スコアの分野を特定
        max_field = max(field_scores, key=field_scores.get)
        max_score = field_scores[max_field]
        
        # デバッグ情報
        logger.debug(f"分野スコア: {field_scores}, 最高: {max_field}({max_score})")
        
        # 強力な単独キーワードによる判定（閾値3.0以上）
        if max_score >= 3.0:
            return max_field
        
        # 70%以上のウェイトがある場合
        if total_score > 0 and (max_score / total_score) >= 0.7:
            return max_field
        
        # 時事問題の要素が強い場合
        if self._is_current_affairs(text):
            # 50%以上でその分野、未満なら時事問題
            if total_score > 0 and (max_score / total_score) >= 0.5:
                return max_field
            return SocialField.CURRENT_AFFAIRS
        
        # 複数分野が拮抗している場合（70%未満）
        # ただし、明確な特徴がある場合は分類する
        if max_score >= 2.0:  # 2.0以上のスコア
            return max_field
        
        # それ以外は総合とする
        return SocialField.MIXED
    
    def _calculate_field_score(self, text: str, field: SocialField, patterns: List[re.Pattern]) -> float:
        """分野の重み付きスコアを計算"""
        score = 0.0
        
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                # パターンの重要度による重み付け
                weight = self._get_pattern_weight(pattern.pattern, field)
                score += len(matches) * weight
        
        return score
    
    def _get_pattern_weight(self, pattern: str, field: SocialField) -> float:
        """パターンの重要度による重み付けを返す"""
        
        # 公民分野の強力キーワード（重み3.0）
        if field == SocialField.CIVICS:
            strong_civics = ['国会', '内閣', '裁判', '司法', '立法', '行政', '三権分立', 
                           '憲法', '選挙', '議員', '首相', '大臣', '最高裁判所']
            if any(keyword in pattern for keyword in strong_civics):
                return 3.0
        
        # 歴史分野の強力キーワード（重み3.0）
        elif field == SocialField.HISTORY:
            strong_history = ['縄文', '弥生', '古墳', '飛鳥', '奈良', '平安', '鎌倉', 
                            '室町', '戦国', '江戸', '明治', '大正', '昭和', '平成', '令和']
            if any(keyword in pattern for keyword in strong_history):
                return 3.0
            
            # 歴史的人物・事件（重み2.5）
            historical_events = ['の乱', 'の変', 'の役', 'の戦い', '革命', '維新', 
                               '天皇', '将軍', '幕府']
            if any(keyword in pattern for keyword in historical_events):
                return 2.5
        
        # 地理分野の強力キーワード（重み3.0）
        elif field == SocialField.GEOGRAPHY:
            strong_geo = ['地図', '地形', '気候', '産業', '人口', '都市', '農業', 
                         '工業', '貿易', '資源', '環境']
            if any(keyword in pattern for keyword in strong_geo):
                return 3.0
        
        # デフォルトの重み
        return 1.0
    
    def _apply_strong_keywords(self, text: str, scores: Dict[SocialField, float]) -> Dict[SocialField, float]:
        """分野特有の強力キーワードによる追加スコア"""
        
        # 公民分野の追加判定
        civics_strong = [
            '三権分立', '国会', '内閣', '衆議院', '参議院', '最高裁判所',
            '憲法', '選挙制度', '民主政治', '地方自治', '政党', '議員'
        ]
        
        for keyword in civics_strong:
            if keyword in text:
                scores[SocialField.CIVICS] += 3.0
                logger.debug(f"公民強力キーワード検出: {keyword}")
        
        # 歴史分野の追加判定（時代名の特別処理）
        history_periods = [
            '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
            '平安時代', '鎌倉時代', '室町時代', '戦国時代', '安土桃山時代',
            '江戸時代', '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
        ]
        
        for period in history_periods:
            if period in text or period.replace('時代', '') in text:
                scores[SocialField.HISTORY] += 3.0
                logger.debug(f"歴史時代キーワード検出: {period}")
        
        # 地理分野の追加判定
        geo_strong = [
            '三大都市圏', '関東地方', '近畿地方', '中部地方', '東北地方',
            '中国地方', '四国地方', '九州地方', '北海道', '沖縄'
        ]
        
        for keyword in geo_strong:
            if keyword in text:
                scores[SocialField.GEOGRAPHY] += 2.5
                logger.debug(f"地理強力キーワード検出: {keyword}")
        
        return scores
    
    def _detect_resources(self, text: str) -> List[ResourceType]:
        """問題文から使用されている資料の種類を検出"""
        resources = []
        
        for resource_type, patterns in self.resource_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    resources.append(resource_type)
                    break
        
        return resources if resources else [ResourceType.NONE]
    
    def _detect_format(self, text: str) -> QuestionFormat:
        """問題文から出題形式を判定"""
        for format_type, patterns in self.format_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return format_type
        
        return QuestionFormat.OTHER
    
    def _is_current_affairs(self, text: str) -> bool:
        """時事問題かどうかを判定"""
        # 年号が2020年以降の場合は時事問題の可能性が高い
        recent_years = re.findall(r'20[2-9]\d年', text)
        if recent_years:
            return True
        
        # 時事キーワードが含まれているか
        text_lower = text.lower()
        for keyword in self.current_affairs_keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """重要キーワードを抽出（詳細版）"""
        keywords = []
        
        # 固有名詞（カタカナ、漢字の連続）を抽出
        katakana = re.findall(r'[ァ-ヴー]{3,}', text)
        keywords.extend(katakana)
        
        # 「」内の用語を抽出
        quoted = re.findall(r'「([^」]+)」', text)
        keywords.extend(quoted)
        
        # 数字を含む用語（第〇次など）
        numbered = re.findall(r'第\d+[次回条][\w]+', text)
        keywords.extend(numbered)
        
        # 特産品・産業関連
        products = re.findall(r'([ぁ-ん]{1,3}[県市町村]の[\w]+)', text)
        keywords.extend(products)
        
        # 歴史的事件（〇〇の乱、〇〇の変など）
        events = re.findall(r'([\w]+の(?:乱|変|役|戦い|条約|同盟|会議))', text)
        keywords.extend(events)
        
        # 政治機構（参議院、衆議院など）
        politics = re.findall(r'((?:衆|参)議院|最高裁判所|内閣府|文部科学省|経済産業省)', text)
        keywords.extend(politics)
        
        # 地名・地域
        regions = re.findall(r'([\w]+(?:地方|平野|山脈|川|湾|海峡|半島|諸島))', text)
        keywords.extend(regions)
        
        # 人名（歴史上の人物）
        persons = re.findall(r'([ぁ-ん]*[一-龥]{2,4}(?:天皇|将軍|上皇|法皇))', text)
        keywords.extend(persons)
        
        return list(set(keywords))[:20]  # 重複を除いて最大20個
    
    def _extract_time_period(self, text: str) -> Optional[str]:
        """歴史問題から時代を抽出"""
        periods = [
            '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
            '平安時代', '鎌倉時代', '室町時代', '戦国時代', '安土桃山時代',
            '江戸時代', '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
        ]
        
        for period in periods:
            if period in text or period.replace('時代', '') in text:
                return period
        
        # 世紀での表記
        century = re.search(r'(\d+)世紀', text)
        if century:
            return f"{century.group(1)}世紀"
        
        return None
    
    def _extract_region(self, text: str) -> Optional[str]:
        """地理問題から地域を抽出"""
        # 日本の地方
        regions_japan = [
            '北海道', '東北', '関東', '中部', '近畿', '中国', '四国', '九州', '沖縄'
        ]
        
        for region in regions_japan:
            if region in text:
                return f"日本・{region}地方"
        
        # 世界の地域
        regions_world = [
            'アジア', 'ヨーロッパ', 'アフリカ', '北アメリカ', '南アメリカ', 'オセアニア'
        ]
        
        for region in regions_world:
            if region in text:
                return region
        
        # 国名を探す
        countries = re.findall(r'(アメリカ|中国|韓国|イギリス|フランス|ドイツ|ロシア|インド)', text)
        if countries:
            return countries[0]
        
        return None
    
    def _extract_topic_from_content(self, content: str) -> Optional[str]:
        """文章から実際の主題を抽出するヘルパーメソッド"""
        # 重要なキーワードを探す
        important_words = [
            '人物', '時代', '時期', '国', '地域', '都市', '制度', '政策',
            '戦争', '条約', '法律', '憲法', '機関', '組織', '宗教',
            '文化', '産業', '経済', '社会', '環境', '資源', '人口'
        ]
        
        for word in important_words:
            if word in content:
                # その単語の前後の固有名詞を探す
                match = re.search(rf'([ぁ-んァ-ヴー一-龥]+){word}', content)
                if match:
                    return match.group(0)
                match = re.search(rf'{word}[のをがはで]([ぁ-んァ-ヴー一-龥]+)', content)
                if match:
                    return match.group(1)
        
        # 「〜した」「〜された」などの動詞パターン
        verb_match = re.search(r'([ぁ-んァ-ヴー一-龥]{2,10})(?:した|された|している|おこなった)', content)
        if verb_match:
            return verb_match.group(1)
        
        # 最初の名詞句を返す
        noun_match = re.search(r'([ぁ-んァ-ヴー一-龥]{2,15})', content)
        if noun_match:
            return noun_match.group(1)
        
        return None
    
    def _extract_topic(self, text: str) -> Optional[str]:
        """問題の主題を抽出（実際の内容を取得）"""
        
        # V2テーマ抽出器を最優先で使用
        if self.theme_extractor_v2:
            result = self.theme_extractor_v2.extract(text)
            if result.theme:
                return result.theme
        
        # 改善されたテーマ抽出器を次に使用
        elif self.improved_extractor:
            result = self.improved_extractor.extract_theme(text)
            if result.theme and result.confidence > 0.3:
                return result.theme
        
        # OCRエラーや解答用紙の問題を除外
        if '社会解答用紙' in text or '採点欄' in text or '受験番号' in text:
            return None  # これらは分析対象外
        
        # 問題文の形式的な部分を除外（「正しい文章を」「まちがっている文章を」など）
        # これらは主題ではなく問題形式なので、他の内容を探す
        
        # 最初に重要な固有名詞や時代名、地名を探す
        # 人物名パターン（選択肢も含めて検索）
        person_patterns = [
            '聖徳太子', '中大兄皇子', '中臣鎌足', '蘇我入鹿', '聖武天皇',
            '織田信長', '豊臣秀吉', '徳川家康', '源頼朝', '足利尊氏',
            '藤原道長', '平清盛', '北条時宗', '足利義満', '武田信玄',
            '大坂城', '江戸城', '鎌倉幕府', '室町幕府', '江戸幕府'
        ]
        for person in person_patterns:
            if person in text:
                return person
        
        # 国名・地名パターン
        country_match = re.search(r'(イスラーム教|キリスト教|仏教|儒教|神道)', text)
        if country_match:
            return country_match.group(1)
        
        # 歴史的出来事・時代
        if '第一次世界大戦' in text:
            return '第一次世界大戦'
        if '太平洋戦争' in text or '第二次世界大戦' in text:
            return '太平洋戦争'
        if '満州事変' in text:
            return '満州事変'
        if 'ユーラシア大陸' in text or 'ナウマンゾウ' in text:
            return '日本列島の成立'
        if '高度経済成長' in text:
            return '高度経済成長'
        if 'オイルショック' in text:
            return 'オイルショック'
        
        # 地理的な内容
        if '中国の次に人口の多い国' in text:
            return '世界の人口'
        if 'ヨーロッパ' in text or 'アメリカ' in text or 'オセアニア' in text:
            if 'オセアニア' in text:
                return '世界の地域'
        if '東京' in text and '大阪' in text and '名古屋' in text:
            return '三大都市圏'
        if '地形図' in text:
            return '地形図の読み取り'
        if 'マドリード' in text or 'イスタンブール' in text or 'パリ' in text:
            return '世界の都市'
        
        # 社会問題・制度
        if '少子高齢化' in text:
            return '少子高齢化'
        if '消費税' in text:
            return '消費税'
        if '閣議' in text or '内閣' in text:
            return '内閣制度'
        if '社会保障' in text or '介護' in text or '育児' in text:
            return '社会保障制度'
        if '景気' in text:
            return '景気循環'
        
        # 環境問題
        if '自然が失われ' in text or '環境' in text:
            return '環境問題'
        if 'エネルギー' in text and ('石炭' in text or '石油' in text):
            return 'エネルギー資源'
            
        # 都市・地域
        if '東京' in text and '大阪' in text and '名古屋' in text:
            return '三大都市圏'
        if '地形図' in text:
            return '地形図の読み取り'
            
        # 「下線①について」パターンでも、その後の内容から抽出を試みる
        underline_match = re.search(r'下線[①②③④⑤⑥⑦⑧⑨⑩\d]+について[、,。]', text)
        if underline_match:
            # 問題文全体から重要語を探す
            content_after = text[underline_match.end():]
            topic = self._extract_topic_from_content(content_after[:100])
            if topic and len(topic) > 2:
                return topic
        
        # 空欄パターンの場合、選択肢から判断
        if '空らん' in text:
            # 選択肢に人名がある場合
            if '聖徳太子' in text or '中大兄皇子' in text:
                return '飛鳥時代の人物'
            # 地名がある場合
            if 'ヨーロッパ' in text or 'アジア' in text:
                return '世界の地域'
            # その他
            return '空欄補充'
        
        # まず特定のキーワードを検索
        special_topics = [
            'SDGs', '日本国憲法', '国際連合', '地球温暖化', '少子高齢化',
            '明治維新', '太平洋戦争', '日米安全保障条約', '三権分立',
            '参議院', '衆議院', '応仁の乱', '関ヶ原の戦い', '大政奉還',
            '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
            '平安時代', '鎌倉時代', '室町時代', '戦国時代', '江戸時代',
            '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
        ]
        
        for topic in special_topics:
            if topic in text:
                return topic
        
        # 「について」「に関して」などの前の文言を主題とする
        patterns = [
            r'([^。、]{2,30}?)(について|に関して|に関する)',
            r'([^。、]{2,30}?)(を説明|を答え|を述べ|を挙げ)',
            r'([^。、]{2,30}?)(とは何か|の特徴|の役割|の目的|の影響|の原因|の結果)',
            r'([^。、]{2,30}?)(はどのような|はなぜ|はいつ|はどこ)',
            r'次の([^。、]{2,30}?)を見て',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                topic = match.group(1).strip()
                # 不要な文字を削除
                topic = topic.replace('「', '').replace('」', '')
                topic = topic.replace('『', '').replace('』', '')
                # 末尾の助詞を削除
                topic = re.sub(r'(を|の|が|は)$', '', topic)
                # 「次の」を削除
                topic = topic.replace('次の', '').strip()
                # よくある不要な語句を削除
                if topic.startswith('それぞれの'):
                    topic = topic[6:]
                if topic.endswith('のうち'):
                    topic = topic[:-3]
                if len(topic) >= 2 and topic not in ['それぞれ', 'うち', 'なかで', 'ため', 'こと']:
                    return topic
        
        # 固有名詞を主題として抽出
        # 地名・人名・制度名など
        proper_nouns = [
            r'([\w]+時代)',
            r'([\w]+の乱|[\w]+の変|[\w]+の役)',
            r'([\w]+条約|[\w]+協定|[\w]+会議)',
            r'([\w]+戦争|[\w]+革命)',
            r'([\w]+制度|[\w]+政策)',
            r'(第[\d]+次[\w]+)',
            r'([\w]+憲法|[\w]+法)',
        ]
        
        for pattern in proper_nouns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # 問題文の最初の重要な名詞句を主題とする
        first_noun = re.search(r'^[^。、]*?([ぁ-んァ-ヴー一-龥]{2,15})', text)
        if first_noun:
            topic = first_noun.group(1).strip()
            if len(topic) >= 2:
                return topic
        
        # 最終的に適切なテーマが見つからない場合はNoneを返す
        return None
    
    def _is_format_only_question(self, text: str) -> bool:
        """問題形式の表現のみで内容がない問題かどうかを判定"""
        format_phrases = [
            'まちがっている文章を', '正しい文章を', '適切なものを選', '不適切なものを選',
            '次の中から選', '以下の.*から.*選', '組み合わせ.*選', 
            '答えなさい', '書きなさい', '述べなさい', '説明しなさい'
        ]
        
        # 問題形式表現を除いた実質的な内容があるかチェック
        clean_text = text
        for phrase in format_phrases:
            clean_text = re.sub(phrase, '', clean_text)
        
        # 実質的な内容が少ない場合は問題形式のみと判定
        content_words = re.findall(r'[ぁ-んァ-ヴー一-龥]{2,}', clean_text)
        meaningful_content = [w for w in content_words if len(w) > 2 and w not in ['について', 'に関して', 'もの', 'こと', 'から']]
        
        return len(meaningful_content) < 2
    
    def _resolve_reference_in_context(self, text: str) -> Optional[str]:
        """参照型表現を文脈から具体的な内容に解決"""
        
        # 下線参照の解決
        underline_match = re.search(r'下線[①②③④⑤⑥⑦⑧⑨⑩\d]+', text)
        if underline_match:
            # 下線周辺から具体的な内容を探す
            resolved = self._extract_content_around_reference(text, underline_match.start())
            if resolved:
                return resolved
        
        # 「この時期」「この時代」の解決
        if re.search(r'この時期|この時代|当時', text):
            time_context = self._infer_time_context(text)
            if time_context:
                return time_context
        
        # 「各都市」「これらの都市」の解決
        if re.search(r'各都市|これらの都市|各地域', text):
            city_context = self._infer_city_context(text)
            if city_context:
                return city_context
        
        # 空欄問題の解決
        if re.search(r'空らん|空欄|空所|\(\s*\)|〔\s*〕|［\s*］', text):
            blank_context = self._infer_blank_context(text)
            if blank_context:
                return blank_context
        
        return None
    
    def _extract_content_around_reference(self, text: str, ref_position: int) -> Optional[str]:
        """参照位置の前後から具体的な内容を抽出"""
        # 参照の前後100文字を取得
        start = max(0, ref_position - 100)
        end = min(len(text), ref_position + 100)
        context = text[start:end]
        
        # 重要な固有名詞を探す
        important_patterns = [
            r'([ぁ-んァ-ヴー一-龥]+時代)',
            r'([ぁ-んァ-ヴー一-龥]{2,4}(?:天皇|将軍|上皇|太子))',
            r'([ぁ-んァ-ヴー一-龥]+(?:の乱|の変|の役|の戦い|戦争|革命|維新))',
            r'([ぁ-んァ-ヴー一-龥]+(?:制度|政策|法律|憲法))',
            r'([ぁ-んァ-ヴー一-龥]+(?:地方|平野|山脈|川|湾|海峡|半島))',
        ]
        
        for pattern in important_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        
        # 選択肢から推測
        return self._infer_from_choices_in_text(text)
    
    def _infer_time_context(self, text: str) -> Optional[str]:
        """時期参照から具体的な時代を推測"""
        # 人物から時代推測
        time_clues = {
            '聖徳太子': '飛鳥時代',
            '中大兄皇子': '飛鳥時代', 
            '中臣鎌足': '飛鳥時代',
            '聖武天皇': '奈良時代',
            '織田信長': '戦国時代',
            '豊臣秀吉': '安土桃山時代',
            '徳川家康': '江戸時代初期',
            '大化の改新': '飛鳥時代',
            '応仁の乱': '室町時代',
            '明治維新': '江戸時代末期・明治時代初期',
            '太平洋戦争': '昭和時代',
            '高度経済成長': '昭和時代'
        }
        
        for clue, period in time_clues.items():
            if clue in text:
                return period
        
        return None
    
    def _infer_city_context(self, text: str) -> Optional[str]:
        """都市参照から具体的な都市群を推測"""
        if '東京' in text and '大阪' in text and '名古屋' in text:
            return '三大都市圏'
        if '関東' in text or '首都圏' in text:
            return '首都圏の都市'
        if '人口' in text and ('都市' in text or '市' in text):
            return '主要都市の人口'
        
        return None
    
    def _infer_blank_context(self, text: str) -> Optional[str]:
        """空欄問題から内容を推測"""
        # 選択肢から推測
        choice_theme = self._infer_from_choices_in_text(text)
        if choice_theme:
            return choice_theme
        
        # 文脈から推測
        if '憲法' in text:
            return '日本国憲法'
        if '戦争' in text and ('太平洋' in text or '第二次' in text):
            return '太平洋戦争'
        if '時代' in text:
            # 時代名の推測
            for period in ['縄文', '弥生', '古墳', '飛鳥', '奈良', '平安', '鎌倉', '室町', '江戸', '明治', '大正', '昭和']:
                if period in text:
                    return f'{period}時代'
        
        return None
    
    def _infer_from_choices_in_text(self, text: str) -> Optional[str]:
        """選択肢から主題を推測"""
        # 選択肢パターンを探す
        choice_patterns = [
            r'[①②③④⑤⑥⑦⑧⑨⑩]\s*([^①②③④⑤⑥⑦⑧⑨⑩]{2,15})',
            r'[ア-ン]\s*([^ア-ン]{2,15})',
        ]
        
        choices = []
        for pattern in choice_patterns:
            matches = re.findall(pattern, text)
            choices.extend([m.strip() for m in matches])
        
        if not choices:
            return None
        
        # 選択肢の共通テーマを分析
        return self._analyze_choice_theme(choices)
    
    def _analyze_choice_theme(self, choices: List[str]) -> Optional[str]:
        """選択肢リストから共通テーマを分析"""
        if not choices:
            return None
        
        # 人物が多い場合
        person_count = sum(1 for choice in choices 
                          if re.search(r'[一-龥]{2,4}(?:天皇|将軍|上皇|太子)', choice))
        if person_count >= len(choices) * 0.6:  # 60%以上が人物
            return '歴史上の人物'
        
        # 地名が多い場合
        place_count = sum(1 for choice in choices 
                         if re.search(r'[ぁ-んァ-ヴー一-龥]+(?:地方|県|市|町|村|国)', choice))
        if place_count >= len(choices) * 0.6:
            return '地域・地名'
        
        # 時代が多い場合
        period_count = sum(1 for choice in choices 
                          if re.search(r'[ぁ-んァ-ヴー一-龥]+時代', choice))
        if period_count >= len(choices) * 0.6:
            return '歴史時代'
        
        # 制度・法律が多い場合
        system_count = sum(1 for choice in choices 
                          if re.search(r'[ぁ-んァ-ヴー一-龥]+(?:制度|法|憲法|政策)', choice))
        if system_count >= len(choices) * 0.6:
            return '政治制度・法律'
        
        # 最初の具体的な選択肢を返す
        for choice in choices:
            if len(choice) >= 3 and not re.search(r'^[①②③④⑤⑥⑦⑧⑨⑩ア-ン]', choice):
                return choice.strip()
        
        return None
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """文書全体を分析して統計情報を生成"""
        # 問題を抽出
        questions = self._extract_questions(text)
        
        # 各問題を分析
        analyzed_questions = []
        for q_num, q_text in questions:
            analyzed_questions.append(self.analyze_question(q_text, q_num))
        
        # 総合と判定された問題を再評価
        analyzed_questions = self._reevaluate_mixed_questions(analyzed_questions)
        
        # 統計情報を集計
        stats = self._calculate_statistics(analyzed_questions)
        
        return {
            'questions': analyzed_questions,
            'statistics': stats,
            'total_questions': len(analyzed_questions)
        }
    
    def _reevaluate_mixed_questions(self, questions: List[SocialQuestion]) -> List[SocialQuestion]:
        """総合と判定された問題を再評価し、全体の傾向に基づいて分野を調整"""
        
        # 全体の分野分布を計算（総合を除く）
        field_counts = {}
        for q in questions:
            if q.field != SocialField.MIXED:
                field_counts[q.field] = field_counts.get(q.field, 0) + 1
        
        # 分野が特定できた問題がない場合は、そのまま返す
        if not field_counts:
            return questions
        
        # 最も多い分野を特定
        total_non_mixed = sum(field_counts.values())
        dominant_field = max(field_counts, key=field_counts.get)
        dominant_percentage = field_counts[dominant_field] / total_non_mixed
        
        # 70%以上のウェイトがある分野がある場合
        if dominant_percentage >= 0.7:
            # 総合と判定された問題を再評価
            for q in questions:
                if q.field == SocialField.MIXED:
                    # テキストを再分析して、該当分野の特徴があるか確認
                    if self._has_field_characteristics(q.text, dominant_field):
                        q.field = dominant_field
                        logger.debug(f"問題 {q.number} を総合から{dominant_field.value}に再分類")
        
        return questions
    
    def _has_field_characteristics(self, text: str, field: SocialField) -> bool:
        """テキストが特定の分野の特徴を持つか判定"""
        if field not in self.field_patterns:
            return False
        
        patterns = self.field_patterns[field]
        matches = sum(1 for pattern in patterns if pattern.search(text))
        
        # 1つ以上のパターンにマッチすれば、その分野の特徴があると判定
        return matches > 0
    
    def _extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """文書から問題を抽出（大問構造を考慮、OCRノイズを除外）"""
        questions = []
        
        # OCRノイズを除外するキーワード
        noise_patterns = [
            r'社会解答用紙',
            r'採点欄',
            r'受験番号',
            r'氏名',
            r'得点',
            r'※[\s\S]*?解答は',
            r'注意[\s\S]*?問題',
            r'配点[\s\S]*?点',
        ]
        
        # ノイズを除外
        cleaned_text = text
        for pattern in noise_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE)
        
        # 大問構造を認識
        large_question_matches = list(re.finditer(r'大問(\d+)', cleaned_text))
        
        if large_question_matches:
            # 大問ごとに処理
            for i, large_match in enumerate(large_question_matches):
                large_num = large_match.group(1)
                start_pos = large_match.end()
                
                # 次の大問までの範囲を取得
                if i + 1 < len(large_question_matches):
                    end_pos = large_question_matches[i + 1].start()
                    section_text = cleaned_text[start_pos:end_pos]
                else:
                    section_text = cleaned_text[start_pos:]
                
                # この大問内の小問を抽出
                sub_questions = self._extract_sub_questions(section_text, large_num)
                questions.extend(sub_questions)
        else:
            # 大問構造がない場合の従来処理（改良版）
            questions = self._extract_simple_questions(cleaned_text)
        
        # 重複する問題番号を調整（同じ番号の場合は連番で修正）
        questions = self._fix_duplicate_question_numbers(questions)
        
        # 最終的なノイズフィルタリング
        questions = self._filter_noise_questions(questions)
        
        return questions
    
    def _extract_sub_questions(self, text: str, large_num: str) -> List[Tuple[str, str]]:
        """大問内の小問を抽出"""
        sub_questions = []
        
        # 小問のパターン
        patterns = [
            re.compile(r'問(\d+)[\.、\s](.+?)(?=問\d+|$)', re.DOTALL),
            re.compile(r'(\d+)[\.、\s](.+?)(?=\d+[\.、\s]|$)', re.DOTALL),
            re.compile(r'【問(\d+)】(.+?)(?=【問\d+】|$)', re.DOTALL),
        ]
        
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                sub_questions = [(f"大問{large_num}-問{m[0]}", m[1].strip()) for m in matches]
                break
        
        return sub_questions
    
    def _extract_simple_questions(self, text: str) -> List[Tuple[str, str]]:
        """シンプルな問題抽出（大問構造がない場合）"""
        questions = []
        
        # 問題番号のパターン
        patterns = [
            re.compile(r'問(\d+)[\.、\s](.+?)(?=問\d+|$)', re.DOTALL),
            re.compile(r'(\d+)[\.、\s](.+?)(?=\d+[\.、\s]|$)', re.DOTALL),
            re.compile(r'【問(\d+)】(.+?)(?=【問\d+】|$)', re.DOTALL),
        ]
        
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                questions = [(f"問{m[0]}", m[1].strip()) for m in matches]
                break
        
        # 問題が見つからない場合は段落で分割
        if not questions:
            paragraphs = text.split('\n\n')
            questions = [(f"問{i+1}", p.strip()) 
                        for i, p in enumerate(paragraphs) 
                        if len(p.strip()) > 20]
        
        return questions
    
    def _fix_duplicate_question_numbers(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """重複する問題番号を修正（大問構造を維持）"""
        # 大問構造があるかチェック
        has_large_questions = any('大問' in q_num for q_num, _ in questions)
        
        if has_large_questions:
            # 大問構造がある場合は大問ごとに処理
            return self._fix_large_question_numbers(questions)
        else:
            # 単純な問題番号の場合
            return self._fix_simple_question_numbers(questions)
    
    def _fix_large_question_numbers(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """大問構造での問題番号修正（出現順で大問を1..Nに正規化、重複排除）"""
        # 出現順に大問キーのリストを作る（'other' は最後）
        ordered_keys: List[str] = []
        buckets: Dict[str, List[Tuple[str, str]]] = {}
        for q_num, q_text in questions:
            m = re.search(r'大問(\d+)', q_num)
            k = m.group(1) if m else 'other'
            if k not in ordered_keys:
                ordered_keys.append(k)
            buckets.setdefault(k, []).append((q_num, q_text))

        # 正規化マップ作成（'other' は末尾）
        normalize: Dict[str, str] = {}
        counter = 1
        for k in ordered_keys:
            if k == 'other':
                continue
            normalize[k] = str(counter)
            counter += 1
        if 'other' in buckets:
            normalize['other'] = str(counter)

        # 生成
        fixed: List[Tuple[str, str]] = []
        for k in ordered_keys:
            norm = normalize.get(k, k)
            for i, (_qnum, q_text) in enumerate(buckets[k], 1):
                new_q = f"問{i}" if k == 'other' else f"大問{norm}-問{i}"
                fixed.append((new_q, q_text))
        return fixed
    
    def _fix_simple_question_numbers(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """シンプルな問題番号修正"""
        seen_numbers = {}
        fixed_questions = []
        
        for q_num, q_text in questions:
            # 基本的な問題番号を抽出（「問3」→「3」）
            base_num_match = re.search(r'問(\d+)', q_num)
            if base_num_match:
                base_num = base_num_match.group(1)
                
                # 重複チェック
                if base_num in seen_numbers:
                    # 重複の場合は連番で修正
                    seen_numbers[base_num] += 1
                    new_q_num = f"問{base_num}-{seen_numbers[base_num]}"
                else:
                    seen_numbers[base_num] = 1
                    new_q_num = q_num
            else:
                new_q_num = q_num
            
            fixed_questions.append((new_q_num, q_text))
        
        return fixed_questions
    
    def _filter_noise_questions(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """ノイズ問題をフィルタリング（改良版 - 正当な問題を残す）"""
        filtered = []
        
        # 明確なノイズキーワード（これらのみの場合は除外）
        pure_noise_keywords = [
            '社会解答用紙', '採点欄', '受験番号', '氏名', '得点',
            '注意', '配点', '解答方法'
        ]
        
        for q_num, q_text in questions:
            # 非常に短い問題文を除外（空文字に近いもの）
            if len(q_text.strip()) < 5:
                logger.debug(f"短すぎる問題として除外: {q_num}")
                continue
            
            # 純粋なノイズキーワードのみの問題を除外
            is_pure_noise = False
            clean_text = q_text.strip()
            
            for noise_keyword in pure_noise_keywords:
                if noise_keyword in clean_text:
                    # ノイズキーワードを除去した後の有効な内容をチェック
                    remaining_text = clean_text.replace(noise_keyword, '').strip()
                    # 残りの文字が少ない場合はノイズと判定
                    if len(remaining_text) < 10:
                        logger.debug(f"ノイズキーワード主体で除外: {q_num} - {clean_text[:30]}...")
                        is_pure_noise = True
                        break
            
            if is_pure_noise:
                continue
            
            # 意味のある内容があるかチェック（個別の語句を正しくカウント）
            # より細かい単位で語句を分割
            meaningful_words = []
            # 助詞・動詞で分割してから単語を抽出
            word_parts = re.split(r'[についてをのかられがはでにから]', q_text)
            for part in word_parts:
                words = re.findall(r'[ぁ-んァ-ヴー一-龥]{2,}', part)
                meaningful_words.extend(words)
            
            # さらに固有名詞を追加カウント
            proper_nouns = re.findall(r'[一-龥]{2,}', q_text)  
            meaningful_words.extend(proper_nouns)
            
            # 重複を除去
            unique_words = list(set(meaningful_words))
            
            if len(unique_words) < 2:  # 2つ未満の場合のみ除外
                logger.debug(f"意味のある語句が不足で除外: {q_num} - 語句数:{len(unique_words)}, 語句:{unique_words}")
                continue
            
            # 教育的な内容のキーワードが含まれている場合は積極的に残す
            educational_keywords = [
                'について', 'に関して', 'を説明', 'について述べ', 'を答え',
                'について答え', 'を選び', 'を選ん', 'なさい', 'てください'
            ]
            
            has_educational_content = any(keyword in q_text for keyword in educational_keywords)
            
            # 意味のある固有名詞があるかチェック
            proper_nouns = re.findall(r'[一-龥]{3,}|[ァ-ヴー]{3,}', q_text)
            has_proper_nouns = len(proper_nouns) > 0
            
            # 教育的内容または固有名詞があれば残す
            if has_educational_content or has_proper_nouns or len(meaningful_words) >= 3:
                filtered.append((q_num, q_text))
            else:
                logger.debug(f"教育的内容不足で除外: {q_num} - {q_text[:30]}...")
        
        return filtered
    
    def _calculate_statistics(self, questions: List[SocialQuestion]) -> Dict[str, Any]:
        """問題リストから統計情報を計算"""
        total = len(questions)
        if total == 0:
            return {}
        
        # 分野別集計
        field_counts = {}
        for q in questions:
            field_counts[q.field.value] = field_counts.get(q.field.value, 0) + 1
        
        # 資料種別集計
        resource_counts = {}
        for q in questions:
            for r in q.resource_types:
                resource_counts[r.value] = resource_counts.get(r.value, 0) + 1
        
        # 出題形式集計
        format_counts = {}
        for q in questions:
            format_counts[q.question_format.value] = format_counts.get(q.question_format.value, 0) + 1
        
        # 時事問題の割合
        current_affairs_count = sum(1 for q in questions if q.is_current_affairs)
        
        return {
            'field_distribution': {
                k: {'count': v, 'percentage': round(v/total*100, 1)}
                for k, v in field_counts.items()
            },
            'resource_usage': {
                k: {'count': v, 'percentage': round(v/total*100, 1)}
                for k, v in resource_counts.items()
            },
            'format_distribution': {
                k: {'count': v, 'percentage': round(v/total*100, 1)}
                for k, v in format_counts.items()
            },
            'current_affairs': {
                'count': current_affairs_count,
                'percentage': round(current_affairs_count/total*100, 1)
            },
            'has_resources': {
                'count': sum(1 for q in questions if ResourceType.NONE not in q.resource_types),
                'percentage': round(sum(1 for q in questions if ResourceType.NONE not in q.resource_types)/total*100, 1)
            }
        }