"""
武蔵中学校専用プラグイン
"""
from typing import List, Dict, Optional
import re

from .base import SchoolAnalyzerPlugin, PluginInfo
from models import ExamSource


class MusashiPlugin(SchoolAnalyzerPlugin):
    """武蔵中学校の入試問題解析プラグイン"""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Musashi Analyzer",
            version="1.0.0",
            school_names=["武蔵中学校"],
            description="武蔵中学校の入試問題に特化した解析プラグイン",
            priority=10
        )
    
    def get_section_markers(self) -> List[str]:
        """武蔵特有の大問マーカー"""
        return ['一', '二', '三', '四', '五']
    
    def get_question_patterns(self) -> Dict[str, List[str]]:
        """武蔵特有の設問パターン"""
        return {
            '記述': [
                r'問[一二三四五六七八九十]+.*について.*書きなさい',
                r'問[一二三四五六七八九十]+.*説明しなさい',
                r'問[一二三四五六七八九十]+.*述べなさい',
                r'〜について、.*字以内で.*書きなさい',
                r'〜について.*説明せよ',
                r'どのような.*か.*書きなさい',
                r'なぜ.*か.*説明しなさい',
            ],
            '選択': [
                r'問[一二三四五六七八九十]+.*選びなさい',
                r'次の[ア-オ]から.*選べ',
                r'最も適当なものを.*選びなさい',
                r'正しいものを.*選べ',
            ],
            '漢字・語句': [
                r'傍線部.*の読みを.*書きなさい',
                r'傍線部.*を漢字で書きなさい',
                r'□に入る.*語句を.*書きなさい',
                r'空欄.*に入る.*言葉',
            ],
            '抜き出し': [
                r'文中から.*抜き出しなさい',
                r'本文中の.*をそのまま.*書きなさい',
                r'該当する.*箇所を.*抜き出せ',
            ]
        }
    
    def get_source_patterns(self) -> List[str]:
        """武蔵特有の出典パターン"""
        return [
            r'（([^）]+)の文による）',  # 武蔵独特の形式
            r'（([^）]+)著）',
            r'『([^』]+)』\s*（([^）]+)）',
            r'『([^』]+)』\s*([^（）\s]+)',
            r'「([^」]+)」\s*（([^）]+)）',
        ]
    
    def _parse_source(self, match: re.Match) -> Optional[ExamSource]:
        """武蔵特有の出典解析"""
        try:
            groups = match.groups()
            raw_source = match.group()
            
            source = ExamSource(raw_source=raw_source)
            
            # 「の文による」形式の特別処理
            if 'の文による' in raw_source:
                # 最初のグループが著者名
                source.author = groups[0].strip() if groups else None
            elif len(groups) >= 2:
                # 通常の形式
                source.title = groups[0].strip()
                source.author = groups[1].strip()
            elif len(groups) == 1:
                # タイトルまたは著者のみ
                text = groups[0].strip()
                if '著' in raw_source or '作' in raw_source:
                    source.author = text
                else:
                    source.title = text
            
            return source
        except Exception:
            return None
    
    def detect_sections(self, text: str) -> List:
        """武蔵の大問検出（独自ロジック）"""
        sections = super().detect_sections(text)
        
        # 武蔵は通常2つの大問
        # 大問間の最小距離を確認
        filtered_sections = []
        for i, section in enumerate(sections):
            if i == 0:
                filtered_sections.append(section)
            else:
                prev_section = filtered_sections[-1]
                distance = section.start_pos - prev_section.end_pos
                
                # 武蔵特有の大問間距離チェック
                if distance >= 500 or len(section.text or "") >= 1000:
                    filtered_sections.append(section)
        
        return filtered_sections
    
    def estimate_theme(self, text: str) -> Optional[str]:
        """武蔵特有のテーマ推定"""
        # 武蔵は哲学的・思想的なテーマが多い
        musashi_themes = {
            '哲学・思想': ['考え', '思索', '人生', '価値', '意味', '本質'],
            '人間の内面': ['心', '感情', '意識', '精神', '内面'],
            '社会と個人': ['社会', '個人', '関係', '共同体', '役割'],
            '自然と人間': ['自然', '人間', '環境', '共生', '調和'],
        }
        
        max_count = 0
        estimated_theme = None
        
        for theme, keywords in musashi_themes.items():
            count = sum(text.count(keyword) for keyword in keywords)
            if count > max_count:
                max_count = count
                estimated_theme = theme
        
        return estimated_theme or super().estimate_theme(text)