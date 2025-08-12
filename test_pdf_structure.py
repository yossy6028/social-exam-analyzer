#\!/usr/bin/env python3
"""
PDFの問題構造を詳細に分析
"""

import re

# 実際のテキストサンプル
text = """
問1 【あ】にあてはまる人物名を漢字で答えなさい。
問2 次の雨温図は、地図中に示したA~Dの都市のいずれかのものです。
問3 地図中で示した地域で考えられる災害とその対策について説明した文としてあやまっているものを選べ。
問4 下線部ⓓで実施された政策のうち、上げ米の制について 30字以上で説明しなさい。
問5 右の表は、日本の海岸線の長さと全国における長さの割合を示したもので、長崎県を表から1つ選び記号で答えなさい。

2. 次の文章を読んで、問いに答えなさい。

問1 室町幕府を滅ぼした織田信長の後継者となった豊臣秀吉について答えなさい。
問2 下線部⑥〜Cの期間におきたできごとを並び替えたとき、3番目になるものを選べ。
問3 日露戦争の頃には鉄鋼業などの重工業がさかんになった理由を説明しなさい。
"""

# 問題番号パターンのテスト
patterns = [
    # パターン1: 基本パターン
    (r'問\s*(\d+)', "基本"),
    # パターン2: 全角数字も含む
    (r'問\s*([０-９\d]+)', "全角対応"),
    # パターン3: 大問の検出
    (r'^(\d+)\.\s*次の', "大問"),
    # パターン4: リセット検出用
    (r'問\s*([０-９\d]+)(.{0,100})', "内容付き"),
]

for pattern_str, name in patterns:
    pattern = re.compile(pattern_str, re.MULTILINE)
    matches = pattern.findall(text)
    print(f"\n{name}パターン:")
    for match in matches[:5]:  # 最初の5件のみ表示
        if isinstance(match, tuple):
            print(f"  - {match}")
        else:
            print(f"  - {match}")

# 大問と小問の階層構造を認識
print("\n=== 階層構造の認識 ===")

# 大問を探す
major_pattern = re.compile(r'^(\d+)\.\s*(.+?)$', re.MULTILINE)
major_matches = list(major_pattern.finditer(text))

if major_matches:
    print(f"大問数: {len(major_matches)}")
    for match in major_matches:
        print(f"  大問{match.group(1)}: {match.group(2)[:30]}...")
        
        # その大問内の小問を探す
        start = match.end()
        end = major_matches[major_matches.index(match) + 1].start() if major_matches.index(match) < len(major_matches) - 1 else len(text)
        section = text[start:end]
        
        minor_pattern = re.compile(r'問\s*([０-９\d]+)')
        minor_matches = minor_pattern.findall(section)
        print(f"    小問: {minor_matches}")
