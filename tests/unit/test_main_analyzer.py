#\!/usr/bin/env python3
"""
main.pyで使用されるアナライザーをテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# main.pyと同じインポート方法を使用
try:
    from modules.social_analyzer_fixed import FixedSocialAnalyzer as SocialAnalyzer
    print("✅ FixedSocialAnalyzerを使用")
except ImportError:
    try:
        from modules.social_analyzer_improved import ImprovedSocialAnalyzer as SocialAnalyzer
        print("⚠️ ImprovedSocialAnalyzerを使用")
    except ImportError:
        from modules.social_analyzer import SocialAnalyzer
        print("❌ 基本のSocialAnalyzerを使用")

# テスト実行
analyzer = SocialAnalyzer()

# テーマ抽出器の確認
if hasattr(analyzer, 'theme_extractor'):
    print(f"  theme_extractor: {type(analyzer.theme_extractor)}")
else:
    print("  theme_extractor: なし")

if hasattr(analyzer, 'theme_extractor_v2'):
    print(f"  theme_extractor_v2: {type(analyzer.theme_extractor_v2)}")
else:
    print("  theme_extractor_v2: なし")

# 実際のテスト
test_text = "江戸時代の農業について説明しなさい。"
question = analyzer.analyze_question(test_text)

print(f"\nテスト結果:")
print(f"  テキスト: {test_text}")
print(f"  抽出テーマ: {question.topic}")
print(f"  分野: {question.field.value}")
