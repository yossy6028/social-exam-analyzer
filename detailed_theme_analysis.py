#!/usr/bin/env python3
"""
詳細な主題分析システム - 小問のワード分析とsubject_index.md照合
"""

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.terms_repository import TermsRepository
from modules.improved_question_extractor import ImprovedQuestionExtractor

class DetailedThemeAnalyzer:
    """詳細な主題分析システム"""
    
    def __init__(self):
        self.terms_repo = TermsRepository()
        self.extractor = ImprovedQuestionExtractor()
        
        # 分野別の重要度重み
        self.field_weights = {
            'geography': 1.0,
            'history': 1.0,
            'civics': 1.0
        }
        
        # キーワード抽出パターン
        self.keyword_patterns = {
            'geography': [
                r'[一-龯]{2,}',  # 漢字の連続
                r'[東南西北]京|[東南西北]海道|[都道府県]|[市町村]',  # 地名
                r'[山岳河川海島平野丘陵盆地]',  # 地形
                r'[農業工業商業貿易交通]',  # 産業
                r'[気候気温降水量]',  # 気候
            ],
            'history': [
                r'\d+世紀|\d+年代|\d+年',  # 年代
                r'[幕府朝廷大名武士農民商人]',  # 歴史用語
                r'[戦争政治文化人物事件制度]',  # 歴史概念
                r'[古代中世近世近代]',  # 時代区分
            ],
            'civics': [
                r'[制政策法憲条約]',  # 制度・政策
                r'[国会内閣裁判所地方自治]',  # 政治機関
                r'[選挙政党外交安全保障]',  # 政治概念
                r'[人権民主主義自由平等]',  # 基本概念
            ]
        }
    
    def analyze_questions(self, ocr_file: str):
        """問題の詳細分析を実行"""
        print("=== 詳細な主題分析システム ===\n")
        
        # OCRテキストを読み込み
        ocr_text = self._load_ocr_text(ocr_file)
        if not ocr_text:
            return
        
        # 大問セクションを抽出
        major_sections = self.extractor._find_major_sections(ocr_text)
        
        if not major_sections:
            print("❌ 大問セクションが見つかりません")
            return
        
        print(f"✅ 検出された大問数: {len(major_sections)}")
        
        # 各大問を詳細分析
        for major_num, section_text in major_sections:
            self._analyze_major_section(major_num, section_text)
    
    def _load_ocr_text(self, ocr_file: str) -> str:
        """OCRテキストファイルを読み込み"""
        try:
            with open(ocr_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ OCRファイルが見つかりません: {ocr_file}")
            return None
    
    def _analyze_major_section(self, major_num: str, section_text: str):
        """大問セクションの詳細分析"""
        print(f"\n{'='*70}")
        print(f"大問{major_num}の詳細分析")
        print(f"{'='*70}")
        
        # 小問を抽出
        minor_questions = self.extractor._extract_minor_questions(section_text)
        
        print(f"抽出された小問数: {len(minor_questions)}")
        
        if not minor_questions:
            print("❌ 小問が見つかりません")
            return
        
        # 各小問を詳細分析
        for i, (q_num, q_text) in enumerate(minor_questions):
            print(f"\n--- 小問{q_num} ---")
            print(f"テキスト: {q_text[:150]}...")
            
            # ステップ1: 分野別キーワード抽出
            field_keywords = self._extract_field_keywords(q_text)
            print(f"分野別キーワード:")
            for field, keywords in field_keywords.items():
                if keywords:
                    print(f"  {field}: {keywords}")
            
            # ステップ2: subject_index.mdとの照合
            matched_terms = self._find_matching_terms(field_keywords)
            print(f"照合結果:")
            for match in matched_terms[:3]:  # 上位3件のみ表示
                print(f"  {match['keyword']} → {match['term']} ({match['field']}, 信頼度: {match['confidence']:.2f})")
            
            # ステップ3: 主題の決定
            main_theme = self._determine_main_theme(matched_terms, q_text)
            print(f"決定された主題: {main_theme}")
            
            # ステップ4: 分野の推定
            inferred_field = self._infer_field_from_theme(main_theme, matched_terms)
            print(f"推定分野: {inferred_field}")
            
            print("-" * 50)
    
    def _extract_field_keywords(self, question_text: str) -> dict:
        """分野別にキーワードを抽出"""
        field_keywords = {field: [] for field in self.keyword_patterns.keys()}
        
        # 基本的な前処理
        text = question_text.strip()
        text = re.sub(r'[【】「」『』()（）\[\]{}]', '', text)
        
        # 句読点で分割
        sentences = re.split(r'[。、，．]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 3:
                continue
            
            # 各分野のパターンでキーワードを抽出
            for field, patterns in self.keyword_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, sentence)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]  # グループ化された場合
                        
                        if len(match) >= 2:  # 2文字以上のキーワードのみ
                            field_keywords[field].append(match)
        
        # 重複を除去
        for field in field_keywords:
            field_keywords[field] = list(set(field_keywords[field]))
        
        return field_keywords
    
    def _find_matching_terms(self, field_keywords: dict) -> list:
        """キーワードとsubject_index.mdの用語を照合"""
        matched_terms = []
        
        for field, keywords in field_keywords.items():
            for keyword in keywords:
                # TermsRepositoryで用語を検索
                found_terms = self.terms_repo.find_terms_in_text(keyword)
                
                if found_terms:
                    for term_field, term in found_terms:
                        confidence = self._calculate_confidence(keyword, term)
                        
                        # 分野の一致度も考慮
                        field_bonus = 1.2 if field == term_field else 1.0
                        final_confidence = confidence * field_bonus
                        
                        matched_terms.append({
                            'keyword': keyword,
                            'term': term,
                            'field': term_field,
                            'confidence': final_confidence,
                            'original_field': field
                        })
        
        # 信頼度でソート
        matched_terms.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matched_terms
    
    def _calculate_confidence(self, keyword: str, term: str) -> float:
        """キーワードと用語の一致度を計算"""
        if keyword == term:
            return 1.0
        elif keyword in term or term in keyword:
            return 0.8
        elif len(set(keyword) & set(term)) / len(set(keyword) | set(term)) > 0.5:
            return 0.6
        else:
            return 0.3
    
    def _determine_main_theme(self, matched_terms: list, question_text: str) -> str:
        """照合結果から主題を決定"""
        if not matched_terms:
            return "主題不明"
        
        # 最も信頼度の高い用語を選択
        best_match = matched_terms[0]
        
        # 信頼度に基づいて主題を決定
        if best_match['confidence'] >= 0.9:
            theme = f"{best_match['term']}について"
        elif best_match['confidence'] >= 0.7:
            theme = f"{best_match['term']}に関する問題"
        elif best_match['confidence'] >= 0.5:
            theme = f"{best_match['keyword']}について"
        else:
            theme = f"{best_match['keyword']}に関する問題"
        
        return theme
    
    def _infer_field_from_theme(self, theme: str, matched_terms: list) -> str:
        """主題から分野を推定"""
        if not matched_terms:
            return "不明"
        
        # 最も信頼度の高い用語の分野を使用
        best_match = matched_terms[0]
        
        # 分野名を日本語に変換
        field_names = {
            'geography': '地理',
            'history': '歴史',
            'civics': '公民'
        }
        
        return field_names.get(best_match['field'], best_match['field'])

def main():
    """メイン関数"""
    analyzer = DetailedThemeAnalyzer()
    
    # 実際のOCRテキストファイルで分析
    ocr_file = "logs/ocr_2023_日工大駒場_社会.txt"
    
    if not os.path.exists(ocr_file):
        print(f"❌ OCRファイルが見つかりません: {ocr_file}")
        return
    
    analyzer.analyze_questions(ocr_file)

if __name__ == "__main__":
    main()
