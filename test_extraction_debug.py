#!/usr/bin/env python3
"""
問題抽出のデバッグスクリプト
"""

import logging
from modules.ocr_handler import OCRHandler
from modules.improved_question_extractor_v2 import ImprovedQuestionExtractorV2

# ロギング設定
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

def debug_extraction():
    """問題抽出をデバッグ"""
    
    # PDFファイルパス
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    # OCR処理
    print("PDFをOCR処理中...")
    ocr = OCRHandler()
    text = ocr.extract_text_from_pdf(pdf_path)
    
    # 最初の3000文字を表示
    print("\n=== OCRテキスト（最初の3000文字）===")
    print(text[:3000])
    print("\n" + "="*50 + "\n")
    
    # 問題抽出器を初期化
    extractor = ImprovedQuestionExtractorV2()
    
    # 階層構造を直接抽出
    print("階層構造を抽出中...")
    structure = extractor.hierarchical_extractor.extract_with_themes(text)
    
    print(f"\n=== 抽出された大問: {len(structure)}個 ===\n")
    
    for i, major in enumerate(structure):
        print(f"大問{i+1}: 番号='{major.number}', 問数={len(major.children)}")
        print(f"  テキスト冒頭: {major.text[:100] if major.text else 'なし'}...")
        
        # 最初の5問を表示
        for j, question in enumerate(major.children[:5]):
            print(f"    問{j+1}: 番号='{question.number}'")
            print(f"      テキスト冒頭: {question.text[:50] if question.text else 'なし'}...")
        
        if len(major.children) > 5:
            print(f"    ... 他{len(major.children)-5}問")
        print()
    
    # 全体の問題数をカウント
    counts = extractor.hierarchical_extractor.count_all_questions(structure)
    print(f"\n=== 問題数サマリー ===")
    print(f"大問: {counts['major']}個")
    print(f"問: {counts['question']}個")
    print(f"小問: {counts['subquestion']}個")
    print(f"合計: {sum(counts.values())}個")
    
    # extract_questionsメソッドの結果
    questions = extractor.extract_questions(text)
    print(f"\n=== extract_questionsの結果: {len(questions)}問 ===\n")
    
    # 大問ごとにグループ化
    by_major = {}
    for q_id, q_text in questions:
        if "大問" in q_id:
            major_num = q_id.split("-")[0] if "-" in q_id else q_id
            if major_num not in by_major:
                by_major[major_num] = []
            by_major[major_num].append(q_id)
    
    for major in sorted(by_major.keys()):
        print(f"{major}: {len(by_major[major])}問")
        for q_id in by_major[major][:3]:
            print(f"  - {q_id}")
        if len(by_major[major]) > 3:
            print(f"  ... 他{len(by_major[major])-3}問")

if __name__ == "__main__":
    debug_extraction()