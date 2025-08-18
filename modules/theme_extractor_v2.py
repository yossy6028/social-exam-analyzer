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

        # 用語カタログ（任意）
        self.terms_repo = None
        try:
            from .terms_repository import TermsRepository
            repo = TermsRepository()
            if repo.available():
                self.terms_repo = repo
        except Exception:
            self.terms_repo = None
        
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
            '歴史_人物': [
                (re.compile(r'源頼朝'), '源頼朝の業績', '歴史'),
                (re.compile(r'源義経'), '源義経の生涯', '歴史'),
                (re.compile(r'平清盛'), '平清盛の政治', '歴史'),
                (re.compile(r'足利尊氏'), '足利尊氏の政権', '歴史'),
                (re.compile(r'足利義満'), '足利義満の政治', '歴史'),
                (re.compile(r'織田信長'), '織田信長の統一事業', '歴史'),
                (re.compile(r'豊臣秀吉'), '豊臣秀吉の政策', '歴史'),
                (re.compile(r'徳川家康'), '徳川家康の統治', '歴史'),
                (re.compile(r'徳川家光'), '徳川家光の政策', '歴史'),
                (re.compile(r'徳川吉宗'), '徳川吉宗の改革', '歴史'),
                (re.compile(r'田沼意次'), '田沼意次の政治', '歴史'),
                (re.compile(r'松平定信'), '松平定信の改革', '歴史'),
                (re.compile(r'水野忠邦'), '水野忠邦の改革', '歴史'),
                (re.compile(r'西郷隆盛'), '西郷隆盛の功績', '歴史'),
                (re.compile(r'大久保利通'), '大久保利通の政策', '歴史'),
                (re.compile(r'木戸孝允'), '木戸孝允の業績', '歴史'),
                (re.compile(r'伊藤博文'), '伊藤博文の政治', '歴史'),
                (re.compile(r'板垣退助'), '板垣退助の自由民権運動', '歴史'),
                (re.compile(r'大隈重信'), '大隈重信の政党政治', '歴史'),
                (re.compile(r'福沢諭吉'), '福沢諭吉の思想', '歴史'),
                (re.compile(r'聖徳太子'), '聖徳太子の政治', '歴史'),
                (re.compile(r'中大兄皇子'), '中大兄皇子の改革', '歴史'),
                (re.compile(r'聖武天皇'), '聖武天皇の政治', '歴史'),
                (re.compile(r'桓武天皇'), '桓武天皇の政策', '歴史'),
                (re.compile(r'藤原道長'), '藤原道長の摂関政治', '歴史'),
                (re.compile(r'藤原頼通'), '藤原頼通の時代', '歴史'),
                (re.compile(r'白河上皇'), '白河上皇の院政', '歴史'),
                (re.compile(r'後白河上皇'), '後白河上皇の院政', '歴史'),
                (re.compile(r'北条時宗'), '北条時宗の政治', '歴史'),
                (re.compile(r'北条泰時'), '北条泰時の政策', '歴史'),
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
            '地理_関西域': [
                (re.compile(r'大阪市|夢洲|関西国際空港'), '大阪府の地理', '地理'),
                (re.compile(r'阪神工業地帯'), '阪神工業地帯の特徴', '地理'),
                (re.compile(r'東大阪市|堺市|千里|泉北|淀川|大淀|淀'), '関西地方の地理', '地理'),
                (re.compile(r'万博|大阪・関西万博'), '大阪・関西万博', '地理'),
            ],
            '歴史_医薬戦争': [
                (re.compile(r'アヘン戦争'), 'アヘン戦争の影響', '歴史'),
                (re.compile(r'征露丸|クレオソート'), '戦争と医薬の関係', '歴史'),
                (re.compile(r'毒ガス'), '毒ガスと医薬研究', '歴史'),
            ],
            '歴史_正倉院医薬': [
                (re.compile(r'正倉院|種々薬帳'), '正倉院と医薬', '歴史'),
                (re.compile(r'鑑真'), '鑑真の時代', '歴史'),
            ],
            '公民_国連': [
                (re.compile(r'国連.*加盟|加盟国|国際連合'), '国際連合の加盟国数', '公民'),
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
                (re.compile(r'核兵器.*?条約'), '核兵器禁止条約の内容', '公民'),
                (re.compile(r'核.*?禁止'), '核兵器禁止条約の内容', '公民'),
                (re.compile(r'NPT'), '核不拡散条約の内容', '公民'),
                (re.compile(r'NATO'), 'NATOの役割', '公民'),
                (re.compile(r'EU|欧州連合'), 'EUの仕組み', '公民'),
                (re.compile(r'ASEAN'), 'ASEANの役割', '公民'),
                (re.compile(r'TPP'), 'TPPの内容', '公民'),
            ],
            '社会問題': [
                (re.compile(r'空き家'), '空き家問題の現状', '公民'),
                (re.compile(r'少子高齢化'), '少子高齢化の影響', '公民'),
                (re.compile(r'男女.*?(平等|共同参画|対等)'), '男女共同参画社会の推進', '公民'),
                (re.compile(r'SDGs'), 'SDGsの目標', '公民'),
                (re.compile(r'持続可能な開発'), '持続可能な開発目標', '公民'),
                (re.compile(r'地球温暖化'), '地球温暖化の対策', '公民'),
                (re.compile(r'気候変動'), '気候変動の影響', '公民'),
                (re.compile(r'環境破壊'), '環境破壊の現状', '公民'),
                (re.compile(r'再生可能エネルギー'), '再生可能エネルギーの活用', '公民'),
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
            (re.compile(r'グラフ.*?(分析|読み取)'), 'グラフの分析'),
            (re.compile(r'地図.*?(読み取り|から)'), '地図の読み取り'),
            (re.compile(r'地図中.*?(都市|地域|県)'), '地図の読み取り'),  # 「地図中の都市」対策
            (re.compile(r'年表.*?読み取り'), '年表の読み取り'),
            (re.compile(r'統計.*?分析'), '統計の分析'),
            (re.compile(r'図表.*?読み取り'), '図表の読み取り'),
            (re.compile(r'表から.*?読み取'), '統計表の分析'),  # 「表から読み取れること」対策
            (re.compile(r'次の表.*?(読み取|説明)'), '統計表の分析'),  # 「次の表から読み取れること」対策
            
            # 図表問題の強化
            (re.compile(r'次の図.*?(見て|答え|選び)'), '図の読み取り'),
            (re.compile(r'次の地図.*?(見て|答え|選び)'), '地図の読み取り'),
            (re.compile(r'次の雨温図.*?(見て|答え|選び)'), '雨温図の読み取り'),
            (re.compile(r'次の地形図.*?(見て|答え|選び)'), '地形図の読み取り'),
            (re.compile(r'次の写真.*?(見て|答え|選び)'), '写真の読み取り'),
            (re.compile(r'図中.*?(記号|地図記号)'), '図の読み取り'),
            (re.compile(r'地図中.*?(記号|地図記号)'), '地図の読み取り'),
            (re.compile(r'地形図.*?(読み取|見て)'), '地形図の読み取り'),
            (re.compile(r'雨温図.*?(見て|答え)'), '雨温図の読み取り'),
            (re.compile(r'図中の.*?地図記号'), '地図記号の読み取り'),
            (re.compile(r'地図記号.*?何を示している'), '地図記号の読み取り'),
            
            # 統計・データ問題の強化
            (re.compile(r'表.*?(都道府県|県|市|町|村)'), '統計表の分析'),
            (re.compile(r'統計.*?(都道府県|県|市|町|村)'), '統計の分析'),
            (re.compile(r'データ.*?(都道府県|県|市|町|村)'), 'データの分析'),
            (re.compile(r'表.*?(頭数|生産量|人口|面積)'), '統計表の分析'),
            (re.compile(r'都道府県別.*?(頭数|生産量|人口|面積)'), '統計表の分析'),
            
            # 平野・地形問題の強化
            (re.compile(r'平野.*?(説明|特徴)'), '平野の特徴'),
            (re.compile(r'地形.*?(説明|特徴)'), '地形の特徴'),
            (re.compile(r'河川.*?(流れ|特徴)'), '河川の特徴'),
            (re.compile(r'気候.*?(特徴|影響)'), '気候の特徴'),
            
            # 産業・農業問題の強化
            (re.compile(r'農業.*?(特徴|作物)'), '農業の特徴'),
            (re.compile(r'工業.*?(特徴|製品)'), '工業の特徴'),
            (re.compile(r'産業.*?(特徴|発展)'), '産業の特徴'),
            
            # 地図記号問題の強化
            (re.compile(r'図中の.*?地図記号'), '地図記号の読み取り'),
            (re.compile(r'地図記号.*?何を示している'), '地図記号の読み取り'),
            (re.compile(r'図中の.*?記号.*?何を示している'), '地図記号の読み取り'),
            (re.compile(r'図中.*?記号'), '図の読み取り'),
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
            # 空欄補充・穴埋め（単独の場合のみ除外）
            re.compile(r'^(空欄補充|穴埋め|空らん)$'),
            # 記号や括弧のみの内容
            re.compile(r'^【[あ-んア-ン]】$|^\([あ-んア-ン]\)$'),
            # 【】にあてはまる形式のみ
            re.compile(r'^【[あ-んア-ン]】.*?にあてはまる$'),  # 【い】にあてはまる
            re.compile(r'^にあてはまる.*?(人物名|語句|言葉)$'),  # にあてはまる人物名
            
            # === 「次の〜」パターン ===
            # 図表等の紹介だけで具体性がないものは除外（読み取り/分析/説明がなければ除外）
            # ただし、問題文として機能するものは除外しない
            re.compile(r'^次の(図|グラフ|資料|写真|地図|雨温図)(?!.*?(読み取|分析|説明|答え|選び|見て))$'),
            re.compile(r'^次の表(?!.*?(読み取|分析|説明|答え|選び|見て))$'),
            re.compile(r'^以下の(うち|中から|選択肢)$'),  # 以下のうちなど
            re.compile(r'^次のア〜$'),  # 次のア〜エからなど
            re.compile(r'から選べ$'),  # 「〜から選べ」で終わる文
            
            # === 下線部関連 ===
            # 下線部単独、または下線部+番号/記号のみを除外
            re.compile(r'^下線部[①-⑳⑪-⑯⑰-⑳❶-❿⓫-⓴]?$'),  # 下線部①など
            re.compile(r'^下線部\d+$'),  # 下線部6など
            re.compile(r'^下線部の(内容|特徴|説明|史料)'),  # 下線部の特徴など
            re.compile(r'^下線部.*?として'),  # 下線部の史料としてなど
            re.compile(r'^傍線部'),  # 傍線部も同様
            
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
            # 社会科に無関係な用語（産業文脈で有用な「電子機器」は除外対象から外す）
            re.compile(r'(電気機械器具|コンピュータ|スマートフォン|携帯電話|グリーンマーク)'),
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
            # 「具体的な」で始まる指示
            re.compile(r'^具体的な'),
            re.compile(r'を用いて.*事例'),  # 「〜を用いて〜事例」パターン
            
            # === 問題解答指示 ===
            # 解答形式の指定（単独の場合のみ除外）
            re.compile(r'^(漢字で答え|ひらがなで答え|カタカナで答え)$'),
            re.compile(r'^(記号で答え|番号で答え|選択肢)$'),
            re.compile(r'^(正しい|適切な|誤って|間違って).*?(選び|答え)$'),
            
            # === 地図・図表の参照（文脈なしでは無意味） ===
            # 地図中の〜（位置指定）- ただし都市名や地域名がある場合は除外しない
            re.compile(r'^地図中の(?!.*?(都市|地域|県|国|山|川|平野))'),
            re.compile(r'^(図中の|表中の|グラフ中の)(?!.*?(読み取|分析|説明))'),
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

            # === その他の参照テキスト（内容が不十分）===
            # 新聞記事の内容など、教材参照のみの断片
            re.compile(r'新聞記事の内容'),
            # 「以下の表」を含むが読み取り等が無い場合は除外
            re.compile(r'以下の表(?!.*?(読み取|分析|説明))$'),
        ]
    
    def extract(self, text: str) -> ExtractedTheme:
        """
        テーマを抽出するメインメソッド
        
        階層的アプローチ:
        1. 用語カタログからのテーマ抽出（最優先）
        2. 除外チェック
        3. 具体的パターンのマッチング
        4. カテゴリパターンのマッチング
        5. 抽象パターンのマッチング
        6. フォールバック処理
        """
        
        # ステップ0: 用語カタログからのテーマ抽出（最優先）
        if self.terms_repo is not None:
            # 用語カタログからテーマを提案
            theme_suggestion = self.terms_repo.suggest_theme(text)
            if theme_suggestion:
                theme, field = theme_suggestion
                return ExtractedTheme(theme, self._field_label_to_category(field), 0.9)
            
            # 時代推定を試みる（歴史の具体化に寄与）
            period = self.terms_repo.infer_history_period(text)
            if period:
                # 文脈語で2文節化
                if '文化' in text:
                    theme = f"{period}の文化"
                elif '政治' in text:
                    theme = f"{period}の政治"
                elif '経済' in text:
                    theme = f"{period}の経済"
                elif '社会' in text:
                    theme = f"{period}の社会"
                else:
                    theme = f"{period}の特徴"
                return ExtractedTheme(theme, '歴史', 0.85)
        
        # ステップ0.5: 選択肢からの共起判定（空欄/選択問題でもテーマを推定）
        opt_cluster = self._match_options_cluster(text)
        if opt_cluster:
            return opt_cluster

        # ステップ1: 除外チェック（ただし上記で強い根拠がある場合は回避済み）
        if self._should_exclude(text):
            return ExtractedTheme(None, None, 0.0)

        # ステップ1.5: キーワードから具体的なテーマを生成
        refined = self._refine_theme_from_keywords(text)
        if refined:
            return refined

        # ステップ2: クラスタ（複数語の共起による高次テーマ）
        cluster_result = self._match_cluster_patterns(text)
        if cluster_result:
            return cluster_result
        
        # ステップ2.5: 具体的パターンのマッチング
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
        # 短い固有名詞や重要用語も処理する
        if '答え' in text or '選び' in text:
            return ExtractedTheme(None, None, 0.0)
            
        return self._fallback_extraction(text)

    def _refine_theme_from_keywords(self, text: str) -> Optional[ExtractedTheme]:
        """キーワードから具体的なテーマを生成"""
        import re
        
        # デバッグ: テキストの内容を確認
        # logger.debug(f"_refine_theme_from_keywords: text='{text}'")
        
        # まず特定のキーワードを直接マッチング
        if '鎌倉幕府' in text:
            # logger.debug("鎌倉幕府マッチ!")
            return ExtractedTheme('鎌倉幕府の成立', '歴史', 0.9)
        if '室町幕府' in text:
            return ExtractedTheme('室町幕府の政治', '歴史', 0.9)
        if '江戸幕府' in text or '徳川幕府' in text:
            return ExtractedTheme('江戸幕府の政治', '歴史', 0.9)
        if '江戸時代' in text:
            if '身分' in text:
                return ExtractedTheme('江戸時代の身分制度', '歴史', 0.95)
            return ExtractedTheme('江戸時代の特徴', '歴史', 0.9)
        if '明治維新' in text:
            return ExtractedTheme('明治維新の改革', '歴史', 0.9)
        if '大日本帝国憲法' in text:
            return ExtractedTheme('大日本帝国憲法の内容', '歴史', 0.9)
        if '日本国憲法' in text:
            return ExtractedTheme('日本国憲法の内容', '公民', 0.9)
        if '人口ピラミッド' in text:
            return ExtractedTheme('人口ピラミッドの分析', '地理', 0.95)
        
        # 年度・西暦の処理
        m_year = re.search(r'(\d{4})年', text)
        if m_year:
            year = m_year.group(1)
            # 周辺語で具体化
            if 'オリンピック' in text:
                return ExtractedTheme(f'{year}年のオリンピック', '歴史', 0.7)
            if '万博' in text or '博覧会' in text:
                return ExtractedTheme(f'{year}年の万博', '地理', 0.7)
            if '選挙' in text:
                return ExtractedTheme(f'{year}年の選挙', '公民', 0.7)
            if '条約' in text:
                return ExtractedTheme(f'{year}年の条約', '歴史', 0.7)
            if '戦争' in text or '大戦' in text:
                return ExtractedTheme(f'{year}年の戦争', '歴史', 0.75)
            return ExtractedTheme(f'{year}年の出来事', '総合', 0.6)

        # 公民の代表用語（より具体化）
        civics_map = [
            ('プライバシー', 'プライバシーの権利'),
            ('オンブズマン', 'オンブズマン制度の仕組み'),
            ('国土交通省', '国土交通省の役割'),
            ('市町村合併', '市町村合併の目的'),
            ('合併', '市町村合併の目的'),
            ('裁判員', '裁判員制度の仕組み'),
            ('個人情報', '個人情報保護の仕組み'),
        ]
        for key, theme in civics_map:
            if key in text:
                return ExtractedTheme(theme, '公民', 0.9)

        # 数字のみ参照の除外（例: 「12について」）
        if re.fullmatch(r'\s*\d{1,3}\s*(について)?\s*', text):
            return ExtractedTheme(None, None, 0.0)

        # 固有名詞の抽出（優先度順）
        patterns = [
            (r'([^、。\s]{2,4}時代)', '歴史', 'の特徴'),
            (r'([^、。\s]{2,6}幕府)', '歴史', 'の成立'),
            (r'([^、。\s]{2,8}(?:の乱|の変|戦争|条約))', '歴史', ''),
            (r'(第\d+次[^、。\s]+)', '歴史', ''),
            (r'([^、。\s]{2,4}(?:天皇|上皇|法皇))', '歴史', 'の政治'),
            (r'([^、。\s]{2,6}(?:県|府|都|道))', '地理', 'の特徴'),
            (r'([^、。\s]{2,6}(?:平野|盆地|山地|高原))', '地理', 'の地形'),
            (r'([^、。\s]{2,8}憲法)', '公民', 'の内容'),
            (r'([^、。\s]{2,6}(?:選挙|投票))', '公民', 'の仕組み'),
        ]
        
        for pattern, field, suffix in patterns:
            matches = re.findall(pattern, text)
            if matches:
                theme = matches[0] + suffix if suffix else matches[0]
                return ExtractedTheme(theme, field, 0.85)
        
        # 人名パターン（フルネーム）
        person_pattern = re.findall(r'([一-龥]{2,4}[\s　]?[一-龥]{2,4})', text)
        if person_pattern:
            for person in person_pattern:
                # 歴史上の重要人物リスト
                if any(name in person for name in ['源頼朝', '平清盛', '織田信長', '豊臣秀吉', '徳川家康', 
                                                    '聖徳太子', '藤原道長', '足利尊氏', '西郷隆盛', '伊藤博文']):
                    return ExtractedTheme(f'{person}の業績', '歴史', 0.85)
        
        # 重要な事件・出来事
        events = ['大化の改新', '承久の乱', '応仁の乱', '本能寺の変', '関ヶ原の戦い', 
                 '明治維新', '太平洋戦争', '日露戦争', '第一次世界大戦', '第二次世界大戦']
        for event in events:
            if event in text:
                return ExtractedTheme(event, '歴史', 0.9)
        
        # 地理的特徴
        # 国名の具体化
        countries = ['フィリピン', 'ウルグアイ', 'ブラジル', 'アメリカ合衆国', 'アメリカ', '中国', 'インド']
        for c in countries:
            if c in text:
                if any(k in text for k in ['産業', '工業', '農業', '貿易']):
                    return ExtractedTheme(f'{c}の産業', '地理', 0.8)
                if any(k in text for k in ['人口', '少子', '高齢']):
                    return ExtractedTheme(f'{c}の人口', '地理', 0.75)
                if any(k in text for k in ['気候', '雨温図']):
                    return ExtractedTheme(f'{c}の気候', '地理', 0.75)
                return ExtractedTheme(f'{c}の地理的特徴', '地理', 0.75)
        if '人口ピラミッド' in text:
            return ExtractedTheme('人口ピラミッドの分析', '地理', 0.9)
        if '雨温図' in text:
            return ExtractedTheme('雨温図の読み取り', '地理', 0.9)
        if '地図' in text and ('読み取' in text or '特徴' in text):
            return ExtractedTheme('地図の読み取り', '地理', 0.85)
        if 'グラフ' in text and ('分析' in text or '読み取' in text):
            return ExtractedTheme('グラフの分析', '地理', 0.85)
        
        return None

    def _match_options_cluster(self, text: str) -> Optional[ExtractedTheme]:
        """ア/イ/ウ/エ の選択肢から強いテーマ候補を推定"""
        import re
        options: List[str] = []
        # 代表的な選択肢フォーマット（全角/半角ドット/カッコ/コロン/読点等）
        patterns = [
            # 典型: ア. テキスト / （ア） テキスト / ア：テキスト / ア、テキスト
            re.compile(r'[（(]?([アイウエ])[）)]?[\s\.:：、,，)]\s*([^\n\r]+)'),
            re.compile(r'[（(]?([あいうえ])[）)]?[\s\.:：、,，)]\s*([^\n\r]+)'),
            # 区切り弱いOCR崩れ: 行頭カタカナ + 空白 + 文章
            re.compile(r'^[\s　]*([アイウエ])\s+([^\n\r]+)', re.MULTILINE),
        ]
        for pat in patterns:
            for m in pat.finditer(text):
                opt_text = (m.group(2) or '').strip()
                if opt_text:
                    options.append(opt_text)
        if not options:
            return None
        # 選択肢だけでクラスタ判定
        joined = '、'.join(options)
        cluster = self._match_cluster_patterns(joined)
        if cluster:
            return cluster
        # 用語カタログによる分野推定
        if getattr(self, 'terms_repo', None) is not None:
            hit = self.terms_repo.suggest_theme(joined)
            if hit:
                theme, field = hit
                return ExtractedTheme(theme, self._field_label_to_category(field), 0.8)
        return None

    def _match_cluster_patterns(self, text: str) -> Optional[ExtractedTheme]:
        """複数の関連語が同時に出るときに、より高次の主題を設定"""
        t = text
        count = 0
        temples = [
            '延暦寺', '東大寺', '法隆寺', '薬師寺', '平等院', '金閣寺', '銀閣寺', '清水寺',
            '唐招提寺', '興福寺', '東寺', '中尊寺', '比叡山', '高野山'
        ]
        count = sum(1 for w in temples if w in t)
        if count >= 2:
            # 代表的寺院が複数同時に出現 → 文化史の俯瞰テーマに集約
            return ExtractedTheme('日本の中世の寺院', '歴史', 0.9)

        # 産業クラスタ（例: 複数の工業製品用語）
        industry_terms = ['半導体', '鉄鋼', '自動車', '電子機器', '石油化学', 'プラスチック']
        if sum(1 for w in industry_terms if w in t) >= 2:
            return ExtractedTheme('日本の工業の特徴', '地理', 0.85)

        # 人口・統計クラスタ
        stats_terms = ['人口ピラミッド', '合計特殊出生率', '高齢化率', '年少人口', '生産年齢人口']
        if sum(1 for w in stats_terms if w in t) >= 2:
            return ExtractedTheme('人口統計の分析', '公民', 0.85)

        # 古典文学の代表作群
        classics = ['伊勢物語', '源氏物語', '竹取物語', '平家物語']
        if sum(1 for w in classics if w in t) >= 2:
            return ExtractedTheme('日本の古典文学', '歴史', 0.85)

        # 中国の王朝名
        dynasties = ['夏', '殷', '周', '秦', '漢', '隋', '唐', '宋', '元', '明', '清']
        if sum(1 for w in dynasties if w in t) >= 2:
            return ExtractedTheme('中国の王朝', '歴史', 0.8)

        # 日本仏教の代表的高僧
        monks = ['栄西', '道元', '日蓮', '法然', '親鸞', '最澄', '空海']
        if sum(1 for w in monks if w in t) >= 2:
            return ExtractedTheme('日本の仏教宗派', '歴史', 0.8)

        # 近現代アジア史の出来事群
        asia_modern = ['韓国併合', '五・四運動', '二十一条の要求', '柳条湖事件']
        if sum(1 for w in asia_modern if w in t) >= 2:
            return ExtractedTheme('近現代アジア史の出来事', '歴史', 0.8)

        # 近現代世界史の出来事群
        world_modern = ['ヴェルサイユ条約', 'ワシントン会議', 'ロカルノ条約', 'ケロッグ・ブリアン条約', '国際連盟', '大西洋憲章']
        if sum(1 for w in world_modern if w in t) >= 2:
            return ExtractedTheme('近現代世界史の出来事', '歴史', 0.8)

        return None
    
    def _should_exclude(self, text: str) -> bool:
        """除外すべきテキストかどうか判定"""
        cleaned_text = text.strip()
        
        # 極端に短すぎる（2文字以下）
        if len(cleaned_text) <= 2:
            return True
        
        # 除外パターンにマッチ
        for pattern in self.exclusion_patterns:
            if pattern.search(cleaned_text):
                try:
                    # ログに除外理由（パターン）を記録（デバッグ容易化）
                    logger.info(f"テーマ除外: pattern='{pattern.pattern}' text='{cleaned_text[:40]}...'")
                except Exception:
                    pass
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
        import re

        # 特殊な資料読み取り問題の処理
        if '地図中' in text and ('都市' in text or '地域' in text or '県' in text):
            return ExtractedTheme('地図の読み取り', '地理', 0.7)
        elif ('次の表' in text and (('読み取' in text) or ('説明' in text) or ('分析' in text))) or ('表から読み取れる' in text):
            # 「次の表」は読み取り・説明・分析の明示がある場合のみ有効
            return ExtractedTheme('統計表の分析', '総合', 0.7)
        elif 'グラフ' in text and '読み取' in text:
            return ExtractedTheme('グラフの分析', '総合', 0.7)

        # 近現代アジア史（単発語でも俯瞰テーマへ）
        for w in ['韓国併合', '五・四運動', '二十一条の要求', '柳条湖事件']:
            if w in text:
                return ExtractedTheme('近現代アジア史の出来事', '歴史', 0.75)

        # 近現代世界史（単発語でも俯瞰テーマへ）
        for w in ['ヴェルサイユ条約', 'ワシントン会議', 'ロカルノ条約', 'ケロッグ・ブリアン条約', '国際連盟', '大西洋憲章']:
            if w in text:
                return ExtractedTheme('近現代世界史の出来事', '歴史', 0.75)

        # 具体キーワードからの即時テーマ化（弱フォールバック）
        # 気候・雨温図
        if '雨温図' in text:
            city = None
            m = re.search(r'(大阪市|大阪|京都市|京都|神戸市|神戸|那覇市|那覇|札幌市|札幌|仙台市|仙台|名古屋市|名古屋|福岡市|福岡|広島市|広島|新潟市|新潟|静岡市|静岡|浜松市|浜松)', text)
            if m:
                city = m.group(1)
                return ExtractedTheme(f'{city}の気候', '地理', 0.7)
            return ExtractedTheme('気候の特徴', '地理', 0.6)

        # 国連加盟国数
        if '国連' in text and ('加盟' in text or '加盟国' in text):
            return ExtractedTheme('国際連合の加盟国数', '公民', 0.7)

        # 万博・夢洲・大阪
        if ('万博' in text and ('大阪' in text or '関西' in text)) or '夢洲' in text:
            return ExtractedTheme('大阪・関西万博', '地理', 0.7)

        # 地域固有の産業・空港・工業地帯
        if '阪神工業地帯' in text:
            return ExtractedTheme('阪神工業地帯の特徴', '地理', 0.7)
        if '地場産業' in text:
            return ExtractedTheme('地場産業の発展', '地理', 0.6)
        if '関西国際空港' in text:
            return ExtractedTheme('関西国際空港の役割', '地理', 0.7)

        # 関西域の地名・河川
        if any(w in text for w in ['淀川', '大淀', '淀', '千里', '泉北', '東大阪市', '堺市']):
            return ExtractedTheme('関西地方の地理', '地理', 0.65)

        # OCRで断片的になった文から重要語を抽出
        # 戦いや事件
        battles = re.findall(r'([ぁ-んァ-ヴー一-龥]+の戦い)', text)
        if battles:
            return ExtractedTheme(f"{battles[0]}の経過", '歴史', 0.6)
        
        incidents = re.findall(r'([ぁ-んァ-ヴー一-龥]+の乱)', text)
        if incidents:
            return ExtractedTheme(f"{incidents[0]}の背景", '歴史', 0.6)
        
        # 人物名を探す（〜が、〜は、〜の）
        person_pattern = re.findall(r'([ぁ-んァ-ヴー一-龥]{2,4})[がはの]', text)
        for person in person_pattern:
            if person in ['源頼朝', '織田信長', '豊臣秀吉', '徳川家康', '聖徳太子', '藤原道長']:
                return ExtractedTheme(f"{person}の業績", '歴史', 0.6)
        
        # 時代を探す
        period_pattern = re.findall(r'([ぁ-んァ-ヴー一-龥]+時代)', text)
        if period_pattern:
            return ExtractedTheme(f"{period_pattern[0]}の特徴", '歴史', 0.6)
        
        # 地名・県名を探す 
        prefecture_pattern = re.findall(r'([ぁ-んァ-ヴー一-龥]{2,4}[県府])', text)
        if prefecture_pattern:
            return ExtractedTheme(f"{prefecture_pattern[0]}の特徴", '地理', 0.6)
            
        city_pattern = re.findall(r'([ぁ-んァ-ヴー一-龥]{2,4}市)', text)
        if city_pattern:
            return ExtractedTheme(f"{city_pattern[0]}の特徴", '地理', 0.6)
        
        # 短い固有名詞や用語の場合の特別処理
        if 2 <= len(text) <= 10:
            # 歴史上の人物名
            if text in ['源頼朝', '織田信長', '豊臣秀吉', '徳川家康', '西郷隆盛', '伊藤博文', '明治天皇']:
                return ExtractedTheme(f"{text}の業績", '歴史', 0.8)
            # 歴史的事件
            elif text in ['米騒動', '大塚一揆', '打ちこわし', '大逆事件']:
                return ExtractedTheme(f"{text}の背景", '歴史', 0.8)
            # 環境・社会問題
            elif '環境' in text or '問題' in text:
                return ExtractedTheme(f"{text}の対策", '公民', 0.7)
            # 条約・制度
            elif '条約' in text or '制度' in text:
                return ExtractedTheme(f"{text}の内容", '公民', 0.7)
            # 地名・地域
            elif any(suffix in text for suffix in ['県', '市', '町', '村', '地方', '平野', '山地', '海峽']):
                return ExtractedTheme(f"{text}の特徴", '地理', 0.7)
            # その他の短い用語
            else:
                field = self._estimate_field(text)
                if field == '歴史':
                    suffix = 'の内容'
                elif field == '地理':
                    suffix = 'の特徴'
                elif field == '公民':
                    suffix = 'の仕組み'
                else:
                    suffix = 'の内容'
                return ExtractedTheme(f"{text}{suffix}", field, 0.6)
        
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
        
        # 2文節形式に変換（一般語の除外）
        if keyword in ['社会', '政治', '経済', '制度', '制定']:
            # 文脈が弱い一般語は除外
            return ExtractedTheme(None, None, 0.0)
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

    def _field_label_to_category(self, label: str) -> str:
        mapping = {
            'history': '歴史',
            'geography': '地理',
            'civics': '公民',
        }
        return mapping.get(label, '総合')
