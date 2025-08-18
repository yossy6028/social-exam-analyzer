"""
階層的な問題番号管理システム
大問→中問→小問の階層構造を正しく管理し、重複を防ぐ
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QuestionNode:
    """問題の階層ノード"""
    id: str  # ユニークID（例: "1-2-3" = 第1問の問2の(3)）
    number: str  # 表示用番号（例: "問2(3)"）
    level: int  # 階層レベル（0:大問, 1:中問, 2:小問）
    text: str  # 問題文
    parent_id: Optional[str] = None
    children: List['QuestionNode'] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class HierarchicalQuestionManager:
    """階層的な問題番号管理クラス"""
    
    def __init__(self):
        self.root_nodes: List[QuestionNode] = []
        self.all_nodes: Dict[str, QuestionNode] = {}
        self.current_major = 0  # 現在の大問番号
        self.current_minor = 0  # 現在の中問番号
        self.current_sub = 0    # 現在の小問番号
        
        # 問題番号パターン（優先順位順）
        self.patterns = {
            'major': [
                re.compile(r'^第\s*([一二三四五六七八九十\d]+)\s*問'),
                re.compile(r'^[【\[]\s*第\s*([一二三四五六七八九十\d]+)\s*問\s*[】\]]'),
                re.compile(r'^大問\s*([一二三四五六七八九十\d]+)'),
            ],
            'minor': [
                re.compile(r'^問\s*([一二三四五六七八九十\d]+)(?![問-])'),
                re.compile(r'^[【\[]\s*問\s*([一二三四五六七八九十\d]+)\s*[】\]]'),
                re.compile(r'^設問\s*([一二三四五六七八九十\d]+)'),
            ],
            'sub': [
                re.compile(r'^[\(（]\s*([一二三四五六七八九十\d]+)\s*[\)）]'),
                re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]'),
                re.compile(r'^[ア-ン](?![ア-ン])'),
            ]
        }
    
    def extract_hierarchical_questions(self, ocr_text: str) -> List[QuestionNode]:
        """OCRテキストから階層的に問題を抽出"""
        lines = ocr_text.split('\n')
        self.root_nodes = []
        self.all_nodes = {}
        self.current_major = 0
        self.current_minor = 0
        self.current_sub = 0
        
        current_major_node = None
        current_minor_node = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 大問を検出
            major_match = self._detect_major_question(line)
            if major_match:
                self.current_major += 1
                self.current_minor = 0
                self.current_sub = 0
                
                node_id = str(self.current_major)
                display_number = f"第{self.current_major}問"
                
                current_major_node = QuestionNode(
                    id=node_id,
                    number=display_number,
                    level=0,
                    text=self._extract_question_text(lines, i)
                )
                
                self.root_nodes.append(current_major_node)
                self.all_nodes[node_id] = current_major_node
                current_minor_node = None
                continue
            
            # 中問を検出
            minor_match = self._detect_minor_question(line)
            if minor_match and current_major_node:
                self.current_minor += 1
                self.current_sub = 0
                
                node_id = f"{self.current_major}-{self.current_minor}"
                display_number = f"問{self.current_minor}"
                
                current_minor_node = QuestionNode(
                    id=node_id,
                    number=display_number,
                    level=1,
                    text=self._extract_question_text(lines, i),
                    parent_id=current_major_node.id
                )
                
                current_major_node.children.append(current_minor_node)
                self.all_nodes[node_id] = current_minor_node
                continue
            
            # 小問を検出
            sub_match = self._detect_sub_question(line)
            if sub_match and current_minor_node:
                self.current_sub += 1
                
                node_id = f"{self.current_major}-{self.current_minor}-{self.current_sub}"
                display_number = f"({self.current_sub})"
                
                sub_node = QuestionNode(
                    id=node_id,
                    number=display_number,
                    level=2,
                    text=self._extract_question_text(lines, i),
                    parent_id=current_minor_node.id
                )
                
                current_minor_node.children.append(sub_node)
                self.all_nodes[node_id] = sub_node
        
        # 問題番号の修正とバリデーション
        self._validate_and_fix_numbers()
        
        return self.root_nodes
    
    def _detect_major_question(self, line: str) -> Optional[re.Match]:
        """大問を検出"""
        for pattern in self.patterns['major']:
            match = pattern.match(line)
            if match:
                return match
        return None
    
    def _detect_minor_question(self, line: str) -> Optional[re.Match]:
        """中問を検出（OCRエラー修正含む）"""
        # OCRエラーパターンの修正
        line = self._fix_ocr_errors(line)
        
        for pattern in self.patterns['minor']:
            match = pattern.match(line)
            if match:
                return match
        return None
    
    def _detect_sub_question(self, line: str) -> Optional[re.Match]:
        """小問を検出"""
        for pattern in self.patterns['sub']:
            match = pattern.match(line)
            if match:
                return match
        return None
    
    def _fix_ocr_errors(self, line: str) -> str:
        """OCRエラーを修正"""
        # 「問問」の重複を修正
        line = re.sub(r'問問+', '問', line)
        
        # 「間」を「問」に修正
        line = re.sub(r'間(\d)', r'問\1', line)
        
        # 「問-」のようなパターンを修正
        line = re.sub(r'問[-－ー]', '問', line)
        
        # 全角数字を半角に統一
        trans_table = str.maketrans('０１２３４５６７８９', '0123456789')
        line = line.translate(trans_table)
        
        return line
    
    def _extract_question_text(self, lines: List[str], start_idx: int, max_lines: int = 5) -> str:
        """問題文を抽出（複数行対応）"""
        text_lines = []
        for i in range(start_idx, min(start_idx + max_lines, len(lines))):
            line = lines[i].strip()
            if line:
                text_lines.append(line)
            # 次の問題番号が来たら終了
            if i > start_idx and self._is_new_question(line):
                break
        
        return ' '.join(text_lines)
    
    def _is_new_question(self, line: str) -> bool:
        """新しい問題の開始かどうかを判定"""
        for level_patterns in self.patterns.values():
            for pattern in level_patterns:
                if pattern.match(line):
                    return True
        return False
    
    def _validate_and_fix_numbers(self):
        """問題番号の重複チェックと修正"""
        # 各階層で番号の重複をチェック
        for major_node in self.root_nodes:
            # 中問レベルの重複チェック
            minor_numbers = {}
            for i, minor_node in enumerate(major_node.children):
                # 番号から数字を抽出
                num_match = re.search(r'\d+', minor_node.number)
                if num_match:
                    num = num_match.group()
                    if num in minor_numbers:
                        # 重複発見、連番に修正
                        new_num = i + 1
                        minor_node.number = f"問{new_num}"
                        minor_node.id = f"{major_node.id}-{new_num}"
                        logger.warning(f"重複番号を修正: {num} -> {new_num}")
                    else:
                        minor_numbers[num] = minor_node
                
                # 小問レベルの重複チェック
                sub_numbers = {}
                for j, sub_node in enumerate(minor_node.children):
                    num_match = re.search(r'\d+', sub_node.number)
                    if num_match:
                        num = num_match.group()
                        if num in sub_numbers:
                            # 重複発見、連番に修正
                            new_num = j + 1
                            sub_node.number = f"({new_num})"
                            sub_node.id = f"{minor_node.id}-{new_num}"
                            logger.warning(f"小問の重複番号を修正: {num} -> {new_num}")
                        else:
                            sub_numbers[num] = sub_node
    
    def get_flattened_questions(self) -> List[Dict]:
        """階層構造をフラット化して返す"""
        questions = []
        
        for major_node in self.root_nodes:
            # 大問を追加
            questions.append(self._node_to_dict(major_node))
            
            for minor_node in major_node.children:
                # 中問を追加（大問番号を含む）
                minor_dict = self._node_to_dict(minor_node)
                minor_dict['number'] = f"{major_node.number} {minor_node.number}"
                questions.append(minor_dict)
                
                for sub_node in minor_node.children:
                    # 小問を追加（大問・中問番号を含む）
                    sub_dict = self._node_to_dict(sub_node)
                    sub_dict['number'] = f"{major_node.number} {minor_node.number}{sub_node.number}"
                    questions.append(sub_dict)
        
        return questions
    
    def _node_to_dict(self, node: QuestionNode) -> Dict:
        """ノードを辞書形式に変換"""
        return {
            'id': node.id,
            'number': node.number,
            'level': node.level,
            'text': node.text,
            'parent_id': node.parent_id,
            'metadata': node.metadata
        }
    
    def fix_invalid_numbers(self, questions: List) -> List:
        """「問-」のような不正な番号を修正"""
        for q in questions:
            if hasattr(q, 'number'):
                original = q.number
                # 「問-」パターンを修正
                q.number = re.sub(r'問[-－ー]', '問', q.number)
                
                # 番号が欠落している場合、文脈から推測
                if '問' in q.number and not re.search(r'\d', q.number):
                    # 前後の問題から推測
                    q.number = self._infer_number_from_context(q, questions)
                
                if original != q.number:
                    logger.info(f"番号修正: {original} -> {q.number}")
        
        return questions
    
    def _infer_number_from_context(self, question, all_questions) -> str:
        """文脈から番号を推測"""
        # デフォルトは「問1」
        return "問1"