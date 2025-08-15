"""
テーマ知識ベースモジュール
social_studies_curriculum.mdとsubject_index.mdの内容を活用してテーマを決定
"""

import re
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ThemeKnowledgeBase:
    """カリキュラムと主題インデックスに基づくテーマ決定"""
    
    def __init__(self):
        self.subject_index_path = Path(__file__).parent.parent / 'docs' / 'subject_index.md'
        self.initialize_knowledge()
        self.load_subject_index()
    
    def load_subject_index(self):
        """subject_index.mdから知識を読み込む"""
        if not self.subject_index_path.exists():
            logger.warning(f"subject_index.md not found at {self.subject_index_path}")
            return
        
        try:
            with open(self.subject_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 歴史分野の情報を抽出
            self._parse_history_section(content)
            # 公民分野の情報を抽出
            self._parse_civics_section(content)
            # 地理分野の情報を抽出
            self._parse_geography_section(content)
            
            logger.info("Successfully loaded subject_index.md")
        except Exception as e:
            logger.error(f"Error loading subject_index.md: {e}")
    
    def _parse_history_section(self, content: str):
        """歴史分野のセクションをパース"""
        history_section = re.search(r'### 歴史分野の分類(.*?)(?=###|$)', content, re.DOTALL)
        if not history_section:
            return
        
        section_text = history_section.group(1)
        
        # 各時代の情報を抽出して既存の辞書を更新
        periods = re.findall(r'- (.*?)(?:\(|（)(.*?)(?:\)|）)\n\s*- 代表語: (.*?)\n\s*- 主題テンプレート例: (.*?)\n', section_text)
        
        for period_name, period_desc, keywords, templates in periods:
            # キーワードをリスト化
            keyword_list = [k.strip() for k in keywords.split('、')]
            
            # 時代名の正規化（例：「原始・古代（旧石器・縄文・弥生）」から各時代を抽出）
            if '旧石器' in period_desc:
                self.history_periods['旧石器'] = keyword_list[:4]  # 最初の数個
            if '縄文' in period_desc:
                self.history_periods['縄文'] = [k for k in keyword_list if '縄文' in k or '土偶' in k or '貝塚' in k or '三内丸山' in k]
            if '弥生' in period_desc:
                self.history_periods['弥生'] = [k for k in keyword_list if '弥生' in k or '稲作' in k or '登呂' in k or '吉野ヶ里' in k]
            
            # 単一時代の場合
            if '・' not in period_name:
                period_key = period_name.replace('時代', '')
                if period_key in self.history_periods:
                    # 既存のキーワードに追加
                    self.history_periods[period_key].extend(keyword_list)
                    self.history_periods[period_key] = list(set(self.history_periods[period_key]))  # 重複除去
    
    def _parse_civics_section(self, content: str):
        """公民分野のセクションをパース"""
        civics_section = re.search(r'### 公民分野の分類(.*?)(?=###|$)', content, re.DOTALL)
        if not civics_section:
            return
        
        section_text = civics_section.group(1)
        
        # 各カテゴリの情報を抽出
        categories = re.findall(r'- (.*?)\n\s*- (.*?):(.*?)\n', section_text)
        
        for category_name, label, content_text in categories:
            if ':' in content_text:
                continue  # 次のカテゴリの開始
            
            # キーワードをリスト化
            keywords = [k.strip() for k in content_text.split('、')]
            
            # カテゴリ名の正規化
            if '政治' in category_name:
                self.civics_themes['政治'].extend(keywords)
            elif '人権' in category_name:
                self.civics_themes['人権'].extend(keywords)
            elif '経済' in category_name:
                self.civics_themes['経済'].extend(keywords)
            elif '国際' in category_name:
                self.civics_themes['国際'].extend(keywords)
            elif '憲法' in category_name:
                self.civics_themes['憲法'].extend(keywords)
            elif '社会' in category_name:
                self.civics_themes['社会'].extend(keywords)
    
    def _parse_geography_section(self, content: str):
        """地理分野のセクションをパース"""
        geography_section = re.search(r'### 地理分野の分類(.*?)(?=###|---|\Z)', content, re.DOTALL)
        if not geography_section:
            return
        
        section_text = geography_section.group(1)
        
        # 世界地理の情報を抽出
        world_geo = re.search(r'- 世界地理(.*?)(?=- 日本地理)', section_text, re.DOTALL)
        if world_geo:
            # 各州の情報を抽出してgeography_themesに追加
            self.geography_themes['世界地理'] = []
            regions = re.findall(r'(アジア|ヨーロッパ|アフリカ|北アメリカ|南アメリカ|オセアニア)(?:（|[(])(.*?)(?:）|[)])', world_geo.group(1))
            for region, keywords in regions:
                keyword_list = [k.strip() for k in keywords.split('、')]
                self.geography_themes['世界地理'].extend(keyword_list)
        
        # 日本地理の情報を抽出
        japan_geo = re.search(r'- 日本地理(.*?)$', section_text, re.DOTALL)
        if japan_geo:
            # 自然、地域、産業などの情報を抽出
            nature_match = re.search(r'日本の自然.*?:(.*?)／', japan_geo.group(1))
            if nature_match:
                nature_keywords = [k.strip() for k in nature_match.group(1).split('、')]
                self.geography_themes['地形'].extend(nature_keywords[:10])
                self.geography_themes['気候'].extend(nature_keywords[10:])
            
            industry_match = re.search(r'日本の産業.*?:(.*?)(?:、現代課題|$)', japan_geo.group(1))
            if industry_match:
                industry_keywords = [k.strip() for k in industry_match.group(1).split('、')]
                self.geography_themes['農業'].extend([k for k in industry_keywords if '農' in k or '畑' in k or '酪農' in k])
                self.geography_themes['漁業'].extend([k for k in industry_keywords if '漁' in k or '養殖' in k])
                self.geography_themes['工業'].extend([k for k in industry_keywords if '工業' in k or 'ハイテク' in k])
    
    def initialize_knowledge(self):
        """知識ベースの初期化（デフォルト値）"""
        # 歴史時代区分と代表的キーワード
        self.history_periods = {
            '旧石器': ['打製石器', '岩宿', '野尻湖', 'ナウマンゾウ'],
            '縄文': ['縄文土器', '土偶', '貝塚', '竪穴住居', '三内丸山'],
            '弥生': ['弥生土器', '稲作', '高床倉庫', '環濠集落', '登呂', '吉野ヶ里', '青銅器', '鉄器'],
            '古墳': ['前方後円墳', '埴輪', '古墳', '大和政権', '大王'],
            '飛鳥': ['聖徳太子', '十七条の憲法', '冠位十二階', '遣隋使', '大化の改新', '中大兄皇子'],
            '奈良': ['平城京', '律令', '班田収授法', '墾田永年私財法', '天平文化', '東大寺', '聖武天皇'],
            '平安': ['平安京', '摂関政治', '藤原道長', '国風文化', '源氏物語', '平等院鳳凰堂', '院政'],
            '鎌倉': ['鎌倉幕府', '源頼朝', '御恩と奉公', '守護・地頭', '御成敗式目', '元寇', '北条'],
            '室町': ['室町幕府', '足利尊氏', '応仁の乱', '北山文化', '東山文化', '金閣', '銀閣'],
            '戦国': ['戦国大名', '下剋上', '分国法', '城下町'],
            '安土桃山': ['織田信長', '豊臣秀吉', '楽市楽座', '太閤検地', '刀狩', '南蛮貿易'],
            '江戸': ['江戸幕府', '徳川家康', '参勤交代', '鎖国', '享保の改革', '寛政の改革', '天保の改革', '元禄文化', '化政文化'],
            '明治': ['明治維新', '富国強兵', '殖産興業', '文明開化', '自由民権運動', '大日本帝国憲法', '日清戦争', '日露戦争'],
            '大正': ['大正デモクラシー', '護憲運動', '普通選挙', '関東大震災'],
            '昭和戦前': ['満州事変', '日中戦争', '太平洋戦争', '国家総動員法'],
            '昭和戦後': ['日本国憲法', 'GHQ', '農地改革', '財閥解体', '高度経済成長', '東京オリンピック'],
            '平成': ['バブル経済', '阪神淡路大震災', '東日本大震災'],
            '令和': ['新型コロナ', 'SDGs', 'デジタル化']
        }
        
        # 地理分野のテーマパターン
        self.geography_themes = {
            '地形': ['山地', '山脈', '平野', '盆地', '台地', '扇状地', '三角州', 'リアス海岸'],
            '気候': ['太平洋側', '日本海側', '内陸性', '瀬戸内', '梅雨', '台風', '季節風', '雨温図'],
            '農業': ['稲作', '畑作', '酪農', '果樹', '施設園芸', '促成栽培', '抑制栽培'],
            '漁業': ['遠洋漁業', '沖合漁業', '沿岸漁業', '養殖業', '栽培漁業'],
            '工業': ['工業地帯', '工業地域', '京浜', '中京', '阪神', '北九州', '瀬戸内'],
            '都市': ['過密', '過疎', '政令指定都市', '中核市', '都市問題'],
            '交通': ['新幹線', '高速道路', '空港', '港湾'],
            '資源': ['エネルギー', '鉱産資源', '森林資源', '水資源'],
            '環境': ['公害', '環境問題', '地球温暖化', 'リサイクル', '再生可能エネルギー'],
            '世界地理': []  # load_subject_indexで追加
        }
        
        # 公民分野のテーマパターン
        self.civics_themes = {
            '憲法': ['日本国憲法', '基本的人権', '国民主権', '平和主義', '三大原則'],
            '政治': ['国会', '内閣', '裁判所', '三権分立', '選挙', '政党', '地方自治'],
            '経済': ['市場経済', '需要と供給', '価格', '企業', '労働', '金融', '財政', '税金'],
            '国際': ['国連', '国際協力', 'ODA', 'PKO', 'NGO', '貿易', 'グローバル化'],
            '社会': ['少子高齢化', '社会保障', '年金', '医療', '介護', '福祉'],
            '人権': ['平等権', '自由権', '社会権', '参政権', '請求権', '新しい人権']
        }
    
    def determine_theme(self, text: str, field: str) -> str:
        """
        テキストと分野からテーマを決定
        
        Args:
            text: 問題文
            field: 分野（地理/歴史/公民/時事・総合）
        
        Returns:
            決定されたテーマ
        """
        if not text:
            return f"{field}問題"
        
        text = text.strip()
        
        # 分野別の詳細なテーマ決定
        if field == '歴史':
            return self._determine_history_theme(text)
        elif field == '地理':
            return self._determine_geography_theme(text)
        elif field == '公民':
            return self._determine_civics_theme(text)
        else:
            return self._determine_general_theme(text, field)
    
    def _determine_history_theme(self, text: str) -> str:
        """歴史分野のテーマ決定（subject_index.mdに基づく具体化）"""
        # まず特定の歴史的事件を探す（最優先）
        specific_events = {
            '大化の改新': ['大化の改新', '中大兄皇子', '中臣鎌足', '蘇我氏'],
            '壬申の乱': ['壬申の乱', '天武天皇', '大友皇子'],
            '保元の乱': ['保元の乱', '崇徳上皇', '後白河天皇'],
            '平治の乱': ['平治の乱', '源義朝', '平清盛'],
            '承久の乱': ['承久の乱', '後鳥羽上皇', '北条義時'],
            '応仁の乱': ['応仁の乱', '細川', '山名'],
            '本能寺の変': ['本能寺の変', '織田信長', '明智光秀'],
            '関ヶ原の戦い': ['関ヶ原', '徳川家康', '石田三成'],
            '大政奉還': ['大政奉還', '徳川慶喜', '王政復古'],
            '戊辰戦争': ['戊辰戦争', '新政府軍', '旧幕府軍'],
            '西南戦争': ['西南戦争', '西郷隆盛'],
            '日清戦争': ['日清戦争', '下関条約', '遼東半島'],
            '日露戦争': ['日露戦争', 'ポーツマス条約', '樺太'],
            '第一次世界大戦': ['第一次世界大戦', 'ベルサイユ条約'],
            '満州事変': ['満州事変', '柳条湖', '満州国'],
            '日中戦争': ['日中戦争', '盧溝橋'],
            '太平洋戦争': ['太平洋戦争', '真珠湾', 'ミッドウェー']
        }
        
        for event_name, keywords in specific_events.items():
            if any(kw in text for kw in keywords):
                # イベントの詳細な側面を判定
                if '原因' in text or '理由' in text or 'きっかけ' in text:
                    return f"{event_name}の原因"
                elif '結果' in text or '影響' in text:
                    return f"{event_name}の影響"
                elif '経過' in text or '展開' in text:
                    return f"{event_name}の経過"
                else:
                    return event_name
        
        # 特定の制度・政策を探す
        specific_policies = {
            '班田収授法': ['班田収授法', '口分田', '公地公民'],
            '墾田永年私財法': ['墾田永年私財法', '荘園'],
            '御恩と奉公': ['御恩と奉公', '御家人', '守護・地頭'],
            '楽市楽座': ['楽市楽座', '織田信長', '商業'],
            '太閤検地': ['太閤検地', '豊臣秀吉', '石高'],
            '刀狩': ['刀狩', '豊臣秀吉', '兵農分離'],
            '参勤交代': ['参勤交代', '大名統制', '江戸幕府'],
            '鎖国': ['鎖国', '出島', 'オランダ', '長崎'],
            '享保の改革': ['享保の改革', '徳川吉宗', '目安箱'],
            '寛政の改革': ['寛政の改革', '松平定信', '倹約'],
            '天保の改革': ['天保の改革', '水野忠邦', '株仲間'],
            '地租改正': ['地租改正', '税制', '土地'],
            '殖産興業': ['殖産興業', '富国強兵', '官営工場'],
            '農地改革': ['農地改革', 'GHQ', '自作農']
        }
        
        for policy_name, keywords in specific_policies.items():
            if any(kw in text for kw in keywords):
                if '内容' in text or '特徴' in text:
                    return f"{policy_name}の内容"
                elif '目的' in text or '理由' in text:
                    return f"{policy_name}の目的"
                elif '結果' in text or '影響' in text:
                    return f"{policy_name}の影響"
                else:
                    return policy_name
        
        # 時代を特定
        detected_period = None
        max_score = 0
        
        for period, keywords in self.history_periods.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                detected_period = period
        
        # 中国王朝の特別処理
        china_dynasties = ['隋', '唐', '宋', '元', '明', '清', '秦', '漢', '三国', '晋', '五代']
        for dynasty in china_dynasties:
            if dynasty in text and ('中国' in text or '王朝' in text or '皇帝' in text):
                return f"{dynasty}朝の特徴"
        
        # 文化の具体化
        specific_cultures = {
            '飛鳥文化': '飛鳥文化',
            '天平文化': '天平文化',
            '国風文化': '国風文化',
            '北山文化': '北山文化と金閣',
            '東山文化': '東山文化と銀閣',
            '桃山文化': '桃山文化',
            '元禄文化': '元禄文化',
            '化政文化': '化政文化'
        }
        
        for culture_key, culture_name in specific_cultures.items():
            if culture_key in text:
                return culture_name
        
        # 人物名を探す
        persons = self._extract_person_names(text)
        if persons:
            person = persons[0]
            # 人物に関連する具体的なテーマ
            if '政策' in text or '改革' in text:
                return f"{person}の政策"
            elif '文化' in text or '作品' in text:
                return f"{person}の文化的業績"
            elif detected_period:
                return f"{detected_period}時代・{person}"
            else:
                return f"{person}の業績"
        
        # 時代が特定できた場合の詳細化
        if detected_period:
            # より具体的な側面を判定
            if '貿易' in text or '交易' in text:
                return f"{detected_period}時代の貿易"
            elif '仏教' in text or '寺' in text:
                return f"{detected_period}時代の仏教"
            elif '武士' in text or '武家' in text:
                return f"{detected_period}時代の武士"
            elif '農民' in text or '百姓' in text:
                return f"{detected_period}時代の農民"
            elif '商人' in text or '商業' in text:
                return f"{detected_period}時代の商業"
            elif '政治' in text or '幕府' in text or '朝廷' in text:
                return f"{detected_period}時代の政治"
            elif '文化' in text or '芸術' in text:
                return f"{detected_period}時代の文化"
            elif '経済' in text or '産業' in text:
                return f"{detected_period}時代の経済"
            elif '社会' in text or '身分' in text:
                return f"{detected_period}時代の社会"
            else:
                return f"{detected_period}時代の特徴"
        
        return "歴史総合問題"
    
    def _determine_geography_theme(self, text: str) -> str:
        """地理分野のテーマ決定（subject_index.mdに基づく具体化）"""
        # 特定の地域・地形を探す
        specific_regions = {
            '関東平野': '関東平野の特徴',
            '濃尾平野': '濃尾平野の農業',
            '石狩平野': '石狩平野の開拓',
            '筑紫平野': '筑紫平野の稲作',
            '瀬戸内': '瀬戸内の気候と産業',
            'リアス海岸': 'リアス海岸と水産業',
            '扇状地': '扇状地の土地利用',
            '三角州': '三角州の形成',
            '中央高地': '中央高地の農業',
            '四大工業地帯': '四大工業地帯',
            '京浜工業地帯': '京浜工業地帯',
            '中京工業地帯': '中京工業地帯',
            '阪神工業地帯': '阪神工業地帯',
            '北九州工業地帯': '北九州工業地帯'
        }
        
        for region_key, theme_name in specific_regions.items():
            if region_key in text:
                return theme_name
        
        # 都道府県の特産品・産業
        prefecture_industries = {
            '北海道': ['酪農', '畑作', '水産業', '観光'],
            '青森': ['りんご', '水産業'],
            '岩手': ['南部鉄器', '農業'],
            '山形': ['さくらんぼ', '米'],
            '新潟': ['米', 'コシヒカリ'],
            '静岡': ['茶', '水産業', 'みかん'],
            '愛知': ['自動車工業', '陶磁器'],
            '京都': ['伝統工業', '観光'],
            '大阪': ['商業', '工業'],
            '兵庫': ['鉄鋼業', '港湾'],
            '広島': ['自動車工業', '造船'],
            '愛媛': ['みかん', '養殖業'],
            '福岡': ['工業', '商業'],
            '鹿児島': ['畜産', 'さつまいも'],
            '沖縄': ['観光', 'さとうきび']
        }
        
        for prefecture, industries in prefecture_industries.items():
            if prefecture in text:
                for industry in industries:
                    if industry in text:
                        return f"{prefecture}の{industry}"
                return f"{prefecture}の産業"
        
        # 農業の具体化
        agricultural_products = {
            '米': '稲作農業',
            'コシヒカリ': 'ブランド米生産',
            '野菜': '野菜栽培',
            'みかん': 'みかん栽培',
            'りんご': 'りんご栽培',
            'ぶどう': 'ぶどう栽培',
            '茶': '茶の栽培',
            '酪農': '酪農業',
            '畜産': '畜産業',
            '施設園芸': '施設園芸農業',
            '促成栽培': '促成栽培',
            '抑制栽培': '抑制栽培',
            '高冷地農業': '高冷地農業'
        }
        
        for product, theme in agricultural_products.items():
            if product in text:
                return theme
        
        # 工業の具体化
        industrial_types = {
            '自動車': '自動車工業',
            '鉄鋼': '鉄鋼業',
            '造船': '造船業',
            '石油化学': '石油化学工業',
            '電子': '電子工業',
            '繊維': '繊維工業',
            '食品': '食品工業',
            '伝統工業': '伝統的工芸品',
            'ハイテク': 'ハイテク産業'
        }
        
        for industry_key, industry_name in industrial_types.items():
            if industry_key in text:
                return industry_name
        
        # 地域名を探す
        regions = re.findall(r'([一-龥]{2,4}(?:地方|平野|盆地|山地|川|湖|海|半島|諸島|県|府|都|道))', text)
        region_name = regions[0] if regions else None
        
        # テーマカテゴリを特定
        detected_theme = None
        max_score = 0
        
        for theme, keywords in self.geography_themes.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                detected_theme = theme
        
        # より具体的なテーマ生成
        if region_name and detected_theme:
            return f"{region_name}の{detected_theme}"
        elif detected_theme:
            if detected_theme == '気候':
                if '雨温図' in text:
                    return "雨温図の読み取り"
                elif '季節風' in text:
                    return "季節風の影響"
                elif '梅雨' in text:
                    return "梅雨の仕組み"
                elif '台風' in text:
                    return "台風の特徴"
                return "日本の気候区分"
            elif detected_theme == '交通':
                if '新幹線' in text:
                    return "新幹線網の発達"
                elif '高速道路' in text:
                    return "高速道路網"
                elif '空港' in text:
                    return "空港と航空路"
                elif '港' in text:
                    return "港湾と海運"
                return "交通網の発達"
            elif detected_theme == '環境':
                if '温暖化' in text:
                    return "地球温暖化問題"
                elif '公害' in text:
                    return "公害問題"
                elif 'リサイクル' in text:
                    return "リサイクル"
                elif '再生可能エネルギー' in text:
                    return "再生可能エネルギー"
                return "環境問題"
            else:
                return f"{detected_theme}の特色"
        elif region_name:
            return f"{region_name}の特徴"
        
        # 資料タイプによる判定
        if 'グラフ' in text:
            if '折れ線' in text:
                return "折れ線グラフの分析"
            elif '棒' in text:
                return "棒グラフの分析"
            elif '円' in text:
                return "円グラフの分析"
            return "統計グラフの分析"
        elif '地図' in text or '地形図' in text:
            return "地形図の読み取り"
        elif '表' in text:
            return "統計表の分析"
        
        return "地理総合問題"
    
    def _determine_civics_theme(self, text: str) -> str:
        """公民分野のテーマ決定"""
        # テーマカテゴリを特定
        detected_theme = None
        max_score = 0
        
        for theme, keywords in self.civics_themes.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                detected_theme = theme
        
        if detected_theme:
            # 詳細なテーマを決定
            if detected_theme == '憲法':
                if '条' in text:
                    articles = re.findall(r'第(\d+)条', text)
                    if articles:
                        return f"憲法第{articles[0]}条"
                return "日本国憲法の原則"
            elif detected_theme == '政治':
                if '選挙' in text:
                    if '東京都知事' in text:
                        return "東京都知事選挙"
                    return "選挙制度"
                elif '国会' in text:
                    return "国会の仕組み"
                elif '内閣' in text:
                    return "内閣の役割"
                elif '裁判' in text:
                    return "司法制度"
                return "政治の仕組み"
            elif detected_theme == '経済':
                if '税' in text:
                    return "税金の仕組み"
                elif '労働' in text:
                    return "労働問題"
                return "経済の仕組み"
            elif detected_theme == '国際':
                orgs = re.findall(r'(国連|UN|WHO|UNESCO|UNICEF|WTO|IMF)', text)
                if orgs:
                    return f"{orgs[0]}の役割"
                return "国際協力"
            else:
                return f"{detected_theme}問題"
        
        return "公民総合問題"
    
    def _determine_general_theme(self, text: str, field: str) -> str:
        """時事・総合分野のテーマ決定"""
        # 大阪万博関連
        if '大阪万博' in text or '万博' in text:
            return "大阪万博2025"
        
        # SDGs関連
        if 'SDGs' in text or '持続可能' in text:
            goals = re.findall(r'目標(\d+)', text)
            if goals:
                return f"SDGs目標{goals[0]}"
            return "SDGs"
        
        # 環境問題
        if any(kw in text for kw in ['温暖化', '環境問題', 'CO2', '脱炭素']):
            return "環境問題"
        
        # 災害関連
        disasters = re.findall(r'([一-龥]{2,6}(?:地震|台風|豪雨|津波|噴火))', text)
        if disasters:
            return f"{disasters[0]}と防災"
        
        # その他の時事テーマ
        if 'オリンピック' in text or '五輪' in text:
            return "オリンピック"
        elif 'コロナ' in text or 'パンデミック' in text:
            return "感染症対策"
        elif 'AI' in text or '人工知能' in text:
            return "AI技術"
        elif 'ウクライナ' in text:
            return "ウクライナ情勢"
        elif 'パレスチナ' in text or 'ガザ' in text:
            return "中東情勢"
        
        return f"{field}総合問題"
    
    def _extract_person_names(self, text: str) -> List[str]:
        """人物名を抽出"""
        # 歴史上の有名人物パターン
        famous_persons = [
            '聖徳太子', '中大兄皇子', '中臣鎌足', '聖武天皇', '桓武天皇',
            '藤原道長', '平清盛', '源頼朝', '源義経', '北条時宗',
            '足利尊氏', '足利義満', '織田信長', '豊臣秀吉', '徳川家康',
            '徳川吉宗', '西郷隆盛', '大久保利通', '伊藤博文', '福沢諭吉'
        ]
        
        found_persons = []
        for person in famous_persons:
            if person in text:
                found_persons.append(person)
        
        # 一般的な人名パターン（姓名の形式）
        if not found_persons:
            patterns = re.findall(r'([一-龥]{2,3}[\s　]?[一-龥]{2,3})', text)
            for p in patterns:
                # 人名らしいパターンをフィルタ
                if not any(exclude in p for exclude in ['年度', '問題', '次の', '以下']):
                    found_persons.append(p)
        
        return found_persons