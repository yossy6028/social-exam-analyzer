#!/usr/bin/env python3
"""
OCRフラグメント100%除去テスト
"""
import sys
import logging
from pathlib import Path
from modules.ocr_handler import OCRHandler
from modules.social_analyzer_fixed import FixedSocialAnalyzer
from modules.gemini_theme_analyzer import GeminiThemeAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

def main():
    """メイン処理"""
    # PDFファイルパス
    pdf_path = '/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf'
    
    print('=' * 60)
    print('OCRフラグメント100%除去テスト')
    print('=' * 60)
    print(f'PDFファイル: {Path(pdf_path).name}')
    
    # OCRでテキスト抽出
    print('\n1. OCR処理中...')
    ocr = OCRHandler()
    text = ocr.process_pdf(pdf_path)
    print(f'   抽出完了: {len(text)}文字')
    
    # 分析実行
    print('\n2. 問題分析中...')
    analyzer = FixedSocialAnalyzer()
    result = analyzer.analyze_document(text)
    print(f'   抽出問題数: {len(result["all_questions"])}問')
    
    # OCRフラグメントのチェック（修正前）
    fragment_patterns = [
        '記号 文武', '兵庫県明', '朱子学以外', 
        '記号 下線部', '核兵器 下線部', '新詳日本史'
    ]
    
    before_fragments = []
    for q in result['all_questions']:
        topic = q.get('topic', '')
        if any(frag in topic for frag in fragment_patterns):
            before_fragments.append({
                'num': q.get('question_number'),
                'topic': topic,
                'field': q.get('field', '不明')
            })
    
    print(f'\n3. OCRフラグメント検出（修正前）:')
    print(f'   フラグメント数: {len(before_fragments)}個')
    if before_fragments:
        for frag in before_fragments[:5]:  # 最初の5個のみ表示
            print(f'   - {frag["num"]}: {frag["topic"]} [{frag["field"]}]')
    
    # Gemini APIによる修正
    print('\n4. Gemini APIによるバッチ修正中...')
    gemini_analyzer = GeminiThemeAnalyzer()
    
    if gemini_analyzer.api_enabled:
        print('   Gemini API有効 - 総括分析実行')
        # バッチ分析の実行
        questions_dict = result['all_questions']
        updated_questions = gemini_analyzer.analyze_all_questions_with_api(questions_dict)
        result['all_questions'] = updated_questions
        
        # 修正後のチェック
        after_fragments = []
        for q in result['all_questions']:
            topic = q.get('topic', '')
            if any(frag in topic for frag in fragment_patterns):
                after_fragments.append({
                    'num': q.get('question_number'),
                    'topic': topic,
                    'field': q.get('field', '不明')
                })
        
        print(f'\n5. 修正結果:')
        print(f'   修正前フラグメント: {len(before_fragments)}個')
        print(f'   修正後フラグメント: {len(after_fragments)}個')
        print(f'   除去率: {(1 - len(after_fragments)/max(len(before_fragments), 1)) * 100:.1f}%')
        
        if after_fragments:
            print(f'\n   残存フラグメント:')
            for frag in after_fragments:
                print(f'   - {frag["num"]}: {frag["topic"]} [{frag["field"]}]')
        
        # 最終精度
        total_questions = len(result['all_questions'])
        accuracy = (1 - len(after_fragments)/total_questions) * 100
        
        print(f'\n6. 最終結果:')
        print(f'   総問題数: {total_questions}問')
        print(f'   OCRフラグメント: {len(after_fragments)}個')
        print(f'   精度: {accuracy:.1f}%')
        
        if accuracy >= 100.0:
            print(f'\n✅ 目標達成！100%の精度を実現しました！')
        else:
            print(f'\n⚠️  目標未達: 100%精度には{100-accuracy:.1f}%不足')
            
            # 具体的な修正提案を表示
            if after_fragments:
                print(f'\n7. 修正提案:')
                for frag in after_fragments:
                    suggestion = suggest_correction(frag['topic'], frag['field'])
                    print(f'   {frag["num"]}: 「{frag["topic"]}」→「{suggestion}」')
    else:
        print('   ⚠️ Gemini API無効')
    
    print('\n' + '=' * 60)
    print('テスト完了')
    print('=' * 60)

def suggest_correction(fragment: str, field: str) -> str:
    """OCRフラグメントの修正案を提案"""
    corrections = {
        '記号 文武': '文武天皇の政治' if field == '歴史' else '奈良時代の文化',
        '兵庫県明': '明治時代の地方制度' if field == '歴史' else '兵庫県の産業',
        '朱子学以外': '江戸時代の学問',
        '記号 下線部': f'{field}総合問題',
        '核兵器 下線部': '核兵器と国際平和',
        '新詳日本史': '日本史総合'
    }
    
    for pattern, suggestion in corrections.items():
        if pattern in fragment:
            return suggestion
    
    return f'{field}関連問題'

if __name__ == '__main__':
    main()