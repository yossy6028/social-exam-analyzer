"""
Gemini APIを使用した最終出力の検証・調整モジュール
問題番号の重複や欠番を検出し、自動修正する
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuestionEntry:
    """問題エントリを表すデータクラス"""
    major_num: str
    question_num: str
    topic: str
    field: str
    keywords: str
    original_line: str


class GeminiValidator:
    """Gemini APIを使用した検証・調整クラス"""
    
    def __init__(self):
        """Gemini APIの初期化"""
        try:
            # API キーの設定
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                # 代替: Google Application Default Credentials
                api_key = self._get_api_key_from_adc()
            
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.enabled = True
                logger.info("Gemini API validator initialized")
            else:
                self.enabled = False
                logger.warning("Gemini API key not found, validator disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            self.enabled = False
    
    def _get_api_key_from_adc(self) -> Optional[str]:
        """ADCからAPIキーを取得"""
        try:
            # ここでADCからAPIキーを取得する処理を実装
            # 現在は簡略化のためNoneを返す
            return None
        except:
            return None
    
    def validate_and_fix(self, output_text: str) -> str:
        """
        出力テキストを検証し、修正する
        
        Args:
            output_text: 検証対象のテキスト
            
        Returns:
            修正後のテキスト
        """
        # Gemini CLIを使用する代替実装
        import subprocess
        import tempfile
        
        try:
            prompt = self._create_validation_prompt(output_text)
            
            # Gemini CLIを使用
            result = subprocess.run(
                ['gemini'],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0 and result.stdout:
                # 出力からプロンプト部分を除去
                lines = result.stdout.split('
')
                
                # "▼ 大問"で始まる行を探す
                start_idx = -1
                for i, line in enumerate(lines):
                    if '▼ 大問' in line or '【出題テーマ一覧】' in line:
                        start_idx = i - 5  # 少し前から取得
                        break
                
                if start_idx >= 0:
                    # 修正されたテキスト部分を抽出
                    fixed_lines = []
                    in_output = False
                    
                    for line in lines[start_idx:]:
                        if '============' in line or '社会科入試問題分析' in line:
                            in_output = True
                        if in_output:
                            fixed_lines.append(line)
                        if '分析終了' in line:
                            break
                    
                    if fixed_lines:
                        fixed_text = '
'.join(fixed_lines)
                        logger.info("Gemini CLIで修正を実行しました")
                        return fixed_text
            
            logger.warning("Gemini CLIから有効な応答がありませんでした")
            return output_text
            
        except FileNotFoundError:
            logger.error("Gemini CLIが見つかりません")
            return output_text
        except Exception as e:
            logger.error(f"Gemini CLI実行エラー: {e}")
            return output_text
        
        try:
            # Geminiに検証・修正を依頼
            prompt = self._create_validation_prompt(output_text)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                fixed_text = response.text
                
                # 修正があった場合はログに記録
                if fixed_text != output_text:
                    logger.info("Gemini validator fixed issues in the output")
                    self._log_changes(output_text, fixed_text)
                
                return fixed_text
            else:
                logger.warning("No response from Gemini, returning original text")
                return output_text
                
        except Exception as e:
            logger.error(f"Gemini validation failed: {e}")
            return output_text
    
    def _create_validation_prompt(self, text: str) -> str:
        """検証用プロンプトを作成"""
        return f"""
以下は日本の中学入試問題の分析結果です。問題番号に重複や欠番がないか確認し、必要に応じて修正してください。

【重要なルール】
1. 各大問内で問題番号は1から連続している必要があります
2. 同じ問題番号が重複してはいけません
3. 問題の総数は変更しないでください
4. 分野（地理・歴史・公民・総合）やテーマは変更しないでください
5. 出力形式は元のフォーマットを維持してください

【チェックポイント】
- 大問1-問9が2つある → 1つは大問2-問9にすべき
- 大問1-問10が2つある → 1つは大問2-問10にすべき
- 大問1-問11が2つある → 1つは大問2-問11にすべき
- 大問2に問9-11が欠番 → 上記の重複分を正しく配置

【入力テキスト】
{text}

【指示】
上記のテキストを検証し、問題番号の重複や欠番を修正してください。
修正後のテキストのみを出力し、説明は不要です。
元のフォーマットを完全に維持してください。
"""
    
    def _log_changes(self, original: str, fixed: str):
        """変更内容をログに記録"""
        original_lines = original.split('\n')
        fixed_lines = fixed.split('\n')
        
        changes = []
        for i, (orig, fix) in enumerate(zip(original_lines, fixed_lines)):
            if orig != fix:
                changes.append(f"Line {i+1}: '{orig}' -> '{fix}'")
        
        if changes:
            logger.info(f"Gemini made {len(changes)} changes:")
            for change in changes[:10]:  # 最初の10件のみログ
                logger.info(f"  {change}")
    
    def validate_sequence(self, questions: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """
        問題番号の連続性を検証
        
        Args:
            questions: [(問題ID, 問題テキスト), ...] のリスト
            
        Returns:
            エラー情報の辞書
        """
        errors = {
            'duplicates': [],
            'missing': [],
            'out_of_order': []
        }
        
        # 大問ごとに問題を整理
        major_questions = {}
        for q_id, _ in questions:
            if '大問' in q_id and '-問' in q_id:
                parts = q_id.split('-')
                major = parts[0]
                q_num = parts[1].replace('問', '')
                
                if major not in major_questions:
                    major_questions[major] = []
                major_questions[major].append(q_num)
        
        # 各大問内で検証
        for major, q_nums in major_questions.items():
            # 重複チェック
            seen = set()
            for num in q_nums:
                if num in seen:
                    errors['duplicates'].append(f"{major}-問{num}")
                seen.add(num)
            
            # 連続性チェック
            try:
                int_nums = sorted([int(n) for n in q_nums])
                expected = list(range(1, max(int_nums) + 1))
                
                # 欠番チェック
                for exp in expected:
                    if exp not in int_nums:
                        errors['missing'].append(f"{major}-問{exp}")
                
                # 順序チェック
                prev = 0
                for num in int_nums:
                    if num <= prev:
                        errors['out_of_order'].append(f"{major}-問{num}")
                    prev = num
                    
            except ValueError:
                logger.warning(f"Could not validate {major}: non-numeric question numbers")
        
        return errors
    
    def auto_fix_duplicates(self, questions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        重複した問題番号を自動修正
        
        Args:
            questions: [(問題ID, 問題テキスト), ...] のリスト
            
        Returns:
            修正後のリスト
        """
        fixed_questions = []
        seen_ids = {}
        
        for q_id, q_text in questions:
            if q_id in seen_ids:
                # 重複を検出
                logger.info(f"Duplicate found: {q_id}")
                
                # 次の大問に移動すべきか判断
                if '大問1-問' in q_id and any('大問2' in x[0] for x in fixed_questions):
                    # 大問1の問題が大問2セクションにある場合
                    new_id = q_id.replace('大問1', '大問2')
                    logger.info(f"Moving {q_id} to {new_id}")
                    fixed_questions.append((new_id, q_text))
                else:
                    # そのまま保持（後で手動修正が必要）
                    fixed_questions.append((q_id, q_text))
            else:
                fixed_questions.append((q_id, q_text))
                seen_ids[q_id] = True
        
        return fixed_questions