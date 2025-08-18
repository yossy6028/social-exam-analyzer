#!/usr/bin/env python3
"""
subject_index.md の重要語句を読み込み、テーマ抽出の精度を向上させるモジュール
"""

import re
from pathlib import Path
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


class SubjectIndexLoader:
    """subject_index.md から重要語句を抽出し、優先度の高いテーマを判定"""
    
    def __init__(self):
        """初期化"""
        self.important_terms = {
            'history': set(),
            'civics': set(),
            'geography': set(),
            'all': set()
        }
        self.load_subject_index()
    
    def load_subject_index(self):
        """subject_index.md を読み込み、重要語句を抽出"""
        
        index_path = Path(__file__).parent.parent / "docs" / "subject_index.md"
        
        if not index_path.exists():
            logger.warning(f"subject_index.md が見つかりません: {index_path}")
            return
        
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 歴史分野の語句抽出
        history_pattern = r'代表語:([^主題テンプレート]+)'
        history_matches = re.findall(history_pattern, content)
        
        for match in history_matches:
            terms = [term.strip() for term in match.split('、')]
            self.important_terms['history'].update(terms)
            self.important_terms['all'].update(terms)
        
        # 地理の特定語句
        geography_terms = [
            # 農業関連
            '促成栽培', '抑制栽培', '施設園芸', '近郊農業', '園芸農業',
            '酪農', '稲作', '畑作', '果樹栽培', '養蚕', '高冷地農業',
            # 工業関連
            '重化学工業', '軽工業', '先端技術産業', 'ハイテク産業',
            '四大工業地帯', '京浜工業地帯', '中京工業地帯', '阪神工業地帯',
            '北九州工業地帯', '京葉工業地域', '東海工業地域',
            # 地形・気候
            '扇状地', '三角州', 'リアス海岸', '台地', '盆地', '平野',
            '季節風', 'モンスーン', '梅雨', '台風', 'やませ', 'からっ風',
            '親潮', '黒潮', '暖流', '寒流',
            # 都市・地域
            '政令指定都市', '中核市', '特例市', '過疎', '過密',
            '都市問題', 'ドーナツ化現象', 'スプロール現象',
            # 世界地理
            'EU', 'ASEAN', 'OPEC', 'APEC', 'TPP',
            'サハラ砂漠', 'アマゾン', 'ヒマラヤ', 'アルプス', 'ロッキー山脈'
        ]
        self.important_terms['geography'].update(geography_terms)
        self.important_terms['all'].update(geography_terms)
        
        # 公民の特定語句
        civics_terms = [
            # 憲法・人権
            '基本的人権', '国民主権', '平和主義', '三権分立',
            '自由権', '社会権', '参政権', '請求権',
            '環境権', 'プライバシー権', '知る権利', '自己決定権',
            # 政治
            '国会', '内閣', '裁判所', '衆議院', '参議院',
            '衆議院の優越', '議院内閣制', '違憲審査権',
            '地方自治', '住民投票', '直接請求権',
            # 経済
            '市場経済', '需要と供給', '独占禁止法', '消費者保護',
            '労働基本権', '労働三法', '社会保障',
            # 国際
            '国連', '安全保障理事会', 'PKO', 'ODA',
            'SDGs', '持続可能な開発', '地球温暖化'
        ]
        self.important_terms['civics'].update(civics_terms)
        self.important_terms['all'].update(civics_terms)
        
        logger.info(f"重要語句を読み込みました: "
                   f"歴史{len(self.important_terms['history'])}語、"
                   f"地理{len(self.important_terms['geography'])}語、"
                   f"公民{len(self.important_terms['civics'])}語")
    
    def find_important_terms(self, text: str) -> Dict[str, List[str]]:
        """
        テキストから重要語句を検出
        
        Args:
            text: 検索対象のテキスト
            
        Returns:
            分野別の検出された重要語句
        """
        found_terms = {
            'history': [],
            'geography': [],
            'civics': [],
            'priority_themes': []  # 最優先テーマ
        }
        
        # 各分野の語句を検索
        for field in ['history', 'geography', 'civics']:
            for term in self.important_terms[field]:
                if term in text:
                    found_terms[field].append(term)
        
        # 優先度の高いテーマを判定
        all_found = found_terms['history'] + found_terms['geography'] + found_terms['civics']
        
        # 特に重要な語句（ユーザーが言及した「促成栽培」など）
        high_priority_terms = [
            '促成栽培', '抑制栽培', '四大工業地帯', '三権分立',
            '基本的人権', '高度経済成長', '明治維新', '鎌倉幕府'
        ]
        
        for term in all_found:
            if term in high_priority_terms:
                found_terms['priority_themes'].append(term)
        
        return found_terms
    
    def get_field_from_terms(self, terms: List[str]) -> str:
        """
        検出された語句から最も適切な分野を判定
        
        Args:
            terms: 検出された語句のリスト
            
        Returns:
            分野名（地理/歴史/公民/時事）
        """
        field_counts = {
            '地理': 0,
            '歴史': 0,
            '公民': 0
        }
        
        for term in terms:
            if term in self.important_terms['geography']:
                field_counts['地理'] += 1
            if term in self.important_terms['history']:
                field_counts['歴史'] += 1
            if term in self.important_terms['civics']:
                field_counts['公民'] += 1
        
        # 最も多い分野を返す
        if field_counts:
            return max(field_counts, key=field_counts.get)
        return '総合'
    
    def get_important_terms_prompt(self) -> str:
        """
        Gemini API用のプロンプトに含める重要語句リストを生成
        
        Returns:
            プロンプト用の重要語句説明
        """
        prompt = """
【重要語句リスト（subject_index.mdより）】
以下の語句が問題文に含まれている場合、優先的にテーマとして採用してください：

地理分野の重要語句:
- 農業: 促成栽培、抑制栽培、施設園芸、近郊農業、酪農、稲作
- 工業: 四大工業地帯、重化学工業、軽工業、ハイテク産業
- 地形: 扇状地、三角州、リアス海岸、平野、盆地
- 気候: 季節風、モンスーン、梅雨、台風、やませ、黒潮、親潮

歴史分野の重要語句:
- 時代: 縄文、弥生、古墳、飛鳥、奈良、平安、鎌倉、室町、安土桃山、江戸、明治、大正、昭和
- 重要事項: 大化の改新、摂関政治、鎌倉幕府、応仁の乱、本能寺の変、明治維新、太平洋戦争

公民分野の重要語句:
- 憲法: 基本的人権、国民主権、平和主義、三権分立
- 政治: 国会、内閣、裁判所、地方自治、選挙
- 経済: 市場経済、需要と供給、労働基本権、社会保障
- 国際: 国連、SDGs、地球温暖化

これらの語句を検出した場合は、それを中心にテーマを構築してください。
"""
        return prompt