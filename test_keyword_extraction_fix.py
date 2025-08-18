#!/usr/bin/env python3
"""
キーワード抽出改善のテスト
"""
import sys
sys.path.insert(0, '/Users/yoshiikatsuhiko/Desktop/02_開発 (Development)/social_exam_analyzer')

from modules.social_analyzer import SocialAnalyzer

def test_keyword_extraction():
    """改善されたキーワード抽出のテスト"""
    
    # テストケース
    test_cases = [
        {
            "text": """問1 次の文章が説明している平野を、地図中のア～カから1つ選び、記号で答えなさい。
            県内を流れるいくつかの河川によって土砂が堆積してできた平野である。
            南北約60kmにわたる範囲に広がるこの平野では、東京に野菜を出荷する近郊農業が盛んである。
            また、ビニールハウスなどの施設を利用した促成栽培も行われており、きゅうりやトマトなどが生産されている。""",
            "expected_keywords": ["促成栽培", "近郊農業"],
            "description": "大問1-問1: 農業関連"
        },
        {
            "text": """問9 リユースやリサイクルを促進し、循環型社会を実現するための法律について答えなさい。
            ペットボトルの回収率を向上させるための施策も含まれています。""",
            "expected_keywords": ["循環型社会", "リユース", "リサイクル", "ペットボトル"],
            "description": "大問1-問9: 環境問題"
        },
        {
            "text": """問1 弥生時代の農耕について、高床式倉庫の役割を説明しなさい。
            稲作農業の発展とともに、収穫した米を保管する施設が必要になりました。""",
            "expected_keywords": ["弥生時代", "高床式倉庫", "稲作農業"],
            "description": "大問2-問1: 歴史（弥生時代）"
        }
    ]
    
    analyzer = SocialAnalyzer()
    
    print("=" * 60)
    print("キーワード抽出テスト")
    print("=" * 60)
    
    all_passed = True
    
    for test_case in test_cases:
        text = test_case["text"]
        expected = test_case["expected_keywords"]
        description = test_case["description"]
        
        # キーワード抽出を実行
        extracted = analyzer._extract_keywords(text)
        
        print(f"\n【{description}】")
        print(f"抽出されたキーワード（上位10個）: {extracted[:10]}")
        
        # 期待されるキーワードが含まれているかチェック
        found = []
        not_found = []
        for kw in expected:
            if kw in extracted:
                found.append(kw)
            else:
                not_found.append(kw)
        
        if not_found:
            print(f"❌ 未抽出: {not_found}")
            all_passed = False
        else:
            print(f"✅ すべての重要語句を抽出")
        
        if found:
            print(f"   発見: {found}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ すべてのテストに合格！")
        print("重要語句の抽出が改善されました：")
        print("• 促成栽培、近郊農業などの農業用語")
        print("• 循環型社会などの環境用語")
        print("• 弥生時代、高床式倉庫などの歴史用語")
    else:
        print("⚠️  一部のキーワードが抽出されていません")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = test_keyword_extraction()
    sys.exit(0 if success else 1)