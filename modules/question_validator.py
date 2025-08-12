"""
設問番号の連続性チェックと検証機能
"""

import re
import unicodedata
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class QuestionValidator:
    """設問番号の検証と連続性チェックを行うクラス"""
    
    # 漢数字と算用数字の対応
    KANJI_TO_NUM = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15
    }
    
    NUM_TO_KANJI = {v: k for k, v in KANJI_TO_NUM.items()}
    
    def __init__(self):
        """初期化"""
        self.warnings = []
    
    def _sanitize_input(self, text: str) -> str:
        """
        入力文字列をサニタイズ
        
        Args:
            text: 入力文字列
            
        Returns:
            サニタイズされた文字列
        """
        if not text:
            return ""
        
        # 文字列長を制限
        if len(text) > 100:
            logger.warning(f"入力文字列が長すぎます: {len(text)}文字")
            text = text[:100]
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 制御文字を除去
        text = ''.join(char for char in text if not unicodedata.category(char).startswith('C'))
        
        # 前後の空白を除去
        return text.strip()
    
    def convert_question_number(self, number_str: str) -> Optional[int]:
        """
        設問番号を数値に変換
        
        Args:
            number_str: 設問番号の文字列（例: '一', '二', '1', '2'）
            
        Returns:
            数値、変換できない場合はNone
        """
        # 入力をサニタイズ
        number_str = self._sanitize_input(number_str)
        
        if not number_str:
            return None
        
        # 漢数字の場合
        if number_str in self.KANJI_TO_NUM:
            return self.KANJI_TO_NUM[number_str]
        
        # 算用数字の場合
        try:
            num = int(number_str)
            # 妙に大きい数値を拒否
            if num < 1 or num > 100:
                logger.warning(f"設問番号が範囲外: {num}")
                return None
            return num
        except ValueError:
            return None
    
    def check_continuity(self, questions: List[Dict]) -> Tuple[bool, List[str]]:
        """
        設問番号の連続性をチェック
        
        Args:
            questions: 設問のリスト
            
        Returns:
            (連続性があるか, 警告メッセージのリスト)
        """
        if not questions:
            return True, []
        
        warnings = []
        numbers = []
        
        # 設問番号を数値に変換
        for q in questions:
            num = self.convert_question_number(q.get('number', ''))
            if num is not None:
                numbers.append(num)
        
        if not numbers:
            warnings.append("設問番号が認識できません")
            return False, warnings
        
        # ソート
        numbers.sort()
        
        # 連続性チェック
        is_continuous = True
        
        # 最初の番号が1でない場合
        if numbers[0] != 1:
            warnings.append(f"設問が問{numbers[0]}から始まっています（通常は問1から）")
            is_continuous = False
        
        # 番号の飛びをチェック
        for i in range(1, len(numbers)):
            if numbers[i] != numbers[i-1] + 1:
                gap_start = numbers[i-1] + 1
                gap_end = numbers[i] - 1
                if gap_start == gap_end:
                    missing = f"問{gap_start}"
                else:
                    missing = f"問{gap_start}〜問{gap_end}"
                warnings.append(f"{missing}が欠落しています")
                is_continuous = False
        
        return is_continuous, warnings
    
    def validate_section_questions(self, sections: List[Dict]) -> Dict[str, any]:
        """
        各セクションの設問を検証
        
        Args:
            sections: セクションのリスト
            
        Returns:
            検証結果
        """
        results = {
            'valid': True,
            'sections': [],
            'warnings': [],
            'suggestions': []
        }
        
        for i, section in enumerate(sections):
            section_num = i + 1
            questions = section.get('questions', [])
            
            # 連続性チェック
            is_continuous, warnings = self.check_continuity(questions)
            
            section_result = {
                'section_number': section_num,
                'question_count': len(questions),
                'is_continuous': is_continuous,
                'warnings': warnings
            }
            
            # 設問番号のリスト
            numbers = []
            for q in questions:
                num = self.convert_question_number(q.get('number', ''))
                if num:
                    numbers.append(num)
            
            if numbers:
                section_result['question_numbers'] = sorted(numbers)
                section_result['first_question'] = min(numbers)
                section_result['last_question'] = max(numbers)
            
            results['sections'].append(section_result)
            
            # 全体の警告に追加
            if warnings:
                for w in warnings:
                    results['warnings'].append(f"セクション{section_num}: {w}")
                results['valid'] = False
        
        # セクション間の関係を分析
        results['suggestions'] = self._analyze_section_relationships(results['sections'])
        
        return results
    
    def _analyze_section_relationships(self, section_results: List[Dict]) -> List[str]:
        """
        セクション間の関係を分析して統合の提案を行う
        
        Args:
            section_results: 各セクションの検証結果
            
        Returns:
            提案のリスト
        """
        suggestions = []
        
        # 連続する設問番号を持つセクションを探す
        for i in range(len(section_results) - 1):
            current = section_results[i]
            next_sec = section_results[i + 1]
            
            # 両方に設問番号がある場合
            if 'last_question' in current and 'first_question' in next_sec:
                # 連続している可能性をチェック
                if next_sec['first_question'] == current['last_question'] + 1:
                    suggestions.append(
                        f"セクション{current['section_number']}と"
                        f"セクション{next_sec['section_number']}は"
                        f"同じ大問の可能性があります（設問が連続）"
                    )
                elif next_sec['first_question'] > current['last_question'] + 1:
                    gap = next_sec['first_question'] - current['last_question'] - 1
                    suggestions.append(
                        f"セクション{current['section_number']}と"
                        f"セクション{next_sec['section_number']}の間に"
                        f"{gap}問の欠落があります"
                    )
        
        return suggestions
    
    def merge_sections_by_continuity(self, sections: List[Dict]) -> List[Dict]:
        """
        設問番号の連続性に基づいてセクションを統合
        
        Args:
            sections: セクションのリスト
            
        Returns:
            統合後のセクションリスト
        """
        if not sections:
            return sections
        
        merged = []
        current_group = [sections[0]]
        
        for i in range(1, len(sections)):
            prev_section = current_group[-1]
            curr_section = sections[i]
            
            # 設問番号を取得
            prev_questions = prev_section.get('questions', [])
            curr_questions = curr_section.get('questions', [])
            
            if prev_questions and curr_questions:
                # 最後と最初の設問番号を比較
                prev_last = self._get_max_question_number(prev_questions)
                curr_first = self._get_min_question_number(curr_questions)
                
                # 連続している場合は統合
                if prev_last and curr_first and curr_first == prev_last + 1:
                    current_group.append(curr_section)
                else:
                    # 統合してmergedに追加
                    if len(current_group) > 1:
                        merged.append(self._merge_section_group(current_group))
                    else:
                        merged.append(current_group[0])
                    current_group = [curr_section]
            else:
                # 設問がない場合は別グループ
                if len(current_group) > 1:
                    merged.append(self._merge_section_group(current_group))
                else:
                    merged.append(current_group[0])
                current_group = [curr_section]
        
        # 最後のグループを追加
        if len(current_group) > 1:
            merged.append(self._merge_section_group(current_group))
        else:
            merged.append(current_group[0])
        
        return merged
    
    def _get_min_question_number(self, questions: List[Dict]) -> Optional[int]:
        """設問リストから最小の番号を取得"""
        numbers = []
        for q in questions:
            num = self.convert_question_number(q.get('number', ''))
            if num:
                numbers.append(num)
        return min(numbers) if numbers else None
    
    def _get_max_question_number(self, questions: List[Dict]) -> Optional[int]:
        """設問リストから最大の番号を取得"""
        numbers = []
        for q in questions:
            num = self.convert_question_number(q.get('number', ''))
            if num:
                numbers.append(num)
        return max(numbers) if numbers else None
    
    def _merge_section_group(self, sections: List[Dict]) -> Dict:
        """
        複数のセクションを1つに統合
        
        Args:
            sections: 統合するセクションのリスト
            
        Returns:
            統合されたセクション
        """
        merged = {
            'number': sections[0]['number'],
            'source': sections[0].get('source'),
            'characters': sum(s.get('characters', 0) for s in sections),
            'questions': [],
            'genre': sections[0].get('genre'),
            'theme': sections[0].get('theme'),
            'is_kanji': sections[0].get('is_kanji', False),
            'merged_from': [s['number'] for s in sections]
        }
        
        # すべての設問を統合
        for section in sections:
            merged['questions'].extend(section.get('questions', []))
        
        # 設問を番号順にソート
        merged['questions'].sort(key=lambda q: self.convert_question_number(q.get('number', '')) or 0)
        
        # 出典情報を優先的に取得
        for section in sections:
            if section.get('source'):
                merged['source'] = section['source']
                break
        
        return merged
    
    def display_validation_results(self, results: Dict):
        """
        検証結果を表示
        
        Args:
            results: 検証結果
        """
        print("\n" + "="*60)
        print("設問番号検証結果")
        print("="*60)
        
        if results['valid']:
            print("✅ すべてのセクションで設問番号が連続しています")
        else:
            print("⚠️  設問番号に不連続な箇所があります")
        
        print("\n【各セクションの詳細】")
        for section in results['sections']:
            print(f"\nセクション{section['section_number']}:")
            print(f"  設問数: {section['question_count']}")
            if 'question_numbers' in section:
                print(f"  設問番号: 問{section['first_question']}〜問{section['last_question']}")
                print(f"  番号リスト: {section['question_numbers']}")
            print(f"  連続性: {'✅ OK' if section['is_continuous'] else '❌ NG'}")
            
            if section['warnings']:
                print("  警告:")
                for w in section['warnings']:
                    print(f"    - {w}")
        
        if results['suggestions']:
            print("\n【提案】")
            for suggestion in results['suggestions']:
                print(f"  💡 {suggestion}")
        
        print("="*60)