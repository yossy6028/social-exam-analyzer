#\!/usr/bin/env python3
"""
実際の問題文でテーマ抽出をテスト
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from modules.theme_extractor_v2 import ThemeExtractorV2

# 実際の問題文（OCRで取得されたもの）
actual_texts = [
    "しろたえ A. 春過ぎて 夏来にけらし 皆妙の 衣干すちょう 笑の番 問2. 次の系図は、B・Cの歌に関係するものです。",
    "F. 古池や蛙飛び込む 水の音 G. 身はたとえ 武蔵の野辺に 朽ちぬとも留めおかまし 大和魂",
    "Dは幸若舞(室町時代に始まった語りをともなう舞)の演目の一つである 『敦盛』の一節です。",
    "ア. 源頼朝は、北条氏の力をかりて兵をあげた。 イ. 一ノ谷の戦いでは平氏が勝利した。",
    "2023 年に、広島県では主要国首脳会議(G7 サミット)が開催される予定です。",
    "エ.飛鳥寺 問4.Eは応仁の乱で荒れはてた京都の様子をなげいた歌です。",
]

extractor = ThemeExtractorV2()

print("=== 実際の問題文でのテーマ抽出テスト ===\n")

for i, text in enumerate(actual_texts, 1):
    result = extractor.extract(text)
    print(f"問題{i}:")
    print(f"  テキスト: {text[:50]}...")
    if result.theme:
        print(f"  ✅ テーマ: {result.theme}")
    else:
        print(f"  ❌ テーマ抽出失敗")
        # デバッグ：なぜ失敗したか
        if extractor._should_exclude(text):
            print(f"     → 除外パターンにマッチ")
        else:
            print(f"     → フォールバック処理でも抽出できず")
    print()
