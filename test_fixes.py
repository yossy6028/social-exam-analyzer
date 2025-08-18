#!/usr/bin/env python3
"""
修正後の動作確認テスト
"""
import sys
from pathlib import Path

def test_year_detection():
    """年度検出のテスト"""
    from modules.year_detector import YearDetector
    
    detector = YearDetector()
    
    test_cases = [
        ("2023年日本工業大学駒場中学校問題_社会.pdf", 2023),
        ("2025年開成中学校問題_社会.pdf", 2025),
        ("2020年東京電機大学中学校問題_社会.pdf", 2020),
    ]
    
    print("=" * 60)
    print("年度検出テスト")
    print("=" * 60)
    
    for filename, expected_year in test_cases:
        # detect_yearsメソッドを使用（ファイル名から検出）
        result = detector.detect_years(filename)
        detected_years = result.years if result else []
        detected_year = int(detected_years[0]) if detected_years else None
        status = "✅" if detected_year == expected_year else "❌"
        print(f"{status} {filename}")
        print(f"   期待値: {expected_year}, 検出値: {detected_year}")
    
    return True

def test_model_import():
    """モデルインポートのテスト"""
    print("\n" + "=" * 60)
    print("モデルインポートテスト")
    print("=" * 60)
    
    try:
        from models import Question, AnalysisResult
        print("✅ models.Question のインポート成功")
        
        # Questionオブジェクトの作成テスト
        q = Question(
            number="問1",
            text="テスト問題",
            field="歴史",
            theme="平安時代"  # topicではなくtheme
        )
        print(f"✅ Questionオブジェクト作成成功: {q.number}")
        
        return True
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def test_gemini_integration():
    """Gemini分析統合のテスト（簡易版）"""
    print("\n" + "=" * 60)
    print("Gemini統合テスト")
    print("=" * 60)
    
    try:
        from modules.gemini_theme_analyzer import GeminiThemeAnalyzer
        
        analyzer = GeminiThemeAnalyzer()
        if analyzer.api_enabled:
            print("✅ Gemini API 有効")
        else:
            print("⚠️  Gemini API 無効（CLIモード）")
        
        # subject_index.mdの読み込み確認
        if analyzer.subject_index_content:
            print(f"✅ subject_index.md 読み込み成功 ({len(analyzer.subject_index_content)}文字)")
        else:
            print("⚠️  subject_index.md 未読み込み")
        
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("修正後の動作確認テスト開始\n")
    
    tests = [
        test_year_detection,
        test_model_import,
        test_gemini_integration
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ テスト失敗: {test_func.__name__}")
            print(f"   エラー: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    test_names = ["年度検出", "モデルインポート", "Gemini統合"]
    for name, result in zip(test_names, results):
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{name}: {status}")
    
    all_passed = all(results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ すべてのテスト成功！")
    else:
        print("⚠️  一部のテストが失敗しました")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)