#!/usr/bin/env python3
"""
GUI修正の最終確認
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# main.pyのdisplay_resultsメソッドが正しく修正されているか確認
def verify_display_results_fix():
    """display_resultsメソッドの修正確認"""
    print("=== display_resultsメソッドの修正確認 ===\n")
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正が含まれているか確認
    checks = [
        ("統計情報の存在チェック", "'statistics' not in self.analysis_result"),
        ("フィールド分布の妥当性チェック", "isinstance(data, dict) and 'count' in data"),
        ("リソース使用の妥当性チェック", "valid_resources = [(k, v) for k, v in stats['resource_usage'].items()"),
        ("フォーマット分布の妥当性チェック", "valid_formats = [(k, v) for k, v in stats['format_distribution'].items()"),
        ("統計情報の再計算", "self.analyzer._calculate_statistics(questions)"),
        ("データなし表示", "（データなし）")
    ]
    
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ {check_name}: OK")
        else:
            print(f"❌ {check_name}: 見つかりません")
    
    return all(check_string in content for _, check_string in checks)

def test_statistics_calculation():
    """統計計算の動作確認"""
    print("\n=== 統計計算の動作確認 ===\n")
    
    from modules.social_analyzer import SocialAnalyzer, SocialQuestion, SocialField, ResourceType, QuestionFormat
    
    # テスト用の問題
    test_questions = [
        SocialQuestion(
            number="問1",
            text="テスト問題",
            field=SocialField.HISTORY,
            resource_types=[ResourceType.MAP],
            question_format=QuestionFormat.SHORT_ANSWER,
            theme="テストテーマ"
        )
    ]
    
    # 統計計算
    analyzer = SocialAnalyzer()
    stats = analyzer._calculate_statistics(test_questions)
    
    # 結果確認
    print(f"統計キー: {list(stats.keys())}")
    
    required_keys = ['field_distribution', 'resource_usage', 'format_distribution', 'current_affairs', 'has_resources']
    for key in required_keys:
        if key in stats:
            print(f"✅ {key}: 存在")
        else:
            print(f"❌ {key}: 存在しない")
    
    # 各統計の詳細確認
    if 'field_distribution' in stats:
        print(f"\n分野別分布: {stats['field_distribution']}")
        for field, data in stats['field_distribution'].items():
            if isinstance(data, dict) and 'count' in data and 'percentage' in data:
                print(f"  ✅ {field}: 正しい形式")
            else:
                print(f"  ❌ {field}: 不正な形式")
    
    return all(key in stats for key in required_keys)

def main():
    """メイン処理"""
    print("GUI表示問題の修正確認\n")
    print("=" * 60)
    
    # display_resultsメソッドの修正確認
    fix_verified = verify_display_results_fix()
    
    # 統計計算の動作確認
    stats_working = test_statistics_calculation()
    
    print("\n" + "=" * 60)
    print("\n【最終確認結果】")
    
    if fix_verified and stats_working:
        print("✅ すべての修正が正しく適用されています")
        print("✅ GUI表示問題は解決されました")
    else:
        if not fix_verified:
            print("⚠️ display_resultsメソッドの修正が不完全です")
        if not stats_working:
            print("⚠️ 統計計算に問題があります")
    
    print("\n【次のステップ】")
    print("1. GUIアプリケーションを起動: python3 main.py")
    print("2. PDFファイルを選択して分析を実行")
    print("3. 分析結果が正しく表示されることを確認")
    print("\n注意: PDFのOCR処理には時間がかかる場合があります")

if __name__ == "__main__":
    main()