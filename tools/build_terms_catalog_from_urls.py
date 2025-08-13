#!/usr/bin/env python3
"""
Predefined URL sets (geography/history/civics) are fetched via Playwright,
terms are extracted with BeautifulSoup, and merged into terms.json/terms_catalog.md.

Use when you want to broaden the catalog quickly without manual HTML saving.

Requires: playwright, beautifulsoup4, lxml
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup  # type: ignore


URLS: Dict[str, List[str]] = {
    # Geography: cities, rivers, airports, bays, plains, mountain ranges, industrial areas
    'geography': [
        'https://ja.wikipedia.org/wiki/政令指定都市',
        'https://ja.wikipedia.org/wiki/日本の空港の一覧',
        'https://ja.wikipedia.org/wiki/日本の河川の一覧',
        'https://ja.wikipedia.org/wiki/日本の工業地帯・工業地域',
        'https://ja.wikipedia.org/wiki/日本の湾の一覧',
        'https://ja.wikipedia.org/wiki/日本の平野の一覧',
        'https://ja.wikipedia.org/wiki/日本の山地の一覧',
    ],
    # History: modern events, treaties, conferences, world heritage, Buddhism in Japan
    'history': [
        'https://ja.wikipedia.org/wiki/日本の歴史年表_(近現代)',
        'https://ja.wikipedia.org/wiki/条約の一覧',
        'https://ja.wikipedia.org/wiki/国際会議の一覧',
        'https://ja.wikipedia.org/wiki/日本の世界遺産',
        'https://ja.wikipedia.org/wiki/日本の仏教',
    ],
    # Civics: constitution, diet, cabinet, supreme court, local governments, tax, finance, elections
    'civics': [
        'https://ja.wikipedia.org/wiki/日本国憲法',
        'https://ja.wikipedia.org/wiki/国会_(日本)',
        'https://ja.wikipedia.org/wiki/内閣_(日本)',
        'https://ja.wikipedia.org/wiki/最高裁判所',
        'https://ja.wikipedia.org/wiki/地方自治',
        'https://ja.wikipedia.org/wiki/日本の税制',
        'https://ja.wikipedia.org/wiki/日本の財政',
        'https://ja.wikipedia.org/wiki/日本の選挙制度',
    ],
}


def fetch_html(url: str) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(300)
        html = page.content()
        browser.close()
        return html


def extract_terms(html: str) -> List[str]:
    soup = BeautifulSoup(html, 'lxml')
    # collect from headings, lists, tables, links
    terms: List[str] = []
    selectors = ['h1', 'h2', 'h3', 'li', 'td', 'th', 'a']
    for sel in selectors:
        for el in soup.select(sel):
            text = (el.get_text(separator=' ', strip=True) or '').strip()
            if not text:
                continue
            if 2 <= len(text) <= 30 and not any(x in text for x in ['編集', '出典', 'ページ', '目次', '脚注']):
                terms.append(text)
    uniq: Dict[str, int] = {}
    for t in terms:
        uniq[t] = uniq.get(t, 0) + 1
    sorted_terms = sorted(uniq.keys(), key=lambda k: (-uniq[k], k))
    return sorted_terms


def merge_catalog(base: Dict[str, List[str]], add: Dict[str, List[str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for field in set(list(base.keys()) + list(add.keys())):
        merged: List[str] = []
        for src in (base.get(field, []), add.get(field, [])):
            for t in src:
                if t not in merged:
                    merged.append(t)
        out[field] = merged
    return out


def main():
    base_dir = Path(__file__).resolve().parents[1]
    out_dir = base_dir / 'data' / 'terms_catalog'
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / 'terms.json'
    # load existing, if any
    current: Dict[str, List[str]] = {}
    if json_path.exists():
        try:
            current = json.loads(json_path.read_text(encoding='utf-8'))
        except Exception:
            current = {}

    new_cat: Dict[str, List[str]] = {}
    for field, urls in URLS.items():
        combined: List[str] = []
        print(f'Fetching field: {field} ({len(urls)} urls)')
        for u in urls:
            try:
                html = fetch_html(u)
                terms = extract_terms(html)
                combined.extend(terms)
                print(f'  + {u} -> {len(terms)} terms')
            except Exception as e:
                print(f'  ! {u} failed: {e}')
        # unique
        uniq: List[str] = []
        for t in combined:
            if t not in uniq:
                uniq.append(t)
        new_cat[field] = uniq
        print(f'  => field {field}: {len(uniq)} unique terms')

    merged = merge_catalog(current, new_cat)
    json_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')

    # write MD
    md_path = base_dir / 'docs' / 'terms_catalog.md'
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with md_path.open('w', encoding='utf-8') as f:
        f.write('# 社会科 重要用語カタログ（統合）\n\n')
        for field, title in [('geography', '地理'), ('history', '歴史'), ('civics', '公民')]:
            items = merged.get(field, [])
            f.write(f'## {title} ({len(items)})\n')
            for t in items:
                f.write(f'- {t}\n')
            f.write('\n')
    print(f'Wrote: {json_path}')
    print(f'Wrote: {md_path}')


if __name__ == '__main__':
    main()

