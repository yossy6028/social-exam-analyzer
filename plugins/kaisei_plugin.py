"""
開成中学校専用プラグイン
"""
from typing import List, Dict

from .base import SchoolAnalyzerPlugin, PluginInfo


class KaiseiPlugin(SchoolAnalyzerPlugin):
    """開成中学校の入試問題解析プラグイン"""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Kaisei Analyzer",
            version="1.0.0",
            school_names=["開成中学校"],
            description="開成中学校の入試問題に特化した解析プラグイン",
            priority=10
        )
    
    def get_section_markers(self) -> List[str]:
        """開成特有の大問マーカー"""
        return ['一', '二', '三', '四']
    
    def get_question_patterns(self) -> Dict[str, List[str]]:
        """開成特有の設問パターン"""
        return {
            '記述': [
                r'問\d+.*について.*説明しなさい',
                r'問\d+.*述べなさい',
                r'〜について.*字以内で.*答えなさい',
                r'理由を.*説明せよ',
                r'どのような.*か.*答えなさい',
                r'\d+字以内で.*まとめなさい',
            ],
            '選択': [
                r'問\d+.*選びなさい',
                r'ア〜[オカキク]から.*選べ',
                r'最も適切なものを.*番号で答えなさい',
                r'正しいものを.*すべて選べ',
            ],
            '漢字・語句': [
                r'傍線部.*の読みを.*ひらがなで.*書きなさい',
                r'傍線部.*を漢字に.*直しなさい',
                r'空欄.*に適する.*語句',
                r'次の.*の意味を.*答えなさい',
            ],
            '抜き出し': [
                r'文中から.*字で.*抜き出しなさい',
                r'本文中から.*探して.*書きなさい',
                r'該当する.*部分を.*抜き出せ',
            ]
        }
    
    def get_source_patterns(self) -> List[str]:
        """開成特有の出典パターン"""
        return [
            r'『([^』]+)』\s*([^（）\s]+)\s*著',
            r'「([^」]+)」\s*（([^）]+)）',
            r'([^（）\s]+)\s*『([^』]+)』',
            r'出典：(.+)',
        ]