"""
社会科目入試問題分析モジュール（改善版）
OCRノイズ除去と大問構造認識、分野判定精度向上
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
import logging

# 改善されたテーマ抽出システムをインポート
try:
    from .improved_theme_extractor import ImprovedThemeExtractor, ThemeExtractionResult
    USE_IMPROVED_EXTRACTOR = True
except ImportError:
    USE_IMPROVED_EXTRACTOR = False

# 既存のクラスをインポート
from .social_analyzer import (
    SocialField, ResourceType, QuestionFormat, SocialQuestion,
    SocialAnalyzer as BaseSocialAnalyzer
)

logger = logging.getLogger(__name__)


class ImprovedSocialAnalyzer(BaseSocialAnalyzer):
    """改善された社会科目問題分析器"""
    
    def __init__(self):
        super().__init__()
        # 重み付けパターンを追加
        self.weighted_field_patterns = self._initialize_weighted_patterns()
    
    def _initialize_weighted_patterns(self) -> Dict[SocialField, List[Tuple[re.Pattern, float]]]:
        """重み付けされた分野判定パターン"""
        return {
            SocialField.CIVICS: [
                (re.compile(r'国会'), 3.0),
                (re.compile(r'内閣'), 3.0),
                (re.compile(r'三権分立'), 3.0),
                (re.compile(r'裁判所'), 2.5),
                (re.compile(r'憲法'), 2.5),
                (re.compile(r'選挙'), 2.0),
                (re.compile(r'参議院'), 2.5),
                (re.compile(r'衆議院'), 2.5),
                (re.compile(r'地方自治'), 2.0),
                (re.compile(r'政治'), 1.5),
            ],
            SocialField.HISTORY: [
                (re.compile(r'昭和時代'), 3.0),
                (re.compile(r'平成時代'), 3.0),
                (re.compile(r'明治時代'), 3.0),
                (re.compile(r'大正時代'), 3.0),
                (re.compile(r'江戸時代'), 3.0),
                (re.compile(r'鎌倉時代'), 3.0),
                (re.compile(r'室町時代'), 3.0),
                (re.compile(r'戦国時代'), 3.0),
                (re.compile(r'平安時代'), 3.0),
                (re.compile(r'奈良時代'), 3.0),
                (re.compile(r'飛鳥時代'), 3.0),
                (re.compile(r'古墳時代'), 3.0),
                (re.compile(r'弥生時代'), 3.0),
                (re.compile(r'縄文時代'), 3.0),
                (re.compile(r'建武の新政'), 2.5),
                (re.compile(r'時代'), 1.0),
            ],
            SocialField.GEOGRAPHY: [
                (re.compile(r'関東地方'), 3.0),
                (re.compile(r'近畿地方'), 3.0),
                (re.compile(r'中部地方'), 3.0),
                (re.compile(r'東北地方'), 3.0),
                (re.compile(r'九州地方'), 3.0),
                (re.compile(r'中国地方'), 3.0),
                (re.compile(r'四国地方'), 3.0),
                (re.compile(r'北海道'), 3.0),
                (re.compile(r'沖縄'), 3.0),
                (re.compile(r'三大都市圏'), 2.5),
                (re.compile(r'地形図'), 2.0),
                (re.compile(r'農業産出額'), 2.0),
                (re.compile(r'貿易'), 2.0),
                (re.compile(r'地方'), 1.5),
                (re.compile(r'都道府県'), 2.0),
            ],
        }
    
    def _detect_field(self, text: str) -> SocialField:
        """改善された分野判定（重み付けスコアリング）"""
        scores = {}
        
        # 重み付けスコアの計算
        for field, weighted_patterns in self.weighted_field_patterns.items():
            score = 0
            for pattern, weight in weighted_patterns:
                if pattern.search(text):
                    score += weight
            if score > 0:
                scores[field] = score
        
        # 通常パターンも併用（重みは1.0）
        for field, patterns in self.field_patterns.items():
            if field not in scores:
                scores[field] = 0
            additional_score = sum(1 for pattern in patterns if pattern.search(text))
            scores[field] += additional_score
        
        # スコアがない場合
        if not scores:
            # 時事問題のキーワードが含まれているか確認
            if self._is_current_affairs(text):
                return SocialField.CURRENT_AFFAIRS
            return SocialField.MIXED
        
        # 合計スコアを計算
        total_score = sum(scores.values())
        
        # 最高スコアの分野を特定
        max_field = max(scores, key=scores.get)
        max_score = scores[max_field]
        
        # デバッグログ
        logger.debug(f"分野判定スコア: {scores}")
        logger.debug(f"最高スコア分野: {max_field.value} ({max_score}/{total_score})")
        
        # 70%以上のウェイトがある場合、その分野に分類
        if total_score > 0 and (max_score / total_score) >= 0.7:
            return max_field
        
        # 時事問題の要素が強い場合
        if self._is_current_affairs(text):
            # 時事問題として分類する閾値を下げる（50%以上）
            if total_score > 0 and (max_score / total_score) >= 0.5:
                return max_field
            return SocialField.CURRENT_AFFAIRS
        
        # 複数分野が拮抗している場合（70%未満）
        # ただし、明確な特徴がある場合は分類する
        if max_score >= 3:  # 3つ以上のパターンにマッチ
            return max_field
        
        # それ以外は総合とする
        return SocialField.MIXED
    
    def _is_ocr_noise(self, text: str) -> bool:
        """テキストがOCRノイズかどうか判定"""
        # 除外すべきキーワード
        noise_keywords = [
            '社会解答用紙', '採点欄', '受験番号', 
            '得点', '評点', '氏名'
        ]
        
        # 教育的内容を含む場合はノイズではない
        educational_keywords = [
            '問題', '説明', '答え', '選', '次の', '下線', '空欄',
            '時代', '地方', '憲法', '政治', '経済'
        ]
        
        text_lower = text.lower()
        
        # 短すぎるテキストはチェック
        if len(text.strip()) < 10:
            return True
        
        # 教育的キーワードがある場合はFalse
        if any(edu_kw in text for edu_kw in educational_keywords):
            return False
        
        # ノイズキーワードがある場合はTrue
        return any(noise_kw in text for noise_kw in noise_keywords)
    
    def _extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """改善された問題抽出（大問構造認識とOCRノイズ除去）"""
        questions = []
        
        # OCRノイズを除外するパターン
        noise_patterns = [
            r'社会解答用紙',
            r'採点欄',
            r'受験番号',
            r'氏\s*名',
            r'得\s*点',
            r'評\s*点',
            r'※[\s\S]*?解答は',
            r'注意[\s\S]*?問題',
            r'配点[\s\S]*?点',
        ]
        
        # ノイズを除外
        cleaned_text = text
        for pattern in noise_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # 大問構造を認識
        large_question_matches = list(re.finditer(r'大問\s*(\d+)|第\s*(\d+)\s*問|^\s*(\d+)\s*\.', cleaned_text, re.MULTILINE))
        
        if large_question_matches:
            # 大問ごとに処理
            for i, large_match in enumerate(large_question_matches):
                # 大問番号を取得
                large_num = large_match.group(1) or large_match.group(2) or large_match.group(3)
                start_pos = large_match.end()
                
                # 次の大問までの範囲を取得
                if i + 1 < len(large_question_matches):
                    end_pos = large_question_matches[i + 1].start()
                    section_text = cleaned_text[start_pos:end_pos]
                else:
                    section_text = cleaned_text[start_pos:]
                
                # 小問を抽出
                small_patterns = [
                    re.compile(r'問\s*(\d+)[\．、\s](.+?)(?=問\s*\d+|$)', re.DOTALL),
                    re.compile(r'【問\s*(\d+)】(.+?)(?=【問\s*\d+】|$)', re.DOTALL),
                    re.compile(r'\((\d+)\)[\s](.+?)(?=\(\d+\)|$)', re.DOTALL),
                ]
                
                found_questions = False
                for pattern in small_patterns:
                    matches = pattern.findall(section_text)
                    if matches:
                        for q_num, q_text in matches:
                            # 大問番号を含めて問題番号を作成
                            full_q_num = f"大問{large_num}-問{q_num}"
                            # OCRノイズでないことを確認
                            if not self._is_ocr_noise(q_text):
                                questions.append((full_q_num, q_text.strip()))
                                found_questions = True
                        break
                
                # 小問が見つからない場合は大問全体を1つの問題として扱う
                if not found_questions and not self._is_ocr_noise(section_text):
                    questions.append((f"大問{large_num}", section_text.strip()))
        
        else:
            # 大問構造がない場合は通常の問題番号を探す
            patterns = [
                re.compile(r'問\s*(\d+)[\．、\s](.+?)(?=問\s*\d+|$)', re.DOTALL),
                re.compile(r'【問\s*(\d+)】(.+?)(?=【問\s*\d+】|$)', re.DOTALL),
            ]
            
            for pattern in patterns:
                matches = pattern.findall(cleaned_text)
                if matches:
                    # 問題番号の重複を避けるため、セットで管理
                    seen_numbers = set()
                    for m in matches:
                        q_num = m[0]
                        q_text = m[1]
                        
                        # 重複チェック
                        if q_num in seen_numbers:
                            # 重複している場合は連番を付ける
                            counter = 2
                            while f"{q_num}-{counter}" in seen_numbers:
                                counter += 1
                            q_num = f"{q_num}-{counter}"
                        
                        seen_numbers.add(q_num)
                        
                        if not self._is_ocr_noise(q_text):
                            questions.append((f"問{q_num}", q_text.strip()))
                    break
            
            # 問題が見つからない場合は段落で分割
            if not questions:
                paragraphs = cleaned_text.split('\n\n')
                for i, p in enumerate(paragraphs):
                    if len(p.strip()) > 20 and not self._is_ocr_noise(p):
                        questions.append((f"問{i+1}", p.strip()))
        
        return questions
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """改善された文書分析"""
        # 問題を抽出
        questions = self._extract_questions(text)
        
        # 各問題を分析
        analyzed_questions = []
        for q_num, q_text in questions:
            analyzed_questions.append(self.analyze_question(q_text, q_num))
        
        # 総合と判定された問題を再評価
        analyzed_questions = self._reevaluate_mixed_questions(analyzed_questions)
        
        # 統計情報を集計
        stats = self._calculate_statistics(analyzed_questions)
        
        return {
            'questions': analyzed_questions,
            'statistics': stats,
            'total_questions': len(analyzed_questions)
        }