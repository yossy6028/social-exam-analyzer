"""
Gemini CLIを使用した高精度テーマ分析モジュール
subject_index.mdの重要語句と照合して最適なテーマを判定
"""

import subprocess
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeminiThemeAnalyzer:
    """Gemini CLIによる高精度テーマ分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.subject_index_path = Path(__file__).parent.parent / "docs" / "subject_index.md"
        self.subject_index_content = self._load_subject_index()
        self.enabled = self._check_gemini_cli()
        
        # Gemini API設定
        self.api_enabled = False
        if GENAI_AVAILABLE:
            # 環境変数またはハードコードされたAPIキーを使用
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                    self.api_enabled = True
                    logger.info("Gemini API初期化成功")
                except Exception as e:
                    logger.error(f"Gemini API初期化失敗: {e}")
                    self.api_enabled = False
            else:
                logger.warning("Gemini API key not found")
        
    def _load_subject_index(self) -> str:
        """subject_index.mdを読み込み"""
        try:
            if self.subject_index_path.exists():
                with open(self.subject_index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info("subject_index.md loaded successfully")
                return content
            else:
                logger.warning(f"subject_index.md not found at {self.subject_index_path}")
                return ""
        except Exception as e:
            logger.error(f"Failed to load subject_index.md: {e}")
            return ""
    
    def _check_gemini_cli(self) -> bool:
        """Gemini CLIが利用可能か確認"""
        try:
            result = subprocess.run(
                ['which', 'gemini'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def analyze_theme(self, ocr_text: str, field: str, question_num: str) -> Dict[str, any]:
        """
        OCRテキストから高精度でテーマを判定
        
        Args:
            ocr_text: OCRで読み取った問題文
            field: 分野（地理/歴史/公民/総合）
            question_num: 問題番号
            
        Returns:
            {
                'theme': テーマ名,
                'keywords': 関連キーワードリスト,
                'confidence': 信頼度（0-1）,
                'reasoning': 判定理由
            }
        """
        # APIが利用可能な場合は優先してAPIを使用
        if self.api_enabled:
            try:
                return self._analyze_theme_with_api(ocr_text, field, question_num)
            except Exception as e:
                logger.warning(f"Gemini API failed, falling back to CLI: {e}")
        
        # CLIによる分析（APIが使用できない場合）
        if not self.enabled:
            logger.warning("Gemini CLI is not available")
            return self._fallback_analysis(ocr_text, field)
        
        try:
            # Gemini用のプロンプトを作成
            prompt = self._create_theme_prompt(ocr_text, field, question_num)
            
            # Gemini CLIを実行（非対話モードで使用）
            result = subprocess.run(
                ['gemini', '-p', prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=15  # タイムアウトを短縮
            )
            
            if result.returncode == 0 and result.stdout:
                # Geminiの応答を解析
                return self._parse_gemini_response(result.stdout, ocr_text, field)
            else:
                logger.warning("Gemini CLI returned no valid response")
                return self._fallback_analysis(ocr_text, field)
                
        except subprocess.TimeoutExpired:
            logger.warning("Gemini CLI timeout")
            return self._fallback_analysis(ocr_text, field)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self._fallback_analysis(ocr_text, field)
    
    def _analyze_theme_with_api(self, ocr_text: str, field: str, question_num: str) -> Dict[str, any]:
        """
        Gemini APIを使用したテーマ分析
        """
        if not self.api_enabled:
            raise Exception("Gemini API not available")
        
        # プロンプトを作成
        prompt = self._create_theme_prompt(ocr_text, field, question_num)
        
        try:
            # APIを使用して分析
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # 応答を解析
                result = self._parse_gemini_response(response.text, ocr_text, field)
                result['reasoning'] = "Gemini API分析による判定"
                logger.info(f"Gemini API分析成功: {question_num} -> {result['theme']}")
                return result
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as api_error:
            # レート制限や他のAPIエラーをハンドリング
            error_msg = str(api_error)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"Gemini API rate limit exceeded for {question_num}")
                raise Exception("Rate limit exceeded")
            elif "403" in error_msg:
                logger.warning(f"Gemini API access denied for {question_num}")
                raise Exception("API access denied")
            else:
                logger.error(f"Gemini API error for {question_num}: {error_msg}")
                raise Exception(f"API error: {error_msg}")
    
    def _create_theme_prompt(self, ocr_text: str, field: str, question_num: str) -> str:
        """Gemini用のプロンプトを作成"""
        # OCRテキストから重要部分を抽出（最初の500文字）
        text_snippet = ocr_text[:500] if ocr_text else ""
        
        # subject_indexから関連部分を抽出
        relevant_keywords = self._extract_relevant_keywords(field)
        
        return f"""以下の社会科入試問題のテーマを判定してください。

分野: {field}
問題文: {text_snippet}

参考キーワード: {relevant_keywords}

次の形式で回答してください：
テーマ: [具体的なテーマ名]
キーワード: [関連語3つ]
信頼度: [高/中/低]

回答のみ、簡潔に。"""
    
    def _extract_relevant_keywords(self, field: str) -> str:
        """分野に応じた重要キーワードを抽出"""
        if not self.subject_index_content:
            return ""
        
        # 分野に応じてキーワードを選択
        if field == "歴史":
            keywords = ["縄文", "弥生", "古墳", "飛鳥", "奈良", "平安", "鎌倉", "室町", 
                       "江戸", "明治", "大正", "昭和", "源頼朝", "徳川家康", "織田信長"]
        elif field == "地理":
            keywords = ["平野", "山脈", "気候", "農業", "工業", "人口", "都市", "貿易"]
        elif field == "公民":
            keywords = ["憲法", "国会", "内閣", "裁判所", "選挙", "人権", "三権分立"]
        else:
            keywords = []
        
        return ", ".join(keywords[:10])
    
    def _parse_gemini_response(self, response: str, ocr_text: str, field: str) -> Dict[str, any]:
        """Geminiの応答を解析（シンプル版）"""
        try:
            # "Loaded cached credentials."を除去
            clean_response = re.sub(r'Loaded cached credentials\.?\n?', '', response)
            
            # テーマを抽出
            theme_match = re.search(r'テーマ[:：]\s*(.+?)[\n\r]', clean_response)
            theme = theme_match.group(1).strip() if theme_match else None
            
            # キーワードを抽出
            keywords_match = re.search(r'キーワード[:：]\s*(.+?)[\n\r]', clean_response)
            keywords = []
            if keywords_match:
                keywords_str = keywords_match.group(1)
                keywords = [k.strip() for k in re.split(r'[,、，]', keywords_str)]
            
            # 信頼度を抽出
            confidence_match = re.search(r'信頼度[:：]\s*([高中低])', clean_response)
            confidence = 0.8 if confidence_match and '高' in confidence_match.group(1) else 0.5
            
            if theme:
                return {
                    'theme': theme,
                    'keywords': keywords[:5],
                    'confidence': confidence,
                    'reasoning': f"Gemini分析による判定"
                }
            
            # パースできない場合は応答全体から推測
            return self._extract_from_unstructured(clean_response, ocr_text, field)
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return self._fallback_analysis(ocr_text, field)
    
    def _extract_from_unstructured(self, response: str, ocr_text: str, field: str) -> Dict[str, any]:
        """構造化されていない応答からテーマを抽出"""
        # キーワードベースの抽出
        theme = "分析対象外"
        keywords = []
        
        # 歴史の時代を探す
        if field == "歴史":
            periods = ["縄文", "弥生", "古墳", "飛鳥", "奈良", "平安", "鎌倉", "室町", 
                      "安土桃山", "江戸", "明治", "大正", "昭和", "平成", "令和"]
            for period in periods:
                if period in response or period in ocr_text:
                    theme = f"{period}時代の特徴"
                    keywords.append(period)
                    break
        
        # 地理のテーマを探す
        elif field == "地理":
            geo_themes = ["農業", "工業", "地形", "気候", "人口", "都市", "交通", "貿易"]
            for geo in geo_themes:
                if geo in response or geo in ocr_text:
                    theme = f"{geo}の特色"
                    keywords.append(geo)
                    break
        
        # 公民のテーマを探す
        elif field == "公民":
            civic_themes = ["憲法", "国会", "内閣", "裁判所", "選挙", "人権", "経済", "国際"]
            for civic in civic_themes:
                if civic in response or civic in ocr_text:
                    theme = f"{civic}の仕組み"
                    keywords.append(civic)
                    break
        
        return {
            'theme': theme,
            'keywords': keywords,
            'confidence': 0.3,  # 低い信頼度
            'reasoning': "構造化されていない応答から推定"
        }
    
    def _validate_theme(self, theme: str, field: str) -> bool:
        """テーマの妥当性をチェック"""
        # 基本的な妥当性チェック
        if not theme or len(theme) < 2 or len(theme) > 50:
            return False
        
        # 分野に応じた妥当性チェック
        if field == "歴史" and not any(word in theme for word in ["時代", "文化", "政治", "改革", "戦争", "条約"]):
            # 歴史的キーワードが含まれているか追加チェック
            historical_keywords = ["幕府", "天皇", "将軍", "大名", "武士", "貴族"]
            if not any(word in theme for word in historical_keywords):
                return False
        
        return True
    
    def analyze_all_questions_with_api(self, questions: List[Dict]) -> List[Dict]:
        """Gemini APIを使用して全問題を総括的に分析"""
        if not self.api_enabled or not questions:
            logger.warning("Gemini API not available")
            return self.analyze_all_questions(questions)  # フォールバック
        
        try:
            # プロンプトを作成
            prompt = self._create_batch_prompt(questions)
            
            # Gemini APIを使用
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # 応答を解析して適用
                return self._apply_batch_analysis(response.text, questions)
            else:
                logger.warning("Gemini API returned empty response")
                return questions
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self.analyze_all_questions(questions)  # フォールバック
    
    def analyze_all_questions(self, questions: List[Dict]) -> List[Dict]:
        """全問題を一括で総括的に分析"""
        if not questions:
            logger.warning("No questions to analyze")
            return questions
        
        # APIが利用可能な場合は優先してAPIを使用
        if self.api_enabled:
            try:
                return self._analyze_all_questions_with_api(questions)
            except Exception as e:
                logger.warning(f"Gemini API batch analysis failed, falling back to CLI: {e}")
        
        # CLIによる分析（APIが使用できない場合）
        if not self.enabled:
            logger.warning("Gemini CLI is not available")
            return questions
        
        try:
            # 全問題をまとめたプロンプトを作成
            prompt = self._create_batch_prompt(questions)
            
            # Gemini CLIを実行（非対話モードで高精度分析）
            result = subprocess.run(
                ['gemini', '-p', prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60  # タイムアウトを短縮
            )
            
            if result.returncode == 0 and result.stdout:
                # バッチ応答を解析して各問題に適用
                return self._apply_batch_analysis(result.stdout, questions)
            else:
                logger.warning("Gemini CLI batch analysis returned no valid response")
                return questions
                
        except subprocess.TimeoutExpired:
            logger.warning("Gemini CLI batch analysis timeout")
            return questions
        except Exception as e:
            logger.error(f"Gemini CLI batch analysis failed: {e}")
            return questions
    
    def _analyze_all_questions_with_api(self, questions: List[Dict]) -> List[Dict]:
        """APIを使用した全問題の一括分析"""
        if not self.api_enabled:
            raise Exception("Gemini API not available")
        
        try:
            # 全問題をまとめたプロンプトを作成
            prompt = self._create_batch_prompt(questions)
            
            # APIを使用して分析
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # バッチ応答を解析して各問題に適用
                result = self._apply_batch_analysis(response.text, questions)
                logger.info("Gemini API batch analysis completed successfully")
                return result
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as api_error:
            error_msg = str(api_error)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning("Gemini API rate limit exceeded for batch analysis")
                raise Exception("Rate limit exceeded")
            else:
                logger.error(f"Gemini API batch analysis error: {error_msg}")
                raise Exception(f"API error: {error_msg}")
    
    def _create_batch_prompt(self, questions: List[Dict]) -> str:
        """バッチ分析用のプロンプトを作成（subject_index.md活用版）"""
        # 問題リストを作成
        question_list = []
        for i, q in enumerate(questions[:30], 1):  # 最大30問まで
            num = q.get('question_number', f'問{i}')
            text = q.get('text', '')[:300]  # 各問題の最初の300文字
            field = q.get('field', '不明')
            current_topic = q.get('topic', '未設定')
            question_list.append(f"{i}. [{num}] 分野:{field} 現在のテーマ:「{current_topic}」\n   問題文: {text}")
        
        # subject_index.mdの重要部分を抽出
        subject_reference = self.subject_index_content[:5000] if self.subject_index_content else ""
        
        return f"""社会科入試問題のテーマを総括的に分析し、正確なテーマを判定してください。

【重要な参照資料（subject_index.md）】
{subject_reference}

【分析対象問題】
{chr(10).join(question_list)}

【分析指示】
1. 各問題について、subject_index.mdの重要語句と照合
2. OCRフラグメント（以下のような不完全なテーマ）は必ず修正：
   - 「記号 文武」→「文武天皇の時代」または「奈良時代の政治」
   - 「兵庫県明」→「明治時代の地方制度」または「兵庫県の地理」
   - 「朱子学以外」→「江戸時代の学問」
   - 「記号 下線部」→文脈から適切なテーマを推定
   - 「核兵器 下線部」→「核兵器と国際平和」または「現代の国際政治」
   - 「新詳日本史」→「日本史総合」
3. 不明な用語があれば、一般的な社会科の知識から推定
4. 各問題の文脈と関連性を考慮した総合的な判定

【出力形式】
各問題について以下の形式で回答（番号順に）：
1. テーマ: [具体的で正確なテーマ]
2. テーマ: [具体的で正確なテーマ]
...

注意：OCRフラグメントは絶対に残さないこと。"""
    
    def _apply_batch_analysis(self, response: str, questions: List[Dict]) -> List[Dict]:
        """バッチ分析結果を各問題に適用"""
        import re
        
        # "Loaded cached credentials."を除去
        clean_response = re.sub(r'Loaded cached credentials\.?\n?', '', response)
        
        # 各行からテーマを抽出
        lines = clean_response.split('\n')
        theme_pattern = re.compile(r'^\d+\.\s*テーマ[:：]\s*(.+)')
        
        themes = {}
        for line in lines:
            match = theme_pattern.match(line.strip())
            if match:
                idx = int(re.match(r'^(\d+)', line).group(1))
                theme = match.group(1).strip()
                if not self._is_ocr_fragment(theme):
                    themes[idx] = theme
        
        # 問題に適用
        for i, q in enumerate(questions, 1):
            if i in themes:
                q['topic'] = themes[i]
                q['gemini_analyzed'] = True
                logger.info(f"Gemini総括分析適用: {q.get('question_number')} -> {themes[i]}")
        
        return questions
    
    def _fix_ocr_fragment(self, theme: str, ocr_text: str = "") -> str:
        """OCRフラグメントを修正"""
        import re
        
        # よくあるOCRエラーの修正マッピング
        ocr_fixes = {
            "兵庫県明": "明治時代の地方制度",
            "記号 文武": "文武天皇の政治",
            "朱子学以外": "江戸時代の学問",
            "記号 下線部": "重要事項の確認",
            "核兵器 下線部": "核兵器と国際平和",
            "新詳日本史": "日本史総合",
            "刑事事件の業績": "司法制度",
            "新聞記事の業績": "メディアと社会",
            "白村江の戦い": "古代の対外関係",
            "日宋貿易の業績": "平安時代の貿易",
            "宣戦布告の業績": "戦争と外交",
            "太平洋地域の業績": "第二次世界大戦",
            "社会保障制度の業績": "社会保障制度",
            "真鍋淑郎氏の業績": "ノーベル賞と科学",
        }
        
        # 完全一致で修正
        if theme in ocr_fixes:
            return ocr_fixes[theme]
        
        # 「〜の業績」パターンの修正
        if theme.endswith("の業績"):
            base = theme[:-3]
            # 人名っぽい場合
            if len(base) <= 5:
                return f"{base}の功績"
        
        # 「総合問題」を具体化
        if "総合問題" in theme:
            field = re.sub(r'総合問題', '', theme).strip()
            if field in ["地理", "歴史", "公民"]:
                return f"{field}の重要事項"
            elif field == "総合":
                return "社会科総合"
        
        return theme
    
    def _is_ocr_fragment(self, theme: str) -> bool:
        """OCRフラグメントかどうかを判定"""
        if not theme:
            return False
        
        fragment_patterns = [
            r'^記号\s+\w+$',
            r'^\w{2,4}県\w{1,2}$',
            r'^[ぁ-ん]+以外$',
            r'^下線部\s*\w*$',
            r'^\w+\s+下線部$',  # 「核兵器 下線部」のようなパターン
            r'^[ア-ンA-Z]\s+',
            r'^\d+年\w{1,2}$',
            r'^第\d+[条項]$',
            r'^新詳\w+$',  # 「新詳日本史」など
            r'^\w+の業績$',  # 「兵庫県明の業績」のような不完全なもの
            r'^\w{1,3}総合問題$',  # 「公民総合問題」など汎用的すぎるもの
            r'^[地歴公総]\w{0,2}総合問題$',
        ]
        
        import re
        for pattern in fragment_patterns:
            if re.match(pattern, theme):
                return True
        
        # 汎用的すぎるテーマも除外
        generic_themes = [
            "地理総合問題", "歴史総合問題", "公民総合問題", "総合総合問題",
            "総合問題", "分析対象外", "地理問題", "歴史問題", "公民問題"
        ]
        if theme in generic_themes:
            return True
        
        return len(theme) <= 2 or re.match(r'^[\W_]+$', theme)
    
    def _fallback_analysis(self, ocr_text: str, field: str) -> Dict[str, any]:
        """フォールバック分析（Geminiが使えない場合）"""
        # OCRテキストから具体的なテーマを抽出
        theme = "分析対象外"
        keywords = []
        
        # より具体的なテーマ抽出
        if field == "歴史":
            # 時代名を探す
            periods = ["縄文", "弥生", "古墳", "飛鳥", "奈良", "平安", "鎌倉", "室町", 
                      "安土桃山", "江戸", "明治", "大正", "昭和", "平成", "令和"]
            for period in periods:
                if period in ocr_text:
                    theme = f"{period}時代の特徴"
                    keywords.append(period)
                    break
            
            # 人物名を探す
            if theme == "分析対象外":
                people = ["源頼朝", "徳川家康", "織田信長", "豊臣秀吉", "聖徳太子", "藤原道長"]
                for person in people:
                    if person in ocr_text:
                        theme = f"{person}の業績"
                        keywords.append(person)
                        break
        
        elif field == "地理":
            # 地理的テーマを探す
            geo_themes = {
                "農業": "農業の特色",
                "工業": "工業の特色",
                "平野": "平野の特色",
                "山脈": "山地・山脈",
                "気候": "気候の特徴",
                "人口": "人口問題",
                "都市": "都市の発展",
                "貿易": "貿易と経済"
            }
            for key, value in geo_themes.items():
                if key in ocr_text:
                    theme = value
                    keywords.append(key)
                    break
        
        elif field == "公民":
            # 公民的テーマを探す
            civic_themes = {
                "憲法": "日本国憲法",
                "国会": "国会の仕組み",
                "内閣": "内閣の役割",
                "裁判": "裁判所の仕組み",
                "選挙": "選挙制度",
                "人権": "基本的人権",
                "三権分立": "三権分立",
                "地方自治": "地方自治"
            }
            for key, value in civic_themes.items():
                if key in ocr_text:
                    theme = value
                    keywords.append(key)
                    break
        
        # それでも見つからない場合
        if theme == "分析対象外":
            theme = f"{field}の重要事項"
        
        return {
            'theme': theme,
            'keywords': keywords[:5],
            'confidence': 0.2,
            'reasoning': "Gemini CLIが利用不可のためフォールバック分析"
        }
    
    def batch_analyze(self, questions: List[Tuple[str, str, str]]) -> List[Dict[str, any]]:
        """
        複数の問題を一括分析
        
        Args:
            questions: [(問題番号, OCRテキスト, 分野), ...] のリスト
            
        Returns:
            分析結果のリスト
        """
        results = []
        for q_num, ocr_text, field in questions:
            result = self.analyze_theme(ocr_text, field, q_num)
            results.append(result)
            logger.info(f"Analyzed {q_num}: {result['theme']} (confidence: {result['confidence']})")
        
        return results