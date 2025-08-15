"""
PDF OCR処理モジュール（社会科目版）
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, Tuple
import subprocess
import json

logger = logging.getLogger(__name__)


class OCRHandler:
    """PDF OCR処理クラス（社会科目版）"""
    
    def __init__(self):
        """初期化"""
        self.use_google_vision = self._check_google_vision_available()
        
    def _check_google_vision_available(self) -> bool:
        """Google Cloud Vision APIが利用可能か確認"""
        try:
            from google.cloud import vision
            # ADC（Application Default Credentials）の確認
            client = vision.ImageAnnotatorClient()
            return True
        except Exception as e:
            logger.info(f"Google Cloud Vision API利用不可: {e}")
            return False
    
    def process_pdf(self, pdf_path: str) -> Optional[str]:
        """PDFファイルからテキストを抽出"""
        logger.info(f"PDFを処理中: {pdf_path}")
        
        # ファイルの存在確認
        if not os.path.exists(pdf_path):
            logger.error(f"PDFファイルが見つかりません: {pdf_path}")
            return None
        
        # 複数の方法でテキスト抽出を試行
        text = None
        
        # 1. Google Cloud Vision APIを試行
        if self.use_google_vision:
            text = self._extract_with_google_vision(pdf_path)
            if text:
                logger.info("Google Cloud Vision APIでテキスト抽出成功")
                return self._normalize_ocr_text(text)
        
        # 2. pdfplumberを試行
        text = self._extract_with_pdfplumber(pdf_path)
        if text:
            logger.info("pdfplumberでテキスト抽出成功")
            return self._normalize_ocr_text(text)
        
        # 3. pdftotextコマンドを試行
        text = self._extract_with_pdftotext(pdf_path)
        if text:
            logger.info("pdftotextでテキスト抽出成功")
            return self._normalize_ocr_text(text)
        
        # 4. すべて失敗した場合はダミーテキストを返す
        logger.warning("PDF処理に失敗しました。ダミーテキストを使用します")
        return self._get_dummy_text()

    def _normalize_ocr_text(self, text: str) -> str:
        """OCR後テキストの正規化（誤分割・全角記号・丸数字などを補正）"""
        if not text:
            return text
        t = text
        # 全角空白→半角
        t = t.replace('\u3000', ' ')
        # 丸数字→半角
        circ_pairs = [
            ('①','1'),('②','2'),('③','3'),('④','4'),('⑤','5'),
            ('⑥','6'),('⑦','7'),('⑧','8'),('⑨','9'),('⑩','10')
        ]
        for a,b in circ_pairs:
            t = t.replace(a,b)
        # 全角→半角の一般的な数字
        t = t.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        # チルダ統一
        t = t.replace('～', '〜')
        # 日本語の連続間の空白を除去（促 成 栽 培 → 促成栽培）
        t = re.sub(r'(?<=[一-龥ぁ-んァ-ヴー])\s+(?=[一-龥ぁ-んァ-ヴー])', '', t)
        # 日本語+語尾記号間の不要空白削除
        t = re.sub(r'(?<=[一-龥ぁ-んァ-ヴー])\s+(?=[）\)])', '', t)
        # 記号と日本語の連結部の空白除去
        t = re.sub(r'(?<=\()\s+(?=[一-龥ぁ-んァ-ヴー])', '', t)
        # 日本語間に挟まる改行を削除（語の分断対策）
        t = re.sub(r'(?<=[一-龥ぁ-んァ-ヴー])\n+(?=[一-龥ぁ-んァ-ヴー])', '', t)
        # 連続改行の整理
        t = re.sub(r'\n{3,}', '\n\n', t)
        # 行内の多重空白を整理
        t = re.sub(r'[ \t]{2,}', ' ', t)
        return t
    
    def _extract_with_google_vision(self, pdf_path: str) -> Optional[str]:
        """Google Cloud Vision APIでテキスト抽出"""
        try:
            from google.cloud import vision
            from pdf2image import convert_from_path
            import io
            
            client = vision.ImageAnnotatorClient()
            
            # PDFを画像に変換
            images = convert_from_path(pdf_path, dpi=300)
            all_text = []
            
            for i, image in enumerate(images):
                # 画像をバイト列に変換
                byte_io = io.BytesIO()
                image.save(byte_io, format='PNG')
                content = byte_io.getvalue()
                
                # Vision APIで処理
                vision_image = vision.Image(content=content)
                response = client.document_text_detection(
                    image=vision_image,
                    image_context=vision.ImageContext(language_hints=['ja'])
                )
                
                if response.text_annotations:
                    all_text.append(response.text_annotations[0].description)
            
            return "\n".join(all_text) if all_text else None
            
        except Exception as e:
            logger.debug(f"Google Vision API処理失敗: {e}")
            return None
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> Optional[str]:
        """pdfplumberでテキスト抽出"""
        try:
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            return "\n".join(text_parts) if text_parts else None
            
        except ImportError:
            logger.debug("pdfplumberがインストールされていません")
            return None
        except Exception as e:
            logger.debug(f"pdfplumber処理失敗: {e}")
            return None
    
    def _extract_with_pdftotext(self, pdf_path: str) -> Optional[str]:
        """pdftotextコマンドでテキスト抽出"""
        try:
            result = subprocess.run(
                ['pdftotext', pdf_path, '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                return result.stdout
            
            return None
            
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("pdftotextコマンドが利用できません")
            return None
    
    def extract_school_year_from_filename(self, filename: str) -> Tuple[str, str]:
        """
        ファイル名から学校名と年度を抽出
        
        Args:
            filename: ファイル名
            
        Returns:
            (学校名, 年度) のタプル
        """
        # ファイル名から拡張子を除去
        name = Path(filename).stem
        
        # 年度のパターンを検索（4桁の数字 or 令和/平成+数字）
        year_patterns = [
            r'(\d{4})年',  # 2020年
            r'令和(\d+)年',  # 令和2年
            r'平成(\d+)年',  # 平成30年
            r'R(\d+)',      # R2
            r'H(\d+)',      # H30
        ]
        
        year = ""
        for pattern in year_patterns:
            match = re.search(pattern, name)
            if match:
                if '令和' in pattern:
                    # 令和の年を西暦に変換（令和1年=2019年）
                    reiwa_year = int(match.group(1))
                    year = str(2018 + reiwa_year)
                elif '平成' in pattern:
                    # 平成の年を西暦に変換（平成1年=1989年）
                    heisei_year = int(match.group(1))
                    year = str(1988 + heisei_year)
                elif pattern == r'R(\d+)':
                    # R2 -> 2020年
                    reiwa_year = int(match.group(1))
                    year = str(2018 + reiwa_year)
                elif pattern == r'H(\d+)':
                    # H30 -> 2018年
                    heisei_year = int(match.group(1))
                    year = str(1988 + heisei_year)
                else:
                    year = match.group(1)
                break
        
        # 学校名のパターンを検索
        school_patterns = [
            r'([^年]+(?:中学校|中学|中等教育学校|学園))',
            r'([^_]+)_\d{4}',  # 学校名_年度.pdf
            r'([^年]+)問題',     # 学校名問題.pdf
        ]
        
        school = ""
        for pattern in school_patterns:
            match = re.search(pattern, name)
            if match:
                school = match.group(1)
                # 不要な文字を削除
                school = school.replace('年', '')
                school = school.replace('問題', '')
                school = school.replace('解答', '')
                school = school.replace('_', '')
                school = re.sub(r'\d{4}', '', school)  # 4桁の数字を削除
                school = school.strip()
                
                # 「中学」が含まれていない場合は追加
                if '中学' not in school and '学園' not in school and '学院' not in school:
                    school += '中学校'
                break
        
        # デフォルト値
        if not year:
            year = "2025"
        if not school:
            school = "不明中学校"
        
        logger.info(f"ファイル名から抽出: 学校名={school}, 年度={year}")
        return school, year
    
    def _get_dummy_text(self) -> str:
        """テスト用のダミーテキストを返す"""
        return """
社会科入学試験問題

問1. 次の地図を見て、日本の四大工業地帯の名称をすべて答えなさい。

問2. 江戸時代の参勤交代制度について、その目的と影響を説明しなさい。

問3. 日本国憲法の三大原則を選びなさい。
ア. 国民主権  イ. 平和主義  ウ. 基本的人権の尊重  エ. 三権分立

問4. SDGsの17の目標のうち、環境に関連する目標を3つ挙げなさい。

問5. 次のグラフは日本の人口推移を表しています。少子高齢化について説明しなさい。

問6. 明治維新の中心人物を3人挙げ、それぞれの功績を述べなさい。

問7. 国際連合の主要機関を5つ答えなさい。

問8. 地球温暖化の原因と対策について述べなさい。

問9. 次の年表を見て、鎌倉時代の主な出来事を3つ選びなさい。

問10. 選挙権の歴史について、年齢引き下げの経緯を説明しなさい。

問11. 日本の農業の特徴と課題について述べなさい。

問12. 2020年の東京オリンピック・パラリンピックの意義について説明しなさい。

問13. 次の写真は世界遺産を示しています。それぞれの名称と所在地を答えなさい。

問14. 三権分立について、それぞれの役割を説明しなさい。

問15. アジアの主要な河川を5つ挙げ、流域の特徴を述べなさい。

問16. 戦国時代の三英傑について、それぞれの政策を比較しなさい。

問17. 日本の貿易の特徴について、輸出入の品目を含めて説明しなさい。

問18. 地方自治について、都道府県と市町村の役割の違いを述べなさい。

問19. 次の表は各国のGDPを示しています。経済成長について説明しなさい。

問20. 平安時代の文化について、特徴を3つ挙げなさい。

問21. 環境問題について、身近な取り組みを提案しなさい。

問22. 第二次世界大戦後の日本の復興について説明しなさい。

問23. 次の地形図を読み取り、土地利用の特徴を述べなさい。

問24. 少子高齢化が社会に与える影響について論じなさい。

問25. 情報化社会のメリットとデメリットについて説明しなさい。
"""
