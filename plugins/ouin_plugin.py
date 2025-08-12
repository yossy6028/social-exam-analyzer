"""
桜蔭中学校専用プラグイン
"""
from typing import List, Dict

from .base import SchoolAnalyzerPlugin, PluginInfo


class OuinPlugin(SchoolAnalyzerPlugin):
    """桜蔭中学校の入試問題解析プラグイン"""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Ouin Analyzer",
            version="1.0.0",
            school_names=["桜蔭中学校", "桜陰中学校"],  # 表記ゆれに対応
            description="桜蔭中学校の入試問題に特化した解析プラグイン",
            priority=10
        )
    
    def get_section_markers(self) -> List[str]:
        """桜蔭特有の大問マーカー"""
        return ['Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', '一', '二', '三', '四']
    
    def get_question_patterns(self) -> Dict[str, List[str]]:
        """桜蔭特有の設問パターン"""
        return {
            '記述': [
                r'問[１-９].*について.*説明しなさい',
                r'問[１-９].*述べなさい',
                r'〜を.*字以内で.*書きなさい',
                r'〜の理由を.*答えなさい',
                r'どのような.*か、.*説明しなさい',
                r'あなたの考えを.*書きなさい',
            ],
            '選択': [
                r'問[１-９].*から選びなさい',
                r'ア〜[オカ]の中から.*選べ',
                r'適切なものを.*記号で答えなさい',
                r'当てはまるものを.*選びなさい',
            ],
            '漢字・語句': [
                r'傍線[①-⑩].*の読みを.*書きなさい',
                r'傍線[①-⑩].*を漢字で.*書きなさい',
                r'（\s*）に入る.*語句',
                r'空欄[ア-オ]に.*当てはまる',
            ],
            '抜き出し': [
                r'文中から.*抜き出して.*答えなさい',
                r'本文から.*字で.*抜き出しなさい',
                r'該当する.*言葉を.*書き抜きなさい',
            ]
        }
    
    def get_source_patterns(self) -> List[str]:
        """桜蔭特有の出典パターン"""
        return [
            r'『([^』]+)』\s*([^（）\s]+)',
            r'「([^」]+)」より\s*（([^）]+)）',
            r'([^（）\s]+)\s*作\s*『([^』]+)』',
            r'※.*『([^』]+)』.*より',
        ]