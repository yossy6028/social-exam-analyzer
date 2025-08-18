#!/usr/bin/env python3
"""
Gemini Analyzerのテストスクリプト
Gemini APIを使用した高精度分析のテスト
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

def test_gemini_text_analysis():
    """テキストベースの分析テスト"""
    
    logger.info("=" * 60)
    logger.info("Gemini テキスト分析テスト")
    logger.info("=" * 60)
    
    # 環境変数を読み込み
    load_dotenv()
    
    # API キーの確認
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY が設定されていません")
        logger.info("以下の方法で設定してください:")
        logger.info("1. .env ファイルを作成")
        logger.info("2. GEMINI_API_KEY=your-api-key を追記")
        logger.info("3. https://makersuite.google.com/app/apikey でAPIキーを取得")
        return False
    
    try:
        # Analyzerの初期化
        analyzer = GeminiAnalyzer(api_key)
        logger.info("GeminiAnalyzer 初期化成功")
        
        # OCRテキストを読み込み（既存のログから）
        ocr_file = project_root / "logs" / "ocr_2023_日工大駒場_社会.txt"
        
        if not ocr_file.exists():
            logger.error(f"OCRファイルが見つかりません: {ocr_file}")
            return False
        
        with open(ocr_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"OCRテキスト読み込み: {len(text)} 文字")
        
        # テキスト分析を実行
        logger.info("\nテキスト分析を開始...")
        result = analyzer.analyze_exam_structure(
            text=text,
            school="日本工業大学駒場中学校",
            year="2023"
        )
        
        # 結果を整形して表示
        formatted = analyzer.format_analysis_result(result)
        print("\n" + formatted)
        
        # 統計情報
        logger.info("\n【検出統計】")
        logger.info(f"総問題数: {result['summary']['total_questions']}")
        logger.info(f"大問数: {result['total_sections']}")
        
        # 期待値との比較
        expected = {
            '大問1': 11,
            '大問2': 13,
            '大問3': 13,
            '大問4': 5
        }
        
        logger.info("\n【期待値との比較】")
        for section in result['sections']:
            section_name = f"大問{section['section_number']}"
            expected_count = expected.get(section_name, 0)
            actual_count = section['question_count']
            
            if expected_count == actual_count:
                logger.info(f"✅ {section_name}: {actual_count}問 (期待値通り)")
            else:
                logger.warning(f"❌ {section_name}: {actual_count}問 (期待値: {expected_count}問)")
        
        return True
        
    except Exception as e:
        logger.error(f"分析エラー: {e}", exc_info=True)
        return False

def test_gemini_vision_analysis():
    """画像ベースの分析テスト（Vision API使用）"""
    
    logger.info("\n" + "=" * 60)
    logger.info("Gemini Vision 分析テスト")
    logger.info("=" * 60)
    
    # 環境変数を読み込み
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY が設定されていません")
        return False
    
    try:
        # Analyzerの初期化
        analyzer = GeminiAnalyzer(api_key)
        logger.info("GeminiAnalyzer (Vision) 初期化成功")
        
        # PDFファイルのパス
        pdf_path = Path('/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf')
        
        if not pdf_path.exists():
            logger.error(f"PDFファイルが見つかりません: {pdf_path}")
            return False
        
        # Vision APIによる分析を実行
        logger.info("\nVision API分析を開始...")
        logger.info("PDFを画像に変換して直接解析します")
        
        result = analyzer.analyze_pdf_with_vision(
            pdf_path=pdf_path,
            school="日本工業大学駒場中学校",
            year="2023"
        )
        
        # 結果を整形して表示
        formatted = analyzer.format_analysis_result(result)
        print("\n" + formatted)
        
        # 統計情報
        logger.info("\n【Vision API検出統計】")
        logger.info(f"総問題数: {result['summary']['total_questions']}")
        logger.info(f"大問数: {result['total_sections']}")
        
        # テーマ抽出のテスト
        logger.info("\n【テーマ抽出テスト】")
        for section in result['sections'][:2]:  # 最初の2つの大問
            logger.info(f"\n大問{section['section_number']}のテーマ:")
            for q in section['questions'][:3]:  # 最初の3問
                if q.get('theme'):
                    logger.info(f"  問{q['question_number']}: {q['theme']}")
                    if q.get('keywords'):
                        logger.info(f"    キーワード: {', '.join(q['keywords'][:3])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Vision分析エラー: {e}", exc_info=True)
        return False

def main():
    """メインテスト実行"""
    
    print("\n" + "=" * 80)
    print("Gemini Analyzer テストスイート")
    print("=" * 80)
    
    # .envファイルの存在確認
    env_file = project_root / ".env"
    if not env_file.exists():
        logger.info("\n.env ファイルが見つかりません")
        logger.info(".env.example をコピーして .env を作成してください:")
        logger.info("  cp .env.example .env")
        logger.info("その後、GEMINI_API_KEY を設定してください")
        return
    
    # テスト選択
    print("\nテストモードを選択してください:")
    print("1. テキスト分析のみ")
    print("2. Vision分析のみ")
    print("3. 両方実行")
    print("0. 終了")
    
    choice = input("\n選択 (0-3): ").strip()
    
    if choice == '1':
        success = test_gemini_text_analysis()
        if success:
            logger.info("\n✅ テキスト分析テスト成功")
        else:
            logger.error("\n❌ テキスト分析テスト失敗")
    
    elif choice == '2':
        success = test_gemini_vision_analysis()
        if success:
            logger.info("\n✅ Vision分析テスト成功")
        else:
            logger.error("\n❌ Vision分析テスト失敗")
    
    elif choice == '3':
        text_success = test_gemini_text_analysis()
        vision_success = test_gemini_vision_analysis()
        
        logger.info("\n【テスト結果サマリー】")
        logger.info(f"テキスト分析: {'✅ 成功' if text_success else '❌ 失敗'}")
        logger.info(f"Vision分析: {'✅ 成功' if vision_success else '❌ 失敗'}")
    
    elif choice == '0':
        logger.info("テストを終了します")
    
    else:
        logger.warning("無効な選択です")

if __name__ == "__main__":
    main()