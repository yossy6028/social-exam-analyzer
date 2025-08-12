"""
改善版テーマ抽出システム v2
根本的な仕組みの改善により、より正確で具体的なテーマ抽出を実現
"""

import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTheme:
    """抽出されたテーマ"""
    theme: Optional[str]
    category: Optional[str]  # 地理/歴史/公民
    confidence: float
    
    
class ThemeExtractorV2:
    """
    改善版テーマ抽出器
    
    設計思想:
    1. 階層的アプローチ: 具体的→抽象的の順で抽出
    2. パターンベース: 確実なパターンから順に適用
    3. コンテキスト重視: 前後の文脈を考慮
    4. 除外ルール明確化: 無効なテーマを体系的に排除
    """
    
    def __init__(self):
        # 階層1: 固有名詞・具体的事象
        self.specific_patterns = self._init_specific_patterns()
        
        # 階層2: 一般的カテゴリ
        self.category_patterns = self._init_category_patterns()
        
        # 階層3: 抽象的概念
        self.abstract_patterns = self._init_abstract_patterns()
        
        # 除外パターン
        self.exclusion_patterns = self._init_exclusion_patterns()
        
    def _init_specific_patterns(self) -> Dict[str, List[Tuple[re.Pattern, str, str]]]:
        """固有名詞や具体的事象のパターン（2文節形式）"""
        return {
            '歴史_事件': [
                (re.compile(r'建武の新政'), '建武の新政の内容', '歴史'),
                (re.compile(r'大化の改新'), '大化の改新の内容', '歴史'),
                (re.compile(r'鎌倉幕府'), '鎌倉幕府の成立', '歴史'),
                (re.compile(r'承久の乱'), '承久の乱の経過', '歴史'),
                (re.compile(r'応仁の乱'), '応仁の乱の影響', '歴史'),
                (re.compile(r'本能寺の変'), '本能寺の変の経過', '歴史'),
                (re.compile(r'関ヶ原の戦い'), '関ヶ原の戦いの結果', '歴史'),
                (re.compile(r'明治維新'), '明治維新の改革', '歴史'),
                (re.compile(r'太平洋戦争'), '太平洋戦争の経過', '歴史'),
                (re.compile(r'五・一五事件'), '五・一五事件の影響', '歴史'),
                (re.compile(r'二・二六事件'), '二・二六事件の影響', '歴史'),
                (re.compile(r'日露戦争'), '日露戦争の結果', '歴史'),
                (re.compile(r'第一次世界大戦'), '第一次世界大戦の影響', '歴史'),
            ],
            '歴史_政策': [
                (re.compile(r'上米の制'), '上米の制の内容', '歴史'),
                (re.compile(r'楽市楽座'), '楽市楽座の政策', '歴史'),
                (re.compile(r'刀狩'), '刀狩の目的', '歴史'),
                (re.compile(r'検地'), '太閤検地の実施', '歴史'),
                (re.compile(r'鎖国'), '鎖国政策の影響', '歴史'),
                (re.compile(r'墾田永年私財法'), '墾田永年私財法の内容', '歴史'),
            ],
            '歴史_文書': [
                (re.compile(r'ポツダム宣言'), 'ポツダム宣言の内容', '歴史'),
                (re.compile(r'サンフランシスコ.*?条約'), 'サンフランシスコ講和条約の内容', '歴史'),
                (re.compile(r'日米安全?保障?条約'), '日米安全保障条約の内容', '歴史'),
            ],
            '歴史_政党': [
                (re.compile(r'大隈重信.*?政党'), '立憲改進党の結成', '歴史'),
                (re.compile(r'板垣退助.*?政党'), '自由党の結成', '歴史'),
                (re.compile(r'伊藤博文.*?政党'), '立憲政友会の結成', '歴史'),
            ],
            '歴史_文化': [
                (re.compile(r'延暦寺'), '延暦寺の歴史', '歴史'),
                (re.compile(r'伊勢物語'), '伊勢物語の成立', '歴史'),
                (re.compile(r'枕草子'), '平安時代の文学', '歴史'),  # 時代を明記
                (re.compile(r'源氏物語'), '平安時代の文学', '歴史'),
                (re.compile(r'古今和歌集'), '平安時代の和歌', '歴史'),
                (re.compile(r'万葉集'), '奈良時代の和歌', '歴史'),
                (re.compile(r'日本書紀'), '奈良時代の歴史書', '歴史'),
                (re.compile(r'古事記'), '奈良時代の歴史書', '歴史'),
            ],
            '地理_災害': [
                (re.compile(r'阪神・淡路大震災'), '阪神・淡路大震災の被害', '地理'),
                (re.compile(r'東日本大震災'), '東日本大震災の影響', '地理'),
                (re.compile(r'関東大震災'), '関東大震災の被害', '歴史'),
            ],
            '地理_インフラ': [
                (re.compile(r'青函トンネル'), '青函トンネルの役割', '地理'),
                (re.compile(r'瀬戸大橋'), '瀬戸大橋の建設', '地理'),
                (re.compile(r'明石海峡大橋'), '明石海峡大橋の構造', '地理'),
                (re.compile(r'東海道新幹線'), '東海道新幹線の発展', '地理'),
            ],
            '地理_産業': [
                (re.compile(r'プラスチック製品'), 'プラスチック製品の生産', '地理'),
                (re.compile(r'半導体'), '半導体産業の発展', '地理'),
            ],
            '公民_制度': [
                (re.compile(r'日本国憲法'), '日本国憲法の三原則', '公民'),
                (re.compile(r'三権分立'), '三権分立の仕組み', '公民'),
                (re.compile(r'議院内閣制'), '議院内閣制の特徴', '公民'),
                (re.compile(r'地方自治'), '地方自治の仕組み', '公民'),
                (re.compile(r'選挙制度'), '選挙制度の仕組み', '公民'),
                (re.compile(r'地方交付税'), '地方交付税の仕組み', '公民'),
                (re.compile(r'ストライキ'), 'ストライキの権利', '公民'),
            ],
            '公民_人口': [
                (re.compile(r'人口ピラミッド'), '人口ピラミッドの分析', '公民'),
            ],
            '国際': [
                (re.compile(r'(1948年.*?ユダヤ|ユダヤ.*?建国|イスラエル.*?建国)'), 'イスラエル建国の経緯', '歴史'),
                (re.compile(r'(ユダヤ.*?アラブ|中東.*?紛争)'), '中東問題の現状', '歴史'),
                (re.compile(r'日独伊三国同盟'), '日独伊三国同盟の成立', '歴史'),
                (re.compile(r'国連|国際連合'), '国連の役割', '公民'),
            ],
            '社会問題': [
                (re.compile(r'空き家'), '空き家問題の現状', '公民'),
                (re.compile(r'少子高齢化'), '少子高齢化の影響', '公民'),
                (re.compile(r'男女.*?(平等|共同参画|対等)'), '男女共同参画社会の推進', '公民'),
            ],
        }
    
    def _init_category_patterns(self) -> Dict[str, Tuple[List[str], str]]:
        """カテゴリベースのパターン（キーワードリスト）"""
        # 全都道府県リスト
        all_prefectures = [
            '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
            '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
            '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
            '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
        
        # 主要都市リスト
        major_cities = [
            '札幌市', '仙台市', 'さいたま市', '千葉市', '東京都', '横浜市', '川崎市',
            '新潟市', '静岡市', '浜松市', '名古屋市', '京都市', '大阪市', '堺市',
            '神戸市', '岡山市', '広島市', '北九州市', '福岡市', '熊本市'
        ]
        
        return {
            '時代': ([
                '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
                '平安時代', '鎌倉時代', '室町時代', '戦国時代', '安土桃山時代',
                '江戸時代', '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
            ], '歴史'),
            '地域': ([
                '北海道', '東北地方', '関東地方', '中部地方', '近畿地方',
                '中国地方', '四国地方', '九州地方', '沖縄'
            ], '地理'),
            '都道府県': (all_prefectures, '地理'),
            '都市': (major_cities, '地理'),
        }
    
    def _init_abstract_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """抽象的な概念のパターン"""
        return [
            (re.compile(r'資料.*?読み取り'), '資料の読み取り'),
            (re.compile(r'グラフ.*?分析'), 'グラフの分析'),
            (re.compile(r'地図.*?(読み取り|から)'), '地図の読み取り'),
            (re.compile(r'地図中'), '地図の読み取り'),  # 「地図中の内容」対策
            (re.compile(r'年表.*?読み取り'), '年表の読み取り'),
            (re.compile(r'統計.*?分析'), '統計の分析'),
            (re.compile(r'図表.*?読み取り'), '図表の読み取り'),
        ]
    
    def _init_exclusion_patterns(self) -> List[re.Pattern]:
        """除外すべきパターン（強化版）"""
        return [
            # === 基本的な指示語・接続語 ===
            # 指示語のみ（単独）
            re.compile(r'^(にあてはまる|あてはまる|答えなさい|選びなさい|について|として|に関して)$'),
            # 短すぎる断片（3文字以下）
            re.compile(r'^.{1,3}(について|として|に関する|の仕組み|の説明)$'),
            
            # === 問題形式の表現 ===
            # 問題番号や記号
            re.compile(r'^(問\d+|【[あ-おア-オ]】|\([あ-おア-オ]\))'),
            # 文字数指定
            re.compile(r'^\d+字(以上|以内)'),
            # 説明の断片
            re.compile(r'^(説明として|関連して|関する文|期間におきた)'),
            
            # === 空欄・穴埋め関連 ===
            # 空欄補充・穴埋め
            re.compile(r'(空欄補充|穴埋め|空らん)'),
            # 記号や括弧のみの内容
            re.compile(r'^【[あ-んア-ン]】|^\([あ-んア-ン]\)'),
            # 【】にあてはまる形式
            re.compile(r'【[あ-んア-ン]】にあてはまる'),
            # 「にあてはまる人物名」形式
            re.compile(r'にあてはまる(人物名|語句|言葉|もの)'),
            
            # === 「次の〜」パターン（問題文の導入部） ===
            re.compile(r'^次の(図|表|グラフ|資料|写真|地図|雨温図|年表|史料|文章)(は|で|を|から|について|に関して)'),
            re.compile(r'^次に示す(図|表|グラフ|資料|写真|地図|雨温図|年表|史料|文章)'),
            re.compile(r'^以下の(図|表|グラフ|資料|写真|地図|雨温図|年表|史料|文章)'),
            # 「次の資料は〜について述べたものです」形式
            re.compile(r'^次の.*?について述べた(もの|内容)'),
            re.compile(r'^次の.*?に関する(資料|文章|記述)'),
            re.compile(r'^次の.*?を示した(もの|図|表|資料)'),
            
            # === 下線部関連 ===
            # 下線部の内容（番号なしの場合）
            re.compile(r'^下線部の(内容|特徴|説明)$'),
            # 番号付き下線部
            re.compile(r'^下線部[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]'),
            re.compile(r'^下線部[（(][あ-おア-オ][)）]'),
            re.compile(r'^下線部[（(]\d+[)）]'),
            re.compile(r'^下線部[あ-おア-オ]'),
            # 下線部を含む一般的なパターン
            re.compile(r'下線部.*?(について|に関して|として|の内容|の特徴|の説明)$'),
            
            # === 参照・引用関連 ===
            # 不完全な表現
            re.compile(r'^この当時の'),
            re.compile(r'^同年'),
            re.compile(r'^この年'),
            re.compile(r'^当時の'),
            re.compile(r'^その後の'),
            
            # === 技術・現代的用語（社会科に不適切） ===
            # ホームページやウェブサイト（社会科に不適切）
            re.compile(r'(ホームページ|ウェブサイト|ウェブページ|Webサイト|気象庁ホームページ)'),
            # 社会科に無関係な用語
            re.compile(r'(電気機械器具|電子機器|コンピュータ|スマートフォン|携帯電話|グリーンマーク)'),
            # 現代的すぎる概念
            re.compile(r'(インターネット|ソーシャルメディア|SNS|AI|人工知能)'),
            
            # === 教科横断・他教科用語 ===
            # 国語関連（社会科ではない）
            re.compile(r'(読書感想文|作文|小説|俳句|短歌|詩|文学作品).*?(特徴|内容|分析)'),
            # 理科関連（地理と重複しないもの）
            re.compile(r'(実験|観察|化学式|分子|原子|DNA)'),
            # 数学関連
            re.compile(r'(方程式|関数|図形|証明)'),
            
            # === 曖昧すぎる表現 ===
            # 河川部など不明瞭な表現
            re.compile(r'(河川部の内容|部の内容)$'),
            # 「〜の内容」だけの曖昧な表現（3文字以下）
            re.compile(r'^.{1,3}の内容$'),
            # 極端に一般的な表現
            re.compile(r'^(内容|特徴|理由|原因|結果|影響|意味|目的)$'),
            
            # === 問題解答指示 ===
            # 解答形式の指定
            re.compile(r'(漢字で答え|ひらがなで答え|カタカナで答え)'),
            re.compile(r'(記号で答え|番号で答え|選択肢)'),
            re.compile(r'(正しい|適切な|誤って|間違って).*?(選び|答え)'),
            
            # === 地図・図表の参照（文脈なしでは無意味） ===
            # 地図中の〜（位置指定）
            re.compile(r'^(地図中の|図中の|表中の|グラフ中の)'),
            # アルファベット・記号での場所指定
            re.compile(r'^[A-Z]([地点|地域|都市|県|国])'),
            re.compile(r'^[ア-ン]([地点|地域|都市|県|国])'),
            
            # === 時間・順序関係（文脈依存） ===
            re.compile(r'^(その後|それ以降|以前|以後|同時期|当該期間)'),
            re.compile(r'^第[一二三四五六七八九十]期'),
            
            # === 不完全な固有名詞 ===
            # 〜県の特徴（県名が具体的でない場合）
            re.compile(r'^この(県|府|道|都|地方|地域)の'),
            # A国、B国のような抽象的表現
            re.compile(r'^[A-Z]国'),
        ]
    
    def extract(self, text: str) -> ExtractedTheme:
        """
        テーマを抽出するメインメソッド
        
        階層的アプローチ:
        1. 除外チェック
        2. 具体的パターンのマッチング
        3. カテゴリパターンのマッチング
        4. 抽象パターンのマッチング
        5. フォールバック処理
        """
        
        # ステップ1: 除外チェック
        if self._should_exclude(text):
            return ExtractedTheme(None, None, 0.0)
        
        # 特殊なケースの処理
        # 「下線部」「新聞記事」などの参照は文脈なしでは意味不明
        if any(keyword in text for keyword in ['下線部', '新聞記事', '資料', 'グラフ', '表']):
            # より具体的な内容を探す
            if '震災' in text:
                if '淡路' in text or '阪神' in text:
                    return ExtractedTheme('阪神・淡路大震災', '地理', 0.9)
                else:
                    return ExtractedTheme('自然災害の影響', '地理', 0.8)
            # 他に具体的な内容がない場合はNone
            if not any(word in text for word in ['について', '説明', '答え', '述べ']):
                return ExtractedTheme(None, None, 0.0)
        
        # 「同年」など文脈依存の表現を除外
        if text.startswith('同年') or text.startswith('この年'):
            return ExtractedTheme(None, None, 0.0)
        
        # ステップ2: 具体的パターンのマッチング
        specific_result = self._match_specific_patterns(text)
        if specific_result:
            return specific_result
        
        # ステップ3: カテゴリパターンのマッチング
        category_result = self._match_category_patterns(text)
        if category_result:
            return category_result
        
        # ステップ4: 抽象パターンのマッチング
        abstract_result = self._match_abstract_patterns(text)
        if abstract_result:
            return abstract_result
        
        # ステップ5: フォールバック処理
        # フォールバックする前に、本当に有効なテーマがあるか確認
        if len(text.strip()) < 10 or '答え' in text or '選び' in text:
            return ExtractedTheme(None, None, 0.0)
            
        return self._fallback_extraction(text)
    
    def _should_exclude(self, text: str) -> bool:
        """除外すべきテキストかどうか判定"""
        # 極端に短すぎる（3文字以下）
        if len(text.strip()) <= 3:
            return True
        
        # 除外パターンにマッチ
        for pattern in self.exclusion_patterns:
            if pattern.search(text.strip()):  # matchではなくsearchを使用
                return True
        
        return False
    
    def _match_specific_patterns(self, text: str) -> Optional[ExtractedTheme]:
        """具体的パターンとのマッチング"""
        for category, patterns in self.specific_patterns.items():
            for pattern, theme, field in patterns:
                if pattern.search(text):
                    return ExtractedTheme(theme, field, 0.95)
        return None
    
    def _match_category_patterns(self, text: str) -> Optional[ExtractedTheme]:
        """カテゴリパターンとのマッチング（必ず2文節化）"""
        for category_name, (keywords, field) in self.category_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    # 必ず2文節形式にする
                    theme = self._make_two_clause_theme(keyword, text, category_name)
                    return ExtractedTheme(theme, field, 0.85)
        return None
    
    def _make_two_clause_theme(self, keyword: str, text: str, category: str) -> str:
        """キーワードを2文節形式のテーマに変換"""
        # 時代の場合
        if category == '時代':
            if '文化' in text:
                return f"{keyword}の文化"
            elif '政治' in text:
                return f"{keyword}の政治"
            elif '経済' in text:
                return f"{keyword}の経済"
            elif '社会' in text:
                return f"{keyword}の社会"
            else:
                return f"{keyword}の特徴"
        
        # 地域・都道府県・都市の場合
        elif category in ['地域', '都道府県', '都市']:
            if '産業' in text or '工業' in text:
                return f"{keyword}の産業"
            elif '農業' in text:
                return f"{keyword}の農業"
            elif '人口' in text:
                return f"{keyword}の人口"
            elif '気候' in text:
                return f"{keyword}の気候"
            elif '地形' in text:
                return f"{keyword}の地形"
            elif '交通' in text:
                return f"{keyword}の交通"
            elif '観光' in text:
                return f"{keyword}の観光"
            else:
                return f"{keyword}の特徴"
        
        # デフォルト
        return f"{keyword}の特徴"
    
    def _match_abstract_patterns(self, text: str) -> Optional[ExtractedTheme]:
        """抽象パターンとのマッチング"""
        for pattern, theme in self.abstract_patterns:
            if pattern.search(text):
                # 分野を推定
                field = self._estimate_field(text)
                return ExtractedTheme(theme, field, 0.75)
        return None
    
    def _fallback_extraction(self, text: str) -> ExtractedTheme:
        """フォールバック: 最も重要なキーワードを抽出して2文節化"""
        
        # 文脈なしでは意味不明な表現を検出
        meaningless_patterns = [
            '下線部', '新聞記事', '資料', 'この', 'その', '同年', '当時',
            'グラフ', '表', '図', '写真', '地図中'
        ]
        
        # これらの表現しか含まない場合はNone
        has_concrete_content = False
        for word in text.split():
            if len(word) > 2 and not any(pattern in word for pattern in meaningless_patterns):
                has_concrete_content = True
                break
        
        if not has_concrete_content:
            return ExtractedTheme(None, None, 0.0)
        
        # 名詞を抽出
        nouns = re.findall(r'[一-龥ァ-ヴー]{3,10}', text)
        
        # 除外語を削除
        exclude_words = {
            'について', '答えなさい', '選びなさい', '説明しなさい', 
            'として', 'あやまって', 'にあてはまる', '次のうち'
        }
        nouns = [n for n in nouns if n not in exclude_words]
        
        # 意味のある名詞がない場合
        if not nouns:
            return ExtractedTheme(None, None, 0.0)
        
        # 最も長い名詞を選択
        keyword = max(nouns, key=len)
        
        # あまりに一般的な語句は除外
        if keyword in ['内容', '仕組み', '特徴', '説明', '理由']:
            return ExtractedTheme(None, None, 0.0)
        
        field = self._estimate_field(text)
        
        # 2文節形式に変換
        if field == '歴史':
            theme = f"{keyword}の歴史"
        elif field == '地理':
            theme = f"{keyword}の特徴"
        elif field == '公民':
            theme = f"{keyword}の仕組み"
        else:
            # フィールドが不明な場合は、キーワードの性質から判断
            if any(suffix in keyword for suffix in ['憲法', '法', '制度', '会議']):
                theme = f"{keyword}の仕組み"
            elif any(suffix in keyword for suffix in ['時代', '戦争', '改革']):
                theme = f"{keyword}の歴史"
            else:
                theme = f"{keyword}の特徴"
        
        return ExtractedTheme(theme, field, 0.5)
    
    def _estimate_field(self, text: str) -> str:
        """テキストから分野を推定"""
        # 時代名があれば歴史
        time_keywords = ['時代', '幕府', '天皇', '将軍', '戦争', '改革']
        if any(k in text for k in time_keywords):
            return '歴史'
        
        # 地理キーワード
        geo_keywords = ['地方', '都道府県', '気候', '産業', '人口', '地形']
        if any(k in text for k in geo_keywords):
            return '地理'
        
        # 公民キーワード
        civics_keywords = ['憲法', '法律', '選挙', '国会', '内閣', '裁判']
        if any(k in text for k in civics_keywords):
            return '公民'
        
        return '総合'