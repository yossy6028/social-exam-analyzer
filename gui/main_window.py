"""
メインウィンドウコンポーネント
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
from .analysis_panel import AnalysisPanel
from .result_panel import ResultPanel
from .menu_bar import MenuBar


class MainWindow:
    """メインウィンドウクラス"""
    
    def __init__(self, root: tk.Tk):
        """初期化"""
        self.root = root
        self.setup_window()
        self.create_widgets()
    
    def setup_window(self):
        """ウィンドウの設定"""
        self.root.title("社会科目入試問題分析システム")
        self.root.geometry("900x700")
        
        # メニューバー
        self.menu_bar = MenuBar(self.root)
        
    def create_widgets(self):
        """ウィジェットの作成"""
        # メインコンテナ
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # 分析パネル
        self.analysis_panel = AnalysisPanel(main_container)
        self.analysis_panel.frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 結果パネル
        self.result_panel = ResultPanel(main_container)
        self.result_panel.frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # イベントの接続
        self.analysis_panel.on_analysis_complete = self.result_panel.display_results
        
    def run(self):
        """アプリケーションの実行"""
        self.root.mainloop()