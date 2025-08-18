#!/usr/bin/env python3
"""
詳細な問題検出デバッグ
"""
import re

# サンプルテキスト
sample_text = """
社会

1 次の文章を読み、各問いに答えなさい。
(1) 雨温図について答えなさい
(2) 野菜栽培について答えなさい
(3) 地形図を読み取りなさい
(4) 津久井湖について答えなさい
(5) 平野の特色を答えなさい
(6) 地形図の記号について答えなさい
(7) 地形図の読み取りについて答えなさい
(8) 川の流れについて答えなさい
(9) 農業について答えなさい
(10) 山地について答えなさい
(11) 気候について答えなさい

2 次の年表を見て、各問いに答えなさい。
(1) 平野の特色について答えなさい
(2) リサイクルについて答えなさい
(3) 明治時代について答えなさい
"""

def test_patterns():
    # 問題番号パターン
    patterns = [
        (r'\(([1-9][0-9]?)\)', 'paren_number'),
        (r'（([１-９][０-９]?)）', 'paren_zenkaku'),
    ]
    
    print("=== パターンマッチングテスト ===\n")
    
    for pattern_str, name in patterns:
        print(f"パターン: {name} = {pattern_str}")
        pattern = re.compile(pattern_str)
        matches = list(pattern.finditer(sample_text))
        print(f"  マッチ数: {len(matches)}")
        
        for match in matches[:5]:
            print(f"    位置{match.start()}: '{match.group(0)}' → 番号: {match.group(1)}")
        
        if len(matches) > 5:
            print(f"    ... 他{len(matches)-5}個")
        print()
    
    # 位置の重複チェックをシミュレート
    print("=== 重複チェックシミュレーション ===\n")
    
    all_matches = []
    for pattern_str, name in patterns:
        pattern = re.compile(pattern_str)
        for match in pattern.finditer(sample_text):
            all_matches.append((match.start(), match.group(1), name))
    
    all_matches.sort(key=lambda x: x[0])
    
    seen_positions = set()
    filtered = []
    
    for pos, num, name in all_matches:
        # 5文字以内の重複チェック
        if any(abs(pos - seen_pos) < 5 for seen_pos in seen_positions):
            print(f"  位置{pos}: ({num}) [{name}] → 除外（重複）")
        else:
            print(f"  位置{pos}: ({num}) [{name}] → 採用")
            filtered.append((pos, num, name))
            seen_positions.add(pos)
    
    print(f"\n最終的に採用: {len(filtered)}個")
    print("採用された問題番号:", [num for _, num, _ in filtered])

if __name__ == "__main__":
    test_patterns()