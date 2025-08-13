#!/usr/bin/env python3
"""
簡易テストランナー

pytest が無い環境でも test_*.py を順番に実行し、
出力の記号や終了コードから成功/失敗を要約表示します。

デフォルトではネットワークや外部依存がありそうなテストを除外します。

使い方:
  python3 run_all_tests.py              # 通常（統合/外部依存を除外）
  python3 run_all_tests.py --all        # すべて実行（除外なし）
  python3 run_all_tests.py -k theme     # ファイル名フィルタ
  python3 run_all_tests.py --stop-on-fail
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple


ROOT = Path(__file__).parent


DEFAULT_EXCLUDES = [
    # ネットワーク/外部サービスの可能性
    'brave', 'web',
    # 実データ/実PDF依存の可能性
    'real', 'pdf_analysis', 'real_pdf',
]


def discover_tests(pattern: str | None, include_all: bool) -> List[Path]:
    files = sorted(ROOT.glob('test_*.py'))

    if pattern:
        files = [f for f in files if pattern in f.name]

    if include_all:
        return files

    def is_excluded(name: str) -> bool:
        return any(key in name for key in DEFAULT_EXCLUDES)

    return [f for f in files if not is_excluded(f.name)]


def run_test(file: Path) -> Tuple[bool, str]:
    env = os.environ.copy()
    # プロジェクト直下を import パスに追加
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')

    proc = subprocess.run(
        [sys.executable, str(file)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
    )

    output = proc.stdout

    # 判定ルール:
    # - 終了コードが非0 -> 失敗
    # - 出力に ❌ / 失敗 を含む -> 失敗
    # - それ以外は成功とみなす
    failed_markers = ['❌', '失敗']
    failed = proc.returncode != 0 or any(m in output for m in failed_markers)

    return (not failed), output


def main():
    ap = argparse.ArgumentParser(description='簡易テストランナー')
    ap.add_argument('--all', action='store_true', help='除外なしですべて実行')
    ap.add_argument('-k', '--pattern', help='ファイル名フィルタ (例: theme)')
    ap.add_argument('--stop-on-fail', action='store_true', help='失敗したらそこで停止')
    args = ap.parse_args()

    tests = discover_tests(args.pattern, include_all=args.all)
    if not tests:
        print('テストが見つかりませんでした。')
        return 1

    print('============================================================')
    print('テスト実行 (簡易ランナー)')
    print('============================================================')
    if not args.all:
        print('除外キーワード:', ', '.join(DEFAULT_EXCLUDES))
    if args.pattern:
        print(f'フィルタ: {args.pattern}')
    print()

    total = 0
    passed = 0

    for test in tests:
        total += 1
        print(f'>>> {test.name}')
        ok, output = run_test(test)
        if ok:
            passed += 1
            print('✅ PASS')
        else:
            print('❌ FAIL')
        # 出力を折りたたまずにそのまま表示
        print(output.rstrip())
        print('-' * 60)
        if not ok and args.stop_on_fail:
            break

    print('============================================================')
    print(f'合計: {total}, 成功: {passed}, 失敗: {total - passed}, 成功率: {passed*100/total:.1f}%')
    print('============================================================')

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())

