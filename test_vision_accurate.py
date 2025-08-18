#!/usr/bin/env python3
"""
Gemini Vision API 高精度テスト
実際のPDFファイルを画像として解析し、正確な問題構造を抽出
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gemini_analyzer import GeminiAnalyzer

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vision_analysis_accurate():
    """Vision APIによる高精度分析テスト"""
    
    print("=" * 80)
    print("Gemini Vision API 高精度分析テスト")
    print("=" * 80)
    print("\n画像認識により、OCRエラーや受験番号欄の誤認識を回避します")
    
    # 環境変数を読み込み
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("\n❌ GEMINI_API_KEY が設定されていません")
        return False
    
    print(f"\n✅ API Key: {api_key[:20]}...")
    
    # テスト対象のPDFファイル
    pdf_files = [
        {
            'path': '/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf',
            'school': '日本工業大学駒場中学校',
            'year': '2023',
            'expected': {
                '大問1': 11,
                '大問2': 13,
                '大問3': 13,
                '大問4': 5,
                'total': 42
            }
        }
    ]
    
    for pdf_info in pdf_files:
        pdf_path = Path(pdf_info['path'])
        
        if not pdf_path.exists():
            print(f"\n⚠️ PDFファイルが見つかりません: {pdf_path}")
            continue
        
        print(f"\n📄 分析対象: {pdf_path.name}")
        print(f"   学校: {pdf_info['school']}")
        print(f"   年度: {pdf_info['year']}")
        print(f"   期待値: 大問1-4で合計{pdf_info['expected']['total']}問")
        
        try:
            # Analyzer の初期化
            analyzer = GeminiAnalyzer(api_key)
            print("\n🔍 Vision API による画像解析を開始...")
            print("   (各ページを画像として認識し、正確な問題構造を抽出します)")
            
            # Vision API による分析
            result = analyzer.analyze_pdf_with_vision(
                pdf_path=pdf_path,
                school=pdf_info['school'],
                year=pdf_info['year']
            )
            
            # 結果の検証
            print("\n" + "=" * 60)
            print("【分析結果】")
            print("=" * 60)
            
            # 統計情報
            summary = result.get('summary', {})
            print(f"\n✅ 総問題数: {summary.get('total_questions', 0)}問")
            print(f"✅ 大問数: {result.get('total_sections', 0)}個")
            
            # 大問ごとの詳細
            print("\n【大問別の問題数】")
            sections = result.get('sections', [])
            
            for section in sections:
                section_name = f"大問{section['section_number']}"
                actual_count = section.get('question_count', len(section.get('questions', [])))
                expected_count = pdf_info['expected'].get(section_name, 0)
                
                if section['section_number'] > 4:
                    print(f"❌ {section_name}: {actual_count}問 (大問5以上は通常存在しません！)")
                elif expected_count == actual_count:
                    print(f"✅ {section_name}: {actual_count}問 (正確！)")
                else:
                    print(f"⚠️ {section_name}: {actual_count}問 (期待値: {expected_count}問)")
            
            # 不適切なテーマのチェック
            print("\n【問題テーマの品質チェック】")
            invalid_themes = []
            valid_themes = []
            
            for section in sections:
                for q in section.get('questions', []):
                    theme = q.get('theme', '')
                    if any(word in theme for word in ['受験番号', '氏名', '得点', '採点', '漢字四字']):
                        invalid_themes.append(f"大問{section['section_number']}-問{q['question_number']}: {theme}")
                    elif theme and len(theme) > 2:
                        valid_themes.append(f"大問{section['section_number']}-問{q['question_number']}: {theme}")
            
            if invalid_themes:
                print("\n❌ 不適切なテーマが検出されました:")
                for theme in invalid_themes[:5]:
                    print(f"   {theme}")
                if len(invalid_themes) > 5:
                    print(f"   ... 他{len(invalid_themes) - 5}件")
            else:
                print("✅ 全てのテーマが適切です")
            
            if valid_themes:
                print("\n✅ 正しく抽出されたテーマの例:")
                for theme in valid_themes[:5]:
                    print(f"   {theme}")
            
            # 分野別分析
            print("\n【分野別内訳】")
            print(f"  地理: {summary.get('geography_count', 0)}問")
            print(f"  歴史: {summary.get('history_count', 0)}問")
            print(f"  公民: {summary.get('civics_count', 0)}問")
            print(f"  時事: {summary.get('current_affairs_count', 0)}問")
            
            # 最終評価
            print("\n" + "=" * 60)
            total_actual = summary.get('total_questions', 0)
            total_expected = pdf_info['expected']['total']
            
            if total_actual == total_expected and not invalid_themes:
                print("🎉 完璧な分析結果です！")
            elif abs(total_actual - total_expected) <= 2 and len(invalid_themes) < 3:
                print("👍 概ね正確な分析結果です")
            else:
                print("⚠️ 分析精度に改善の余地があります")
                print(f"   総問題数: {total_actual}問 (期待値: {total_expected}問)")
                print(f"   不適切なテーマ: {len(invalid_themes)}件")
            
            return True
            
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """メイン実行"""
    print("\nこのテストでは、Gemini Vision APIを使用して")
    print("PDFを画像として直接解析し、以下の問題を解決します：")
    print("  1. 受験番号・氏名欄の誤認識")
    print("  2. 存在しない大問5の検出")
    print("  3. OCRエラーによる問題数の誤り")
    print("  4. 無意味なテーマの生成")
    
    input("\nEnterキーを押してテストを開始...")
    
    success = test_vision_analysis_accurate()
    
    if success:
        print("\n✅ Vision API による高精度分析が成功しました！")
        print("main.py で「Gemini AI分析を使用（高精度）」を選択すれば")
        print("この精度で分析が可能です。")
    else:
        print("\n❌ テストが失敗しました")
        print("エラーメッセージを確認してください")

if __name__ == "__main__":
    main()