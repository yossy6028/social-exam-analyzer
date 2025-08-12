"""
社会科目分析結果のテキスト出力モジュール
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from .social_analyzer import SocialQuestion

logger = logging.getLogger(__name__)


class TextFormatter:
    """社会科目分析結果をテキスト形式で出力"""
    
    def __init__(self):
        # 保存先ディレクトリ（デスクトップの過去問_社会フォルダ）
        self.output_dir = Path("/Users/yoshiikatsuhiko/Desktop/過去問_社会")
    
    def create_text_report(self, analysis_results: Dict[str, Any], 
                           school_name: str, year: str) -> str:
        """分析結果からテキストレポートを作成"""
        
        lines = []
        
        # ヘッダー
        lines.append("=" * 70)
        lines.append(f"{school_name} {year}年度 社会科入試問題分析")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"分析日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        lines.append(f"総問題数: {analysis_results.get('total_questions', 0)}問")
        lines.append("")
        
        # 統計情報
        stats = analysis_results.get('statistics', {})
        
        # 1. 分野別出題状況
        lines.append("【分野別出題状況】")
        lines.append("-" * 40)
        if 'field_distribution' in stats:
            for field, data in stats['field_distribution'].items():
                bar = "■" * int(data['percentage'] / 5)
                lines.append(f"{field:8s}: {data['count']:3d}問 ({data['percentage']:5.1f}%) {bar}")
        lines.append("")
        
        # 2. 資料活用状況
        lines.append("【資料活用状況】")
        lines.append("-" * 40)
        if 'resource_usage' in stats:
            sorted_resources = sorted(stats['resource_usage'].items(), 
                                     key=lambda x: x[1]['count'], 
                                     reverse=True)
            for resource, data in sorted_resources:
                if data['count'] > 0:
                    lines.append(f"{resource:12s}: {data['count']:3d}回 ({data['percentage']:5.1f}%)")
        
        if 'has_resources' in stats:
            lines.append("")
            lines.append(f"資料あり問題: {stats['has_resources']['count']}問 "
                        f"({stats['has_resources']['percentage']:.1f}%)")
        lines.append("")
        
        # 3. 出題形式分布
        lines.append("【出題形式分布】")
        lines.append("-" * 40)
        if 'format_distribution' in stats:
            sorted_formats = sorted(stats['format_distribution'].items(),
                                   key=lambda x: x[1]['count'],
                                   reverse=True)
            for format_type, data in sorted_formats:
                if data['count'] > 0:
                    lines.append(f"{format_type:10s}: {data['count']:3d}問 ({data['percentage']:5.1f}%)")
        lines.append("")
        
        # 4. 時事問題
        lines.append("【時事問題】")
        lines.append("-" * 40)
        if 'current_affairs' in stats:
            lines.append(f"時事問題数: {stats['current_affairs']['count']}問 "
                        f"({stats['current_affairs']['percentage']:.1f}%)")
        lines.append("")
        
        # 5. テーマ一覧
        lines.append("【出題テーマ一覧】")
        lines.append("-" * 40)
        questions = analysis_results.get('questions', [])
        themes = []
        for q in questions:
            if q.topic:
                themes.append(f"  {q.number}: {q.topic}")
        
        if themes:
            for theme in themes:  # 全件表示（省略なし）
                lines.append(theme)
        else:
            lines.append("  （テーマ情報なし）")
        lines.append("")
        
        # 6. 問題詳細
        lines.append("【問題詳細】")
        lines.append("=" * 70)
        
        questions = analysis_results.get('questions', [])
        for q in questions:
            lines.append("")
            lines.append(f"◆ {q.number}")
            lines.append(f"  分野: {q.field.value}")
            
            if q.resource_types and q.resource_types[0].value != "資料なし":
                resources = ", ".join([r.value for r in q.resource_types])
                lines.append(f"  資料: {resources}")
            
            lines.append(f"  形式: {q.question_format.value}")
            
            if q.is_current_affairs:
                lines.append(f"  時事: ○")
            
            if q.time_period:
                lines.append(f"  時代: {q.time_period}")
            
            if q.region:
                lines.append(f"  地域: {q.region}")
            
            if q.topic:
                lines.append(f"  主題: {q.topic}")
            
            if q.keywords:
                lines.append(f"  キーワード: {', '.join(q.keywords[:5])}")
            
            # 問題文の冒頭
            text_preview = q.text[:100] + "..." if len(q.text) > 100 else q.text
            lines.append(f"  問題文: {text_preview}")
        
        lines.append("")
        lines.append("=" * 70)
        lines.append("分析完了")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def save_text_report(self, report_text: str, school_name: str, year: str) -> str:
        """テキストレポートをファイルに保存"""
        
        # 保存先ディレクトリの確認・作成
        if not self.output_dir.exists():
            logger.warning(f"保存先ディレクトリが存在しません: {self.output_dir}")
            # デスクトップに直接保存
            self.output_dir = Path("/Users/yoshiikatsuhiko/Desktop")
            logger.info(f"代替保存先: {self.output_dir}")
        
        # ファイル名を生成（学校名_年度_社会.txt）
        filename = f"{school_name}_{year}_社会.txt"
        
        # 既存ファイルがある場合はタイムスタンプを追加
        filepath = self.output_dir / filename
        if filepath.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{school_name}_{year}_社会_{timestamp}.txt"
            filepath = self.output_dir / filename
        
        try:
            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            logger.info(f"テキストファイルを保存しました: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            # エラー時は現在のディレクトリに保存
            fallback_path = Path.cwd() / filename
            with open(fallback_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"代替パスに保存: {fallback_path}")
            return str(fallback_path)
    
    def format_analysis(self, questions: List[SocialQuestion], school_name: str, year: str) -> str:
        """分析結果を直接フォーマット（analyze_documentの結果から）"""
        
        # analyze_document形式のデータ構造を作成
        analysis_results = {
            'total_questions': len(questions),
            'questions': questions,
            'statistics': self._calculate_statistics(questions)
        }
        
        return self.create_text_report(analysis_results, school_name, year)
    
    def _calculate_statistics(self, questions: List[SocialQuestion]) -> Dict[str, Any]:
        """問題リストから統計を計算"""
        from collections import Counter
        
        total = len(questions)
        
        # 分野分布
        field_counts = Counter(q.field.value for q in questions)
        field_distribution = {}
        for field, count in field_counts.items():
            field_distribution[field] = {
                'count': count,
                'percentage': count / total * 100 if total > 0 else 0
            }
        
        # 資料活用
        resource_counts = Counter()
        for q in questions:
            if q.resource_types:
                for r in q.resource_types:
                    resource_counts[r.value] += 1
        
        resource_distribution = {}
        total_resources = sum(resource_counts.values())
        for resource, count in resource_counts.items():
            resource_distribution[resource] = {
                'count': count,
                'percentage': count / total_resources * 100 if total_resources > 0 else 0
            }
        
        # 出題形式
        format_counts = Counter(q.question_format.value for q in questions)
        format_distribution = {}
        for fmt, count in format_counts.items():
            format_distribution[fmt] = {
                'count': count,
                'percentage': count / total * 100 if total > 0 else 0
            }
        
        # 時事問題
        current_affairs = [q for q in questions if q.is_current_affairs]
        
        return {
            'field_distribution': field_distribution,
            'resource_distribution': resource_distribution,
            'format_distribution': format_distribution,
            'current_affairs_count': len(current_affairs),
            'current_affairs_percentage': len(current_affairs) / total * 100 if total > 0 else 0
        }