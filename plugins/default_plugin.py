"""
デフォルトプラグイン（汎用）
"""
from typing import List, Dict

from .base import SchoolAnalyzerPlugin, PluginInfo
from config.settings import Settings


class DefaultPlugin(SchoolAnalyzerPlugin):
    """汎用の入試問題解析プラグイン"""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="Default Analyzer",
            version="1.0.0",
            school_names=["*"],  # すべての学校に対応
            description="汎用の入試問題解析プラグイン",
            priority=0  # 最低優先度
        )
    
    def get_section_markers(self) -> List[str]:
        """標準的な大問マーカー"""
        return ['一', '二', '三', '四', '五', 'Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', 'Ⅴ', '１', '２', '３', '４', '５']
    
    def get_question_patterns(self) -> Dict[str, List[str]]:
        """標準的な設問パターン（Settings から取得）"""
        return Settings.QUESTION_PATTERNS
    
    def get_source_patterns(self) -> List[str]:
        """標準的な出典パターン"""
        return Settings.SOURCE_PATTERNS.get('default', [])
    
    def supports_school(self, school_name: str) -> bool:
        """すべての学校をサポート"""
        return True