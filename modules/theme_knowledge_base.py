"""
テーマ知識ベースモジュール
social_studies_curriculum.mdとsubject_index.mdの内容を活用してテーマを決定
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ThemeKnowledgeBase:
    """カリキュラムと主題インデックスに基づくテーマ決定"""
    
    def __init__(self):
        self.initialize_knowledge()
    
    def initialize_knowledge(self):
        """知識ベースの初期化"""
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
            '環境': ['公害', '環境問題', '地球温暖化', 'リサイクル', '再生可能エネルギー']
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
        """歴史分野のテーマ決定"""
        # 時代を特定
        detected_period = None
        max_score = 0
        
        for period, keywords in self.history_periods.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                detected_period = period
        
        # 特定の歴史的事件や人物を探す
        events = re.findall(r'([一-龥]{2,8}(?:の乱|の変|戦争|条約|改革|革命|事件))', text)
        if events:
            return events[0]
        
        # 人物名を探す
        persons = self._extract_person_names(text)
        if persons:
            if detected_period:
                return f"{detected_period}時代・{persons[0]}"
            return f"{persons[0]}の業績"
        
        # 文化を探す
        cultures = re.findall(r'([一-龥]{2,4}文化)', text)
        if cultures:
            return cultures[0]
        
        # 時代が特定できた場合
        if detected_period:
            # 文脈から詳細を判定
            if '政治' in text or '幕府' in text or '朝廷' in text:
                return f"{detected_period}時代の政治"
            elif '文化' in text or '芸術' in text:
                return f"{detected_period}時代の文化"
            elif '経済' in text or '産業' in text:
                return f"{detected_period}時代の経済"
            elif '社会' in text or '身分' in text:
                return f"{detected_period}時代の社会"
            else:
                return f"{detected_period}時代"
        
        return "歴史総合問題"
    
    def _determine_geography_theme(self, text: str) -> str:
        """地理分野のテーマ決定"""
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
        
        # 地域とテーマを組み合わせ
        if region_name and detected_theme:
            return f"{region_name}の{detected_theme}"
        elif detected_theme:
            # 詳細なテーマを決定
            if detected_theme == '農業':
                crops = re.findall(r'(米|稲|野菜|果物|みかん|りんご|ぶどう|茶)', text)
                if crops:
                    return f"{crops[0]}の生産"
                return "農業の特色"
            elif detected_theme == '工業':
                industries = re.findall(r'([一-龥]{2,4}工業)', text)
                if industries:
                    return industries[0]
                return "工業の発展"
            elif detected_theme == '気候':
                if '雨温図' in text:
                    return "雨温図の読み取り"
                return "気候の特徴"
            else:
                return f"{detected_theme}の特色"
        elif region_name:
            return f"{region_name}の特徴"
        
        # 資料タイプによる判定
        if 'グラフ' in text:
            return "統計グラフの分析"
        elif '地図' in text:
            return "地図の読み取り"
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