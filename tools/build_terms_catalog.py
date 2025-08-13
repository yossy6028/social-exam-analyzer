#!/usr/bin/env python3
"""
Playwright またはオフラインHTMLを用いて以下の用語集サイトから重要用語を取り込み、
分野別（歴史/地理/公民）に分類した用語カタログを構築します。

対象:
- 一般用語: https://study.005net.com/yogo/yogo.php
- 地理用語: https://study.005net.com/chiriYogo/chiriYogo.php
- 公民用語: https://study.005net.com/kominYogo/kominYogo.php

出力:
- data/terms_catalog/terms.json
- docs/terms_catalog.md

実行:
  オンライン取得（Playwright）:
    pip install playwright beautifulsoup4 lxml
    playwright install
    python3 tools/build_terms_catalog.py

  オフライン取得（mcp-chrome等で保存したHTMLを利用）:
    # 予め HTML を data/terms_catalog/html/ 配下に保存
    #   history.html, geography.html, civics.html など
    pip install beautifulsoup4 lxml
    python3 tools/build_terms_catalog.py --offline-dir data/terms_catalog/html

備考:
  環境によりサイト構造が変わる場合は、select_terms() 内の選択子を調整してください。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup  # type: ignore
import argparse


def select_terms(html: str) -> List[str]:
    """ページの HTML から用語らしき文字列を抽出する汎用ロジック。
    想定: リスト、表、リンクテキスト、見出しなど。
    """
    soup = BeautifulSoup(html, 'lxml')
    terms: List[str] = []

    # 見出しやリストのテキスト
    for sel in ['h1', 'h2', 'h3', 'li', 'td', 'th', 'a']:
        for el in soup.select(sel):
            text = (el.get_text() or '').strip()
            if not text:
                continue
            # 日本語の用語らしさ: 2〜20文字程度の漢字/かな/カナ主体
            if 2 <= len(text) <= 20:
                # ノイズっぽい凡語を軽く除去
                if any(x in text for x in ['トップ', '戻る', '次へ', '前へ']):
                    continue
                terms.append(text)

    # 重複除去・頻出ベースでソート
    uniq: Dict[str, int] = {}
    for t in terms:
        uniq[t] = uniq.get(t, 0) + 1
    # 出現回数優先、同点は辞書順
    sorted_terms = sorted(uniq.keys(), key=lambda x: (-uniq[x], x))
    return sorted_terms


def scrape_with_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright  # lazy import
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        # ページが遅い場合は軽く待機
        page.wait_for_timeout(500)
        html = page.content()
        browser.close()
        return html


def load_offline_htmls(offline_dir: Path, field: str) -> List[str]:
    """オフラインHTML: フィールドに対応する複数のHTMLをまとめて読み込む
    探索規約:
      - {field}.html があれば採用
      - {field}-*.html / {field}*.html を併せて結合
      - 従来の別名 (yogo/chiriYogo/kominYogo) も考慮
    """
    names_map = {
        'history': ['history.html', 'yogo.html'],
        'geography': ['geography.html', 'chiriYogo.html'],
        'civics': ['civics.html', 'kominYogo.html']
    }
    htmls: List[str] = []
    # 既定名
    for name in names_map.get(field, []):
        p = offline_dir / name
        if p.exists():
            htmls.append(p.read_text(encoding='utf-8', errors='ignore'))
    # プレフィックス一致
    for p in sorted(offline_dir.glob(f"{field}*.html")):
        try:
            htmls.append(p.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            pass
    # サフィックス一致（history-*.htmlなど）
    for p in sorted(offline_dir.glob(f"{field}-*.html")):
        try:
            htmls.append(p.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            pass
    if not htmls:
        raise FileNotFoundError(f"offline html not found for field={field} in {offline_dir}")
    return htmls


def main():
    ap = argparse.ArgumentParser(description='用語カタログ構築ツール')
    ap.add_argument('--offline-dir', help='オフラインHTMLディレクトリ（mcp-chrome等で保存したもの）')
    args = ap.parse_args()

    base = Path(__file__).resolve().parents[1]
    out_dir = base / 'data' / 'terms_catalog'
    md_dir = base / 'docs'
    out_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)

    sources: List[Tuple[str, str]] = [
        ('history', 'https://study.005net.com/yogo/yogo.php'),
        ('geography', 'https://study.005net.com/chiriYogo/chiriYogo.php'),
        ('civics', 'https://study.005net.com/kominYogo/kominYogo.php'),
    ]

    catalog: Dict[str, List[str]] = {}

    offline_dir: Path | None = Path(args.offline_dir) if args.offline_dir else None

    for field, url in sources:
        if offline_dir:
            print(f'Loading (offline): {field} <- {offline_dir}')
            html_list = load_offline_htmls(offline_dir, field)
            merged_terms: List[str] = []
            for html in html_list:
                merged_terms.extend(select_terms(html))
            # 重複除去
            uniq = []
            for t in merged_terms:
                if t not in uniq:
                    uniq.append(t)
            catalog[field] = uniq
            print(f'  extracted {len(uniq)} terms from {len(html_list)} file(s)')
        else:
            print(f'Fetching: {field} -> {url}')
            html = scrape_with_playwright(url)
            terms = select_terms(html)
            catalog[field] = terms
            print(f'  extracted {len(terms)} terms')

    # JSON 保存
    json_path = out_dir / 'terms.json'
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    # Markdown 保存
    md_path = md_dir / 'terms_catalog.md'
    with md_path.open('w', encoding='utf-8') as f:
        f.write('# 社会科 重要用語カタログ\n\n')
        f.write('更新手順: tools/build_terms_catalog.py を実行\n\n')
        for field_label, title in [('history', '歴史'), ('geography', '地理'), ('civics', '公民')]:
            f.write(f'## {title}\n')
            for term in catalog.get(field_label, [])[:1000]:
                f.write(f'- {term}\n')
            f.write('\n')

    print(f'Wrote: {json_path}')
    print(f'Wrote: {md_path}')


if __name__ == '__main__':
    # 環境変数 PLAYWRIGHT_BROWSERS_PATH を指定するとキャッシュを共有できます
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', '0')
    main()
