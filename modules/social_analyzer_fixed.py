"""
社会科目入試問題分析モジュール（修正版）
OCR生データの正確な処理と問題構造の適切な認識
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field as dataclass_field
from enum import Enum
import logging

# 改善されたテーマ抽出システムをインポート（強化版優先）
try:
    from .theme_extractor_enhanced import EnhancedThemeExtractor, ExtractedTheme
    USE_ENHANCED_EXTRACTOR = True
    USE_V2_EXTRACTOR = False
    USE_IMPROVED_EXTRACTOR = False
except ImportError:
    try:
        from .theme_extractor_v2 import ThemeExtractorV2, ExtractedTheme
        EnhancedThemeExtractor = ThemeExtractorV2  # フォールバック
        USE_ENHANCED_EXTRACTOR = False
        USE_V2_EXTRACTOR = True
        USE_IMPROVED_EXTRACTOR = False
    except ImportError:
        try:
            from .improved_theme_extractor import ImprovedThemeExtractor, ThemeExtractionResult
            USE_IMPROVED_EXTRACTOR = True
            USE_V2_EXTRACTOR = False
            USE_ENHANCED_EXTRACTOR = False
        except ImportError:
            USE_IMPROVED_EXTRACTOR = False
            USE_V2_EXTRACTOR = False
            USE_ENHANCED_EXTRACTOR = False

# 既存のクラスをインポート
from .social_analyzer import (
    SocialField, ResourceType, QuestionFormat, SocialQuestion,
    SocialAnalyzer as BaseSocialAnalyzer
)

logger = logging.getLogger(__name__)


class FixedSocialAnalyzer(BaseSocialAnalyzer):
    """修正された社会科目問題分析器"""
    
    def __init__(self):
        super().__init__()
        # 重み付けパターンを追加
        self.weighted_field_patterns = self._initialize_weighted_patterns()
        
        # 強化版テーマ抽出器を初期化（Web検索無効で除外パターンを優先）
        if USE_ENHANCED_EXTRACTOR or USE_V2_EXTRACTOR:
            self.theme_extractor = EnhancedThemeExtractor(enable_web_search=False)
            # 基底クラスとの互換性のため両方の名前で設定
            self.theme_extractor_v2 = self.theme_extractor
            logger.info("強化版テーマ抽出器を使用します（Web検索無効）")
        else:
            self.theme_extractor = None
            self.theme_extractor_v2 = None
            logger.info("従来のテーマ抽出を使用します")
    
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
        
        # まず時代名を明示的にチェック（歴史優先）
        time_period_patterns = [
            '縄文時代', '弥生時代', '古墳時代', '飛鳥時代', '奈良時代',
            '平安時代', '鎌倉時代', '室町時代', '戦国時代', '安土桃山時代',
            '江戸時代', '明治時代', '大正時代', '昭和時代', '平成時代', '令和時代'
        ]
        
        # 時代名が含まれている場合は歴史として強く判定
        for period in time_period_patterns:
            if period in text:
                # 時代が主題の場合は歴史として確定
                if '特徴' in text or '文化' in text or '政治' in text or '経済' in text:
                    return SocialField.HISTORY
                # 時代名があれば歴史のスコアに大きなボーナス
                scores[SocialField.HISTORY] = scores.get(SocialField.HISTORY, 0) + 5.0
        
        # 重み付けスコアの計算
        for field, weighted_patterns in self.weighted_field_patterns.items():
            score = scores.get(field, 0)
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
    
    def _clean_ocr_text(self, text: str) -> str:
        """OCRテキストのクリーニング"""
        # 試験の注意事項と表紙情報を除去（強化版）
        patterns_to_remove = [
            r'【注意】[\s\S]*?問題は次のページから始まります。',
            r'令和\d+年度\s*第\d+回入試[\s\S]*?\(問題用紙\)',
            r'注意[\s\S]*?(?=\d+\.|$)',  # 「注意」から数字で始まる行まで
            r'\d+\.\s*指示があるまで開けてはいけません[\s\S]*?(?=\d+\.|$)',
            r'\d+\.\s*問題は\d+.*?まであります[\s\S]*?(?=\d+\.|$)', 
            r'\d+\.\s*声を出して読んではいけません[\s\S]*?(?=\d+\.|$)',
            r'\d+\.\s*答えはすべて解答用紙に記入し[\s\S]*?(?=\d+\.|$)',
            r'答えはすべて解答用紙に記入すること[^。]*。',
            r'試験終了後は[^。]*。',
            r'問題用紙には名前を書く必要はありません[^。]*。',
            r'開始の合図があるまで開けないこと[^。]*。',
            r'社会解答用紙[^\n]*\n',
            r'採点欄[^\n]*\n',
            r'受験番号[^\n]*\n',
            r'氏\s*名[^\n]*\n',
            r'得\s*点[^\n]*\n',
            r'評\s*点[^\n]*\n',
        ]
        
        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.DOTALL)
        
        return cleaned
    
    def _extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """改善された問題抽出（堅牢な問題構造認識）"""
        questions = []
        
        # OCRテキストをクリーニング
        cleaned_text = self._clean_ocr_text(text)
        
        # デバッグ用：クリーニング後のテキストをログ出力
        logger.debug(f"クリーニング後テキスト（最初の500文字）: {cleaned_text[:500]}")
        
        # 複数の問題抽出パターンを順番に試行
        questions = self._extract_with_multiple_patterns(cleaned_text)
        
        # 問題が見つからない場合の警告とフォールバック
        if not questions:
            logger.warning("問題が抽出できませんでした")
            # フォールバック：適切な内容のセクションのみを抽出
            questions = self._fallback_extraction(cleaned_text)
        
        return questions
    
    def _extract_with_reset_detection(self, text: str) -> List[Tuple[str, str]]:
        """問題番号のリセットを検出して大問を判定（改善版）"""
        questions = []
        
        # 問題番号パターン（問1、問2、問1.など）
        question_pattern = re.compile(r'問\s*(\d+)[\.\s]*([^問]+?)(?=問\s*\d+|$)', re.DOTALL)
        all_matches = list(question_pattern.finditer(text))
        
        if not all_matches:
            return questions
        
        # 大問番号を追跡
        current_large = 1
        previous_num = 0
        reset_count = 0  # リセット回数をカウント
        consecutive_count = 0  # 連続した問題番号のカウント
        
        for i, match in enumerate(all_matches):
            q_num = int(match.group(1))
            q_text = match.group(2)
            
            # 問題番号がリセットされた条件
            # 主要条件: 問題番号が1に戻る（問2以上から問1へ）
            if q_num == 1 and previous_num >= 2:
                current_large += 1
                reset_count += 1
                consecutive_count = 0
                logger.debug(f"問題番号リセット検出: 問{previous_num} → 問1、大問{current_large}へ")
            # 連続性チェック: 期待される番号と異なる場合
            elif previous_num > 0:
                expected_num = previous_num + 1
                # 番号が飛んで1に戻った場合
                if q_num == 1 and previous_num != 1:
                    current_large += 1
                    reset_count += 1
                    consecutive_count = 0
                    logger.debug(f"番号ジャンプによるリセット: 問{previous_num} → 問1、大問{current_large}へ")
                # 番号が期待通り増加
                elif q_num == expected_num:
                    consecutive_count += 1
                # 番号が減少（1以外）
                elif q_num < previous_num:
                    # 大きく戻る場合は大問変更の可能性
                    if previous_num - q_num >= 3:
                        current_large += 1
                        reset_count += 1
                        consecutive_count = 0
                        logger.debug(f"大きな番号減少: 問{previous_num} → 問{q_num}、大問{current_large}へ")
            
            # 問題を追加
            q_text = self._format_question_text(q_text)
            if self._is_valid_question(q_text):
                questions.append((f"大問{current_large}-問{q_num}", q_text.strip()))
            
            previous_num = q_num
        
        # デバッグ情報
        logger.info(f"検出された大問数: {current_large} (リセット回数: {reset_count})")
        
        return questions
    
    def _extract_with_multiple_patterns(self, text: str) -> List[Tuple[str, str]]:
        """複数のパターンで問題抽出を試行"""
        questions = []
        
        # まず大問構造を探す
        # パターン1: 「1. 次の」形式（東京電機大学など）
        large_pattern1 = re.compile(r'^(\d+)\.\s*次の.*?$', re.MULTILINE)
        # パターン2: 単独数字「1」「2」（日本工業大学など）
        large_pattern2 = re.compile(r'^(\d+)\s*\n\s*次の', re.MULTILINE)
        
        large_matches = list(large_pattern1.finditer(text))
        if not large_matches:
            large_matches = list(large_pattern2.finditer(text))
        
        if large_matches:
            # 大問ごとに処理
            for i, match in enumerate(large_matches):
                large_num = match.group(1)
                start_pos = match.start()
                end_pos = large_matches[i + 1].start() if i < len(large_matches) - 1 else len(text)
                section_text = text[start_pos:end_pos]
                
                # 各大問内で問題を抽出（複数のパターンに対応）
                # パターンA: 問1、問2（ピリオドあり・なし両対応）
                pattern_a = re.compile(r'問\s*(\d+)[\.\s]*([^問]+?)(?=問\s*\d+|$)', re.DOTALL)
                matches_a = pattern_a.findall(section_text)
                
                if matches_a:
                    for q_num, q_text in matches_a:
                        q_text = self._format_question_text(q_text)
                        if self._is_valid_question(q_text):
                            questions.append((f"大問{large_num}-問{q_num}", q_text.strip()))
                
                # パターンB: (1)、(2)のような番号
                if not matches_a:
                    pattern_b = re.compile(r'\((\d+)\)([^\(]+?)(?=\(\d+\)|$)', re.DOTALL)
                    matches_b = pattern_b.findall(section_text)
                    for q_num, q_text in matches_b:
                        q_text = self._format_question_text(q_text)
                        if self._is_valid_question(q_text):
                            questions.append((f"大問{large_num}-({q_num})", q_text.strip()))
        
        # 大問構造がない、または問題が少ない場合は全体から問題を探す
        if len(questions) < 10:  # 閾値を5から10に上げる
            # 直接的な問番号（問1、問2、問1.など）を全文から探す
            # ピリオドありなし両対応
            direct_pattern = re.compile(r'問\s*(\d+)[\.\s]*([^問]+?)(?=問\s*\d+|$)', re.DOTALL)
            direct_matches = direct_pattern.findall(text)
            
            # 既に抽出済みの問題番号を記録
            existing_nums = set()
            for q in questions:
                if '問' in q[0]:
                    # 大問1-問2 から 問2 を抽出
                    parts = q[0].split('問')
                    if len(parts) > 1:
                        existing_nums.add(parts[-1])
            
            for q_num, q_text in direct_matches:
                # 大問番号と問題番号の組み合わせで重複チェック
                if q_num not in existing_nums:
                    q_text = self._format_question_text(q_text)
                    if self._is_valid_question(q_text):
                        # 大問番号を推測（テキスト位置から）
                        found_in_large = False
                        for large_match in large_matches:
                            if text.find(f"問{q_num}") > large_match.start():
                                large_num = large_match.group(1)
                                if f"大問{large_num}-問{q_num}" not in [q[0] for q in questions]:
                                    questions.append((f"大問{large_num}-問{q_num}", q_text.strip()))
                                    found_in_large = True
                                    break
                        
                        if not found_in_large:
                            questions.append((f"問{q_num}", q_text.strip()))
                            existing_nums.add(q_num)
        
        # パターン3: 番号付きセクション（1.、2.など）大問として
        if len(questions) < 5:
            numbered_pattern = re.compile(
                r'^(\d+)\.\s*([\s\S]*?)(?=^\d+\.|$)',
                re.MULTILINE
            )
            
            numbered_matches = numbered_pattern.findall(text)
            for num, q_text in numbered_matches:
                q_text = self._format_question_text(q_text)
                if self._is_valid_question(q_text) and not self._is_instruction_text(q_text):
                    # 既存の問題と重複しないか確認
                    if f"問{num}" not in [q[0] for q in questions]:
                        questions.append((f"問{num}", q_text.strip()))
        
        return questions
    
    def _extract_topic(self, text: str) -> Optional[str]:
        """テーマ抽出をオーバーライド（確実に強化版抽出器を使用）"""
        # 強化版テーマ抽出器を使用
        if hasattr(self, 'theme_extractor') and self.theme_extractor:
            result = self.theme_extractor.extract(text)
            if result.theme:
                logger.debug(f"テーマ抽出成功: '{text[:50]}...' -> '{result.theme}'")
                return result.theme
            else:
                logger.debug(f"テーマ除外: '{text[:50]}...' -> None")
                return None
        
        # フォールバック（基底クラスの処理）
        return super()._extract_topic(text)
    
    def _fallback_extraction(self, text: str) -> List[Tuple[str, str]]:
        """フォールバック用の問題抽出"""
        questions = []
        
        # 段落ベースでの抽出（注意事項を除外）
        paragraphs = text.split('\n\n')
        valid_section_count = 0
        
        for i, p in enumerate(paragraphs):
            p = p.strip()
            if (len(p) > 50 and 
                not self._is_instruction_text(p) and
                self._contains_question_content(p)):
                valid_section_count += 1
                questions.append((f"セクション{valid_section_count}", p[:500] + "..." if len(p) > 500 else p))
        
        return questions
    
    def _is_instruction_text(self, text: str) -> bool:
        """テキストが指示・注意事項かどうかを判定"""
        instruction_keywords = [
            '注意', '指示', '開けてはいけません', '声を出して読んで', 
            '解答用紙に記入', '問題用紙', '試験', '受験番号', '氏名',
            '入試', '回入試', '令和', '年度'
        ]
        
        return any(keyword in text for keyword in instruction_keywords)
    
    def _contains_question_content(self, text: str) -> bool:
        """テキストが実際の問題内容を含んでいるかを判定"""
        question_indicators = [
            '次の', 'について', 'について答え', '選びなさい', '答えなさい',
            '正しいもの', '適切なもの', 'あてはまるもの', '間違っている',
            '地図', '図', 'グラフ', '表', '資料'
        ]
        
        return any(indicator in text for indicator in question_indicators)
    
    def _format_question_text(self, text: str) -> str:
        """問題文を整形"""
        # 選択肢の整形
        text = re.sub(r'([アイウエ])\s*\.\s*', r'\1. ', text)
        
        # 改行の整理
        text = re.sub(r'\n+', '\n', text)
        
        # 余分な空白の削除
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text
    
    def _is_valid_question(self, text: str) -> bool:
        """有効な問題文かどうか判定（緩和版）"""
        # 短すぎるテキストは無効（闾値を低く）
        if len(text.strip()) < 10:
            return False
        
        # 数値データのみの場合は無効
        if re.match(r'^[\d\s\.\,\%]+$', text.strip()):
            return False
        
        # 空文字や空白のみの場合は無効
        if not text.strip():
            return False
        
        # 問題文らしいキーワードがあるか（拡張版）
        question_keywords = [
            '答えなさい', '選びなさい', '説明しなさい', '述べなさい',
            '次の', '空らん', '下線', '適切な', '正しい', 'まちがって',
            '地図', '表', 'グラフ', '図', '資料', '文章', '関連',
            'あてはまる', 'ものを', 'ことを', 'について', 'に関して'
        ]
        
        # キーワードが含まれているか、または一定以上の長さがある場合はOK
        has_keywords = any(keyword in text for keyword in question_keywords)
        is_long_enough = len(text.strip()) >= 50
        
        return has_keywords or is_long_enough
    
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