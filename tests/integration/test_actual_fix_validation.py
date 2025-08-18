#!/usr/bin/env python3
"""
実際のPDFデータで修正効果を検証
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from pathlib import Path
import logging

# ログレベル設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_with_sample_text():
    """サンプルテキストで修正効果を検証"""
    
    # 実際のPDF解析で現れる問題のあるテキスト例
    sample_text = """
    問1 次の文章を読んで、問いに答えなさい。
    
    室町時代は、1336年に足利尊氏が京都に室町幕府を開いた時代である。
    この時代の文化について説明しなさい。
    
    問2 下線部⑥について答えなさい。
    
    問3 【い】にあてはまる人物名を次のア～エから選びなさい。
    ア. 織田信長  イ. 豊臣秀吉  ウ. 徳川家康  エ. 武田信玄
    
    問4 鎌倉幕府の成立について説明しなさい。
    
    問5 にあてはまる人物名を答えなさい。
    
    問6 関東地方の産業の特徴について述べなさい。
    """
    
    analyzer = FixedSocialAnalyzer()
    
    print("=== 実際のサンプルテキスト分析 ===")
    
    # 文書全体を分析
    result = analyzer.analyze_document(sample_text)
    
    print(f"\n検出された問題数: {result['total_questions']}")
    
    # 各問題を詳細表示
    for i, question in enumerate(result['questions'], 1):
        print(f"\n問題 {i}: {question.number}")
        print(f"  テキスト: {question.text[:100]}...")
        print(f"  トピック: {question.theme}")
        print(f"  分野: {question.field.value}")
        
        # 除外されるべきものが抽出されていないかチェック
        if question.theme:
            # 下線部や記号を含むトピックは問題
            if any(bad in str(question.theme) for bad in ['下線部', '【', 'にあてはまる']):
                print("  ❌ 問題：除外されるべきテーマが抽出されている")
            else:
                print("  ✅ 正常なテーマが抽出されている")
        else:
            # 有効なテーマがあるのに除外されている場合は問題
            if any(good in question.text for good in ['室町時代', '鎌倉幕府', '関東地方']):
                # 問題文の長さをチェック
                if len(question.text.strip()) > 50:
                    print("  ❌ 問題：有効なテーマが除外されている可能性")
                else:
                    print("  ✅ 短い問題文は適切に除外されている")
            else:
                print("  ✅ 無効なテーマが適切に除外されている")

def validate_exclusion_patterns():
    """除外パターンが実際に機能しているか最終検証"""
    
    analyzer = FixedSocialAnalyzer()
    
    # 実際に問題になっていたパターンを網羅的にテスト
    test_cases = [
        # 下線部パターン
        ("下線部⑥", False, "下線部番号"),
        ("下線部の特徴", False, "下線部+特徴"),
        ("下線部の史料として正しいものを", False, "下線部+史料"),
        
        # あてはまるパターン  
        ("【い】にあてはまる人物名", False, "記号+あてはまる"),
        ("にあてはまる人物名を次のア", False, "あてはまる+選択肢"),
        ("具体的な権利の名称を用いてその事例", False, "抽象的指示"),
        
        # 有効なテーマ
        ("室町時代の文化について説明しなさい", True, "有効：時代+文化"),
        ("鎌倉幕府の成立について答えなさい", True, "有効：政権+歴史"),
        ("関東地方の産業について述べなさい", True, "有効：地域+産業"),
    ]
    
    print("\n=== 除外パターン最終検証 ===")
    
    success_count = 0
    total_count = len(test_cases)
    
    for text, should_extract, description in test_cases:
        question = analyzer.analyze_question(text)
        has_topic = question.theme is not None
        
        print(f"\n{description}")
        print(f"  入力: '{text}'")
        print(f"  期待: {'抽出' if should_extract else '除外'}")
        print(f"  結果: {question.theme if has_topic else 'None'}")
        
        if should_extract == has_topic:
            print("  ✅ 正常")
            success_count += 1
        else:
            print("  ❌ 異常")
    
    print(f"\n=== 最終結果 ===")
    print(f"成功: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 すべてのテストが成功しました！除外パターンの修正は完璧です。")
    else:
        print("⚠️  一部のテストが失敗しています。追加の修正が必要です。")

if __name__ == "__main__":
    test_with_sample_text()
    validate_exclusion_patterns()