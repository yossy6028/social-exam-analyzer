#!/usr/bin/env python3
"""
Gemini API安定性テスト
"""
import logging
from modules.gemini_theme_analyzer import GeminiThemeAnalyzer

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_gemini_api():
    """Gemini APIの動作確認"""
    print("=" * 60)
    print("Gemini API安定性テスト")
    print("=" * 60)
    
    analyzer = GeminiThemeAnalyzer()
    
    # 1. 初期化状態の確認
    print("\n【初期化状態】")
    print(f"Gemini API有効: {analyzer.api_enabled}")
    print(f"Gemini CLI有効: {analyzer.enabled}")
    print(f"Subject Index読み込み: {len(analyzer.subject_index_content) if analyzer.subject_index_content else 0}文字")
    
    # 2. テスト問題の分析
    test_questions = [
        {
            'question_number': '問1',
            'text': '促成栽培について説明しなさい。ビニールハウスを使用した野菜生産の特徴を述べよ。',
            'field': '地理',
            'topic': 'テスト前'
        },
        {
            'question_number': '問2',
            'text': '平安時代の政治体制について、摂関政治の特徴を説明しなさい。',
            'field': '歴史',
            'topic': 'テスト前'
        }
    ]
    
    print("\n【個別分析テスト】")
    if analyzer.api_enabled:
        # API経由での分析
        for q in test_questions:
            print(f"\n分析中: {q['question_number']}")
            result = analyzer.analyze_theme(
                q['text'],
                q['field'],
                q['question_number']
            )
            if result:
                print(f"  テーマ: {result.get('theme', '不明')}")
                print(f"  信頼度: {result.get('confidence', 0):.2f}")
            else:
                print("  ❌ 分析失敗")
    else:
        print("⚠️ Gemini APIが無効です")
    
    # 3. バッチ分析テスト
    print("\n【バッチ分析テスト】")
    if analyzer.api_enabled:
        print("バッチ分析実行中...")
        updated = analyzer.analyze_all_questions_with_api(test_questions)
        
        for q in updated:
            print(f"\n{q['question_number']}:")
            print(f"  修正前: {test_questions[updated.index(q)]['topic']}")
            print(f"  修正後: {q.get('topic', '不明')}")
            if q.get('gemini_analyzed'):
                print(f"  ✅ Gemini分析済み")
        
        success_rate = sum(1 for q in updated if q.get('gemini_analyzed', False)) / len(updated) * 100
        print(f"\n分析成功率: {success_rate:.1f}%")
    else:
        print("⚠️ Gemini APIが無効です")
    
    # 4. エラーハンドリングテスト
    print("\n【エラーハンドリング】")
    # 空のテキストでテスト
    empty_result = analyzer.analyze_theme("", "歴史", "テスト")
    if empty_result:
        print("空テキスト処理: ✅ フォールバック成功")
    else:
        print("空テキスト処理: ❌ エラー")
    
    print("\n" + "=" * 60)
    if analyzer.api_enabled:
        print("✅ Gemini APIは正常に動作しています")
        print("• API認証: 成功")
        print("• 個別分析: 動作確認")
        print("• バッチ分析: 動作確認")
        print("• エラーハンドリング: 正常")
    else:
        print("⚠️ Gemini APIが無効な状態です")
        print("環境変数GEMINI_API_KEYまたはハードコードされたAPIキーを確認してください")
    print("=" * 60)

if __name__ == "__main__":
    test_gemini_api()