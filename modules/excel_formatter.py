"""
Excelデータベース用フォーマッター
入試問題分析結果を標準化されたフォーマットでExcelに保存
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
from pathlib import Path


class ExcelFormatter:
    """入試問題分析結果をExcel形式に整形するクラス"""
    
    # Excelの列定義（固定スキーマ）
    COLUMNS = [
        # 基本情報
        '年度',
        '分析日',
        '総文字数',
        '大問数',
        '総設問数',
        
        # 大問1の情報
        '大問1_ジャンル',
        '大問1_テーマ',
        '大問1_著者',
        '大問1_作品',
        '大問1_出版社',
        '大問1_文字数',
        '大問1_設問数',
        '大問1_内容要約',
        
        # 大問2の情報
        '大問2_ジャンル',
        '大問2_テーマ',
        '大問2_著者',
        '大問2_作品',
        '大問2_出版社',
        '大問2_文字数',
        '大問2_設問数',
        '大問2_内容要約',
        
        # 大問3の情報（必要に応じて）
        '大問3_ジャンル',
        '大問3_テーマ',
        '大問3_著者',
        '大問3_作品',
        '大問3_出版社',
        '大問3_文字数',
        '大問3_設問数',
        '大問3_内容要約',
        
        # 大問4の情報（必要に応じて）
        '大問4_ジャンル',
        '大問4_テーマ',
        '大問4_著者',
        '大問4_作品',
        '大問4_出版社',
        '大問4_文字数',
        '大問4_設問数',
        '大問4_内容要約',
        
        # 大問5の情報（必要に応じて）
        '大問5_ジャンル',
        '大問5_テーマ',
        '大問5_著者',
        '大問5_作品',
        '大問5_出版社',
        '大問5_文字数',
        '大問5_設問数',
        '大問5_内容要約',
        
        # 設問タイプ別集計
        '記述_問題数',
        '選択_問題数',
        '抜き出し_問題数',
        '漢字語句_問題数',
        '脱文挿入_問題数',
        'その他_問題数',
        
        # 詳細情報
        '出題傾向',
        '特記事項',
        'OCRファイル名',
        '備考'
    ]
    
    def __init__(self, excel_path: str = "/Users/yoshiikatsuhiko/Desktop/01_仕事 (Work)/オンライン家庭教師資料/過去問/entrance_exam_database.xlsx"):
        """
        初期化
        
        Args:
            excel_path: Excelファイルのパス
        """
        self.excel_path = excel_path
        
    def format_analysis_data(self, 
                            school_name: str,
                            year: int,
                            analysis_result: Dict[str, Any],
                            ocr_filename: str = None) -> Dict[str, Any]:
        """
        分析結果を標準フォーマットに整形
        
        Args:
            school_name: 学校名
            year: 年度
            analysis_result: 分析結果の辞書
            ocr_filename: OCRファイル名
            
        Returns:
            整形されたデータ辞書
        """
        # 空の行データを作成
        row_data = {col: None for col in self.COLUMNS}
        
        # 基本情報を設定
        row_data['年度'] = year
        row_data['分析日'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data['総文字数'] = analysis_result.get('total_characters', 0)
        row_data['大問数'] = len(analysis_result.get('sections', []))
        row_data['総設問数'] = analysis_result.get('total_questions', 0)
        
        # 各大問の情報を設定
        sections = analysis_result.get('sections', [])
        for i, section in enumerate(sections[:5], 1):  # 最大5つの大問まで対応
            prefix = f'大問{i}_'
            
            # 出典情報
            if section.get('source'):
                row_data[f'{prefix}著者'] = section['source'].get('author')
                row_data[f'{prefix}作品'] = section['source'].get('work')
            
            # その他の情報
            row_data[f'{prefix}ジャンル'] = section.get('genre', '不明')
            row_data[f'{prefix}テーマ'] = section.get('theme', '不明')
            row_data[f'{prefix}文字数'] = section.get('characters', 0)
            row_data[f'{prefix}設問数'] = len(section.get('questions', []))
            
            # 内容要約（必要に応じて追加）
            if section.get('summary'):
                row_data[f'{prefix}内容要約'] = section['summary']
        
        # 設問タイプ別集計
        question_types = analysis_result.get('question_types', {})
        row_data['記述_問題数'] = question_types.get('記述', 0)
        row_data['選択_問題数'] = question_types.get('選択', 0)
        row_data['抜き出し_問題数'] = question_types.get('抜き出し', 0)
        row_data['漢字語句_問題数'] = question_types.get('漢字・語句', 0)
        row_data['脱文挿入_問題数'] = question_types.get('脱文挿入', 0)
        
        # その他の設問タイプの合計
        other_count = sum(
            count for key, count in question_types.items()
            if key not in ['記述', '選択', '抜き出し', '漢字・語句', '脱文挿入']
        )
        row_data['その他_問題数'] = other_count if other_count > 0 else 0
        
        # 追加情報
        if ocr_filename:
            row_data['OCRファイル名'] = ocr_filename
        
        return row_data
    
    def save_to_excel(self, 
                     school_name: str,
                     row_data: Dict[str, Any],
                     backup: bool = True) -> bool:
        """
        データをExcelファイルに保存
        
        Args:
            school_name: 学校名（シート名）
            row_data: 保存するデータ
            backup: バックアップを作成するか
            
        Returns:
            成功した場合True
        """
        try:
            # バックアップ作成
            if backup and os.path.exists(self.excel_path):
                backup_path = f"data/backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(self.excel_path)}"
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                import shutil
                shutil.copy2(self.excel_path, backup_path)
                print(f"バックアップを作成: {backup_path}")
            
            # 既存のExcelファイルを読み込むか新規作成
            if os.path.exists(self.excel_path):
                excel_file = pd.ExcelFile(self.excel_path)
                sheets = {sheet: pd.read_excel(excel_file, sheet_name=sheet) 
                         for sheet in excel_file.sheet_names}
            else:
                sheets = {}
            
            # 学校のシートが存在しない場合は新規作成
            if school_name not in sheets:
                sheets[school_name] = pd.DataFrame(columns=self.COLUMNS)
            
            # データフレームを取得
            df = sheets[school_name]
            
            # 同じ年度のデータが存在する場合は更新、なければ追加
            year = row_data['年度']
            if year in df['年度'].values:
                # 既存データを更新
                index = df[df['年度'] == year].index[0]
                for col, value in row_data.items():
                    if col in df.columns:
                        df.at[index, col] = value
                print(f"{school_name} {year}年のデータを更新")
            else:
                # 新規データを追加
                new_row = pd.DataFrame([row_data])
                df = pd.concat([df, new_row], ignore_index=True)
                print(f"{school_name} {year}年のデータを新規追加")
            
            # 年度順にソート
            df = df.sort_values('年度')
            sheets[school_name] = df
            
            # Excelファイルに書き込み
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                for sheet_name, sheet_df in sheets.items():
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=True)
            
            print(f"データを保存しました: {self.excel_path}")
            return True
            
        except Exception as e:
            print(f"Excel保存エラー: {e}")
            return False
    
    def get_school_data(self, school_name: str) -> pd.DataFrame:
        """
        特定の学校のデータを取得
        
        Args:
            school_name: 学校名
            
        Returns:
            データフレーム
        """
        if not os.path.exists(self.excel_path):
            return pd.DataFrame(columns=self.COLUMNS)
        
        try:
            return pd.read_excel(self.excel_path, sheet_name=school_name)
        except:
            return pd.DataFrame(columns=self.COLUMNS)
    
    def get_summary_statistics(self, school_name: str) -> Dict[str, Any]:
        """
        学校の統計情報を取得
        
        Args:
            school_name: 学校名
            
        Returns:
            統計情報の辞書
        """
        df = self.get_school_data(school_name)
        
        if df.empty:
            return {}
        
        stats = {
            '登録年度数': len(df),
            '平均総文字数': df['総文字数'].mean(),
            '平均設問数': df['総設問数'].mean(),
            '最頻出ジャンル': self._get_most_common_value(df, ['大問1_ジャンル', '大問2_ジャンル']),
            '最頻出テーマ': self._get_most_common_value(df, ['大問1_テーマ', '大問2_テーマ']),
            '記述問題の平均': df['記述_問題数'].mean() if '記述_問題数' in df else 0,
            '選択問題の平均': df['選択_問題数'].mean() if '選択_問題数' in df else 0,
        }
        
        return stats
    
    def _get_most_common_value(self, df: pd.DataFrame, columns: List[str]) -> str:
        """
        複数列から最頻値を取得
        
        Args:
            df: データフレーム
            columns: 対象列のリスト
            
        Returns:
            最頻値
        """
        all_values = []
        for col in columns:
            if col in df.columns:
                values = df[col].dropna().tolist()
                all_values.extend(values)
        
        if not all_values:
            return '不明'
        
        from collections import Counter
        counter = Counter(all_values)
        return counter.most_common(1)[0][0] if counter else '不明'