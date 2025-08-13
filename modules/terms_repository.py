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
        if self.json_path.exists():
            try:
                self.terms = json.loads(self.json_path.read_text(encoding='utf-8'))
            except Exception:
                self.terms = {}

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

    def suggest_theme(self, text: str) -> Optional[Tuple[str, str]]:
        """テキストからテーマ（2文節）と分野を提案する。"""
        field = self.best_field_for_text(text)
        if not field:
            return None
        # 単純な2文節化ルール
        if field == 'history':
            theme = '歴史の重要用語'
        elif field == 'geography':
            theme = '地理の重要用語'
        elif field == 'civics':
            theme = '公民の重要用語'
        else:
            theme = '重要用語'
        return (theme, field)

