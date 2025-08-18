#!/usr/bin/env python3
"""
Gemini APIを使用した詳細な社会科問題分析
各問題を一問一問、正確に内容とテーマを抽出
"""

import sys
import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv()

# Google Generative AI
import google.generativeai as genai

# ローカルモジュール
from modules.ocr_handler import OCRHandler


class GeminiDetailedAnalyzer:
    """Gemini APIを使用した詳細な問題分析"""
    
    def __init__(self):
        """初期化"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEYが設定されていません")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 分析結果を格納
        self.questions = []
        self.raw_text = ""
    
    def extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """テキストから問題を抽出"""
        prompt = """
以下の社会科入試問題のテキストから、すべての問題を抽出してください。
解答欄や答えの部分は除外し、問題文のみを抽出してください。

出力形式（JSON）:
{{
  "questions": [
    {{
      "number": "大問1-問1",
      "text": "問題文全体",
      "type": "選択式/記述式/穴埋め等"
    }}
  ]
}}

注意事項:
- 大問番号と小問番号を正確に識別
- 問題文は省略せず全文を含める
- 下線部や資料への参照がある場合、その前後の文脈も含める
- 「下線部⑥」などの参照がある場合、その下線部の実際の内容も探して含める
- 解答欄の記号（ア、イ、ウ等）は含めない
- 資料（地図、グラフ等）への言及は残す

テキスト:
---
{}
---
""".format(text[:15000])  # 15000文字まで拡張（全大問をカバー）
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # JSONを抽出
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())['questions']
            return []
        except Exception as e:
            print(f"問題抽出エラー: {e}")
            return []
    
    def analyze_single_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """単一の問題を詳細分析"""
        # 問題文から文脈を補完
        question_text = question['text']
        
        # 「下線部」への参照がある場合、文脈から内容を推測するヒント
        context_hint = ""
        if "下線部" in question_text:
            context_hint = """
この問題は下線部への参照を含んでいます。
問題文の文脈から、下線部が何を指しているか推測して、
テーマには具体的な内容を記載してください。
"""
        
        prompt = f"""
以下の社会科入試問題を詳細に分析してください。
{context_hint}

問題番号: {question['number']}
問題文: {question['text']}

以下の項目を正確に判定してください:

1. 分野（必須）: 地理/歴史/公民/時事問題 のいずれか1つ
2. 具体的なテーマ（必須）: 問題の中心的な内容を20文字以内で具体的に
3. キーワード（必須）: 問題に含まれる重要な用語を3-5個
4. 時代・地域（該当する場合）: 歴史なら時代、地理なら地域
5. 資料の種類（該当する場合）: 地図/グラフ/年表/写真等
6. 難易度（必須）: 易/中/難 の3段階
7. 出題形式（必須）: 以下から正確に判定
   - 短答式: 用語や年号など短い答えを記入
   - 記号選択: ア、イ、ウなどから選択
   - 記述式: 文章で説明を求める
   - 穴埋め: 文中の空欄を埋める
   - 正誤判定: 文の正誤を判断
   - 組み合わせ: 複数の項目を組み合わせる
   - その他: 上記に該当しない形式

出力形式（JSON）:
{{
  "field": "分野",
  "theme": "具体的なテーマ",
  "keywords": ["キーワード1", "キーワード2", "キーワード3"],
  "period_or_region": "時代または地域",
  "resource_type": "資料の種類",
  "difficulty": "難易度",
  "question_format": "出題形式"
}}

注意:
- テーマは「地理の問題」のような曖昧な表現を避け、「促成栽培」「楽市楽座」のように具体的に
- 「下線部⑥について」のような参照表現は避け、実際の内容を推測して具体的に記述
  例: 「下線部⑥の記述に関する正誤判断」→「〇〇に関する正誤判断」（〇〇は問題文から推測）
- テーマには問題が実際に問うている内容を記載（「下線部」「資料A」等の参照記号は使わない）
- 分野は必ず1つに絞る（複合的な場合は主要な方を選択）
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # JSONを抽出
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                # 問題情報と分析結果を統合
                return {
                    'number': question['number'],
                    'text': question['text'],
                    'type': question.get('type', '不明'),
                    **analysis
                }
            return question
        except Exception as e:
            print(f"問題分析エラー ({question['number']}): {e}")
            return question
    
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """PDFを分析"""
        print("=" * 80)
        print("Gemini APIによる詳細分析")
        print("=" * 80)
        print()
        
        # OCR処理
        print("【1. PDFからテキスト抽出】")
        ocr_handler = OCRHandler()
        self.raw_text = ocr_handler.process_pdf(pdf_path)
        
        if not self.raw_text:
            print("❌ テキスト抽出失敗")
            return {}
        
        print(f"✅ {len(self.raw_text)}文字を抽出")
        print()
        
        # 問題抽出
        print("【2. 問題の抽出】")
        extracted_questions = self.extract_questions_from_text(self.raw_text)
        
        if not extracted_questions:
            # フォールバック: 簡易的な問題抽出
            print("⚠️ Gemini抽出失敗、簡易パターンで再試行")
            extracted_questions = self._fallback_extraction()
        
        print(f"✅ {len(extracted_questions)}問を検出")
        
        # 大問の分布を確認
        major_counts = {}
        for q in extracted_questions:
            if 'number' in q:
                major_match = re.match(r'大問(\d+)', q['number'])
                if major_match:
                    major_num = int(major_match.group(1))
                    major_counts[major_num] = major_counts.get(major_num, 0) + 1
        
        if major_counts:
            print(f"  大問別: {', '.join([f'大問{k}={v}問' for k, v in sorted(major_counts.items())])}")
        print()
        
        # 各問題を詳細分析
        print("【3. 各問題の詳細分析】")
        analyzed_questions = []
        
        for i, question in enumerate(extracted_questions, 1):
            print(f"  分析中: {question['number']} ({i}/{len(extracted_questions)})")
            analyzed = self.analyze_single_question(question)
            analyzed_questions.append(analyzed)
            
            # API制限対策
            if i % 5 == 0:
                time.sleep(1)
        
        print(f"✅ 分析完了")
        print()
        
        # 統計情報を計算
        statistics = self._calculate_statistics(analyzed_questions)
        
        return {
            'questions': analyzed_questions,
            'statistics': statistics,
            'total_questions': len(analyzed_questions)
        }
    
    def _fallback_extraction(self) -> List[Dict[str, Any]]:
        """簡易的な問題抽出（フォールバック）"""
        questions = []
        
        # 複数の大問パターンに対応
        major_patterns = [
            r'([1-5])\s*[．.]\s*次の',
            r'大問\s*([1-5])',
            r'第\s*([1-5])\s*問',
            r'([１-５])\s*[．.]\s*'  # 全角数字にも対応
        ]
        
        major_sections = []
        for pattern in major_patterns:
            matches = list(re.finditer(pattern, self.raw_text))
            if matches:
                major_sections = matches
                break
        
        # 大問が見つからない場合は全体を1つの大問として扱う
        if not major_sections:
            major_sections = [type('obj', (object,), {'group': lambda x: '1', 'start': lambda: 0})]
        
        for i, match in enumerate(major_sections):
            major_num = match.group(1) if hasattr(match, 'group') else '1'
            start_pos = match.start() if hasattr(match, 'start') else 0
            end_pos = major_sections[i+1].start() if i+1 < len(major_sections) and hasattr(major_sections[i+1], 'start') else len(self.raw_text)
            
            section_text = self.raw_text[start_pos:end_pos]
            
            # 小問を探す（複数パターン）
            minor_patterns = [
                r'問\s*(\d+)[^0-9]',
                r'問\s*([一二三四五六七八九十]+)',
                r'\((\d+)\)[^)]*[^。、]'
            ]
            
            for pattern in minor_patterns:
                minor_matches = list(re.finditer(pattern, section_text))
                if minor_matches:
                    for minor_match in minor_matches:
                        minor_num = minor_match.group(1)
                        q_start = minor_match.start()
                        q_text = section_text[q_start:min(q_start+500, len(section_text))]  # 500文字まで
                        
                        questions.append({
                            'number': f"大問{major_num}-問{minor_num}",
                            'text': q_text.strip(),
                            'type': '不明'
                        })
                    break
        
        return questions[:60]  # 最大60問まで（大問4まで対応）
    
    def _calculate_statistics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """統計情報を計算"""
        total = len(questions)
        if total == 0:
            return {}
        
        # 分野別集計
        field_counts = {}
        theme_list = []
        difficulty_counts = {'易': 0, '中': 0, '難': 0}
        format_counts = {}
        
        # 分野別主要語集計
        field_keywords = {
            '地理': set(),
            '歴史': set(),
            '公民': set(),
            '時事問題': set(),
            'その他': set()
        }
        
        for q in questions:
            # 分野
            field = q.get('field', '不明')
            field_counts[field] = field_counts.get(field, 0) + 1
            
            # テーマ
            if theme := q.get('theme'):
                theme_list.append(theme)
            
            # 難易度
            difficulty = q.get('difficulty', '中')
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1
            
            # 出題形式
            q_format = q.get('question_format', 'その他')
            format_counts[q_format] = format_counts.get(q_format, 0) + 1
            
            # 分野別キーワード収集
            if keywords := q.get('keywords'):
                field_key = field if field in field_keywords else 'その他'
                for kw in keywords:
                    if kw and len(kw) > 1:  # 1文字のキーワードは除外
                        field_keywords[field_key].add(kw)
        
        # パーセンテージ計算
        field_distribution = {
            field: {
                'count': count,
                'percentage': round(count / total * 100, 1)
            }
            for field, count in field_counts.items()
        }
        
        # 出題形式の分布
        format_distribution = {
            fmt: {
                'count': count,
                'percentage': round(count / total * 100, 1)
            }
            for fmt, count in format_counts.items()
        }
        
        # 分野別キーワードを辞書形式に変換（空のセットは除外）
        field_keywords_dict = {}
        for field, keywords_set in field_keywords.items():
            if keywords_set:  # 空でない場合のみ追加
                field_keywords_dict[field] = sorted(list(keywords_set))
        
        return {
            'field_distribution': field_distribution,
            'difficulty_distribution': difficulty_counts,
            'format_distribution': format_distribution,
            'field_keywords': field_keywords_dict,  # 分野別キーワードを追加
            'unique_themes': len(set(theme_list)),
            'total_questions': total
        }
    
    def display_results(self, result: Dict[str, Any]):
        """結果を表示"""
        print("=" * 80)
        print("【分析結果】")
        print("=" * 80)
        print()
        
        # 統計情報
        if stats := result.get('statistics'):
            print(f"◆ 総問題数: {stats.get('total_questions', 0)}問")
            print(f"◆ ユニークテーマ数: {stats.get('unique_themes', 0)}")
            print()
            
            # 分野別
            if field_dist := stats.get('field_distribution'):
                print("◆ 分野別分布:")
                for field, data in sorted(field_dist.items()):
                    print(f"  {field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
                print()
            
            # 難易度
            if diff_dist := stats.get('difficulty_distribution'):
                print("◆ 難易度分布:")
                for level, count in diff_dist.items():
                    print(f"  {level}: {count:3d}問")
                print()
            
            # 出題形式
            if format_dist := stats.get('format_distribution'):
                print("◆ 出題形式分布:")
                for fmt, data in sorted(format_dist.items(), key=lambda x: x[1]['count'], reverse=True):
                    print(f"  {fmt:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
                print()
            
            # 分野別主要語一覧
            if field_keywords := stats.get('field_keywords'):
                print("◆ 分野別主要語一覧:")
                for field in ['地理', '歴史', '公民', '時事問題', 'その他']:
                    if keywords := field_keywords.get(field):
                        print(f"\n  【{field}】")
                        # 5個ずつ改行して表示
                        for i in range(0, len(keywords), 5):
                            batch = keywords[i:i+5]
                            print(f"    {', '.join(batch)}")
                print()
        
        # 各問題の詳細（最初の30問）
        print("◆ 問題別詳細:")
        print("-" * 80)
        
        questions = result.get('questions', [])
        for q in questions[:30]:
            number = q.get('number', 'N/A')
            theme = q.get('theme', '(テーマ未設定)')
            field = q.get('field', '不明')
            q_format = q.get('question_format', '不明')
            
            # テーマ、ジャンル、出題形式を1行で表示
            print(f"\n▼ {number}")
            print(f"  テーマ: {theme} | ジャンル: {field} | 出題形式: {q_format}")
            
            # 問題文の冒頭
            text = q.get('text', '')[:100]
            if text:
                print(f"  問題文: {text}...")
        
        if len(questions) > 30:
            print(f"\n... 他 {len(questions) - 30} 問")
        
        print()
        print("=" * 80)
        print("分析完了")
        print("=" * 80)
    
    def save_results(self, result: Dict[str, Any], output_path: str):
        """結果をJSONファイルに保存"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ 結果を保存: {output_path}")
        except Exception as e:
            print(f"❌ 保存エラー: {e}")


def main():
    """メイン処理"""
    pdf_path = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/日本工業大学駒場中学校/2023年日本工業大学駒場中学校問題_社会.pdf"
    
    print("Gemini APIによる詳細分析を開始します")
    print(f"対象PDF: {Path(pdf_path).name}")
    print()
    
    try:
        analyzer = GeminiDetailedAnalyzer()
        result = analyzer.analyze_pdf(pdf_path)
        
        # 結果表示
        analyzer.display_results(result)
        
        # JSON保存
        output_path = Path(__file__).parent / "gemini_analysis_result.json"
        analyzer.save_results(result, str(output_path))
        
        return result
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()