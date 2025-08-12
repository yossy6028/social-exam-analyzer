"""
内容種別ベースのExcelフォーマッター
「文章1」「文章2」「その他1」「その他2」形式でデータを整理
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.app_config import get_config

logger = logging.getLogger(__name__)


class ContentTypeFormatter:
    """内容種別ベースでExcelに出力するフォーマッター"""
    
    def __init__(self, excel_path: str = None):
        """
        初期化
        
        Args:
            excel_path: 出力先のExcelファイルパス
        """
        config = get_config()
        
        if excel_path is None:
            excel_path = str(config.get_new_excel_path())
        
        self.excel_path = excel_path
        self.columns = self._generate_columns()
    
    def _generate_columns(self) -> List[str]:
        """カラム名を生成"""
        base_columns = [
            '学校名', '年度', '総設問数', '総文字数',
            '選択_問題数', '記述_問題数', '抜き出し_問題数', '漢字_問題数', '語句_問題数'
        ]
        
        # 文章1, 文章2, 文章3のカラム
        for i in range(1, 4):
            base_columns.extend([
                f'文章{i}_著者',
                f'文章{i}_作品',
                f'文章{i}_ジャンル',
                f'文章{i}_テーマ',
                f'文章{i}_文字数',
                f'文章{i}_設問数'
            ])
        
        # その他1, その他2, その他3のカラム
        for i in range(1, 4):
            base_columns.extend([
                f'その他{i}_種別',  # 漢字・語句、説明文など
                f'その他{i}_著者',
                f'その他{i}_作品',
                f'その他{i}_ジャンル',
                f'その他{i}_テーマ',
                f'その他{i}_文字数',
                f'その他{i}_設問数'
            ])
        
        base_columns.append('更新日時')
        
        return base_columns
    
    def categorize_sections(self, sections: List[Dict]) -> Dict[str, List[Dict]]:
        """
        セクションを内容種別で分類
        
        Args:
            sections: セクション情報のリスト
            
        Returns:
            分類されたセクション
        """
        categorized = {
            '文章': [],  # 出典のある文章
            'その他': []  # 漢字・語句、出典のない説明文など
        }
        
        for section in sections:
            if section.get('source') and not section.get('is_kanji'):
                # 出典がある文章問題
                categorized['文章'].append(section)
            else:
                # 漢字・語句または出典のない文章
                categorized['その他'].append(section)
        
        return categorized
    
    def format_data(self, analysis_result: Dict[str, Any], school_name: str, year: int) -> Dict[str, Any]:
        """
        分析結果を新形式にフォーマット
        
        Args:
            analysis_result: 分析結果
            school_name: 学校名
            year: 年度
            
        Returns:
            フォーマット済みデータ
        """
        # セクションを分類
        categorized = self.categorize_sections(analysis_result.get('sections', []))
        
        # 基本情報
        data = {
            '学校名': school_name,
            '年度': year,
            '総設問数': analysis_result.get('total_questions', 0),
            '総文字数': analysis_result.get('total_characters', 0)
        }
        
        # 問題タイプ別の集計（実際の問題数をカウント）
        question_types = {
            '選択_問題数': 0,
            '記述_問題数': 0,
            '抜き出し_問題数': 0,
            '漢字_問題数': 0,
            '語句_問題数': 0
        }
        
        # 各セクションから問題数を集計
        for section in analysis_result.get('sections', []):
            questions = section.get('questions', [])
            for q in questions:
                q_type = q.get('type', '記述')
                if q_type == '選択':
                    question_types['選択_問題数'] += 1
                elif q_type == '記述':
                    question_types['記述_問題数'] += 1
                elif q_type == '抜き出し':
                    question_types['抜き出し_問題数'] += 1
                elif q_type == '漢字・語句':
                    # ジャンルで判定
                    if section.get('genre') == '漢字・語句':
                        question_types['漢字_問題数'] += 1
                    else:
                        question_types['語句_問題数'] += 1
        
        data.update(question_types)
        
        # 文章セクション（最大3つ）
        texts = categorized['文章'][:3]
        for i, section in enumerate(texts, 1):
            source = section.get('source', {})
            data[f'文章{i}_著者'] = source.get('author', '')
            data[f'文章{i}_作品'] = source.get('work', '')
            data[f'文章{i}_ジャンル'] = section.get('genre', '')
            data[f'文章{i}_テーマ'] = section.get('theme', '')
            data[f'文章{i}_文字数'] = section.get('characters', 0)
            data[f'文章{i}_設問数'] = len(section.get('questions', []))
        
        # 文章が3つ未満の場合は空欄を埋める
        for i in range(len(texts) + 1, 4):
            data[f'文章{i}_著者'] = ''
            data[f'文章{i}_作品'] = ''
            data[f'文章{i}_ジャンル'] = ''
            data[f'文章{i}_テーマ'] = ''
            data[f'文章{i}_文字数'] = 0
            data[f'文章{i}_設問数'] = 0
        
        # その他セクション（最大3つ）
        others = categorized['その他'][:3]
        for i, section in enumerate(others, 1):
            # 種別を判定
            if section.get('is_kanji'):
                type_name = '漢字・語句'
            elif section.get('genre') == '説明文':
                type_name = '説明文'
            elif section.get('genre') == '論説文':
                type_name = '論説文'
            else:
                type_name = 'その他'
            
            data[f'その他{i}_種別'] = type_name
            
            # 出典がある場合
            source = section.get('source', {})
            data[f'その他{i}_著者'] = source.get('author', '') if source else ''
            data[f'その他{i}_作品'] = source.get('work', '') if source else ''
            data[f'その他{i}_ジャンル'] = section.get('genre', '')
            data[f'その他{i}_テーマ'] = section.get('theme', '')
            data[f'その他{i}_文字数'] = section.get('characters', 0)
            data[f'その他{i}_設問数'] = len(section.get('questions', []))
        
        # その他が3つ未満の場合は空欄を埋める
        for i in range(len(others) + 1, 4):
            data[f'その他{i}_種別'] = ''
            data[f'その他{i}_著者'] = ''
            data[f'その他{i}_作品'] = ''
            data[f'その他{i}_ジャンル'] = ''
            data[f'その他{i}_テーマ'] = ''
            data[f'その他{i}_文字数'] = 0
            data[f'その他{i}_設問数'] = 0
        
        # 更新日時
        data['更新日時'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return data
    
    def save_to_excel(self, data: Dict[str, Any], sheet_name: str = None):
        """
        データをExcelファイルに保存
        
        Args:
            data: 保存するデータ
            sheet_name: シート名（指定しない場合は学校名を使用）
        """
        if sheet_name is None:
            sheet_name = data.get('学校名', 'データ')
        
        # DataFrameを作成
        df_new = pd.DataFrame([data], columns=self.columns)
        
        # 既存ファイルがある場合
        if os.path.exists(self.excel_path):
            try:
                # 既存データを読み込み
                with pd.ExcelFile(self.excel_path) as xls:
                    sheets_dict = {}
                    for sn in xls.sheet_names:
                        sheets_dict[sn] = pd.read_excel(xls, sheet_name=sn)
                
                # 対象シートが存在する場合
                if sheet_name in sheets_dict:
                    df_existing = sheets_dict[sheet_name]
                    
                    # 同じ年度のデータがあるか確認
                    year = data.get('年度')
                    if year and '年度' in df_existing.columns:
                        # 既存データから同じ年度のものを除外
                        df_existing = df_existing[df_existing['年度'] != year]
                    
                    # 新しいデータを追加
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    sheets_dict[sheet_name] = df_combined
                else:
                    # 新しいシートとして追加
                    sheets_dict[sheet_name] = df_new
                
                # 全シートを書き込み
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    for sn, df in sheets_dict.items():
                        df.to_excel(writer, sheet_name=sn, index=False)
                
            except Exception as e:
                logger.error(f"既存ファイルの処理中にエラー: {e}")
                # エラーの場合は新規作成
                with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                    df_new.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # 新規作成
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                df_new.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"データを保存しました: {self.excel_path} (シート: {sheet_name})")
    
    def display_formatted_data(self, data: Dict[str, Any]):
        """
        フォーマット済みデータを表示
        
        Args:
            data: 表示するデータ
        """
        print("\n" + "="*60)
        print(f"学校名: {data.get('学校名', 'N/A')}")
        print(f"年度: {data.get('年度', 'N/A')}")
        print(f"総設問数: {data.get('総設問数', 0)}")
        print(f"総文字数: {data.get('総文字数', 0):,}")
        print("-"*60)
        
        # 文章セクション
        print("\n【文章セクション】")
        for i in range(1, 4):
            author = data.get(f'文章{i}_著者', '')
            work = data.get(f'文章{i}_作品', '')
            if author or work:
                print(f"\n文章{i}:")
                print(f"  著者: {author}")
                print(f"  作品: {work}")
                print(f"  ジャンル: {data.get(f'文章{i}_ジャンル', '')}")
                print(f"  テーマ: {data.get(f'文章{i}_テーマ', '')}")
                print(f"  文字数: {data.get(f'文章{i}_文字数', 0):,}")
                print(f"  設問数: {data.get(f'文章{i}_設問数', 0)}")
        
        # その他セクション
        print("\n【その他セクション】")
        for i in range(1, 4):
            type_name = data.get(f'その他{i}_種別', '')
            if type_name:
                print(f"\nその他{i}:")
                print(f"  種別: {type_name}")
                author = data.get(f'その他{i}_著者', '')
                work = data.get(f'その他{i}_作品', '')
                if author or work:
                    print(f"  著者: {author}")
                    print(f"  作品: {work}")
                print(f"  ジャンル: {data.get(f'その他{i}_ジャンル', '')}")
                print(f"  テーマ: {data.get(f'その他{i}_テーマ', '')}")
                print(f"  文字数: {data.get(f'その他{i}_文字数', 0):,}")
                print(f"  設問数: {data.get(f'その他{i}_設問数', 0)}")
        
        # 問題タイプ別統計
        print("\n【問題タイプ別統計】")
        print(f"  選択問題: {data.get('選択_問題数', 0)}問")
        print(f"  記述問題: {data.get('記述_問題数', 0)}問")
        print(f"  抜き出し問題: {data.get('抜き出し_問題数', 0)}問")
        print(f"  漢字問題: {data.get('漢字_問題数', 0)}問")
        print(f"  語句問題: {data.get('語句_問題数', 0)}問")
        print("="*60)