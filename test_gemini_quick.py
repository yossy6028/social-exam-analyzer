#!/usr/bin/env python3
"""
Gemini Analyzer クイックテスト
既存のOCRテキストを使用した簡易テスト
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gemini_analyzer import GeminiAnalyzer

def main():
    """クイックテスト実行"""
    
    print("=" * 60)
    print("Gemini Analyzer クイックテスト")
    print("=" * 60)
    
    # 環境変数を読み込み
    load_dotenv()
    
    # API キーの確認
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("\n❌ GEMINI_API_KEY が設定されていません")
        print("   .env ファイルを確認してください")
        return
    
    print(f"\n✅ API Key configured: {api_key[:10]}...")
    
    try:
        # Analyzerの初期化
        print("\nGeminiAnalyzer を初期化中...")
        analyzer = GeminiAnalyzer(api_key)
        print("✅ 初期化成功")
        
        # OCRテキストを読み込み
        ocr_file = project_root / "logs" / "ocr_2023_日工大駒場_社会.txt"
        
        if not ocr_file.exists():
            print(f"\n❌ OCRファイルが見つかりません: {ocr_file}")
            return
        
        with open(ocr_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"\n📄 OCRテキスト読み込み: {len(text)} 文字")
        
        # 最初の1000文字でテスト（高速化のため）
        test_text = text[:5000]
        
        print("\n🤖 Gemini AI分析を開始...")
        print("   (初回は数秒かかる場合があります)")
        
        # テキスト分析を実行
        result = analyzer.analyze_exam_structure(
            text=test_text,
            school="日本工業大学駒場中学校",
            year="2023"
        )
        
        print("\n✅ 分析完了！")
        print("=" * 60)
        
        # サマリー表示
        summary = result.get('summary', {})
        print(f"\n総問題数: {summary.get('total_questions', 0)}問")
        print(f"大問数: {result.get('total_sections', 0)}個")
        
        print("\n【分野別内訳】")
        print(f"  地理: {summary.get('geography_count', 0)}問")
        print(f"  歴史: {summary.get('history_count', 0)}問")
        print(f"  公民: {summary.get('civics_count', 0)}問")
        print(f"  時事: {summary.get('current_affairs_count', 0)}問")
        
        # 最初の大問の詳細
        if result.get('sections'):
            first_section = result['sections'][0]
            print(f"\n【大問{first_section['section_number']}の詳細】")
            print(f"問題数: {first_section.get('question_count', 0)}問")
            
            for q in first_section.get('questions', [])[:3]:
                print(f"  問{q['question_number']}: {q.get('theme', '不明')} [{q.get('field', '')}]")
        
        print("\n" + "=" * 60)
        print("テスト成功！Gemini Analyzer は正常に動作しています。")
        print("本番環境では analyze_pdf_with_vision() を使用すると")
        print("より高精度な分析が可能です。")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()