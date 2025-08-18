#!/usr/bin/env python3
"""
年度・学校名欄の更新動作テスト
"""
import tkinter as tk
from pathlib import Path
from typing import Optional
import re
from datetime import datetime

class TestFieldUpdate:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("フィールド更新テスト")
        self.root.geometry("500x300")
        
        # テスト用の入力欄
        tk.Label(self.root, text="学校名:").grid(row=0, column=0, padx=10, pady=10)
        self.school_entry = tk.Entry(self.root, width=30)
        self.school_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(self.root, text="年度:").grid(row=1, column=0, padx=10, pady=10)
        self.year_entry = tk.Entry(self.root, width=30)
        self.year_entry.grid(row=1, column=1, padx=10, pady=10)
        # デフォルト値を設定（現在の年）
        self.year_entry.insert(0, str(datetime.now().year))
        
        # テストケース
        test_files = [
            "2023年日本工業大学駒場中学校問題_社会.pdf",
            "2025年開成中学校問題_国語.pdf",
            "令和5年度_麻布中学校.pdf",
            "平成31年度_筑波大学附属駒場中学校.pdf",
        ]
        
        # ボタン作成
        for i, filename in enumerate(test_files):
            btn = tk.Button(self.root, text=f"選択: {filename[:30]}...", 
                          command=lambda f=filename: self.select_file(f))
            btn.grid(row=2+i, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # 結果表示ラベル
        self.result_label = tk.Label(self.root, text="", fg="blue")
        self.result_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
    
    def select_file(self, filename):
        """ファイル選択をシミュレート（main.pyと同じロジック）"""
        # Path.stemの動作をシミュレート
        filename_stem = filename.replace('.pdf', '')
        
        # 年度を抽出
        year = self._extract_year_from_filename(filename_stem)
        if year:
            # ファイルから年度が抽出できた場合は、既存の値をクリアして新しい値を設定
            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, str(year))
        
        # 学校名を抽出（年度情報を除去してから）
        # 年度パターンを除去
        school_name = filename_stem
        # 年度パターンを削除（「度」も含めて削除）
        school_name = re.sub(r'20\d{2}年度?', '', school_name)
        school_name = re.sub(r'令和\d+年度?', '', school_name)
        school_name = re.sub(r'R\d+年?度?', '', school_name)
        school_name = re.sub(r'平成\d+年度?', '', school_name)
        school_name = re.sub(r'H\d+年?度?', '', school_name)
        school_name = re.sub(r'\d{2}年度?', '', school_name)
        # 前後の不要な文字（アンダースコア、ハイフン、スペース）を削除
        school_name = re.sub(r'^[_\-\s]+', '', school_name)
        school_name = re.sub(r'[_\-\s]+$', '', school_name)
        # アンダースコアで分割して最初の部分を取得
        school_name = school_name.split('_')[0] if '_' in school_name else school_name
        # 「問題」で分割して学校名部分のみ取得
        school_name = school_name.split('問題')[0] if '問題' in school_name else school_name
        # 最終的なクリーンアップ
        school_name = school_name.strip()
        if school_name:
            # 既存の値をクリアして新しい値を設定
            self.school_entry.delete(0, tk.END)
            self.school_entry.insert(0, school_name)
        
        # 結果表示
        self.result_label.config(text=f"選択: {filename[:40]}...")
    
    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """ファイル名から年度を抽出（main.pyと同じロジック）"""
        # 現在の年を取得（上限チェック用）
        current_year = datetime.now().year
        
        # 1. 4桁の西暦年（2020年、2020など）
        match = re.search(r'(20\d{2})年?', filename)
        if match:
            year = int(match.group(1))
            if 2000 <= year <= current_year + 1:  # 未来の入試問題も考慮
                return year
        
        # 2. 令和年号（令和5年、令和5、R5など）
        match = re.search(r'令和(\d+)年?', filename)
        if match:
            reiwa_year = int(match.group(1))
            return 2018 + reiwa_year  # 令和元年 = 2019年
        
        match = re.search(r'R(\d+)年?', filename)
        if match:
            reiwa_year = int(match.group(1))
            return 2018 + reiwa_year
        
        # 3. 平成年号（平成31年、平成31、H31など）
        match = re.search(r'平成(\d+)年?', filename)
        if match:
            heisei_year = int(match.group(1))
            return 1988 + heisei_year  # 平成元年 = 1989年
        
        match = re.search(r'H(\d+)年?', filename)
        if match:
            heisei_year = int(match.group(1))
            return 1988 + heisei_year
        
        # 4. 2桁の年（23年など）- 2000年代として解釈
        match = re.search(r'(\d{2})年', filename)
        if match:
            two_digit_year = int(match.group(1))
            # 00-99の範囲で、現在の年の下2桁より大きければ1900年代、そうでなければ2000年代
            current_two_digit = current_year % 100
            if two_digit_year <= current_two_digit + 1:
                return 2000 + two_digit_year
            elif two_digit_year >= 90:  # 90年代は1990年代と解釈
                return 1900 + two_digit_year
            else:
                return 2000 + two_digit_year
        
        # 年度が見つからない場合はNoneを返す
        return None
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("フィールド更新テストGUIを起動中...")
    print("各ボタンをクリックして、年度と学校名が正しく更新されることを確認してください。")
    print()
    print("期待される結果:")
    print("1. 2023年日本工業大学駒場中学校 → 年度: 2023, 学校名: 日本工業大学駒場中学校")
    print("2. 2025年開成中学校 → 年度: 2025, 学校名: 開成中学校")
    print("3. 令和5年度_麻布中学校 → 年度: 2023, 学校名: 麻布中学校")
    print("4. 平成31年度_筑波大学附属駒場中学校 → 年度: 2019, 学校名: 筑波大学附属駒場中学校")
    print()
    
    app = TestFieldUpdate()
    app.run()