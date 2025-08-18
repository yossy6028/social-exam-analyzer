#!/usr/bin/env python3
"""
GUI直接実行テスト（Gemini詳細分析モード）
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数をロード
from dotenv import load_dotenv
load_dotenv()

# メインGUIを起動
if __name__ == "__main__":
    print("=" * 60)
    print("社会科目入試問題分析システム")
    print("Gemini詳細分析モード統合版")
    print("=" * 60)
    print()
    print("使用方法:")
    print("1. PDFファイルを選択")
    print('2. 「Gemini詳細分析を使用」にチェック')
    print("3. 「分析開始」をクリック")
    print()
    print("起動中...")
    print()
    
    # tkinterが利用可能か確認
    try:
        import tkinter as tk
        from main import SocialExamAnalyzerGUI
        
        # GUIを起動
        root = tk.Tk()
        app = SocialExamAnalyzerGUI(root)
        root.mainloop()
        
    except ImportError as e:
        print(f"エラー: {e}")
        print("tkinterがインストールされていません")
    except Exception as e:
        print(f"起動エラー: {e}")
        import traceback
        traceback.print_exc()