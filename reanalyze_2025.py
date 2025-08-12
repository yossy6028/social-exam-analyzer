#!/usr/bin/env python3
"""
2025年東京電機大学中学校の社会科入試問題を改善版で再分析
"""

import re
from pathlib import Path
from modules.improved_theme_extractor import ImprovedThemeExtractor

def reanalyze_2025():
    """2025年のテキストファイルを再分析"""
    
    # 既存のファイルを読み込み
    file_path = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会/東京電機大学中学校_2025_社会.txt")
    
    if not file_path.exists():
        print(f"ファイルが見つかりません: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 改善版テーマ抽出器
    extractor = ImprovedThemeExtractor()
    
    # 問題のあるテーマを抽出して再分析
    lines = content.split('\n')
    problematic_themes = []
    
    for i, line in enumerate(lines):
        if line.strip().startswith('問') and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                question_num = parts[0].strip()
                theme = parts[1].strip()
                
                # 問題のあるテーマを検出
                bad_patterns = [
                    '空欄補充', '空らん', '正しい文章を', 'まちがっている文章を',
                    '下線', 'この当時', 'この選挙', '次の図', '次の文章',
                    '現象全然ダメ'
                ]
                
                if any(bad in theme for bad in bad_patterns):
                    problematic_themes.append({
                        'num': question_num,
                        'old_theme': theme,
                        'line_num': i
                    })
    
    print("=== 2025年度 東京電機大学中学校 社会科 テーマ再分析 ===\n")
    print(f"問題のあるテーマ数: {len(problematic_themes)}個\n")
    
    # 各問題のテーマを改善
    improvements = []
    
    for item in problematic_themes:
        print(f"{item['num']}: {item['old_theme']}")
        
        # 問題文を探す（簡易的に次の数行から推測）
        problem_text = ""
        for j in range(item['line_num'] + 1, min(item['line_num'] + 10, len(lines))):
            if lines[j].strip().startswith('問題文:'):
                problem_text = lines[j].replace('問題文:', '').strip()
                # 次の行も取得
                if j + 1 < len(lines) and not lines[j + 1].strip().startswith('◆'):
                    problem_text += " " + lines[j + 1].strip()
                break
        
        # もし問題文が見つからない場合、テーマ自体から推測
        if not problem_text:
            problem_text = item['old_theme']
        
        # 改善版で再抽出
        result = extractor.extract_theme(problem_text[:200] if len(problem_text) > 200 else problem_text)
        new_theme = result.theme if result.theme else None
        
        print(f"  → 改善後: {new_theme if new_theme else '（除外）'}")
        
        improvements.append({
            'num': item['num'],
            'old': item['old_theme'],
            'new': new_theme,
            'improved': new_theme is None or (new_theme and item['old_theme'] != new_theme)
        })
        print()
    
    # 改善率を計算
    improved_count = sum(1 for imp in improvements if imp['improved'])
    improvement_rate = improved_count / len(improvements) * 100 if improvements else 0
    
    print(f"=== 改善結果 ===")
    print(f"改善されたテーマ: {improved_count}/{len(improvements)} ({improvement_rate:.1f}%)")
    
    # 推奨される修正内容を出力
    print("\n=== 推奨される修正 ===")
    for imp in improvements:
        if imp['improved']:
            if imp['new']:
                print(f"{imp['num']}: {imp['old']} → {imp['new']}")
            else:
                print(f"{imp['num']}: {imp['old']} → （削除）")
    
    # 改善版のファイルを生成
    print("\n改善版ファイルを生成しますか？ (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        # 新しいファイル内容を作成
        new_lines = []
        for line in lines:
            modified = False
            for imp in improvements:
                if imp['improved'] and line.strip().startswith(imp['num'] + ':'):
                    if imp['new']:
                        new_lines.append(f"  {imp['num']}: {imp['new']}")
                    else:
                        # テーマが除外される場合はスキップ
                        pass
                    modified = True
                    break
            
            if not modified:
                new_lines.append(line)
        
        # 改善版ファイルを保存
        output_path = file_path.parent / f"{file_path.stem}_改善版.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ 改善版を保存しました: {output_path}")

if __name__ == "__main__":
    reanalyze_2025()