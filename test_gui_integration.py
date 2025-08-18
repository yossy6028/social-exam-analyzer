#!/usr/bin/env python3
"""
GUI統合のテストスクリプト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# モジュールのインポートテスト
print("=" * 60)
print("GUI統合テスト")
print("=" * 60)
print()

# 1. インポートチェック
print("【1. モジュールインポートチェック】")
try:
    from modules.gemini_bridge import GeminiBridge
    print("  ✅ GeminiBridge: OK")
except ImportError as e:
    print(f"  ❌ GeminiBridge: {e}")

try:
    from analyze_with_gemini_detailed import GeminiDetailedAnalyzer
    print("  ✅ GeminiDetailedAnalyzer: OK")
except ImportError as e:
    print(f"  ❌ GeminiDetailedAnalyzer: {e}")

print()

# 2. 環境変数チェック
print("【2. 環境変数チェック】")
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print(f"  ✅ GEMINI_API_KEY: 設定済み（{len(api_key)}文字）")
else:
    print("  ❌ GEMINI_API_KEY: 未設定")

print()

# 3. GeminiBridge動作チェック
print("【3. GeminiBridge動作チェック】")
try:
    bridge = GeminiBridge()
    if bridge.check_availability():
        print("  ✅ 利用可能")
    else:
        print("  ❌ 利用不可")
except Exception as e:
    print(f"  ❌ エラー: {e}")

print()

# 4. GUI起動チェック（tkinterなし）
print("【4. main.pyのインポートチェック】")
try:
    # tkinterをモックして、main.pyがインポートできるか確認
    import unittest.mock as mock
    
    # tkinterをモック
    sys.modules['tkinter'] = mock.MagicMock()
    sys.modules['tkinter.filedialog'] = mock.MagicMock()
    sys.modules['tkinter.messagebox'] = mock.MagicMock()
    sys.modules['tkinter.ttk'] = mock.MagicMock()
    
    # main.pyをインポート
    import main
    
    # 必要な属性を確認
    if hasattr(main, 'GEMINI_BRIDGE_AVAILABLE'):
        if main.GEMINI_BRIDGE_AVAILABLE:
            print("  ✅ GEMINI_BRIDGE_AVAILABLE: True")
        else:
            print("  ⚠️ GEMINI_BRIDGE_AVAILABLE: False")
    else:
        print("  ❌ GEMINI_BRIDGE_AVAILABLE が定義されていません")
    
except Exception as e:
    print(f"  ❌ main.pyのインポートエラー: {e}")

print()

# 5. 統合の準備状態
print("【5. 統合の準備状態】")
all_ok = True

checks = [
    ("GeminiBridge利用可能", lambda: GeminiBridge().check_availability()),
    ("API Key設定済み", lambda: bool(os.getenv('GEMINI_API_KEY'))),
    ("analyze_with_gemini_detailed.py存在", lambda: Path("analyze_with_gemini_detailed.py").exists())
]

for name, check in checks:
    try:
        if check():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}")
            all_ok = False
    except:
        print(f"  ❌ {name}")
        all_ok = False

print()
print("=" * 60)

if all_ok:
    print("✅ GUI統合の準備が完了しています")
    print()
    print("次のステップ:")
    print("1. python3 main.py でGUIを起動")
    print("2. PDFファイルを選択")
    print("3. 「Gemini詳細分析を使用」にチェック")
    print("4. 「分析開始」をクリック")
else:
    print("⚠️ 一部の準備が完了していません")

print("=" * 60)