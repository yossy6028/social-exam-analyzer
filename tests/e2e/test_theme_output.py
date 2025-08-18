"""
テーマ出力機能のテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.theme_knowledge_base import ThemeKnowledgeBase

def test_theme_knowledge():
    """知識ベースのテーマ決定をテスト"""
    kb = ThemeKnowledgeBase()
    
    # テストケース
    test_cases = [
        # 歴史
        ("鎌倉幕府が成立した後、源頼朝が征夷大将軍に任命された", "歴史"),
        ("明治維新により、日本は富国強兵と殖産興業を進めた", "歴史"),
        ("平安時代に藤原道長が摂関政治を行った", "歴史"),
        
        # 地理
        ("関東平野は日本最大の平野であり、利根川が流れている", "地理"),
        ("瀬戸内海式気候は降水量が少ないのが特徴", "地理"),
        ("京浜工業地帯は東京湾沿いに発達した", "地理"),
        
        # 公民
        ("日本国憲法の三大原則は国民主権、基本的人権の尊重、平和主義である", "公民"),
        ("国会は国権の最高機関であり、唯一の立法機関である", "公民"),
        ("選挙は普通選挙、平等選挙、直接選挙、秘密選挙の原則がある", "公民"),
        
        # 時事・総合
        ("SDGsの目標13は気候変動への対策である", "時事・総合"),
        ("地球温暖化により気温が上昇している", "時事・総合"),
    ]
    
    print("=" * 60)
    print("テーマ決定のテスト結果")
    print("=" * 60)
    
    for text, field in test_cases:
        theme = kb.determine_theme(text, field)
        print(f"\n【{field}】")
        print(f"問題文: {text[:40]}...")
        print(f"決定されたテーマ: {theme}")
    
    print("\n" + "=" * 60)
    print("テスト完了")

if __name__ == "__main__":
    test_theme_knowledge()