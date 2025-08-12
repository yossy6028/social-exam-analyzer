"""
年度検出モジュール - テキストから入試年度を検出
"""
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from config.settings import Settings
from models import YearDetectionResult
from exceptions import YearDetectionError
from utils.text_utils import normalize_text


@dataclass
class YearPattern:
    """年度パターンの定義"""
    name: str
    pattern: str
    converter: callable
    priority: int = 0


class YearDetector:
    """年度検出クラス"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self._compile_patterns()
    
    def _initialize_patterns(self) -> List[YearPattern]:
        """年度パターンを初期化"""
        patterns = []
        
        # 漢数字の西暦パターン（二〇二五年度など）
        # 4文字の漢数字年度を検出（正字・略字・全角数字を含む）
        patterns.append(YearPattern(
            name="year_kanji",
            pattern=r'([一二三四五六七八九〇零壱弐参肆伍陸柒捌玖０-９]{4})年度?',
            converter=self._kanji_year_to_year,
            priority=11
        ))
        
        # 漢数字2桁年度パターン（平成二十七年など）
        patterns.append(YearPattern(
            name="year_kanji_2digit",
            pattern=r'([一二三四五六七八九〇零壱弐参肆伍陸柒捌玖０-９]{2})年度?',
            converter=self._kanji_year_to_year,
            priority=10
        ))
        
        # 西暦4桁パターン
        patterns.append(YearPattern(
            name="year_4digit",
            pattern=r'(20\d{2})年度?',
            converter=lambda x: x,
            priority=9
        ))
        
        # 令和パターン
        patterns.append(YearPattern(
            name="reiwa",
            pattern=r'令和(\d{1,2})年度?',
            converter=self._reiwa_to_year,
            priority=8
        ))
        
        # 平成パターン（通常の数字）
        patterns.append(YearPattern(
            name="heisei",
            pattern=r'平成(\d{1,2})年度?',
            converter=self._heisei_to_year,
            priority=7
        ))
        
        # 平成漢数字パターン（平成二十七年など）
        patterns.append(YearPattern(
            name="heisei_kanji",
            pattern=r'平成([一二三四五六七八九十]{1,4})年度?',
            converter=self._heisei_kanji_to_year,
            priority=7
        ))
        
        # 学校名+2桁年度パターン
        for school_pattern in Settings.SCHOOL_YEAR_PATTERNS:
            patterns.append(YearPattern(
                name=f"school_{school_pattern}",
                pattern=school_pattern,
                converter=self._two_digit_to_year,
                priority=7
            ))
        
        # 単独の2桁年度パターン（優先度低）
        # 年や年度という文字が必須で、改行直後の数字は除外
        # 平成・令和の後は除外（既に上位パターンで処理済み）
        # また、括弧内の数字「(00)」「(15)」のようなパターンは除外
        patterns.append(YearPattern(
            name="year_2digit",
            pattern=r'(?<![(\d\n平成令和])(\d{2})年度?(?![)\d])',
            converter=self._two_digit_to_year,
            priority=5
        ))
        
        return patterns
    
    def _compile_patterns(self):
        """正規表現パターンをコンパイル"""
        for pattern_obj in self.patterns:
            pattern_obj.compiled = re.compile(pattern_obj.pattern, re.MULTILINE)
    
    def detect_years(self, text: str, file_path: Optional[Path] = None) -> YearDetectionResult:
        """
        テキストから年度を検出
        
        Args:
            text: 検出対象のテキスト
            file_path: ファイルパス（ファイル名からも年度を推測）
        
        Returns:
            YearDetectionResult: 検出結果
        """
        detected_years = {}
        detection_patterns = {}
        
        # ファイル名から年度を推測
        if file_path:
            file_years = self._detect_from_filename(file_path.name)
            if file_years:
                detected_years.update({year: 0 for year in file_years})
                detection_patterns['filename'] = [(0, year) for year in file_years]
        
        # 各パターンで検出
        for pattern_obj in sorted(self.patterns, key=lambda x: x.priority, reverse=True):
            matches = pattern_obj.compiled.finditer(text)
            
            for match in matches:
                try:
                    year = pattern_obj.converter(match.group(1))
                    if self._is_valid_year(year):
                        position = match.start()
                        
                        # 重複チェック（位置が近い場合は優先度の高いものを採用）
                        if not self._is_duplicate(year, position, detected_years, detection_patterns):
                            detected_years[year] = position
                            
                            if pattern_obj.name not in detection_patterns:
                                detection_patterns[pattern_obj.name] = []
                            detection_patterns[pattern_obj.name].append((position, year))
                except (ValueError, IndexError):
                    continue
        
        # 結果を作成
        years = sorted(detected_years.keys())
        
        # 複数年度が検出された場合の処理
        if len(years) > 1:
            # まず歴史的文脈をフィルタリング
            filtered_detected_years = self._filter_historical_contexts(text, detected_years, detection_patterns)
            
            if len(filtered_detected_years) >= 1 and len(filtered_detected_years) < len(detected_years):
                # フィルタリングで年度数が減った場合
                years = sorted(filtered_detected_years.keys())
                
                if len(years) == 1:
                    # 単一年度になった場合
                    confidence = 0.9
                else:
                    # まだ複数年度の場合は更に絞り込み
                    years = self._select_single_primary_year(text, years, detection_patterns)
                    confidence = 0.8
            else:
                # フィルタリングで変化がない場合
                is_year_range = self._is_year_range(years)
                
                if is_year_range:
                    # 年度範囲の場合は複数年度を維持
                    confidence = self._calculate_confidence(years, detection_patterns)
                else:
                    # 年度範囲でない場合、強制的に単一年度を選択
                    years = self._select_single_primary_year(text, years, detection_patterns)
                    confidence = 0.8
        else:
            confidence = self._calculate_confidence(years, detection_patterns)
        
        # ファイル名から検出された年度を優先（単一年度の場合）
        if file_path and 'filename' in detection_patterns:
            file_years = [year for _, year in detection_patterns['filename']]
            if len(file_years) == 1:
                # ファイル名から単一年度が検出された場合はそれを採用
                years = file_years
                confidence = 1.0  # ファイル名からの単一年度は信頼度最高
            elif file_years and len(years) > len(file_years):
                # ファイル名の年度より多く検出された場合は、ファイル名の年度を優先
                years = file_years
                confidence = 0.9
        
        # 漢数字パターンで単一年度が検出され、他に複数の年度が検出された場合
        # 漢数字パターンを優先（最も信頼度が高い）
        if 'year_kanji' in detection_patterns:
            kanji_years = list(set([year for _, year in detection_patterns['year_kanji']]))
            if len(kanji_years) == 1 and len(years) > 1:
                # 漢数字で単一年度が明確な場合はそれを優先
                years = kanji_years
                confidence = 0.95
        
        # 年度が検出できない場合でもファイル名から推測した年度があれば使用
        if not years and file_path:
            file_years = self._detect_from_filename(file_path.name)
            if file_years:
                years = file_years
                confidence = 0.5  # ファイル名のみからの推測なので信頼度は低め
        
        if not years:
            # デバッグ情報を含む詳細なエラーメッセージ
            debug_info = []
            debug_info.append(f"テキストサンプル: {repr(text[:200])}")
            
            # 各パターンでのマッチ結果をデバッグ
            for pattern_obj in self.patterns:
                matches = list(pattern_obj.compiled.finditer(text))
                if matches:
                    debug_info.append(f"{pattern_obj.name}: {len(matches)}件マッチ")
                    for match in matches[:3]:  # 最初の3件まで
                        converted = None
                        is_valid = False
                        try:
                            converted = pattern_obj.converter(match.group(1))
                            is_valid = self._is_valid_year(converted)
                        except:
                            pass
                        debug_info.append(f"  - '{match.group(1)}' → '{converted}' (有効: {is_valid})")
                else:
                    debug_info.append(f"{pattern_obj.name}: マッチなし")
            
            # 特別に漢数字年度をもう一度チェック
            kanji_pattern = r'[一二三四五六七八九〇１２３４５６７８９０]{4}年度?'
            kanji_matches = list(re.finditer(kanji_pattern, text))
            if kanji_matches:
                debug_info.append(f"追加漢数字チェック: {len(kanji_matches)}件マッチ")
                for match in kanji_matches[:3]:
                    debug_info.append(f"  - '{match.group(0)}'")
            
            error_msg = "テキストから年度を検出できませんでした。\n" + "\n".join(debug_info)
            raise YearDetectionError(error_msg, [p.name for p in self.patterns])
        
        return YearDetectionResult(
            years=years,
            detection_patterns=detection_patterns,
            confidence=confidence
        )
    
    def _detect_from_filename(self, filename: str) -> List[str]:
        """ファイル名から年度を検出"""
        years = []
        
        # 連続する年度範囲（例: 14-25）
        range_match = re.search(r'(\d{2})-(\d{2})', filename)
        if range_match:
            start = self._two_digit_to_year(range_match.group(1))
            end = self._two_digit_to_year(range_match.group(2))
            
            if self._is_valid_year(start) and self._is_valid_year(end):
                start_year = int(start)
                end_year = int(end)
                if start_year <= end_year:
                    years = [str(year) for year in range(start_year, end_year + 1)]
        
        # 個別の年度
        if not years:
            # 4桁年度
            matches_4digit = re.findall(r'20\d{2}', filename)
            for match in matches_4digit:
                if self._is_valid_year(match) and match not in years:
                    years.append(match)
            
            # 2桁年度（学校名の前後にある場合）
            # パターン1: 学校名の後ろ（例: 開成25）
            school_pattern_after = r'(?:開成|武蔵|桜蔭|桜陰|麻布|渋谷|渋渋)(\d{2})'
            school_matches = re.findall(school_pattern_after, filename)
            for match in school_matches:
                year = self._two_digit_to_year(match)
                if self._is_valid_year(year) and year not in years:
                    years.append(year)
            
            # パターン2: 学校名の前（例: 25開成）
            school_pattern_before = r'(\d{2})(?:開成|武蔵|桜蔭|桜陰|麻布|渋谷|渋渋)'
            school_matches = re.findall(school_pattern_before, filename)
            for match in school_matches:
                year = self._two_digit_to_year(match)
                if self._is_valid_year(year) and year not in years:
                    years.append(year)
            
            # それでも見つからない場合は単独の2桁数字を試す
            if not years:
                matches_2digit = re.findall(r'(?:^|\D)(\d{2})(?:\D|$)', filename)
                for match in matches_2digit:
                    year = self._two_digit_to_year(match)
                    if self._is_valid_year(year) and year not in years:
                        years.append(year)
        
        return years
    
    def _two_digit_to_year(self, two_digit: str) -> str:
        """2桁年度を4桁に変換"""
        try:
            num = int(two_digit)
            if Settings.MIN_YEAR_2DIGIT <= num <= Settings.MAX_YEAR_2DIGIT:
                return f"20{num:02d}"
            elif 90 <= num <= 99:
                return f"19{num:02d}"
            else:
                return f"20{num:02d}"
        except ValueError:
            return two_digit
    
    def _reiwa_to_year(self, reiwa_year: str) -> str:
        """令和を西暦に変換"""
        try:
            year = 2018 + int(reiwa_year)
            return str(year)
        except ValueError:
            return reiwa_year
    
    def _heisei_to_year(self, heisei_year: str) -> str:
        """平成を西暦に変換"""
        try:
            year = 1988 + int(heisei_year)
            return str(year)
        except ValueError:
            return heisei_year
    
    def _heisei_kanji_to_year(self, heisei_kanji: str) -> str:
        """平成の漢数字を西暦に変換（平成二十七年→2015）"""
        try:
            # 簡単な漢数字変換（十の位と一の位）
            kanji_to_digit = {
                '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
            }
            
            # 「二十七」のパターンを処理
            if '十' in heisei_kanji:
                if len(heisei_kanji) == 1:  # 「十」のみ
                    heisei_num = 10
                elif heisei_kanji.startswith('十'):  # 「十七」など
                    heisei_num = 10 + kanji_to_digit.get(heisei_kanji[1], 0)
                elif heisei_kanji.endswith('十'):  # 「二十」など
                    heisei_num = kanji_to_digit.get(heisei_kanji[0], 0) * 10
                else:  # 「二十七」など
                    parts = heisei_kanji.split('十')
                    if len(parts) == 2:
                        tens = kanji_to_digit.get(parts[0], 0) if parts[0] else 1
                        ones = kanji_to_digit.get(parts[1], 0) if parts[1] else 0
                        heisei_num = tens * 10 + ones
                    else:
                        return heisei_kanji
            else:
                # 単純な一桁
                heisei_num = kanji_to_digit.get(heisei_kanji, 0)
            
            if heisei_num > 0:
                year = 1988 + heisei_num
                return str(year)
        except:
            pass
        return heisei_kanji
    
    def _is_valid_year(self, year: str) -> bool:
        """有効な年度かチェック"""
        try:
            year_num = int(year)
            return Settings.MIN_VALID_YEAR <= year_num <= Settings.MAX_VALID_YEAR
        except ValueError:
            return False
    
    def _is_duplicate(self, year: str, position: int, detected_years: Dict[str, int], detection_patterns: Dict) -> bool:
        """重複した検出かチェック"""
        if year not in detected_years:
            return False
        
        # 同じ年度が近い位置で検出された場合は重複とみなす
        existing_position = detected_years[year]
        
        # 位置が近い場合（100文字以内）は重複
        if abs(position - existing_position) < 100:
            return True
        
        # 平成・令和年度と同じ年度の2桁年度が重複している場合も除外
        for pattern_name, matches in detection_patterns.items():
            if pattern_name in ['heisei', 'heisei_kanji', 'reiwa']:
                for match_pos, match_year in matches:
                    if match_year == year and abs(position - match_pos) < 50:
                        return True
        
        return False
    
    def _filter_historical_contexts(self, text: str, detected_years: Dict[str, int], patterns: Dict) -> Dict[str, int]:
        """歴史的文脈の年号を除外"""
        historical_patterns = [
            r'平成\d{1,2}年[にで]',          # 平成15年に、平成27年で
            r'昭和\d{1,2}年[にで]',          # 昭和60年に、昭和50年で
            r'西暦\d{4}年[のに]',            # 西暦2000年の、西暦1995年に  
            r'\d{4}年[のに]起[きこ]',        # 2000年に起きた、1995年に起こった
            r'\d{4}年[のに]制定',           # 2000年に制定された
            r'創立[記念]*[:\s]*\d{4}年[設立]', # 創立記念: 2000年設立、創立 1995年設立
            r'\d{4}年[のに][設建]',         # 2000年に設立、1995年に建設
            r'\d{4}年[のに].*?事[件変]',     # 2000年に起きた事件（非貪欲マッチ）
            r'\d{4}年[設建][立設]',         # 2000年設立、1995年建設
            r'平成\d{1,2}年[のに].*?[建設]',  # 平成15年に校舎を建設
        ]
        
        filtered_years = detected_years.copy()
        years_to_remove = set()
        
        for pattern in historical_patterns:
            for match in re.finditer(pattern, text):
                # マッチした年号から年度を抽出
                year_match = re.search(r'\d{4}', match.group(0))
                if year_match:
                    historical_year = year_match.group(0)
                    
                    # 検出された年度の中にこの歴史的年号があるかチェック
                    if historical_year in filtered_years:
                        # この年度が歴史的文脈で使われているため除外候補に
                        years_to_remove.add(historical_year)
                            
                # 平成年号の場合は西暦変換もチェック  
                heisei_match = re.search(r'平成(\d{1,2})年', match.group(0))
                if heisei_match:
                    heisei_year = str(1988 + int(heisei_match.group(1)))
                    if heisei_year in filtered_years:
                        # 平成年号が歴史的文脈（「に」「で」「を」等）で使われている場合のみ除外
                        context_start = max(0, match.start() - 10)
                        context_end = min(len(text), match.end() + 10)
                        context = text[context_start:context_end]
                        if any(marker in context for marker in ['に制定', 'に起き', 'に設立', 'に建設', 'について', 'の出来事']):
                            years_to_remove.add(heisei_year)
        
        # 除外対象の年度を削除
        for year in years_to_remove:
            if year in filtered_years:
                del filtered_years[year]
        
        return filtered_years
    
    def _select_primary_year(self, text: str, years: List[str], patterns: Dict) -> Optional[str]:
        """複数年度から主要年度を選択"""
        if not years:
            return None
        
        year_scores = {}
        
        for year in years:
            score = 0
            
            # 文書前半での検出（試験年度の可能性が高い）
            for pattern_name, matches in patterns.items():
                for pos, detected_year in matches:
                    if detected_year == year:
                        if pos < 50:  # 文書冒頭
                            score += 10
                        elif pos < 200:  # 文書前半
                            score += 5
                        
                        # パターンタイプによるスコア調整
                        if pattern_name in ['year_kanji', 'reiwa']:
                            score += 5  # 明確な年度表記
                        elif pattern_name == 'year_4digit':
                            score += 3
                        elif pattern_name == 'heisei':
                            score -= 2  # 歴史的文脈の可能性
            
            # より新しい年度を優先（現在の試験年度と推定）
            try:
                year_num = int(year)
                if year_num >= 2020:  # 比較的最近の年度
                    score += 5
                elif year_num < 2010:  # 古い年度は歴史的文脈の可能性
                    score -= 5
            except:
                pass
            
            # 歴史的文脈にある年度はスコアを大幅減点
            historical_context_patterns = [
                r'創立.*?' + re.escape(year) + r'年',
                re.escape(year) + r'年設立',
                r'平成\d{1,2}年に.*?建設',
                r'昭和\d{1,2}年に.*?建設',
            ]
            
            for hist_pattern in historical_context_patterns:
                if re.search(hist_pattern, text):
                    score -= 8  # 歴史的文脈は大幅減点
            
            year_scores[year] = score
        
        # 最高スコアの年度を選択
        if year_scores:
            best_year = max(year_scores, key=year_scores.get)
            # スコアが正の場合のみ返す
            if year_scores[best_year] > 0:
                return best_year
        
        return None
    
    def _is_year_range(self, years: List[str]) -> bool:
        """複数年度が連続する年度範囲かどうかを判定"""
        if len(years) <= 1:
            return False
        
        try:
            year_nums = sorted([int(year) for year in years])
            
            # 連続する年度かチェック（最大3年度まで）
            if len(year_nums) <= 3:
                # 全て最近の年度（2020年以降）の場合のみ年度範囲として扱う
                all_recent = all(year_num >= 2020 for year_num in year_nums)
                
                if all_recent:
                    for i in range(len(year_nums) - 1):
                        if year_nums[i + 1] - year_nums[i] != 1:
                            return False
                    return True
            
        except ValueError:
            pass
        
        return False
    
    def _get_highest_priority_year(self, years: List[str], patterns: Dict) -> Optional[str]:
        """最も優先度が高いパターンで検出された年度を選択"""
        pattern_priority = {
            'year_kanji': 11,
            'reiwa': 8,
            'year_4digit': 9,
            'heisei': 7,
            'year_2digit': 5
        }
        
        best_year = None
        best_priority = -1
        
        for pattern_name, matches in patterns.items():
            if pattern_name in pattern_priority:
                priority = pattern_priority[pattern_name]
                
                for pos, year in matches:
                    if year in years and priority > best_priority:
                        best_year = year
                        best_priority = priority
        
        return best_year
    
    def _select_single_primary_year(self, text: str, years: List[str], patterns: Dict) -> List[str]:
        """複数年度から確実に単一年度を選択"""
        if len(years) <= 1:
            return years
        
        # まず主要年度選択を試行
        primary_year = self._select_primary_year(text, years, patterns)
        if primary_year:
            return [primary_year]
        
        # 失敗した場合は最高優先度パターンで選択
        best_year = self._get_highest_priority_year(years, patterns)
        if best_year:
            return [best_year]
        
        # それでも失敗した場合は最新の年度を選択
        try:
            year_nums = [(int(year), year) for year in years]
            latest_year = max(year_nums)[1]
            return [latest_year]
        except:
            pass
        
        # 最後の手段として最初の年度を返す
        return [years[0]]
    
    def _calculate_confidence(self, years: List[str], patterns: Dict) -> float:
        """検出の信頼度を計算"""
        if not years:
            return 0.0
        
        score = 0.0
        
        # ファイル名から検出された場合は信頼度が高い
        if 'filename' in patterns:
            score += 0.5
        
        # 複数のパターンで検出された場合は信頼度が高い
        if len(patterns) > 1:
            score += 0.2
        
        # 年度が連続している場合は信頼度が高い
        if len(years) > 1:
            year_nums = sorted([int(y) for y in years])
            consecutive = all(
                year_nums[i] + 1 == year_nums[i + 1]
                for i in range(len(year_nums) - 1)
            )
            if consecutive:
                score += 0.2
        
        # 高優先度パターンで検出された場合
        if any(p in patterns for p in ['year_4digit', 'reiwa', 'heisei']):
            score += 0.3
        elif 'year_2digit' in patterns and len(patterns) == 1:
            # 2桁年度のみの場合は信頼度を下げる
            score = max(score, 0.3)
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def split_text_by_years(self, text: str, years: List[str]) -> Dict[str, str]:
        """
        年度ごとにテキストを分割
        
        Args:
            text: 分割対象のテキスト
            years: 検出された年度のリスト
        
        Returns:
            年度ごとのテキスト辞書
        """
        if len(years) <= 1:
            # 単一年度の場合は分割しない
            return {years[0]: text} if years else {}
        
        year_positions = []
        
        # 各年度の位置を特定
        for year in years:
            # 様々なパターンで年度マーカーを検索
            patterns = [
                f"{year}年",
                f"令和{self._year_to_reiwa(year)}年" if self._year_to_reiwa(year) else None,
                f"平成{self._year_to_heisei(year)}年" if self._year_to_heisei(year) else None,
            ]
            
            # 2桁年度の場合、学校名パターンも追加
            two_digit = year[-2:] if len(year) == 4 else year
            for school_pattern in ['武蔵', '開成', '麻布', '桜蔭']:
                patterns.append(f"{school_pattern}{two_digit}")
            
            for pattern in patterns:
                if pattern:
                    pos = text.find(pattern)
                    if pos != -1:
                        year_positions.append((pos, year))
                        break
        
        # 位置でソート
        year_positions.sort()
        
        # テキストを分割
        result = {}
        for i, (pos, year) in enumerate(year_positions):
            if i < len(year_positions) - 1:
                next_pos = year_positions[i + 1][0]
                year_text = text[pos:next_pos]
            else:
                year_text = text[pos:]
            
            result[year] = year_text
        
        return result
    
    def _year_to_reiwa(self, year: str) -> Optional[str]:
        """西暦を令和に変換"""
        try:
            year_num = int(year)
            if year_num >= 2019:
                return str(year_num - 2018)
        except ValueError:
            pass
        return None
    
    def _year_to_heisei(self, year: str) -> Optional[str]:
        """西暦を平成に変換"""
        try:
            year_num = int(year)
            if 1989 <= year_num <= 2019:
                return str(year_num - 1988)
        except ValueError:
            pass
        return None
    
    def _kanji_year_to_year(self, kanji_year: str) -> str:
        """漢数字の年度を西暦に変換"""
        # 漢数字と全角数字を半角数字に変換
        kanji_to_num = {
            '〇': '0', '０': '0', '零': '0',
            '一': '1', '１': '1', '壱': '1',
            '二': '2', '２': '2', '弐': '2',
            '三': '3', '３': '3', '参': '3',
            '四': '4', '４': '4', '肆': '4',
            '五': '5', '５': '5', '伍': '5',
            '六': '6', '６': '6', '陸': '6',
            '七': '7', '７': '7', '柒': '7',
            '八': '8', '８': '8', '捌': '8',
            '九': '9', '９': '9', '玖': '9'
        }
        
        result = ''
        for char in kanji_year:
            if char in kanji_to_num:
                result += kanji_to_num[char]
            elif char.isdigit():
                result += char
            # その他の文字は無視（年度の「年」「度」など）
        
        # 結果が4桁の数字になっているか確認
        if len(result) == 4 and result.isdigit():
            return result
        
        # 2桁の場合は21世紀として補完
        if len(result) == 2 and result.isdigit():
            num = int(result)
            if 90 <= num <= 99:
                return f"19{result}"
            else:
                return f"20{result}"
        
        return kanji_year