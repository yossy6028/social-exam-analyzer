#!/usr/bin/env python3
"""
実際のPDFファイルでの分析テスト
"""

import sys
import os
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# モジュールのインポート
from modules.social_analyzer import SocialAnalyzer
from modules.social_excel_formatter import SocialExcelFormatter
from modules.ocr_handler import OCRHandler
from modules.hierarchical_question_manager import HierarchicalQuestionManager
from modules.theme_refinement import ThemeRefiner

def analyze_pdf(pdf_path):
    """PDFファイルを分析"""
    print(f"\n=== PDFファイルの分析開始 ===")
    print(f"ファイル: {Path(pdf_path).name}")
    print("=" * 60)
    
    # 各モジュールの初期化
    analyzer = SocialAnalyzer()
    formatter = SocialExcelFormatter()
    ocr_handler = OCRHandler()
    theme_refiner = ThemeRefiner()
    
    try:
        # PDFからテキスト抽出
        print("\n1. PDFからテキストを抽出中...")
        text = ocr_handler.process_pdf(pdf_path)
        
        if not text:
            print("❌ テキストの抽出に失敗しました")
            return None
            
        print(f"✅ テキスト抽出完了（{len(text)}文字）")
        
        # 階層的な問題番号管理システムで問題を抽出
        print("\n2. 問題を階層構造で抽出中...")
        hierarchy_manager = HierarchicalQuestionManager()
        hierarchical_questions = hierarchy_manager.extract_hierarchical_questions(text)
        flattened_questions = hierarchy_manager.get_flattened_questions()
        
        print(f"✅ {len(flattened_questions)}個の問題を検出")
        
        # 分析実行
        print("\n3. 問題を分析中...")
        if hasattr(analyzer, 'analyze_document_with_hierarchy'):
            analysis_result = analyzer.analyze_document_with_hierarchy(text, flattened_questions)
        else:
            analysis_result = analyzer.analyze_document(text)
        
        print(f"✅ 分析完了")
        
        # 統計情報の確認
        print("\n4. 統計情報の確認...")
        if 'statistics' in analysis_result:
            print("✅ 統計情報が生成されています")
            stats = analysis_result['statistics']
            print(f"   統計キー: {list(stats.keys())}")
        else:
            print("⚠️ 統計情報が存在しません - 再計算中...")
            if 'questions' in analysis_result:
                stats = analyzer._calculate_statistics(analysis_result['questions'])
                analysis_result['statistics'] = stats
                print("✅ 統計情報を再計算しました")
        
        # Gemini APIによるテーマ分析（可能な場合）
        try:
            from modules.gemini_theme_analyzer import GeminiThemeAnalyzer
            gemini_analyzer = GeminiThemeAnalyzer()
            
            if gemini_analyzer.api_enabled and 'questions' in analysis_result:
                print("\n5. Gemini APIでテーマを分析中...")
                questions = analysis_result['questions']
                questions = gemini_analyzer.analyze_all_questions_with_api(questions)
                analysis_result['questions'] = questions
                print("✅ Gemini分析完了")
        except Exception as e:
            print(f"⚠️ Gemini分析はスキップされました: {e}")
        
        # テーマの精緻化
        if 'questions' in analysis_result:
            print("\n6. テーマを精緻化中...")
            questions = theme_refiner.refine_all_themes(analysis_result['questions'])
            analysis_result['questions'] = questions
            print("✅ 精緻化完了")
        
        # 結果の表示
        display_results(analysis_result)
        
        # Excel保存オプション
        save_option = input("\nExcelファイルとして保存しますか？ (y/n): ")
        if save_option.lower() == 'y':
            output_path = Path(pdf_path).parent / f"{Path(pdf_path).stem}_分析結果.xlsx"
            save_to_excel(analysis_result, formatter, output_path, "日本工業大学駒場中学校", "2023")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

def display_results(analysis_result):
    """分析結果を表示（GUIのdisplay_resultsメソッドをシミュレート）"""
    if not analysis_result:
        print("\n分析結果がありません")
        return
    
    print("\n" + "=" * 60)
    print("分析結果サマリー")
    print("=" * 60)
    
    print(f"\n総問題数: {analysis_result.get('total_questions', 0)}問")
    
    if 'statistics' not in analysis_result:
        print("\n⚠️ 統計情報が不完全です")
        if 'questions' in analysis_result:
            print("\n検出された問題（最初の10問）:")
            for i, q in enumerate(analysis_result['questions'][:10], 1):
                num = getattr(q, 'number', f'問題{i}')
                theme = getattr(q, 'theme', '（テーマなし）')
                print(f"  {num}: {theme}")
        return
    
    stats = analysis_result['statistics']
    
    # 分野別分布
    print("\n【分野別出題状況】")
    if 'field_distribution' in stats and stats['field_distribution']:
        for field, data in stats['field_distribution'].items():
            if isinstance(data, dict) and 'count' in data and 'percentage' in data:
                print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    else:
        print("  （データなし）")
    
    # 資料活用状況
    print("\n【資料活用状況】")
    if 'resource_usage' in stats and stats['resource_usage']:
        valid_resources = [(k, v) for k, v in stats['resource_usage'].items() 
                          if isinstance(v, dict) and 'count' in v]
        if valid_resources:
            for resource, data in sorted(valid_resources, 
                                        key=lambda x: x[1].get('count', 0), 
                                        reverse=True)[:5]:
                print(f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)")
    else:
        print("  （データなし）")
    
    # 出題形式
    print("\n【出題形式分布】")
    if 'format_distribution' in stats and stats['format_distribution']:
        valid_formats = [(k, v) for k, v in stats['format_distribution'].items() 
                        if isinstance(v, dict) and 'count' in v]
        if valid_formats:
            for format_type, data in sorted(valid_formats,
                                           key=lambda x: x[1].get('count', 0),
                                           reverse=True)[:5]:
                print(f"  {format_type:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
    else:
        print("  （データなし）")
    
    # 時事問題
    print("\n【時事問題】")
    if 'current_affairs' in stats and isinstance(stats['current_affairs'], dict):
        count = stats['current_affairs'].get('count', 0)
        percentage = stats['current_affairs'].get('percentage', 0)
        print(f"  時事問題数: {count}問 ({percentage:.1f}%)")
    else:
        print("  （データなし）")
    
    # 問題とテーマのサンプル表示
    if 'questions' in analysis_result and analysis_result['questions']:
        print("\n【検出された問題とテーマ（最初の10問）】")
        for i, q in enumerate(analysis_result['questions'][:10], 1):
            num = getattr(q, 'number', f'問題{i}')
            theme = getattr(q, 'theme', '（テーマなし）')
            field = getattr(q, 'field', '')
            if hasattr(field, 'value'):
                field = field.value
            print(f"  {num}: [{field}] {theme}")

def save_to_excel(analysis_result, formatter, output_path, school, year):
    """Excel形式で保存"""
    try:
        print(f"\nExcelファイルを保存中: {output_path}")
        formatter.save_to_excel(analysis_result, str(output_path), school, year)
        print(f"✅ 保存完了: {output_path}")
    except Exception as e:
        print(f"❌ Excel保存エラー: {e}")

if __name__ == "__main__":
    # テスト対象のPDFファイル
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    if Path(pdf_path).exists():
        result = analyze_pdf(pdf_path)
        if result:
            print("\n✅ 分析が正常に完了しました")
        else:
            print("\n❌ 分析に失敗しました")
    else:
        print(f"❌ ファイルが見つかりません: {pdf_path}")