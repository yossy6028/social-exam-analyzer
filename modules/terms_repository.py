from __future__ import annotations

"""
用語カタログを読み込み、用語→分野・テーマの推定を補助するモジュール。
ファイル: data/terms_catalog/terms.json （tools/build_terms_catalog.py が生成）
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TermsRepository:
    def __init__(self, base_dir: Optional[Path] = None):
        base = base_dir or Path(__file__).resolve().parents[1]
        self.json_path = base / 'data' / 'terms_catalog' / 'terms.json'
        self.terms: Dict[str, List[str]] = {}
        # 歴史の時代インデックス
        self.history_index_path = base / 'data' / 'subject_index' / 'history_periods.json'
        self.history_index: Dict[str, Dict[str, List[str]]] = {}
        if self.json_path.exists():
            try:
                self.terms = json.loads(self.json_path.read_text(encoding='utf-8'))
            except Exception:
                self.terms = {}
        if self.history_index_path.exists():
            try:
                self.history_index = json.loads(self.history_index_path.read_text(encoding='utf-8'))
            except Exception:
                self.history_index = {}

    def available(self) -> bool:
        return bool(self.terms)

    def find_terms_in_text(self, text: str) -> List[Tuple[str, str]]:
        """テキストに含まれる既知用語を (field, term) で返す"""
        hits: List[Tuple[str, str]] = []
        if not text:
            return hits
        for field, items in self.terms.items():
            for term in items:
                if term and term in text:
                    hits.append((field, term))
        return hits

    def best_field_for_text(self, text: str) -> Optional[str]:
        hits = self.find_terms_in_text(text)
        if not hits:
            return None
        # 最多ヒットの分野
        count: Dict[str, int] = {}
        for field, _ in hits:
            count[field] = count.get(field, 0) + 1
        return max(count, key=count.get)

    def infer_history_period(self, text: str) -> Optional[str]:
        """時代インデックスから歴史の時代を推定する。"""
        t = text or ''
        # 時代語の一致を優先
        for period, data in self.history_index.items():
            for kw in data.get('時代語', []):
                if kw and kw in t:
                    return period
        # 代表語の一致で次点判定
        best_period = None
        best_hits = 0
        for period, data in self.history_index.items():
            hits = 0
            for kw in data.get('代表語', []):
                if kw and kw in t:
                    hits += 1
            if hits > best_hits:
                best_hits = hits
                best_period = period
        return best_period if best_hits > 0 else None

    def suggest_theme(self, text: str) -> Optional[Tuple[str, str]]:
        """テキストから具体的なテーマ（2文節程度）と分野を提案する。

        可能な限り具体語からテーマを自動生成し、
        それが難しい場合のみ『〇〇の重要用語』にフォールバックする。
        """
        field = self.best_field_for_text(text)
        if not field:
            return None

        hits = self.find_terms_in_text(text)

        def choose_best_term(candidates: list[str]) -> Optional[str]:
            if not candidates:
                return None
            # 長さ優先 + 出現順で安定化
            sorted_terms = sorted(set(candidates), key=lambda t: (-len(t), candidates.index(t)))
            return sorted_terms[0]

        def build_theme_from_term(term: str, f: str) -> str:
            # 簡易規則で具体化
            if f == 'geography':
                suffix_mappings = [
                    ('工業地帯', 'の特徴'),
                    ('地方', 'の特徴'),
                    ('平野', 'の特徴'),
                    ('山地', 'の特徴'),
                    ('盆地', 'の特徴'),
                    ('湾', 'の特徴'),
                    ('川', 'の特徴'),
                    ('空港', 'の役割'),
                    ('都', 'の特徴'),
                    ('市', 'の特徴'),
                    ('県', 'の特徴'),
                ]
                for suf, tail in suffix_mappings:
                    if term.endswith(suf):
                        return f"{term}{tail}"
                # キーワードで判定
                if '人口ピラミッド' in term:
                    return '人口ピラミッドの分析'
                if '雨温図' in term:
                    return '雨温図の読み取り'
                if any(k in term for k in ['地図', '地形', '気候', '産業']):
                    return f"{term}の特徴"
                return f"{term}について"
            if f == 'history':
                if any(k in term for k in ['の乱', 'の変', '戦争', '条約', '維新', '改革']):
                    return term
                # 人名・組織名らしき場合
                if len(term) <= 8:
                    return f"{term}の業績"
                return f"{term}の歴史的意義"
            if f == 'civics':
                if any(k in term for k in ['憲法', '三権分立', '国会', '内閣', '裁判所', '選挙']):
                    return f"{term}の仕組み"
                if any(k in term for k in ['税', '権利', '制度', '条約']):
                    return f"{term}の内容"
                return f"{term}について"
            return f"{term}について"

        if hits:
            # 指定分野のヒット語のみを対象に候補を作成
            field_terms = [term for fld, term in hits if fld == field]
            best = choose_best_term(field_terms)
            if best:
                return (build_theme_from_term(best, field), field)

        # 具体化できない場合のフォールバック
        if field == 'history':
            theme = '歴史の重要用語'
        elif field == 'geography':
            theme = '地理の重要用語'
        elif field == 'civics':
            theme = '公民の重要用語'
        else:
            theme = '重要用語'
        return (theme, field)

