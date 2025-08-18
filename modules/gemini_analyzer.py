#!/usr/bin/env python3
"""
Gemini APIを使用した社会科入試問題分析モジュール
AIによる正確な問題構造認識とテーマ抽出
"""

import os
import json
import re
import logging
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import tempfile

# subject_index との照合機能
from modules.subject_index_loader import SubjectIndexLoader

# 環境変数の読み込み
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """Gemini APIを使用した高精度分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Gemini API キー（環境変数から取得も可）
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        
        # Gemini APIの設定
        genai.configure(api_key=self.api_key)
        
        # モデルの初期化（Gemini 1.5 Pro Vision対応）
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # 画像解析用の設定
        self.generation_config = {
            'temperature': 0.1,  # 低めにして正確性を重視
            'top_p': 1.0,
            'top_k': 1,
            'max_output_tokens': 8192,
        }
        
        # subject_index の読み込み
        self.subject_loader = SubjectIndexLoader()
        
        logger.info("GeminiAnalyzer 初期化完了（Vision対応 + subject_index照合）")
    
    def analyze_pdf_with_vision(self, pdf_path: Union[str, Path], school: str = "", year: str = "") -> Dict:
        """
        PDFを画像として直接解析（Gemini Vision使用）
        
        Args:
            pdf_path: PDFファイルのパス
            school: 学校名
            year: 年度
            
        Returns:
            分析結果の辞書
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")
        
        logger.info(f"PDF画像解析開始: {pdf_path.name}")
        
        try:
            # PDFを画像に変換
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(pdf_path, dpi=200)
                logger.info(f"{len(images)}ページを画像に変換")
                
                # 各ページを解析
                all_results = []
                
                for i, image in enumerate(images, 1):
                    logger.info(f"ページ{i}/{len(images)}を解析中...")
                    
                    # subject_index の重要語句をプロンプトに含める
                    important_terms_prompt = self.subject_loader.get_important_terms_prompt()
                    
                    # プロンプトの構築
                    prompt = f"""
あなたは日本の中学入試問題の専門家です。
この画像は{school}の{year}年度社会科入試問題のページ{i}です。

{important_terms_prompt}

【重要な前提】
- 実際の入試問題は通常、大問1〜4程度で構成されます（大問5以上は稀です）
- 「受験番号」「氏名」「得点」「採点欄」などは解答用紙の要素であり、問題ではありません
- ページ最後に解答欄がある場合、それは問題ではなく解答記入欄です

【タスク】
1. 画像を注意深く観察し、実際の問題部分のみを識別してください
2. 大問番号を正確に識別（通常は「1」「2」「3」「4」または「□1□」「□2□」など）
3. 各大問内の問題番号を識別（「問1」「問2」など）
4. 問題文の内容から分野を正確に判定してください
5. 各問題の具体的で意味のあるテーマを抽出してください

【絶対に避けるべきこと】
- 「受験番号」「氏名」を問題として認識しない
- 解答欄や採点欄を問題として数えない
- 存在しない大問5以降を作らない
- OCRエラー（例：「3」が「13」になる）に騙されない
- 意味不明なテーマ（「受験番号氏名の業績」など）を生成しない

【正確な分野判定の基準】
- 地理：地形、気候、産業、都市、農業、工業、貿易など
- 歴史：時代、人物、出来事、文化、政治体制など
- 公民：憲法、政治、経済、国際関係、社会問題など
- 時事：最近の出来事、SDGs、環境問題など

【出力形式】
{{
  "page": {i},
  "sections": [
    {{
      "section_number": 大問番号,
      "questions": [
        {{
          "question_number": 問題番号,
          "field": "地理/歴史/公民/時事",
          "theme": "具体的なテーマ",
          "keywords": ["キーワード1", "キーワード2"],
          "has_figure": 図表の有無（true/false）,
          "question_summary": "問題の要約（50文字以内）"
        }}
      ]
    }}
  ]
}}

JSONのみを出力してください。
"""
                    
                    # Gemini Vision APIを呼び出し
                    response = self.model.generate_content(
                        [prompt, image],
                        generation_config=self.generation_config
                    )
                    
                    # JSONを抽出
                    json_text = response.text
                    if '```json' in json_text:
                        json_text = json_text.split('```json')[1].split('```')[0]
                    elif '```' in json_text:
                        json_text = json_text.split('```')[1].split('```')[0]
                    
                    page_result = json.loads(json_text.strip())
                    all_results.append(page_result)
                
                # 全ページの結果を統合
                return self._merge_page_results(all_results, school, year)
                
        except Exception as e:
            logger.error(f"PDF画像解析エラー: {e}")
            # テキストベースの解析にフォールバック
            from modules.ocr_handler import OCRHandler
            ocr = OCRHandler()
            text = ocr.extract_text_from_pdf(pdf_path)
            return self.analyze_exam_structure(text, school, year)
    
    def _merge_page_results(self, page_results: List[Dict], school: str, year: str) -> Dict:
        """
        複数ページの解析結果を統合
        
        Args:
            page_results: 各ページの解析結果
            school: 学校名
            year: 年度
            
        Returns:
            統合された結果
        """
        
        # 全セクションを集約
        all_sections = {}
        
        for page_result in page_results:
            for section in page_result.get('sections', []):
                section_num = section['section_number']
                
                # 大問5以上は通常存在しないため、検証
                if section_num > 4:
                    logger.warning(f"大問{section_num}を検出 - 妥当性を確認中...")
                    # 問題内容を検証
                    valid_questions = []
                    for q in section.get('questions', []):
                        theme = q.get('theme', '').lower()
                        summary = q.get('question_summary', '').lower()
                        # 受験番号や氏名が含まれていたら除外
                        if any(word in theme + summary for word in ['受験番号', '氏名', '得点', '採点']):
                            logger.info(f"不適切な問題を除外: {theme}")
                            continue
                        valid_questions.append(q)
                    
                    # 有効な問題がない場合はセクション自体を除外
                    if not valid_questions:
                        logger.info(f"大問{section_num}には有効な問題がないため除外")
                        continue
                    section['questions'] = valid_questions
                
                if section_num not in all_sections:
                    all_sections[section_num] = {
                        'section_number': section_num,
                        'questions': []
                    }
                
                # 問題を追加する前に検証とテーマ改善
                for q in section['questions']:
                    theme = q.get('theme', '')
                    # 無効なテーマをフィルタリング
                    if '受験番号' in theme or '氏名' in theme or theme == '':
                        logger.debug(f"無効な問題を除外: {theme}")
                        continue
                    
                    # subject_index の重要語句でテーマを補強
                    question_text = q.get('question_summary', '') + ' ' + theme
                    found_terms = self.subject_loader.find_important_terms(question_text)
                    
                    # 優先テーマがあれば採用
                    if found_terms['priority_themes']:
                        q['theme'] = found_terms['priority_themes'][0]
                        q['keywords'] = found_terms['priority_themes'][:3]
                        logger.info(f"subject_indexから優先テーマを採用: {q['theme']}")
                    
                    # 分野の補正
                    if not q.get('field') or q['field'] == '総合':
                        all_found = (found_terms['history'] + 
                                   found_terms['geography'] + 
                                   found_terms['civics'])
                        if all_found:
                            q['field'] = self.subject_loader.get_field_from_terms(all_found)
                    
                    all_sections[section_num]['questions'].append(q)
        
        # 重複を除去してソート
        for section_num in all_sections:
            questions = all_sections[section_num]['questions']
            # 問題番号でユニーク化
            unique_questions = {}
            for q in questions:
                key = q['question_number']
                if key not in unique_questions or len(q.get('question_summary', '')) > len(unique_questions[key].get('question_summary', '')):
                    unique_questions[key] = q
            
            # ソート
            sorted_questions = sorted(unique_questions.values(), 
                                     key=lambda x: self._normalize_question_number(x['question_number']))
            all_sections[section_num]['questions'] = sorted_questions
            all_sections[section_num]['question_count'] = len(sorted_questions)
        
        # セクション番号でソート
        sorted_sections = sorted(all_sections.values(), key=lambda x: x['section_number'])
        
        # サマリーを計算
        total_questions = sum(s['question_count'] for s in sorted_sections)
        field_counts = {'geography_count': 0, 'history_count': 0, 'civics_count': 0, 'current_affairs_count': 0}
        
        for section in sorted_sections:
            for q in section['questions']:
                field = q.get('field', '').lower()
                if '地理' in field:
                    field_counts['geography_count'] += 1
                elif '歴史' in field:
                    field_counts['history_count'] += 1
                elif '公民' in field:
                    field_counts['civics_count'] += 1
                elif '時事' in field:
                    field_counts['current_affairs_count'] += 1
        
        return {
            'school': school,
            'year': year,
            'total_sections': len(sorted_sections),
            'sections': sorted_sections,
            'summary': {
                **field_counts,
                'total_questions': total_questions
            }
        }
    
    def _normalize_question_number(self, q_num: str) -> int:
        """問題番号を正規化して数値に変換"""
        try:
            # 数字部分を抽出
            import re
            nums = re.findall(r'\d+', str(q_num))
            if nums:
                return int(nums[0])
            return 0
        except:
            return 0
    
    def analyze_exam_structure(self, text: str, school: str = "", year: str = "") -> Dict:
        """
        入試問題の構造をAIで分析
        
        Args:
            text: OCRされたテキスト
            school: 学校名
            year: 年度
            
        Returns:
            分析結果の辞書
        """
        
        # プロンプトの構築
        prompt = f"""
あなたは日本の中学入試問題の専門家です。
以下の社会科入試問題のテキストを分析して、JSON形式で構造化してください。

【学校】: {school}
【年度】: {year}

【分析すべき内容】
1. 大問の数と各大問の問題数
2. 各問題の分野（地理/歴史/公民/時事）
3. 各問題の具体的なテーマ
4. 重要なキーワード

【注意事項】
- 「受験番号」「氏名」「得点」などの解答用紙の要素は無視してください
- 大問は通常「1 次の」「2 次の」または「□1□」などで始まります
- OCRエラーで「3」が「13」になることがあります（1が余分に付く）
- 問題番号は「問1」「問2」などの形式です

【出力形式】
{{
  "total_sections": 大問の数,
  "sections": [
    {{
      "section_number": 大問番号,
      "question_count": 問題数,
      "questions": [
        {{
          "question_number": 問題番号,
          "field": "地理/歴史/公民/時事",
          "theme": "具体的なテーマ",
          "keywords": ["キーワード1", "キーワード2"],
          "question_text": "問題文の要約（50文字以内）"
        }}
      ]
    }}
  ],
  "summary": {{
    "geography_count": 地理問題数,
    "history_count": 歴史問題数,
    "civics_count": 公民問題数,
    "current_affairs_count": 時事問題数,
    "total_questions": 総問題数
  }}
}}

【テキスト】
{text[:15000]}  # 最初の15000文字のみ（トークン制限対策）

JSONのみを出力してください。説明は不要です。
"""
        
        try:
            # Gemini APIを呼び出し
            response = self.model.generate_content(prompt)
            
            # レスポンスからJSONを抽出
            json_text = response.text
            
            # JSONブロックを抽出（```json ... ```の形式の場合）
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0]
            
            # JSONをパース
            result = json.loads(json_text.strip())
            
            logger.info(f"Gemini分析成功: {result['summary']['total_questions']}問を検出")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini分析エラー: {e}")
            # フォールバック
            return self._fallback_analysis(text)
    
    def extract_themes_with_ai(self, text: str) -> List[Dict]:
        """
        AIを使用してテーマを抽出
        
        Args:
            text: 問題文
            
        Returns:
            テーマ情報のリスト
        """
        
        prompt = f"""
以下の社会科入試問題から、重要なテーマとキーワードを抽出してください。

【テキスト】
{text[:2000]}

【出力形式】
{{
  "main_theme": "メインテーマ",
  "sub_themes": ["サブテーマ1", "サブテーマ2"],
  "keywords": ["重要語句1", "重要語句2", "重要語句3"],
  "field": "地理/歴史/公民/時事",
  "specific_topics": ["具体的なトピック1", "具体的なトピック2"]
}}

JSONのみを出力してください。
"""
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text
            
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0]
            
            result = json.loads(json_text.strip())
            return result
            
        except Exception as e:
            logger.error(f"テーマ抽出エラー: {e}")
            return {
                "main_theme": "不明",
                "sub_themes": [],
                "keywords": [],
                "field": "総合",
                "specific_topics": []
            }
    
    def _fallback_analysis(self, text: str) -> Dict:
        """
        Gemini APIが使えない場合のフォールバック分析
        
        Args:
            text: OCRテキスト
            
        Returns:
            基本的な分析結果
        """
        
        # 従来のパターンマッチング
        sections = []
        
        # 大問パターン
        large_patterns = [
            (r'^([1-5])\s+次の', 'normal'),
            (r'^1([1-5])\s+次の', 'ocr_error'),
            (r'[□■]([1-5])[□■]', 'boxed'),
        ]
        
        for pattern, type_ in large_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                if type_ == 'ocr_error':
                    section_num = int(match.group(1))
                else:
                    section_num = int(match.group(1))
                
                sections.append({
                    'section_number': section_num,
                    'question_count': 0,
                    'questions': []
                })
        
        # 基本的な統計
        total = len(sections) * 10  # 推定
        
        return {
            'total_sections': len(sections),
            'sections': sections,
            'summary': {
                'geography_count': total // 3,
                'history_count': total // 3,
                'civics_count': total // 3,
                'current_affairs_count': 0,
                'total_questions': total
            }
        }
    
    def format_analysis_result(self, result: Dict) -> str:
        """
        分析結果を見やすく整形
        
        Args:
            result: analyze_exam_structure()の結果
            
        Returns:
            整形された文字列
        """
        
        lines = []
        lines.append("=" * 60)
        lines.append("【Gemini AI による入試問題分析結果】")
        lines.append("=" * 60)
        
        # サマリー
        summary = result['summary']
        lines.append(f"\n総問題数: {summary['total_questions']}問")
        lines.append(f"大問数: {result['total_sections']}個")
        lines.append(f"\n【分野別内訳】")
        lines.append(f"  地理: {summary['geography_count']}問")
        lines.append(f"  歴史: {summary['history_count']}問")
        lines.append(f"  公民: {summary['civics_count']}問")
        lines.append(f"  時事: {summary['current_affairs_count']}問")
        
        # 各大問の詳細
        lines.append(f"\n【大問別詳細】")
        for section in result['sections']:
            lines.append(f"\n▼ 大問{section['section_number']} ({section['question_count']}問)")
            lines.append("-" * 40)
            
            for q in section['questions']:
                keywords = ', '.join(q['keywords'][:3]) if q['keywords'] else ''
                if keywords:
                    lines.append(f"  問{q['question_number']}: {q['theme']} [{q['field']}] | {keywords}")
                else:
                    lines.append(f"  問{q['question_number']}: {q['theme']} [{q['field']}]")
        
        return '\n'.join(lines)