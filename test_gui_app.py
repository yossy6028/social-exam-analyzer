#!/usr/bin/env python3
"""
GUI動作確認用スクリプト（実際のファイル選択無しで動作確認）
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数設定（必要に応じて）
# os.environ['GEMINI_API_KEY'] = 'your-api-key-here'

def main():
    """GUIアプリケーションのテスト起動"""
    try:
        # main.pyから必要なクラスをインポート
        from main import SocialExamAnalyzerGUI
        
        # GUI起動
        root = tk.Tk()
        app = SocialExamAnalyzerGUI(root)
        
        # テスト用にサンプルテキストで分析実行する関数
        def run_test_analysis():
            # サンプルPDFの代わりにテストテキストを使用
            test_text = """
            大問1 歴史分野
            問1 江戸時代の三大改革について説明しなさい。
            問2 明治維新の主要な改革を3つ挙げなさい。
            
            大問2 公民分野
            問1 日本国憲法の三原則を答えなさい。
            問2 国会の種類と役割について述べなさい。
            
            大問3 地理分野
            問1 日本の四大工業地帯を答えなさい。
            問2 地図を見て、県庁所在地を答えなさい。
            """
            
            # 一時的にOCRハンドラーをモック
            class MockOCRHandler:
                def process_pdf(self, file_path):
                    return test_text
            
            # OCRハンドラーを置き換え
            app.ocr_handler = MockOCRHandler()
            
            # ダミーファイルパスを設定
            app.selected_file = "/dummy/test.pdf"
            app.file_label.config(text="テストファイル: test.pdf")
            app.analyze_button.config(state=tk.NORMAL)
            
            # 学校情報を設定
            app.school_entry.delete(0, tk.END)
            app.school_entry.insert(0, "テスト中学校")
            app.year_entry.delete(0, tk.END)
            app.year_entry.insert(0, "2025")
            
            # 分析開始
            app.start_analysis()
        
        # テストボタンを追加
        test_button = tk.Button(root, text="テスト分析実行", command=run_test_analysis,
                               bg="lightblue", font=('', 10, 'bold'))
        test_button.place(x=10, y=10)
        
        # インストラクションを追加
        instruction = tk.Label(root, text="「テスト分析実行」ボタンをクリックしてテストデータで動作確認",
                              fg="blue")
        instruction.place(x=120, y=15)
        
        print("✅ GUIアプリケーションが起動しました")
        print("「テスト分析実行」ボタンをクリックして動作を確認してください")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()