"""
問題番号の再割り当てモジュール
OCRで順序が乱れた問題を正しい大問に再割り当て
"""

from typing import List, Dict, Tuple, TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

# 型チェック時のみQuestionクラスを定義（循環インポート回避）
if TYPE_CHECKING:
    from dataclasses import dataclass, field
    
    @dataclass
    class Question:
        """問題を表すデータクラス"""
        level: str
        number: str
        text: str
        position: Tuple[int, int]
        marker_type: str
        children: List['Question']
        themes: List[str]


class QuestionReassigner:
    """問題の再割り当てを行うクラス"""
    
    def reassign_questions(self, structure: List[Question]) -> List[Question]:
        """
        問題番号に基づいて問題を正しい大問に再割り当て
        
        Args:
            structure: 階層構造（大問のリスト）
            
        Returns:
            再割り当て後の階層構造
        """
        if not structure:
            return structure
        
        # 各大問の問題を収集
        major_questions_map = {}
        for major in structure:
            major_num = major.number
            major_questions_map[major_num] = {
                'major': major,
                'questions': list(major.children)  # コピーを作成
            }
        
        # 問題番号の連続性をチェックして再割り当て
        for major_num in sorted(major_questions_map.keys()):
            major_data = major_questions_map[major_num]
            questions = major_data['questions']
            
            if not questions:
                continue
            
            # 問題番号を整数に変換してソート
            try:
                sorted_questions = sorted(questions, key=lambda q: int(q.number))
            except (ValueError, TypeError):
                # 番号が整数に変換できない場合はスキップ
                continue
            
            # 連続性をチェック
            reassigned = []
            expected_start = 1
            
            for q in sorted_questions:
                try:
                    q_num = int(q.number)
                    
                    # 番号が大きすぎる場合（次の大問の問題の可能性）
                    if q_num > expected_start + 15:  # 15問以上のギャップは異常
                        # 次の大問に移動する候補
                        next_major_num = str(int(major_num) + 1)
                        if next_major_num in major_questions_map:
                            # 次の大問の最初の問題番号として妥当か確認
                            if q_num <= 3:  # 問1-3なら次の大問の可能性が高い
                                logger.info(f"問{q.number}を大問{major_num}から大問{next_major_num}へ移動")
                                major_questions_map[next_major_num]['questions'].append(q)
                                continue
                    
                    # 番号が小さすぎる場合（前の大問の問題の可能性）
                    if q_num < expected_start - 5:  # 既に処理した番号より5つ以上前
                        # 前の大問に移動する候補
                        prev_major_num = str(int(major_num) - 1)
                        if prev_major_num in major_questions_map:
                            # 前の大問の続きの番号として妥当か確認
                            prev_questions = major_questions_map[prev_major_num]['questions']
                            if prev_questions:
                                max_prev = max(int(pq.number) for pq in prev_questions)
                                if q_num > max_prev and q_num <= max_prev + 3:
                                    logger.info(f"問{q.number}を大問{major_num}から大問{prev_major_num}へ移動")
                                    major_questions_map[prev_major_num]['questions'].append(q)
                                    continue
                    
                    # 正常な範囲内なら保持
                    reassigned.append(q)
                    expected_start = q_num + 1
                    
                except (ValueError, TypeError):
                    # 番号が処理できない場合は保持
                    reassigned.append(q)
            
            # 再割り当て後の問題リストを更新
            major_data['questions'] = reassigned
        
        # 移動した問題がある大問の問題を再ソート
        for major_num, major_data in major_questions_map.items():
            try:
                major_data['questions'] = sorted(
                    major_data['questions'], 
                    key=lambda q: int(q.number)
                )
            except (ValueError, TypeError):
                pass  # ソートできない場合はそのまま
        
        # 構造を再構築
        result = []
        for major_num in sorted(major_questions_map.keys()):
            major = major_questions_map[major_num]['major']
            major.children = major_questions_map[major_num]['questions']
            result.append(major)
        
        # デバッグ情報
        for major in result:
            q_nums = [q.number for q in major.children]
            logger.info(f"再割り当て後 - 大問{major.number}: {len(major.children)}問 ({', '.join(q_nums[:10])}...)")
        
        return result
    
    def detect_misplaced_questions(self, structure: List[Question]) -> Dict[str, List[str]]:
        """
        誤配置された問題を検出
        
        Args:
            structure: 階層構造
            
        Returns:
            各大問の誤配置問題のリスト
        """
        misplaced = {}
        
        for major in structure:
            major_num = major.number
            questions = major.children
            
            if not questions:
                continue
            
            misplaced_nums = []
            
            # 期待される問題番号の範囲を推定
            try:
                q_nums = [int(q.number) for q in questions]
                q_nums.sort()
                
                # 連続性をチェック
                expected = 1
                for num in q_nums:
                    if num > expected + 2:  # 2つ以上のギャップ
                        # この番号は誤配置の可能性
                        for q in questions:
                            if int(q.number) >= num:
                                misplaced_nums.append(q.number)
                        break
                    expected = num + 1
                
                # 大問1で9以上の番号が早期に出現する場合
                if major_num == '1' and any(num >= 9 for num in q_nums[:3]):
                    for q in questions:
                        if int(q.number) >= 9:
                            misplaced_nums.append(q.number)
                
            except (ValueError, TypeError):
                pass
            
            if misplaced_nums:
                misplaced[f"大問{major_num}"] = misplaced_nums
        
        return misplaced