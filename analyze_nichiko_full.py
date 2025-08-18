#!/usr/bin/env python3
"""
日本工業大学駒場中学校2023年社会科PDFの完全分析
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Any
sys.path.insert(0, str(Path(__file__).parent))

from modules.ocr_handler import OCRHandler
from modules.social_analyzer import SocialAnalyzer, SocialQuestion, SocialField

def extract_all_questions(text: str) -> List[Dict[str, str]]:
    """すべての問題を抽出"""
    questions = []
    
    # 大問を探す（1 次の、2 次の、など）
    major_sections = re.split(r'([1-4])\s+次の', text)
    
    current_major = 0
    for i in range(1, len(major_sections), 2):
        if i < len(major_sections):
            current_major = major_sections[i]
            section_text = major_sections[i+1] if i+1 < len(major_sections) else ""
            
            # この大問内の問題を探す
            # 問1, 問2などのパターン
            problem_pattern = r'問(\d+)[^\d]'
            problems = re.split(problem_pattern, section_text)
            
            for j in range(1, len(problems), 2):
                if j < len(problems) and j+1 < len(problems):
                    q_num = problems[j]
                    q_text = problems[j+1][:500]  # 最初の500文字
                    
                    # 小問も探す (1), (2)など
                    sub_questions = re.findall(r'\((\d+)\)([^(）]+?)(?=\(\d+\)|$)', q_text)
                    
                    if sub_questions:
                        for sub_num, sub_text in sub_questions:
                            questions.append({
                                'number': f"大問{current_major}-問{q_num}({sub_num})",
                                'text': sub_text.strip()[:200]
                            })
                    else:
                        questions.append({
                            'number': f"大問{current_major}-問{q_num}",
                            'text': q_text.strip()[:200]
                        })
    
    return questions

def analyze_questions(questions: List[Dict[str, str]]) -> Dict[str, Any]:
    """問題を分析"""
    analyzer = SocialAnalyzer()
    analyzed = []
    
    for q in questions:
        result = analyzer.analyze_question(q['text'], q['number'])
        analyzed.append(result)
    
    # 統計を計算
    stats = analyzer._calculate_statistics(analyzed)
    
    return {
        'questions': analyzed,
        'statistics': stats,
        'total_questions': len(analyzed)
    }

def display_detailed_results(result: Dict[str, Any]):
    """詳細な結果を表示"""
    
    print("\n" + "=" * 80)
    print("【詳細分析結果】")
    print("=" * 80)
    
    # 総問題数
    print(f"\n◆ 総問題数: {result['total_questions']}問")
    
    # 統計情報
    if 'statistics' in result:
        stats = result['statistics']
        
        # 分野別
        print("\n◆ 分野別分布:")
        if 'field_distribution' in stats:
            for field, data in sorted(stats['field_distribution'].items()):
                print(f"  {field:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
        
        # 資料活用
        print("\n◆ 資料活用状況:")
        if 'resource_usage' in stats:
            sorted_res = sorted(
                [(k, v) for k, v in stats['resource_usage'].items() if isinstance(v, dict)],
                key=lambda x: x[1].get('count', 0),
                reverse=True
            )[:5]
            for res, data in sorted_res:
                print(f"  {res:12s}: {data['count']:3d}回")
        
        # 出題形式
        print("\n◆ 出題形式:")
        if 'format_distribution' in stats:
            for fmt, data in sorted(stats['format_distribution'].items()):
                print(f"  {fmt:10s}: {data['count']:3d}問")
    
    # 各問題の詳細
    print("\n◆ 問題別詳細分析:")
    print("-" * 80)
    
    if 'questions' in result:
        for q in result['questions']:
            number = getattr(q, 'number', 'N/A')
            text = getattr(q, 'text', '')[:80]
            field = getattr(q, 'field', None)
            theme = getattr(q, 'theme', None)
            keywords = getattr(q, 'keywords', [])
            resource_types = getattr(q, 'resource_types', [])
            question_format = getattr(q, 'question_format', None)
            
            # フィールドの値
            if hasattr(field, 'value'):
                field_str = field.value
            else:
                field_str = str(field) if field else '不明'
            
            # リソースの値
            resource_str = ', '.join([r.value if hasattr(r, 'value') else str(r) for r in resource_types])
            
            # フォーマットの値
            if hasattr(question_format, 'value'):
                format_str = question_format.value
            else:
                format_str = str(question_format) if question_format else '不明'
            
            print(f"\n▼ {number}")
            print("-" * 40)
            if theme:
                print(f"  テーマ: {theme}")
            else:
                if keywords:
                    print(f"  キーワード: {', '.join(keywords[:5])}")
                else:
                    print(f"  テーマ: （未設定）")
            print(f"  分野: {field_str}")
            print(f"  資料: {resource_str if resource_str else 'なし'}")
            print(f"  形式: {format_str}")
            print(f"  問題文: {text}...")

def main():
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    print("=" * 80)
    print("日本工業大学駒場中学校 2023年度 社会科入試問題")
    print("完全分析レポート")
    print("=" * 80)
    
    # OCR処理
    print("\n◆ PDFからテキスト抽出中...")
    ocr_handler = OCRHandler()
    text = ocr_handler.process_pdf(pdf_path)
    
    if not text:
        print("❌ テキスト抽出失敗")
        return
    
    print(f"✅ {len(text)}文字を抽出")
    
    # 問題抽出
    print("\n◆ 問題を抽出中...")
    questions = extract_all_questions(text)
    print(f"✅ {len(questions)}問を検出")
    
    # 分析
    print("\n◆ 社会科分析を実行中...")
    result = analyze_questions(questions)
    print(f"✅ 分析完了")
    
    # 結果表示
    display_detailed_results(result)
    
    print("\n" + "=" * 80)
    print("分析完了")
    print("=" * 80)

if __name__ == "__main__":
    main()