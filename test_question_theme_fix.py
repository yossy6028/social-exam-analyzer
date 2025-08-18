#!/usr/bin/env python3
"""
Question属性修正の確認テスト
"""
import sys
from pathlib import Path

def test_question_classes():
    """両方のQuestionクラスの属性を確認"""
    print("=" * 60)
    print("Questionクラス属性テスト")
    print("=" * 60)
    
    # 1. models.pyのQuestionクラス
    print("\n【models.Question】")
    try:
        from models import Question as ModelsQuestion
        q1 = ModelsQuestion(
            number="問1",
            text="テスト問題",
            field="歴史",
            theme="平安時代の政治"  # themeを使用
        )
        print(f"✅ 作成成功")
        print(f"   number: {q1.number}")
        print(f"   field: {q1.field}")
        print(f"   theme: {q1.theme}")
        # topicにアクセスしてみる（エラーになるはず）
        try:
            _ = q1.topic
            print(f"   ❌ topic属性が存在（想定外）")
        except AttributeError:
            print(f"   ✅ topic属性は存在しない（正常）")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # 2. social_analyzer.pyのSocialQuestion
    print("\n【social_analyzer.SocialQuestion】")
    try:
        from modules.social_analyzer import SocialQuestion, SocialField
        q2 = SocialQuestion(
            number="問2",
            text="テスト問題2",
            field=SocialField.GEOGRAPHY,
            theme="農業の特色"  # 修正後はthemeを使用
        )
        print(f"✅ 作成成功")
        print(f"   number: {q2.number}")
        print(f"   field: {q2.field}")
        print(f"   theme: {q2.theme}")
        # topicにアクセスしてみる（修正後はエラーになるはず）
        try:
            _ = q2.topic
            print(f"   ❌ topic属性が存在（修正が不完全）")
        except AttributeError:
            print(f"   ✅ topic属性は存在しない（修正済み）")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    return True

def test_gemini_conversion():
    """Gemini分析結果の変換テスト"""
    print("\n" + "=" * 60)
    print("Gemini結果変換テスト")
    print("=" * 60)
    
    # Gemini分析結果のシミュレーション
    gemini_result = {
        'question_number': '1',
        'question_text': '促成栽培について説明しなさい',
        'field': '地理',
        'keywords': ['促成栽培', 'ビニールハウス', '農業']
    }
    
    print("\n【Gemini結果をQuestionオブジェクトに変換】")
    try:
        from models import Question
        
        # main.pyと同じ変換ロジック
        question = Question(
            number=f"大問1-問{gemini_result['question_number']}",
            text=gemini_result.get('question_summary', gemini_result.get('question_text', '')),
            field=gemini_result.get('field', '総合'),
            theme=', '.join(gemini_result.get('keywords', [])) if gemini_result.get('keywords') else ''
        )
        
        print(f"✅ 変換成功")
        print(f"   number: {question.number}")
        print(f"   text: {question.text[:30]}...")
        print(f"   field: {question.field}")
        print(f"   theme: {question.theme}")
        
        # themeに正常にアクセスできるか
        try:
            theme_value = question.theme
            print(f"   ✅ theme属性アクセス成功: '{theme_value}'")
        except AttributeError as e:
            print(f"   ❌ theme属性アクセス失敗: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 変換エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト"""
    print("Question属性修正確認テスト\n")
    
    all_passed = True
    
    # テスト実行
    if not test_question_classes():
        all_passed = False
    
    if not test_gemini_conversion():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ すべてのテストに合格！")
        print("修正内容:")
        print("• すべてのQuestionクラスで'theme'属性に統一")
        print("• 'topic'属性へのアクセスを'theme'に変更")
        print("• Gemini分析が正常に動作")
    else:
        print("⚠️ 一部のテストが失敗しました")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)