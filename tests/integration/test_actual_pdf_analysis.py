#!/usr/bin/env python3
"""実際のPDFファイルでの大問検出テスト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.theme_extractor_v2 import ThemeExtractorV2
import logging

# ロギング設定
logging.basicConfig(level=logging.DEBUG)

def test_actual_pdf():
    """実際のPDFから抽出されたテキストでテスト"""
    
    # サンプルテキスト（実際の入試問題を模擬）
    test_text = """
    1. 次の文章を読んで、問1から問12までの問いに答えなさい。
    
    問1 次の写真は、淡路島と本州を結ぶ橋である。兵庫県について説明しなさい。
    
    問2 平等院鳳凰堂について正しいものを選びなさい。
    
    問3 日宋貿易について説明しなさい。
    
    問4 鎌倉幕府の成立について答えなさい。
    
    問5 下線部①について説明しなさい。
    
    問6 下線部②について説明しなさい。
    
    問7 江戸時代の身分制度について答えなさい。
    
    問8 【ア】にあてはまる語句を答えなさい。
    
    問9 【い】にあてはまる人物名を漢字で答えなさい。
    
    問10 大日本帝国憲法について説明しなさい。
    
    問11 阪神淡路大震災について述べなさい。
    
    問12 新聞記事を読んで答えなさい。
    
    2. 次の資料を見て、問1から問12までの問いに答えなさい。
    
    問1 内閣総理大臣の役割について説明しなさい。
    
    問2 内閣総理大臣の選出方法について答えなさい。
    
    問3 改正公職選挙法施行後の変化について述べなさい。
    
    問4 日本国憲法の三原則について答えなさい。
    
    問5 国民の三大義務について説明しなさい。
    
    問6 検察審査会の役割について答えなさい。
    
    問7 衆議院議員選挙の仕組みについて説明しなさい。
    
    問8 同年アメリカ合衆国で起きた出来事を答えなさい。
    
    問9 企業の社会的責任について説明しなさい。
    
    問10 政党は実現したい政策を国民に示す。これを何というか。
    
    問11 国連の役割について説明しなさい。
    
    問12 社会保障制度について答えなさい。
    
    3. 次の地図を見て、問1から問5までの問いに答えなさい。
    
    問1 全欧安全保障協力会議について説明しなさい。
    
    問2 下線部③について答えなさい。
    
    問3 核兵器禁止条約について説明しなさい。
    
    問4 アメリカ大統領の権限について答えなさい。
    
    問5 NATOに加盟する国を選びなさい。
    """
    
    analyzer = FixedSocialAnalyzer()
    extractor = ThemeExtractorV2()
    
    # 問題を抽出
    questions = analyzer._extract_with_reset_detection(test_text)
    
    print("=" * 60)
    print("実際のPDF形式での大問検出テスト")
    print("=" * 60)
    
    # 大問ごとに集計
    large_sections = {}
    for q_id, q_text in questions:
        # テーマ抽出
        theme_result = extractor.extract(q_text)
        theme = theme_result.theme if theme_result.theme else "（テーマなし）"
        
        if '-' in q_id:
            large_num = q_id.split('-')[0]
            if large_num not in large_sections:
                large_sections[large_num] = []
            large_sections[large_num].append((q_id, theme))
    
    print(f"\n検出された大問数: {len(large_sections)}")
    
    for section, items in sorted(large_sections.items()):
        print(f"\n{section}: {len(items)}問")
        for q_id, theme in items[:5]:  # 最初の5問だけ表示
            status = "❌" if "下線部" in theme or "【" in theme or "にあてはまる" in theme else "✅"
            print(f"  {status} {q_id}: {theme}")
        if len(items) > 5:
            print(f"  ... 他{len(items)-5}問")

if __name__ == "__main__":
    test_actual_pdf()