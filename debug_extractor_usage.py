#!/usr/bin/env python3
"""
FixedSocialAnalyzerが使用しているextractorを確認
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.theme_extractor_enhanced import EnhancedThemeExtractor
from modules.theme_extractor_v2 import ThemeExtractorV2

def debug_extractor_usage():
    """FixedSocialAnalyzerの使用extractor確認"""
    
    problematic_text = "次の資料は明治時代の工業について述べたものです"
    
    print("=== Extractor使用状況の確認 ===")
    
    # FixedSocialAnalyzerのインスタンス作成
    analyzer = FixedSocialAnalyzer()
    
    print(f"analyzer.theme_extractor の型: {type(analyzer.theme_extractor)}")
    print(f"analyzer.theme_extractor: {analyzer.theme_extractor}")
    
    # 各extractorで個別テスト
    print("\n=== 各Extractor個別テスト ===")
    
    extractors = {
        'V2 (direct)': ThemeExtractorV2(),
        'Enhanced (direct)': EnhancedThemeExtractor(enable_web_search=False),
        'FixedAnalyzer': analyzer.theme_extractor
    }
    
    for name, extractor in extractors.items():
        if extractor is None:
            print(f"{name}: None")
            continue
            
        result = extractor.extract(problematic_text)
        print(f"{name}: '{result.theme}' (conf: {result.confidence:.2f})")
    
    # Import状況の確認
    print("\n=== Import状況確認 ===")
    import modules.social_analyzer_fixed as fixed_module
    print(f"USE_ENHANCED_EXTRACTOR: {fixed_module.USE_ENHANCED_EXTRACTOR}")
    print(f"USE_V2_EXTRACTOR: {fixed_module.USE_V2_EXTRACTOR}")
    print(f"USE_IMPROVED_EXTRACTOR: {fixed_module.USE_IMPROVED_EXTRACTOR}")
    
    # Enhanced ExtractorとV2 Extractorの除外パターン確認
    print("\n=== 除外パターン数確認 ===")
    v2 = ThemeExtractorV2()
    enhanced = EnhancedThemeExtractor(enable_web_search=False)
    
    print(f"V2 exclusion patterns: {len(v2.exclusion_patterns)}")
    print(f"Enhanced exclusion patterns: {len(enhanced.exclusion_patterns)}")
    
    # パターン内容の一部を確認
    print("\n=== 「次の」関連除外パターン確認 ===")
    for i, pattern in enumerate(v2.exclusion_patterns):
        if '次の' in pattern.pattern:
            print(f"V2 Pattern {i}: {pattern.pattern}")
    
    print()
    for i, pattern in enumerate(enhanced.exclusion_patterns):
        if '次の' in pattern.pattern:
            print(f"Enhanced Pattern {i}: {pattern.pattern}")


if __name__ == '__main__':
    debug_extractor_usage()