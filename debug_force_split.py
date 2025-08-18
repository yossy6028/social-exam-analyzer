#!/usr/bin/env python3
"""
強制分割の動作をデバッグ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.improved_question_extractor import ImprovedQuestionExtractor

def debug_force_split():
    """強制分割の動作をデバッグ"""
    
    print("=== 強制分割の動作をデバッグ ===\n")
    
    # ImprovedQuestionExtractorのインスタンスを作成
    extractor = ImprovedQuestionExtractor()
    
    # 実際のOCRテキストファイルを読み込み
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    try:
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_text = f.read()
    except FileNotFoundError:
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    print(f"📁 OCRファイル: {ocr_file}")
    print(f"📊 ファイルサイズ: {len(ocr_text)} 文字")
    print(f"📝 行数: {len(ocr_text.split())} 行")
    
    print("\n" + "="*50)
    print("段階的な検出戦略のテスト:")
    
    # 各戦略を個別にテスト
    strategies = [
        ("明示的パターン", extractor._detect_by_explicit_patterns),
        ("内容分析", extractor._detect_by_content_analysis),
        ("問題番号リセット", extractor._detect_by_question_reset)
    ]
    
    for name, strategy in strategies:
        print(f"\n--- {name} ---")
        try:
            result = strategy(ocr_text)
            print(f"結果: {len(result)}個の大問")
            for i, (major_num, section_text) in enumerate(result):
                print(f"  大問{major_num}: {len(section_text)}文字")
        except Exception as e:
            print(f"エラー: {e}")
    
    print("\n" + "="*50)
    print("強制分割のテスト:")
    
    try:
        force_result = extractor._force_three_major_sections(ocr_text)
        print(f"強制分割結果: {len(force_result)}個の大問")
        for i, (major_num, section_text) in enumerate(force_result):
            print(f"  大問{major_num}: {len(section_text)}文字")
            print(f"    内容: {section_text[:100]}...")
    except Exception as e:
        print(f"エラー: {e}")
    
    print("\n" + "="*50)
    print("最終的な大問検出のテスト:")
    
    try:
        final_result = extractor._find_major_sections(ocr_text)
        print(f"最終結果: {len(final_result)}個の大問")
        for i, (major_num, section_text) in enumerate(final_result):
            print(f"  大問{major_num}: {len(section_text)}文字")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    debug_force_split()
