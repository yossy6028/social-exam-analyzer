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
        
        # 改善された問題抽出器を初期化
        try:
            from .improved_question_extractor import ImprovedQuestionExtractor
            self.question_extractor = ImprovedQuestionExtractor()
            logger.info("改善された問題抽出器を使用します")
        except ImportError:
            self.question_extractor = None
            logger.info("標準の問題抽出を使用します")

        # 用語カタログ（任意）
        try:
            from .terms_repository import TermsRepository
            repo = TermsRepository()
            self.terms_repo = repo if repo.available() else None
        except Exception:
            self.terms_repo = None
    
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
        """問題文から分野を検出（バランスの取れた判定）"""
        if not text:
            return SocialField.MIXED
        
        # 地理の特徴的なキーワード
        geography_keywords = [
            '地図', '地形図', '雨温図', '気候', '気温', '降水量',
            '農業', '工業', '漁業', '産業', '貿易', '輸出', '輸入',
            '都道府県', '地方', '平野', '盆地', '山地', '川', '湖', '海',
            '人口', '都市', '過疎', '過密', '交通', '鉄道', '空港', '港',
            '資源', 'エネルギー', '環境問題', '公害', '自然災害',
            '北海道', '東北', '関東', '中部', '近畿', '中国', '四国', '九州',
            '農産物', '工業製品', '水産物', '特産品', '観光',
            '国土', '領土', '排他的経済水域', '大陸棚'
        ]
        
        # 公民の特徴的なキーワード（現代政治制度に特化）
        civics_keywords = [
            '憲法', '法律', '条文', '権利', '義務', '自由',
            '選挙', '投票', '議会', '国会', '内閣', '裁判',
            '政党', '民主主義', '主権', '三権分立',
            '地方自治', '知事', '市長', '議員', '条例',
            '税金', '予算', '財政', '社会保障', '年金', '医療', '福祉',
            '経済', '市場', '需要', '供給', '価格', '企業', '労働',
            '国連', '国際機関', 'ODA', 'PKO', 'NGO', 'SDGs',
            '人権', '平等', '差別', '環境権', 'プライバシー',
            # 現代政治に特化（歴史的制度と区別）
            '日本国憲法', '議院内閣制', '司法権', '立法権', '行政権'
        ]
        
        # 歴史の特徴的なキーワード（強化版）
        history_keywords = [
            '縄文', '弥生', '古墳', '飛鳥', '奈良', '平安', '鎌倉', '室町',
            '戦国', '安土桃山', '江戸', '明治', '大正', '昭和', '平成',
            '時代', '世紀', '年号', '元号', '西暦',
            '天皇', '将軍', '幕府', '朝廷', '藩', '武士', '貴族',
            '戦争', '戦い', '乱', '変', '事件', '条約', '改革',
            '文化', '仏教', '神道', 'キリスト教', '寺', '神社',
            '遺跡', '遺産', '史跡', '城', '古文書',
            # 中国王朝も歴史として扱う（拡張）
            '秦', '漢', '隋', '唐', '宋', '元', '明', '清', '王朝', '三国', '晋', '五代', '十国',
            '皇帝', '皇后', '太子', '宦官', '科挙', '郡県制', '封建制', '律令制',
            '三省六部', '中央集権', '皇室', '朝廷'
        ]
        
        # 重要度の高いキーワード（これらが含まれていたら優先的にその分野と判定）
        geography_strong = ['雨温図', '地形図', '地図', '気候区分', '農産物', '工業地帯', '都道府県', '関東地方', '近畿地方', '中部地方', '産業']
        civics_strong = ['選挙', '投票', '議会', '憲法', '三権分立', '人権', '税金', '条例', '国会', '内閣', '裁判所', '選挙制度']
        history_strong = [
            '縄文', '弥生', '古墳', '幕府', '天皇', '将軍', '戦国', '明治維新',
            # 中国王朝を歴史の強いキーワードに追加
            '秦', '漢', '隋', '唐', '宋', '元', '明', '清', '王朝', '皇帝'
        ]
        
        # スコアリング
        geo_score = 0
        civ_score = 0
        his_score = 0
        
        # 中国王朝の特別処理（最優先）
        chinese_dynasties = ['秦', '漢', '隋', '唐', '宋', '元', '明', '清', '三国', '晋', '五代', '十国']
        for dynasty in chinese_dynasties:
            if dynasty in text:
                # 王朝名が含まれている場合は歴史として強く判定
                his_score += 5
                logger.debug(f"中国王朝検出: {dynasty} -> 歴史分野に+5点")
                break
        
        # 歴史的政治制度か現代政治制度かの判別
        if any(kw in text for kw in ['政治制度', '政治の仕組み']):
            # 歴史的キーワードが含まれていれば歴史、そうでなければ公民
            historical_context = any(kw in text for kw in ['江戸', '明治', '大正', '昭和', '戦前', '古代', '中世', '近世'])
            if historical_context:
                his_score += 3
                logger.debug("歴史的政治制度として判定")
            else:
                civ_score += 3
                logger.debug("現代政治制度として判定")
        
        # 地理・産業系の処理を強化
        if any(kw in text for kw in ['関東地方', '近畿地方', '中部地方', '東北地方', '九州地方', '中国地方', '四国地方', '北海道', '沖縄']):
            if any(kw in text for kw in ['産業', '農業', '工業', '漁業', '気候', '地形', '人口']):
                geo_score += 4
                logger.debug("地方の産業・地理として判定")
        
        # 選挙制度の公民判定を強化
        if '選挙' in text and any(kw in text for kw in ['制度', '仕組み', '方法']):
            civ_score += 4
            logger.debug("選挙制度として公民に判定")
        
        # 強いキーワードのチェック（重み付け2倍）
        for kw in geography_strong:
            if kw in text:
                geo_score += 2
        
        for kw in civics_strong:
            if kw in text:
                civ_score += 2
        
        for kw in history_strong:
            if kw in text:
                his_score += 2
        
        # 通常のキーワードチェック
        for kw in geography_keywords:
            if kw in text:
                geo_score += 1
        
        for kw in civics_keywords:
            if kw in text:
                civ_score += 1
        
        for kw in history_keywords:
            if kw in text:
                his_score += 1
        
        # 最高スコアの分野を返す
        max_score = max(geo_score, civ_score, his_score)
        
        if max_score == 0:
            return SocialField.MIXED
        
        # 同点の場合は総合とする
        if (geo_score == max_score and civ_score == max_score) or \
           (geo_score == max_score and his_score == max_score) or \
           (civ_score == max_score and his_score == max_score):
            return SocialField.MIXED
        
        if geo_score == max_score:
            return SocialField.GEOGRAPHY
        elif civ_score == max_score:
            return SocialField.CIVICS
        elif his_score == max_score:
            return SocialField.HISTORY
        
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
        
        # 改善された問題抽出器を優先的に使用
        if self.question_extractor:
            try:
                questions = self.question_extractor.extract_questions(text)
                if questions:
                    logger.info(f"改善された抽出器で{len(questions)}問を抽出")
                    return questions
            except Exception as e:
                logger.error(f"改善された抽出器でエラー: {e}")
        
        # フォールバック：従来の方法
        questions = []
        
        # OCRテキストをクリーニング
        cleaned_text = self._clean_ocr_text(text)
        
        # デバッグ用：クリーニング後のテキストをログ出力
        logger.debug(f"クリーニング後テキスト（最初の500文字）: {cleaned_text[:500]}")
        
        # 複数の問題抽出パターンを順番に試行
        questions = self._extract_with_multiple_patterns(cleaned_text)
        if questions:
            try:
                logger.info(f"問題抽出: {len(questions)}問を検出（複数パターン）")
            except Exception:
                pass
        
        # 問題が見つからない場合の警告とフォールバック
        if not questions:
            logger.warning("問題が抽出できませんでした")
            # フォールバック：適切な内容のセクションのみを抽出
            questions = self._fallback_extraction(cleaned_text)
            if questions:
                try:
                    logger.info(f"フォールバック抽出: {len(questions)}セクションを疑似設問として採用")
                except Exception:
                    pass
        
        return questions
    
    def _extract_with_reset_detection(self, text: str) -> List[Tuple[str, str]]:
        """問題番号のリセットを検出して大問を判定（改良版・寛容抽出）"""
        questions: List[Tuple[str, str]] = []
        
        # 見出し（大問）候補: 先頭に数字と句点
        large_heading_pattern = re.compile(r'^(\d+)[\.\)]\s*.*$', re.MULTILINE)
        headings = [(m.start(), int(m.group(1))) for m in large_heading_pattern.finditer(text)]
        
        # 問題番号（全角/半角、ピリオドや空白あり）
        question_pattern = re.compile(
            r'問\s*([０-９\d]+)[．\.:：\s　]*([\s\S]*?)(?=\n?問\s*[０-９\d]+|$)'
        )
        all_matches = list(question_pattern.finditer(text))
        if not all_matches:
            return questions
        
        # 全角→半角変換テーブル
        z2h = str.maketrans({chr(ord('０')+i): str(i) for i in range(10)})
        
        current_large = 1
        previous_num = 0
        reset_count = 0
        last_heading_num = None
        
        for m in all_matches:
            raw_num = m.group(1)
            try:
                q_num = int(raw_num.translate(z2h))
            except ValueError:
                continue
            q_text = m.group(2)
            
            # 直前の見出しで大問を上書き（存在する場合）
            pos = m.start()
            heading_candidates = [h for h in headings if h[0] <= pos]
            if heading_candidates:
                _, hnum = heading_candidates[-1]
                if last_heading_num != hnum:
                    current_large = hnum
                    last_heading_num = hnum
            
            # 番号リセット検出
            if q_num == 1 and previous_num >= 2:
                current_large = current_large + 1 if last_heading_num is None else current_large
                reset_count += 1
            elif previous_num > 0:
                expected = previous_num + 1
                if q_num == 1 and previous_num != 1:
                    current_large = current_large + 1 if last_heading_num is None else current_large
                    reset_count += 1
                elif q_num < previous_num and (previous_num - q_num) >= 3:
                    current_large = current_large + 1 if last_heading_num is None else current_large
                    reset_count += 1
            
            # 整形
            q_text = self._format_question_text(q_text)
            
            # 大問検出のため寛容に採用（短文でも「について」や最低限の長さで許可）
            minimal_ok = ('について' in q_text) or (len(q_text.strip()) >= 8)
            if self._is_valid_question(q_text) or minimal_ok:
                questions.append((f"大問{current_large}-問{q_num}", q_text.strip()))
            
            previous_num = q_num
        
        logger.info(f"検出された大問数(推定): {len(set(q[0].split('-')[0] for q in questions))} (リセット: {reset_count})")
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
                # パターンA: 問1、問2（ピリオドあり・なし両対応、全角数字も対応）
                pattern_a = re.compile(r'問\s*([０-９\d]+)[\s\.\:：　]*([^問]+?)(?=問\s*[０-９\d]+|$)', re.DOTALL)
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
            # ピリオドありなし両対応、全角数字も対応
            direct_pattern = re.compile(r'問\s*([０-９\d]+)[\s\.\:：　]*([^問]+?)(?=問\s*[０-９\d]+|$)', re.DOTALL)
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
    
    def _extract_theme_from_context(self, text: str) -> Optional[str]:
        """文脈から具体的なテーマを推定（下線部や代名詞問題用）"""
        
        # 下線部問題の処理
        if '下線部' in text:
            # 前後の文章から具体的な内容を抽出
            context_patterns = [
                # 歴史的制度・政策
                (re.compile(r'参勤交代|幕藩体制|鎖国|検地|刀狩|楽市楽座'), '歴史政策の内容'),
                (re.compile(r'三大改革|享保の改革|寛政の改革|天保の改革'), '江戸時代の改革'),
                (re.compile(r'明治維新|廃藩置県|四民平等|地租改正'), '明治時代の改革'),
                
                # 政治制度
                (re.compile(r'三権分立|議院内閣制|国会|内閣|裁判所'), '政治制度の仕組み'),
                (re.compile(r'憲法|基本的人権|国民主権|平和主義'), '日本国憲法の原則'),
                
                # 地理・産業
                (re.compile(r'工業地帯|工業地域|農業|林業|漁業'), '産業の特徴'),
                (re.compile(r'気候|地形|人口|都市化'), '地理的特徴'),
                
                # 国際関係
                (re.compile(r'条約|同盟|戦争|講和'), '国際関係の変化'),
            ]
            
            for pattern, theme_template in context_patterns:
                if pattern.search(text):
                    return theme_template
        
        # 「この」「その」などの代名詞問題
        pronoun_patterns = [
            # 地方・地域関連
            (re.compile(r'この地方.*?産業'), '地方の産業'),
            (re.compile(r'この地域.*?特徴'), '地域の特徴'),
            (re.compile(r'この地方.*?気候'), '地方の気候'),
            (re.compile(r'この都市.*?発展'), '都市の発展'),
            
            # 時代・政治関連
            (re.compile(r'この時代.*?政治'), '時代の政治'),
            (re.compile(r'この時期.*?社会'), '時期の社会'),
            (re.compile(r'この制度.*?目的'), '制度の目的'),
            (re.compile(r'この政策.*?影響'), '政策の影響'),
            
            # 経済・産業関連
            (re.compile(r'この産業.*?発展'), '産業の発展'),
            (re.compile(r'この工業.*?特徴'), '工業の特徴'),
            (re.compile(r'この貿易.*?変化'), '貿易の変化'),
        ]
        
        for pattern, theme in pronoun_patterns:
            if pattern.search(text):
                return theme
        
        # 説明・答えなさい系の問題
        if any(keyword in text for keyword in ['説明しなさい', '述べなさい', '答えなさい']):
            # 重要なキーワードを探して2文節形式にする
            historical_keywords = ['江戸時代', '明治時代', '大正時代', '昭和時代', '平安時代', '鎌倉時代', '室町時代']
            for keyword in historical_keywords:
                if keyword in text:
                    return f"{keyword}の特徴"
            
            geo_keywords = ['関東地方', '近畿地方', '中部地方', '東北地方', '九州地方', '中国地方', '四国地方']
            for keyword in geo_keywords:
                if keyword in text:
                    return f"{keyword}の特徴"
            
            # 一般的なパターン
            if '産業' in text:
                return '産業の特徴'
            elif '政治' in text:
                return '政治の仕組み'
            elif '制度' in text:
                return '制度の内容'
            elif '改革' in text:
                return '改革の内容'
        
        return None
    
    def _extract_topic(self, text: str) -> Optional[str]:
        """テーマ抽出をオーバーライド（文脈解析を強化）"""
        # 強化版テーマ抽出器を使用
        if hasattr(self, 'theme_extractor') and self.theme_extractor:
            result = self.theme_extractor.extract(text)
            if result.theme:
                # 低信頼度はINFOで可視化、それ以外はDEBUG
                if getattr(result, 'confidence', 1.0) < 0.7:
                    logger.info(
                        f"テーマ抽出低信頼度: '{text[:50]}...' -> '{result.theme}' conf={getattr(result,'confidence',None)}"
                    )
                else:
                    logger.debug(
                        f"テーマ抽出成功: '{text[:50]}...' -> '{result.theme}' conf={getattr(result,'confidence',None)}"
                    )
                return result.theme
            else:
                # 除外されたケースでも、文脈から推定を試みる
                context_theme = self._extract_theme_from_context(text)
                if context_theme:
                    logger.info(f"文脈からテーマ推定: '{text[:50]}...' -> '{context_theme}'")
                    return context_theme
                else:
                    logger.info(f"テーマ抽出なし: '{text[:50]}...' -> None")
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
        """改善された文書分析（文脈情報を保持）"""
        # 全体テキストを保存（問題分析時に使用）
        self._current_full_text = text
        
        # 問題を抽出
        questions = self._extract_questions(text)
        
        # 問題が抽出できない場合のデバッグ情報
        if not questions:
            logger.warning("問題が抽出できませんでした")
            logger.debug(f"入力テキストの最初の1000文字: {text[:1000]}")
            # フォールバック：セクション分割を試みる
            questions = self._emergency_question_extraction(text)
        
        # 各問題を分析
        analyzed_questions = []
        for q_num, q_text in questions:
            # 文脈強化：前後のテキストを含める
            enhanced_text = self._find_question_context(text, q_text)
            # 資料語彙のスコア加点（資料ブロックのキーワードを明示付与）
            enhanced_text = self._augment_with_material_terms(text, enhanced_text)
            analyzed_question = self.analyze_question(enhanced_text, q_num)
            # 元のテキストも保持
            analyzed_question.original_text = q_text
            # ログ: 各設問の主題・分野を可視化
            try:
                logger.info(
                    f"設問分析: {q_num} field={analyzed_question.field.value} "
                    f"topic={analyzed_question.topic if analyzed_question.topic else 'None'}"
                )
            except Exception:
                pass
            analyzed_questions.append(analyzed_question)
        
        # 総合と判定された問題を再評価
        analyzed_questions = self._reevaluate_mixed_questions(analyzed_questions)
        
        # 統計情報を集計
        stats = self._calculate_statistics(analyzed_questions)
        
        return {
            'questions': analyzed_questions,
            'statistics': stats,
            'total_questions': len(analyzed_questions)
        }

    def _augment_with_material_terms(self, full_text: str, ctx_text: str) -> str:
        """資料ブロックの語彙を抽出し、設問文に付与してテーマ化を後押し"""
        try:
            import re
            if not ctx_text:
                return ctx_text
            frag = ctx_text[:30].strip()
            pos = full_text.find(frag) if frag else -1
            start = max(0, pos - 2000) if pos >= 0 else 0
            end = min(len(full_text), pos + 2000) if pos >= 0 else len(full_text)
            window = full_text[start:end]
            material_terms = []
            for m in re.finditer(r'資料[【\[]?.{0,30}?[】\]]?', window):
                block_start = m.start()
                block_end = min(len(window), block_start + 800)
                block = window[block_start:block_end]
                nouns = re.findall(r'[一-龥ァ-ヴー]{2,}', block)
                priority = [
                    '延暦寺','東大寺','法隆寺','薬師寺','鑑真','正倉院','種々薬帳',
                    '韓国併合','柳条湖事件','五・四運動','二十一条の要求',
                    '大阪','大阪市','夢洲','関西国際空港','阪神工業地帯',
                    '人口ピラミッド','雨温図','国連','国際連合'
                ]
                # terms.json を優先的に反映（地理の語彙は重みを大きく）
                repo_hits = []
                if getattr(self, 'terms_repo', None) is not None:
                    try:
                        repo_hits = self.terms_repo.find_terms_in_text(block)
                    except Exception:
                        repo_hits = []
                freq = {}
                for w in nouns:
                    freq[w] = freq.get(w, 0) + 1
                scored = sorted(freq.items(), key=lambda kv: (-(kv[1] + (5 if kv[0] in priority else 0)), -len(kv[0])))
                top = [w for w,_ in scored[:20]]
                # 用語カタログの地理語彙を加点（川/空港/地名/工業地帯など）
                geo_terms = []
                for field, term in repo_hits:
                    if field == 'geography':
                        geo_terms.append(term)
                # 代表的な後方一致も拾う（川/空港/湾/平野/山地）
                extra_geo = re.findall(r'[一-龥ァ-ヴー]{2,}(川|空港|湾|平野|山地|工業地帯)', block)
                material_terms.extend(top)
                if geo_terms:
                    material_terms.extend(geo_terms)
                if extra_geo:
                    material_terms.extend(extra_geo)
            if not material_terms:
                return ctx_text
            uniq = []
            for w in material_terms:
                if w not in uniq:
                    uniq.append(w)
            # 地理語彙は重みを強めに（3倍）、その他は2倍
            if getattr(self, 'terms_repo', None) is not None:
                geo_set = set(self.terms_repo.terms.get('geography', []))
            else:
                geo_set = set()
            geo_terms = [w for w in uniq if (w in geo_set) or re.search(r'(川|空港|湾|平野|山地|工業地帯|市|府|県)$', w)]
            other_terms = [w for w in uniq if w not in geo_terms]
            booster_geo = (' ' + ' '.join(geo_terms[:20])) if geo_terms else ''
            booster_other = (' ' + ' '.join(other_terms[:20])) if other_terms else ''
            # 地理語彙 4倍、その他 2倍へ調整
            boosted = f"{ctx_text}{booster_geo*4}{booster_other*2}"
            return boosted
        except Exception:
            return ctx_text

    def _extract_nouns(self, text: str):
        """形態素解析（可能なら）で名詞候補を抽出。失敗時は空を返す。"""
        try:
            from fugashi import Tagger  # type: ignore
            tagger = Tagger()
            nouns = []
            for w in tagger(text):
                pos = ','.join((w.feature.pos or [])) if hasattr(w.feature, 'pos') else (w.feature.part_of_speech if hasattr(w.feature, 'part_of_speech') else '')
                if '名詞' in pos and len(str(w)) >= 2:
                    nouns.append(str(w))
            return nouns
        except Exception:
            try:
                from janome.tokenizer import Tokenizer  # type: ignore
                t = Tokenizer()
                nouns = [token.surface for token in t.tokenize(text) if token.part_of_speech.startswith('名詞') and len(token.surface) >= 2]
                return nouns
            except Exception:
                return []
    
    def _find_question_context(self, full_text: str, question_text: str) -> str:
        """問題文の文脈を特定して強化"""
        # 問題文の最初の30文字で検索
        search_fragment = question_text[:30].strip()
        if not search_fragment:
            return question_text
        
        lines = full_text.split('\n')
        enhanced_lines = []
        
        for i, line in enumerate(lines):
            if search_fragment in line:
                # 前後の行を含める（特に前の行に設問文がある場合）
                start = max(0, i - 8)  # 文脈拡張
                end = min(len(lines), i + 5)
                context_lines = lines[start:end]
                
                # 意味のある内容を含む行だけを選択
                meaningful_lines = []
                for line in context_lines:
                    line = line.strip()
                    if (line and 
                        not line.isdigit() and  # 単独の数字は除外
                        len(line) > 3):  # 短すぎる行は除外
                        meaningful_lines.append(line)
                
                # 直近の「資料」ブロックも追加
                extra_context = []
                k = i
                # 上方向に遡って「資料」見出しを探索
                while k >= 0 and (i - k) <= 30:
                    if '資料' in lines[k]:
                        # 見出し行から数行を追加
                        for j in range(k, min(k + 8, len(lines))):
                            s = lines[j].strip()
                            if s and len(s) > 3 and not s.isdigit():
                                extra_context.append(s)
                        break
                    k -= 1

                enhanced_lines = (meaningful_lines + extra_context)[:14]  # 最大14行
                break
        
        if enhanced_lines:
            enhanced_text = ' '.join(enhanced_lines)
            logger.debug(f"文脈強化: '{question_text[:30]}...' -> '{enhanced_text[:100]}...'")
            return enhanced_text
        
        return question_text
    
    def _emergency_question_extraction(self, text: str) -> List[Tuple[str, str]]:
        """緊急時の問題抽出（通常の抽出が失敗した場合）"""
        questions = []
        
        # より単純なパターンで問題を探す
        simple_patterns = [
            # 「問」で始まる行
            re.compile(r'^問\s*(\d+)[．\.\s]*(.*?)$', re.MULTILINE),
            # 「(1)」形式
            re.compile(r'^\((\d+)\)\s*(.*?)$', re.MULTILINE),
            # 「1.」形式
            re.compile(r'^(\d+)[．\.]\s*(.*?)$', re.MULTILINE),
        ]
        
        for pattern in simple_patterns:
            matches = pattern.findall(text)
            for num, q_text in matches:
                if len(q_text.strip()) > 10:  # 最低限の長さ
                    questions.append((f"緊急抽出-{num}", q_text.strip()))
        
        if not questions:
            # 最後の手段：段落ベースの分割
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
            for i, p in enumerate(paragraphs[:10]):  # 最大10段落
                if any(keyword in p for keyword in ['について', '答え', '選び', '説明']):
                    questions.append((f"段落-{i+1}", p))
        
        logger.info(f"緊急抽出により{len(questions)}問を抽出しました")
        return questions
