#!/usr/bin/env python3
"""
シンプルなデバッグスクリプト
"""

# サンプルテキスト（実際のPDFから抽出されたパターン）
sample_text = """
社会

1 次の文章を読み、各問いに答えなさい。
(1) 雨温図について答えなさい
(2) 野菜栽培について答えなさい
(3) 地形図を読み取りなさい
(4) 津久井湖について答えなさい
(5) 平野の特色を答えなさい
(6) 地形図の記号について答えなさい
(7) 地形図の読み取りについて答えなさい
(8) 川の流れについて答えなさい
(9) 農業について答えなさい
(10) 山地について答えなさい
(11) 気候について答えなさい

2 次の年表を見て、各問いに答えなさい。
(1) 平野の特色について答えなさい
(2) リサイクルについて答えなさい
(3) 明治時代について答えなさい
"""

from modules.improved_question_extractor_v2 import ImprovedQuestionExtractorV2

def test_simple():
    extractor = ImprovedQuestionExtractorV2()
    
    # 階層構造を抽出
    structure = extractor.hierarchical_extractor.extract_with_themes(sample_text)
    
    print(f"検出された大問数: {len(structure)}")
    
    for i, major in enumerate(structure):
        print(f"\n大問{major.number}:")
        print(f"  問数: {len(major.children)}")
        for j, question in enumerate(major.children[:5]):
            print(f"    問{question.number}")

if __name__ == "__main__":
    test_simple()