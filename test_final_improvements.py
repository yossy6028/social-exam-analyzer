#!/usr/bin/env python3
"""
最終的なテーマ抽出改善テスト
"""

from modules.improved_theme_extractor import ImprovedThemeExtractor

def test_final_improvements():
    """最終改善テスト"""
    
    extractor = ImprovedThemeExtractor()
    
    # ユーザーが報告した問題のあるテーマの実際の問題文
    problematic_cases = [
        {
            'original_theme': '下線④',
            'text': '下線④について、まちがっている文章を、次のア~エの中から一つ選び記号で答えなさい。',
            'expected': None  # 問題形式なのでNoneが期待される
        },
        {
            'original_theme': '空欄補充',
            'text': '空らん(⑤)について、空らんに適切な語句を答えなさい。',
            'expected': None  # 参照型でコンテキストがないのでNone
        },
        {
            'original_theme': 'この時期',
            'text': '下線④について、次の(1)と(2)の設問に答えなさい。(1)この時期に生まれた人たちの現在の年代を、次のア~エの中から一つ選び記号で答えなさい。',
            'expected': None  # 参照型でコンテキストがないのでNone
        },
        {
            'original_theme': '各都市',
            'text': '下線⑥について、次のグラフA〜Dは、首都圏にある人口20万人規模の各都市について、昼間と夜間の人口をあらわしたものです。',
            'expected': '首都圏の都市' # または'主要都市の人口'
        },
        {
            'original_theme': 'まちがっている文章を',
            'text': '下線④について、まちがっている文章を、次のア~エの中から一つ選び記号で答えなさい。',
            'expected': None  # 問題形式なのでNone
        },
        {
            'original_theme': '正しい文章を',
            'text': '下線⑤について、正しい文章を、次のア~エの中から一つ選び記号で答えなさい。',
            'expected': None  # 問題形式なのでNone
        },
        # 良いテーマの例
        {
            'original_theme': '日本列島の成立',
            'text': 'この頃の日本のようすについて正しい文章を、次のア~エの中から一つ選び記号で答えなさい。ア,ユーラシア大陸と陸続きでナウマンゾウがやってきた。',
            'expected': '日本列島の成立'
        },
        {
            'original_theme': '聖徳太子',
            'text': '空らん(⑧)について、空らんに適切な人名を、次のア~エの中から一つ選び記号で答えなさい。ア.蘇我入鹿 イ.聖徳太子 ウ.中大兄皇子 エ.中臣鎌足',
            'expected': '聖徳太子'  # 選択肢から推測
        },
        {
            'original_theme': '三大都市圏',
            'text': '下線⑤について、その中心となる都市の組み合わせを、次のア~エの中から一つ選び記号で答えなさい。ア.東京-大阪-京都 ウ.東京-大阪-名古屋',
            'expected': '三大都市圏'
        }
    ]
    
    print("=== 最終的なテーマ抽出改善テスト ===\n")
    
    success_count = 0
    partial_count = 0
    fail_count = 0
    
    for i, case in enumerate(problematic_cases, 1):
        print(f"ケース {i}: 元のテーマ「{case['original_theme']}」")
        print(f"  問題文: {case['text'][:80]}...")
        
        result = extractor.extract_theme(case['text'])
        extracted = result.theme
        confidence = result.confidence
        
        print(f"  抽出結果: {extracted if extracted else 'None'} (信頼度: {confidence:.2f})")
        print(f"  期待値: {case['expected'] if case['expected'] else 'None'}")
        
        # 評価
        if case['expected'] is None:
            if extracted is None:
                print("  ✅ 成功: 適切に除外")
                success_count += 1
            else:
                print(f"  ❌ 失敗: 除外すべきだが「{extracted}」を抽出")
                fail_count += 1
        else:
            if extracted == case['expected']:
                print("  ✅ 成功: 正しく抽出")
                success_count += 1
            elif extracted and extracted not in ['下線④', 'この時期', '各都市', '空欄補充', 'まちがっている', '正しい']:
                print(f"  ⚠️  部分的成功: 期待と異なるが改善「{extracted}」")
                partial_count += 1
            else:
                print(f"  ❌ 失敗: 期待「{case['expected']}」だが「{extracted}」")
                fail_count += 1
        
        print("-" * 60)
    
    total = len(problematic_cases)
    print(f"\n=== 結果サマリー ===")
    print(f"成功: {success_count}/{total} ({success_count/total*100:.1f}%)")
    print(f"部分的成功: {partial_count}/{total} ({partial_count/total*100:.1f}%)")
    print(f"失敗: {fail_count}/{total} ({fail_count/total*100:.1f}%)")
    print(f"総合成功率: {(success_count + partial_count)/total*100:.1f}%")
    
    if success_count + partial_count >= total * 0.8:
        print("\n✅ テーマ抽出の改善は成功しました！")
        print("問題のあったテーマ（下線④、この時期、各都市、まちがっている文章を、正しい文章を）が")
        print("適切に除外またはより具体的な内容に変換されています。")
    else:
        print("\n⚠️  さらなる改善が必要です。")

if __name__ == "__main__":
    test_final_improvements()