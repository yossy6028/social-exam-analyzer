#!/usr/bin/env python3
"""
日本工業大学駒場中学校2023年社会科PDFの分析
"""

import sys
import os
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# モジュールのインポート
from modules.social_analyzer import SocialAnalyzer
from modules.ocr_handler import OCRHandler
from modules.hierarchical_question_manager import HierarchicalQuestionManager
from modules.theme_refinement import ThemeRefiner

def analyze_nichiko_2023():
    """日工大駒場中2023年の社会科PDFを分析"""
    
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    print("=" * 80)
    print("日本工業大学駒場中学校 2023年度 社会科入試問題分析")
    print("=" * 80)
    print()
    
    # OCRハンドラーの初期化
    ocr_handler = OCRHandler()
    
    try:
        # PDFからテキスト抽出
        print("【1. PDFからテキスト抽出中...】")
        text = ocr_handler.process_pdf(pdf_path)
        
        if not text:
            print("❌ テキストの抽出に失敗しました")
            return
        
        print(f"✅ テキスト抽出完了（{len(text)}文字）")
        print(f"   最初の500文字: {text[:500]}...")
        print()
        
        # 階層的問題抽出
        print("【2. 問題の階層構造を抽出中...】")
        hierarchy_manager = HierarchicalQuestionManager()
        hierarchical_questions = hierarchy_manager.extract_hierarchical_questions(text)
        flattened_questions = hierarchy_manager.get_flattened_questions()
        
        print(f"✅ {len(flattened_questions)}個の問題を検出")
        print()
        
        # 社会科分析
        print("【3. 社会科分析を実行中...】")
        analyzer = SocialAnalyzer()
        
        if hasattr(analyzer, 'analyze_document_with_hierarchy'):
            analysis_result = analyzer.analyze_document_with_hierarchy(text, flattened_questions)
        else:
            analysis_result = analyzer.analyze_document(text)
        
        print(f"✅ 分析完了")
        print()
        
        # Gemini APIによるテーマ強化（利用可能な場合）
        try:
            from modules.gemini_theme_analyzer import GeminiThemeAnalyzer
            gemini_analyzer = GeminiThemeAnalyzer()
            
            if gemini_analyzer.api_enabled and 'questions' in analysis_result:
                print("【4. Gemini APIでテーマを強化中...】")
                questions = analysis_result['questions']
                questions = gemini_analyzer.analyze_all_questions_with_api(questions)
                analysis_result['questions'] = questions
                print("✅ Gemini分析完了")
                print()
        except Exception as e:
            print(f"⚠️ Gemini分析はスキップされました: {e}")
            print()
        
        # テーマの精緻化
        if 'questions' in analysis_result:
            print("【5. テーマを精緻化中...】")
            theme_refiner = ThemeRefiner()
            questions = theme_refiner.refine_all_themes(analysis_result['questions'])
            analysis_result['questions'] = questions
            print("✅ 精緻化完了")
            print()
        
        # 統計情報の確認と再計算
        if 'statistics' not in analysis_result or not analysis_result['statistics']:
            print("【6. 統計情報を計算中...】")
            if 'questions' in analysis_result:
                analysis_result['statistics'] = analyzer._calculate_statistics(analysis_result['questions'])
                print("✅ 統計計算完了")
                print()
        
        # 結果の表示
        display_analysis_results(analysis_result)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"分析エラー: {e}")
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

def display_analysis_results(result):
    """分析結果を表示"""
    
    print("=" * 80)
    print("分析結果")
    print("=" * 80)
    print()
    
    # 基本情報
    print(f"【総問題数】 {result.get('total_questions', 0)}問")
    print()
    
    # 統計情報
    if 'statistics' in result and result['statistics']:
        stats = result['statistics']
        
        # 分野別分布
        print("【分野別出題状況】")
        if 'field_distribution' in stats:
            for field, data in stats['field_distribution'].items():
                if isinstance(data, dict) and 'count' in data:
                    print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
        print()
        
        # 資料活用状況
        print("【資料活用状況】")
        if 'resource_usage' in stats:
            sorted_resources = sorted(
                [(k, v) for k, v in stats['resource_usage'].items() if isinstance(v, dict)],
                key=lambda x: x[1].get('count', 0),
                reverse=True
            )[:5]
            for resource, data in sorted_resources:
                print(f"  {resource:10s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)")
        print()
        
        # 出題形式
        print("【出題形式分布】")
        if 'format_distribution' in stats:
            sorted_formats = sorted(
                [(k, v) for k, v in stats['format_distribution'].items() if isinstance(v, dict)],
                key=lambda x: x[1].get('count', 0),
                reverse=True
            )[:5]
            for fmt, data in sorted_formats:
                print(f"  {fmt:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
        print()
        
        # 時事問題
        print("【時事問題】")
        if 'current_affairs' in stats and isinstance(stats['current_affairs'], dict):
            ca_data = stats['current_affairs']
            print(f"  時事問題数: {ca_data.get('count', 0)}問 ({ca_data.get('percentage', 0):.1f}%)")
        print()
    
    # 問題詳細（最初の20問）
    print("【検出された問題とテーマ】")
    if 'questions' in result and result['questions']:
        questions = result['questions'][:20]  # 最初の20問のみ表示
        
        for q in questions:
            number = getattr(q, 'number', 'N/A')
            theme = getattr(q, 'theme', None)
            field = getattr(q, 'field', None)
            
            # フィールドの値を取得
            if hasattr(field, 'value'):
                field_str = field.value
            else:
                field_str = str(field) if field else '不明'
            
            # テーマの表示
            if theme:
                theme_str = theme
            else:
                # テーマがない場合、キーワードから生成
                keywords = getattr(q, 'keywords', [])
                if keywords:
                    theme_str = ', '.join(keywords[:3])
                else:
                    theme_str = '（テーマ未設定）'
            
            print(f"  {number:10s}: {theme_str:30s} [{field_str}]")
        
        if len(result['questions']) > 20:
            print(f"  ... 他 {len(result['questions']) - 20} 問")
    print()
    
    # 階層情報（あれば）
    if 'hierarchy_info' in result:
        print("【階層構造】")
        hierarchy = result['hierarchy_info']
        print(f"  大問数: {hierarchy.get('major_count', 0)}")
        print(f"  中問数: {hierarchy.get('minor_count', 0)}")
        print(f"  小問数: {hierarchy.get('sub_count', 0)}")

if __name__ == "__main__":
    print("分析を開始します...\n")
    result = analyze_nichiko_2023()
    
    if result:
        print("\n" + "=" * 80)
        print("✅ 分析が正常に完了しました")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ 分析に失敗しました")
        print("=" * 80)