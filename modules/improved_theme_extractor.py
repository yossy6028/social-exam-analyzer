"""
改善されたテーマ抽出システム（社会科目版）
問題文と選択肢から共通キーワードを抽出し、最小単位のテーマを特定
"""

import re
from typing import Optional, List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import Counter


@dataclass
class ThemeExtractionResult:
    """テーマ抽出結果"""
    theme: Optional[str]
    confidence: float
    category: Optional[str]


class ImprovedThemeExtractor:
    """改善されたテーマ抽出クラス（社会科目版）"""
    
    def __init__(self):
        self.theme_keyword_map = self._init_theme_keyword_map()
        self.category_patterns = self._init_category_patterns()
        self.exclusion_words = self._init_exclusion_words()
        
    def _init_theme_keyword_map(self) -> Dict[str, Dict[str, List[str]]]:
        """テーマとキーワードのマッピング"""
        return {
            '歴史': {
                # 時代別
                '縄文時代': ['縄文', '土器', '竪穴', '土偶', '貝塚', '狩猟', '採集', '打製石器'],
                '弥生時代': ['弥生', '稲作', '水田', '高床', '銅鐸', '環濠集落', '倭国', '邪馬台国'],
                '古墳時代': ['古墳', '前方後円墳', '埴輪', '豪族', '大和政権', '渡来人'],
                '飛鳥時代': ['聖徳太子', '推古天皇', '冠位十二階', '十七条憲法', '遣隋使', '法隆寺', '飛鳥'],
                '奈良時代': ['平城京', '東大寺', '大仏', '聖武天皇', '遣唐使', '天平文化', '万葉集'],
                '平安時代': ['平安京', '藤原', '摂関政治', '国風文化', '源氏物語', '枕草子', '院政', '平氏'],
                '鎌倉時代': ['源頼朝', '北条', '執権', '御成敗式目', '元寇', '鎌倉幕府', '守護', '地頭'],
                '室町時代': ['足利', '金閣寺', '銀閣寺', '応仁の乱', '戦国大名', '室町幕府', '勘合貿易'],
                '戦国時代': ['織田信長', '豊臣秀吉', '楽市楽座', '検地', '刀狩', '長篠の戦い', '本能寺'],
                '江戸時代': ['徳川家康', '参勤交代', '鎖国', '寺子屋', '浮世絵', '歌舞伎', '蘭学', '幕末'],
                '明治時代': ['明治維新', '文明開化', '富国強兵', '地租改正', '廃藩置県', '日清戦争', '日露戦争'],
                '大正時代': ['大正デモクラシー', '第一次世界大戦', '米騒動', '普通選挙', '関東大震災'],
                '昭和時代': ['満州事変', '日中戦争', '太平洋戦争', '終戦', '日本国憲法', '高度経済成長', 'オイルショック'],
                '平成時代': ['バブル', '阪神淡路大震災', '東日本大震災', 'IT革命', 'グローバル化'],
                
                # 重要な出来事・制度
                '大化の改新': ['中大兄皇子', '中臣鎌足', '蘇我入鹿', '公地公民', '班田収授', '租庸調'],
                '平城京遷都': ['元明天皇', '710年', '奈良', '藤原京'],
                '平安京遷都': ['桓武天皇', '794年', '京都', '長岡京'],
                '承久の乱': ['後鳥羽上皇', '北条義時', '執権政治', '六波羅探題'],
                '建武の新政': ['後醍醐天皇', '足利尊氏', '新田義貞', '南北朝'],
                '応仁の乱': ['細川', '山名', '足利義政', '東軍', '西軍'],
                '本能寺の変': ['織田信長', '明智光秀', '1582年', '天下統一'],
                '関ヶ原の戦い': ['徳川家康', '石田三成', '1600年', '東軍', '西軍'],
                '明治維新': ['大政奉還', '王政復古', '戊辰戦争', '五箇条の御誓文', '版籍奉還'],
            },
            '地理': {
                # 都道府県・地域
                '北海道': ['札幌', '函館', '旭川', '酪農', '漁業', 'じゃがいも', '雪まつり', '知床'],
                '青森': ['りんご', 'ねぶた', '津軽', '八戸', '三内丸山遺跡', 'ホタテ', 'ねぶた祭り', 'りんご生産', '生産量日本一'],
                '東京': ['首都', '23区', '多摩', '新宿', '渋谷', '浅草', 'スカイツリー', '皇居'],
                '京都': ['古都', '金閣寺', '清水寺', '祇園', '嵐山', '伏見稲荷', '舞妓'],
                '大阪': ['商都', '道頓堀', '通天閣', '大阪城', 'たこ焼き', '商人', '天下の台所'],
                '沖縄': ['那覇', '首里城', '美ら海', 'さとうきび', '基地', '琉球', 'サンゴ礁'],
                
                # 地理的特徴
                '関東地方': ['東京', '神奈川', '千葉', '埼玉', '茨城', '栃木', '群馬', '首都圏'],
                '近畿地方': ['大阪', '京都', '兵庫', '奈良', '和歌山', '滋賀', '関西'],
                '中部地方': ['愛知', '岐阜', '静岡', '長野', '山梨', '新潟', '富山', '石川', '福井'],
                '三大都市圏': ['東京', '大阪', '名古屋', '首都圏', '関西圏', '中京圏'],
                '日本アルプス': ['飛騨山脈', '木曽山脈', '赤石山脈', '北アルプス', '中央アルプス', '南アルプス'],
                '瀬戸内海': ['瀬戸内', '内海', '多島海', '瀬戸大橋', '明石海峡大橋', 'しまなみ海道'],
                
                # 産業・特産品
                '稲作': ['米', '水田', '田んぼ', 'コシヒカリ', 'ササニシキ', '二期作', '二毛作'],
                '漁業': ['漁港', '水揚げ', 'マグロ', 'カツオ', 'サンマ', 'イカ', '養殖'],
                '工業地帯': ['京浜', '中京', '阪神', '北九州', '太平洋ベルト', 'コンビナート'],
                '伝統工芸': ['西陣織', '輪島塗', '有田焼', '益子焼', '南部鉄器', '京友禅'],
            },
            '公民': {
                # 政治制度
                '日本国憲法': ['憲法', '基本的人権', '国民主権', '平和主義', '三大原則', '改正'],
                '三権分立': ['立法', '行政', '司法', '国会', '内閣', '裁判所', 'チェック'],
                '選挙制度': ['選挙', '投票', '比例代表', '小選挙区', '参議院', '衆議院', '選挙権'],
                '国会': ['衆議院', '参議院', '法律', '予算', '条約', '国会議員', '通常国会'],
                '内閣': ['内閣総理大臣', '国務大臣', '閣議', '行政', '内閣府', '省庁'],
                '裁判所': ['最高裁判所', '地方裁判所', '裁判官', '司法', '違憲審査', '三審制'],
                '地方自治': ['都道府県', '市町村', '知事', '市長', '議会', '条例', '地方税'],
                
                # 経済
                '市場経済': ['需要', '供給', '価格', '競争', '独占', '寡占', '市場'],
                '財政': ['税金', '予算', '歳入', '歳出', '国債', '地方債', '消費税'],
                '金融': ['日本銀行', '金利', '為替', '株式', '債券', '投資', '預金'],
                '労働': ['雇用', '失業', '賃金', '労働組合', '働き方改革', 'ブラック企業'],
                '社会保障': ['年金', '医療保険', '介護保険', '生活保護', '福祉', '少子高齢化'],
                
                # 国際関係
                '国際連合': ['国連', '安全保障理事会', '総会', 'UNESCO', 'WHO', 'PKO'],
                '国際協力': ['ODA', 'NGO', 'NPO', 'ボランティア', '開発援助', 'JICA'],
                '貿易': ['輸出', '輸入', '関税', 'FTA', 'EPA', 'TPP', 'WTO'],
                '環境問題': ['地球温暖化', '温室効果ガス', 'CO2', '京都議定書', 'パリ協定', 'SDGs'],
            }
        }
    
    def _init_category_patterns(self) -> Dict[str, List[re.Pattern]]:
        """カテゴリー判定パターン"""
        return {
            '歴史': [
                re.compile(r'(時代|世紀|年代|天皇|将軍|幕府|戦い|の乱|の変|維新|改革|文化)'),
            ],
            '地理': [
                re.compile(r'(都道府県|地方|地域|地形|気候|産業|農業|工業|漁業|特産)'),
            ],
            '公民': [
                re.compile(r'(憲法|法律|政治|選挙|国会|内閣|裁判|経済|国際|環境)'),
            ],
        }
    
    def _init_exclusion_words(self) -> Set[str]:
        """テーマとして除外すべき一般的な単語"""
        return {
            '空欄', '空らん', '下線', '下線部', 'について', 'こと', 'もの', 'ため',
            '次の', 'うち', 'なかで', 'それぞれ', '文章', '正しい', '誤り', 'まちがい',
            '選びなさい', '答えなさい', '書きなさい', '述べなさい', '説明しなさい',
            '問題', '設問', '選択肢', 'ア', 'イ', 'ウ', 'エ', 'オ',
            '①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩',
            'あてはまる', '語句', '漢字', '二字', '三字', '四字', '組み合わせ',
            '【あ】', '【い】', '【う】', '【え】', '【お】',
            '以上', '以下', '字以上', '字以下',
        }
    
    def extract_theme(self, text: str) -> ThemeExtractionResult:
        """
        問題文から具体的なテーマを抽出
        
        Args:
            text: 問題文（選択肢を含む）
            
        Returns:
            ThemeExtractionResult: 抽出したテーマと信頼度
        """
        # 問題文の断片のみの場合は早期リターン
        invalid_fragments = [
            'の設問に答えなさい',
            'について答えなさい', 
            'を答えなさい',
            'に答えなさい',
            '次の問いに答えなさい',
        ]
        
        # 完全一致の場合のみスキップ
        if text.strip() in invalid_fragments:
            return ThemeExtractionResult(None, 0.0, None)
        
        # 穴埋め問題や語句問題の場合もスキップ
        if re.match(r'^【[あ-おア-オ]\】|^[\(（][あ-おア-オ][\)）]', text.strip()):
            return ThemeExtractionResult(None, 0.0, None)
        
        # 「〜について」だけで実質的な内容がない場合もスキップ
        if re.match(r'^.{1,5}について$', text.strip()):
            return ThemeExtractionResult(None, 0.0, None)
        
        # 「字以上」などの断片的な指示文の場合もスキップ
        if re.match(r'^\d+字以上|^漢字\d+字|^語句', text.strip()):
            return ThemeExtractionResult(None, 0.0, None)
        
        # テキストのクリーニング
        cleaned_text = self._clean_text(text)
        
        # キーワードを抽出
        keywords = self._extract_keywords(cleaned_text)
        
        # まず具体的なテーマを抽出（cleaned_textを使用）
        concrete_theme = self._extract_concrete_theme(cleaned_text, keywords)
        if concrete_theme:
            # カテゴリーを判定
            category = self._detect_category(cleaned_text)
            theme_result = ThemeExtractionResult(concrete_theme, 0.9, category)
        else:
            # キーワードからテーマを推定
            theme_result = self._infer_theme_from_keywords(keywords, cleaned_text)
            
            # テーマが見つからない場合は、パターンマッチングを試行
            if not theme_result.theme:
                theme_result = self._fallback_pattern_matching(cleaned_text)
        
        # テーマを2文節形式に拡張
        if theme_result.theme:
            enhanced_theme = self._enhance_theme_description(
                theme_result.theme, cleaned_text, theme_result.category
            )
            theme_result = ThemeExtractionResult(
                enhanced_theme, theme_result.confidence, theme_result.category
            )
        
        return theme_result
    
    def _clean_text(self, text: str) -> str:
        """テキストのクリーニング"""
        # 改行を空白に
        text = text.replace('\n', ' ')
        # 複数の空白を単一に
        text = re.sub(r'\s+', ' ', text)
        # 記号の正規化
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('「', '').replace('」', '')
        text = text.replace('『', '').replace('』', '')
        return text.strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """重要なキーワードを抽出"""
        keywords = []
        
        # 固有名詞パターン（漢字・カタカナの連続）
        proper_nouns = re.findall(r'[一-龥ァ-ヴー]{2,}', text)
        keywords.extend(proper_nouns)
        
        # 数字を含む年代
        years = re.findall(r'\d{3,4}年', text)
        keywords.extend(years)
        
        # 地名・人名らしきもの（「〜の」で終わらない2-5文字の漢字）
        names = re.findall(r'(?<![のはがをにでとも])[一-龥]{2,5}(?![のはがをにでとも])', text)
        keywords.extend(names)
        
        # カタカナ語
        katakana = re.findall(r'[ァ-ヴー]{3,}', text)
        keywords.extend(katakana)
        
        # 除外語を削除
        keywords = [k for k in keywords if k not in self.exclusion_words]
        
        return keywords
    
    def _infer_theme_from_keywords(self, keywords: List[str], full_text: str) -> ThemeExtractionResult:
        """キーワードからテーマを推定"""
        best_theme = None
        best_score = 0
        best_category = None
        
        # 各カテゴリーのテーマをチェック
        for category, themes in self.theme_keyword_map.items():
            for theme_name, theme_keywords in themes.items():
                # キーワードの一致数をカウント
                matches = 0
                matched_keywords = []
                
                for keyword in keywords:
                    for theme_kw in theme_keywords:
                        if theme_kw in keyword or keyword in theme_kw:
                            matches += 1
                            matched_keywords.append(keyword)
                            break
                
                # フルテキストでの追加チェック
                for theme_kw in theme_keywords:
                    if theme_kw in full_text and theme_kw not in matched_keywords:
                        matches += 0.5  # 部分点
                
                # スコア計算（マッチ数 / テーマキーワード数）
                if matches > 0:
                    score = matches / len(theme_keywords)
                    # 複数のキーワードがマッチした場合はボーナス
                    if matches >= 2:
                        score *= 1.5
                    
                    if score > best_score:
                        best_score = score
                        best_theme = theme_name
                        best_category = category
        
        # 信頼度の計算
        confidence = min(best_score, 1.0) if best_score > 0 else 0.0
        
        # 閾値を超えた場合のみテーマとして採用
        if confidence >= 0.3:
            return ThemeExtractionResult(best_theme, confidence, best_category)
        
        return ThemeExtractionResult(None, 0.0, None)
    
    def _extract_concrete_theme(self, text: str, keywords: List[str]) -> Optional[str]:
        """キーワードから具体的なテーマを抽出"""
        # 歴史的な政策・文書
        if '上げ米の制' in text or '上米の制' in text:
            return "上げ米の制"
        elif '大隈重信' in text and '政党' in text:
            return "立憲改進党"
        elif 'ポツダム' in text:
            return "ポツダム宣言"
        elif 'サンフランシスコ' in text and ('講和' in text or '条約' in text):
            return "サンフランシスコ講和条約"
        elif '五・一五事件' in text or '二・二六事件' in text:
            return "昭和初期の政変"
        elif 'ドイツ' in text and 'イタリア' in text and ('同盟' in text or '日本' in text):
            return "日独伊三国同盟"
        elif '男女' in text and ('平等' in text or '共同参画' in text or '対等' in text):
            return "男女共同参画社会"
        elif '空き家' in text:
            return "空き家問題"
        
        # 交通インフラ関連
        if any(k in text for k in ['青函トンネル', '瀬戸大橋', '明石海峡大橋']):
            if '高速交通網' in text:
                return "日本の交通インフラ"
            elif '青函トンネル' in text and '瀬戸大橋' in text:
                return "日本の交通インフラ"
            elif '青函トンネル' in text:
                return "青函トンネル"
            elif '瀬戸大橋' in text:
                return "瀬戸大橋"
        
        # 国際関係
        if '1948年' in text and 'ユダヤ' in text:
            return "イスラエル建国"
        elif 'ユダヤ' in text and ('アラブ' in text or 'イスラエル' in text or '建国' in text):
            if '1948年' in text:
                return "イスラエル建国"
            else:
                return "中東問題"
        elif 'イスラエル' in text:
            return "イスラエル建国"
        
        # 資料の種類を特定
        if '雨温図' in text:
            return "気候の特徴"
        if 'グラフ' in text:
            if '人口' in text:
                return "人口推移"
            elif '輸出' in text or '輸入' in text:
                return "貿易統計"
            else:
                return "統計データ"
        
        # 下線部の内容を特定
        if '下線部' in text:
            # 下線部の後の具体的な内容を探す
            import re
            pattern = re.search(r'下線部[①-⑩ⓐ-ⓩ]?[のにをはが]*([^、。\s]{2,10})', text)
            if pattern:
                content = pattern.group(1)
                if content and content not in ['について', 'に関して', 'として']:
                    return content
        
        return None
    
    def _fallback_pattern_matching(self, text: str) -> ThemeExtractionResult:
        """フォールバック：シンプルなパターンマッチング"""
        # 問題文の断片のみの場合はテーマを抽出しない
        invalid_fragments = [
            'の設問に答えなさい',
            'について答えなさい', 
            'を答えなさい',
            'に答えなさい',
            '次の問いに答えなさい',
        ]
        
        # 短すぎて問題文の断片のみの場合はスキップ
        # 完全一致の場合のみスキップ
        if text.strip() in invalid_fragments:
            return ThemeExtractionResult(None, 0.0, None)
        
        # 最も特徴的なキーワードを探す
        
        # 時代名を直接探す
        time_periods = [
            '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
            '平安時代', '鎌倉時代', '室町時代', '戦国時代', '江戸時代',
            '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
        ]
        for period in time_periods:
            if period in text:
                return ThemeExtractionResult(period, 0.8, '歴史')
        
        # 歴史的事件を探す
        historical_events = [
            '建武の新政', '大化の改新', '承久の乱', '応仁の乱',
            '本能寺の変', '関ヶ原の戦い', '明治維新', '太平洋戦争'
        ]
        for event in historical_events:
            if event in text:
                return ThemeExtractionResult(event, 0.8, '歴史')
        
        # 地名を探す
        regions = [
            '北海道', '東北地方', '関東地方', '中部地方', '近畿地方',
            '中国地方', '四国地方', '九州地方', '沖縄'
        ]
        for region in regions:
            if region in text:
                return ThemeExtractionResult(region, 0.7, '地理')
        
        # 都道府県名を探す（主要なもの）
        prefectures = [
            '東京都', '大阪府', '京都府', '神奈川県', '愛知県',
            '広島県', '福岡県', '北海道', '沖縄県'
        ]
        for pref in prefectures:
            if pref in text:
                return ThemeExtractionResult(pref, 0.7, '地理')
        
        # 重要な制度名を探す
        systems = [
            '日本国憲法', '三権分立', '選挙制度', '国会', '内閣',
            '裁判所', '地方自治', '国際連合'
        ]
        for system in systems:
            if system in text:
                return ThemeExtractionResult(system, 0.7, '公民')
        
        # カテゴリーを判定
        category = self._detect_category(text)
        
        # 最も長い固有名詞を探す
        proper_nouns = re.findall(r'[一-龥ァ-ヴー]{3,8}', text)
        valid_nouns = [n for n in proper_nouns if n not in self.exclusion_words]
        
        if valid_nouns:
            # 出現頻度でソート
            noun_counts = Counter(valid_nouns)
            most_common = noun_counts.most_common(1)[0][0]
            # 一般的すぎる名詞は除外
            if most_common not in ['について', '答えなさい', '選びなさい', '説明しなさい']:
                return ThemeExtractionResult(most_common, 0.4, category)
        
        return ThemeExtractionResult(None, 0.0, None)
    
    def _detect_category(self, text: str) -> Optional[str]:
        """テキストのカテゴリーを判定"""
        scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(text):
                    score += 1
            scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return None
    
    def _enhance_theme_description(self, base_theme: str, text: str, category: Optional[str]) -> str:
        """
        テーマを2文節程度の具体的な表現に拡張する
        
        Args:
            base_theme: 基本テーマ
            text: 問題文
            category: カテゴリー
        
        Returns:
            拡張されたテーマ（例：「日本の漁業」「平安時代の文化」）
        """
        # 既に2文節以上の場合、または具体的なテーマが既に抽出されている場合はそのまま返す
        if 'の' in base_theme or '・' in base_theme or len(base_theme) >= 8:
            return base_theme
        
        # 具体的な国際関係や歴史的事件のテーマの場合は上書きしない
        specific_themes = [
            'イスラエル建国', '中東問題', 'ポツダム宣言', 'サンフランシスコ講和条約',
            '日独伊三国同盟', '男女共同参画社会', '上げ米の制', '立憲改進党',
            '昭和初期の政変', '日本の交通インフラ', '青函トンネル', '瀬戸大橋'
        ]
        if base_theme in specific_themes:
            return base_theme
        
        # 時代を検出
        time_periods = {
            '縄文': '縄文時代', '弥生': '弥生時代', '古墳': '古墳時代',
            '飛鳥': '飛鳥時代', '奈良': '奈良時代', '平安': '平安時代',
            '鎌倉': '鎌倉時代', '室町': '室町時代', '戦国': '戦国時代',
            '安土桃山': '安土桃山時代', '江戸': '江戸時代',
            '明治': '明治時代', '大正': '大正時代', '昭和': '昭和時代',
            '平成': '平成時代', '令和': '令和時代'
        }
        
        detected_period = None
        for period_key, period_name in time_periods.items():
            if period_key in text:
                detected_period = period_name
                break
        
        # カテゴリー別の拡張パターン
        if category == '歴史':
            # 時代名の場合
            if '時代' in base_theme:
                if '文化' in text:
                    return f"{base_theme}の文化"
                elif '政治' in text or '政策' in text:
                    return f"{base_theme}の政治"
                elif '経済' in text or '産業' in text:
                    return f"{base_theme}の経済"
                else:
                    return f"{base_theme}の特徴"
            
            # 人物名・人物関連の場合
            elif '人物' in base_theme or self._is_person_name(text):
                # 特定の人物名が含まれている場合はその人物名を使用
                person_names = self._extract_person_names(text)
                if person_names:
                    return f"{person_names[0]}の功績"
                
                if detected_period:
                    # 複数の時代が検出された場合は時代範囲を示す
                    all_periods = []
                    for period_key, period_name in time_periods.items():
                        if period_key in text:
                            all_periods.append(period_name)
                    
                    if len(all_periods) >= 2:
                        return f"{all_periods[0]}〜{all_periods[-1]}の人物"
                    else:
                        return f"{detected_period}の人物"
                else:
                    # 時代が不明な場合は文脈から推測
                    if '戦国' in text or '武将' in text:
                        return "戦国時代の武将"
                    elif '幕府' in text and '江戸' not in text:
                        return "武家政権の人物"
                    elif '天皇' in text:
                        return "歴代天皇"
                    else:
                        return "歴史上の人物"
            
            # 事件・改革の場合
            elif '改革' in base_theme or '改新' in base_theme:
                return f"{base_theme}の内容"
            elif '戦争' in base_theme or '戦い' in base_theme:
                return f"{base_theme}の経過"
            elif '条約' in base_theme:
                return f"{base_theme}の内容"
            else:
                if detected_period:
                    return f"{detected_period}の{base_theme}"
                else:
                    return f"{base_theme}の歴史"
        
        elif category == '地理':
            # 地方・地域名の場合
            if '地方' in base_theme or '県' in base_theme:
                if '産業' in text or '工業' in text:
                    return f"{base_theme}の産業"
                elif '気候' in text or '雨温図' in text:
                    return f"{base_theme}の気候"
                elif '人口' in text:
                    return f"{base_theme}の人口"
                else:
                    return f"{base_theme}の特徴"
            
            # 自然・地形の場合
            elif '山' in base_theme or '川' in base_theme or '湖' in base_theme:
                return f"日本の{base_theme}"
            
            # 産業の場合
            elif '工業' in base_theme:
                if '軽工業' in text:
                    return "日本の軽工業"
                elif '重工業' in text:
                    return "日本の重工業"
                else:
                    return "日本の工業"
            elif '農業' in base_theme:
                return "日本の農業"
            elif '漁業' in base_theme:
                return "日本の漁業"
            
            # 気候関連
            elif '雨温図' in base_theme:
                if '都市' in text:
                    return "都市の気候"
                else:
                    return "気候の特徴"
            
            # 貿易関連
            elif '貿易' in base_theme:
                return "日本の貿易"
            
            # 都市関連
            elif '都市' in base_theme:
                return "日本の都市"
            
            else:
                return f"日本の{base_theme}"
        
        elif category == '公民':
            # 憲法関連
            if '憲法' in base_theme:
                if '条文' in text:
                    return "憲法の条文"
                else:
                    return "日本国憲法"
            
            # 選挙関連
            elif '選挙' in base_theme:
                if '制度' in text:
                    return "選挙制度"
                else:
                    return "選挙の仕組み"
            
            # 三権関連
            elif '国会' in base_theme:
                return "国会の役割"
            elif '内閣' in base_theme:
                return "内閣の役割"
            elif '裁判' in base_theme:
                return "裁判所の役割"
            
            # 地方自治
            elif '地方自治' in base_theme:
                return "地方自治の仕組み"
            
            # 国際関係
            elif '国際' in base_theme or '国連' in base_theme:
                return "国際関係"
            
            # 経済
            elif '経済' in base_theme:
                if '政策' in text:
                    return "経済政策"
                else:
                    return "日本の経済"
            
            # 社会保障
            elif '社会保障' in base_theme:
                return "社会保障制度"
            
            # 財政
            elif '財政' in base_theme:
                return "日本の財政"
            
            else:
                return f"{base_theme}の仕組み"
        
        # カテゴリーが不明な場合の汎用パターン
        # 「〜人」（民族）ではなく、実際の人物を指している場合のみ
        if ('人物' in text or 
            (self._is_person_name(text) and not any(ethnic in text for ethnic in ['ユダヤ人', 'アメリカ人', '日本人', '中国人', '朝鮮人', 'ドイツ人']))):
            if detected_period:
                return f"{detected_period}の人物"
            else:
                return "人物の功績"
        elif '図' in base_theme or 'グラフ' in base_theme:
            return "資料の読み取り"
        elif '年' in text and detected_period:
            return f"{detected_period}の出来事"
        else:
            # 文脈から判断
            if '日本' in text:
                return f"日本の{base_theme}"
            elif '世界' in text:
                return f"世界の{base_theme}"
            else:
                return f"{base_theme}について"
    
    def _is_person_name(self, text: str) -> bool:
        """テキストに人物名が含まれているかを判定"""
        person_indicators = [
            '人物', '氏', '天皇', '将軍', '大臣', '総理',
            '名前', '誰', 'だれ', '人名', '武将', '家', '公'
        ]
        return any(indicator in text for indicator in person_indicators)
    
    def _extract_person_names(self, text: str) -> List[str]:
        """テキストから具体的な人物名を抽出"""
        person_names = []
        
        # 有名な歴史上の人物名パターン
        famous_persons = [
            '聖徳太子', '藤原道長', '源頼朝', '北条時宗', '足利義満',
            '織田信長', '豊臣秀吉', '徳川家康', '西郷隆盛', '大久保利通',
            '伊藤博文', '大隈重信', '板垣退助', '福沢諭吉', '明治天皇'
        ]
        
        for person in famous_persons:
            if person in text:
                person_names.append(person)
        
        # 「〜天皇」パターン
        emperor_pattern = re.findall(r'([一-龥]{2,4})天皇', text)
        for emperor in emperor_pattern:
            if emperor not in ['の', 'は', 'が', 'を', 'に', 'と']:
                person_names.append(f"{emperor}天皇")
        
        # 「〜将軍」パターン
        shogun_pattern = re.findall(r'([一-龥]{2,4})将軍', text)
        for shogun in shogun_pattern:
            if shogun not in ['の', 'は', 'が', 'を', 'に', 'と']:
                person_names.append(f"{shogun}将軍")
        
        return person_names
    
    def extract_theme_with_choices(self, question_text: str, choices: List[str]) -> ThemeExtractionResult:
        """
        問題文と選択肢を組み合わせてテーマを抽出
        
        Args:
            question_text: 問題文
            choices: 選択肢のリスト
            
        Returns:
            ThemeExtractionResult: 抽出したテーマと信頼度
        """
        # 問題文と選択肢を結合
        full_text = question_text + ' ' + ' '.join(choices)
        
        # 選択肢から共通キーワードを抽出
        choice_keywords = []
        for choice in choices:
            keywords = self._extract_keywords(choice)
            choice_keywords.extend(keywords)
        
        # 頻出キーワードを重視
        keyword_counts = Counter(choice_keywords)
        common_keywords = [kw for kw, count in keyword_counts.items() if count >= 2]
        
        # 共通キーワードがある場合は、それを優先してテーマを推定
        if common_keywords:
            theme_result = self._infer_theme_from_keywords(common_keywords, full_text)
            if theme_result.theme:
                # 選択肢からの推定は信頼度を上げる
                theme_result.confidence = min(theme_result.confidence * 1.2, 1.0)
                return theme_result
        
        # 通常の抽出処理
        return self.extract_theme(full_text)