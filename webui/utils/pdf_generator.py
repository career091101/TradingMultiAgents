"""
PDF レポート生成モジュール
"""

from datetime import datetime
from pathlib import Path
import tempfile
from typing import Dict, Any, Optional
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultEncoding

class PDFReportGenerator:
    """TradingAgents分析レポートのPDF生成クラス"""
    
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_japanese_font()
        self._setup_styles()
        
    def _setup_japanese_font(self):
        """日本語フォントの設定"""
        self.japanese_font = 'Helvetica'  # デフォルト値を先に設定
        
        try:
            # 1. まず内蔵CIDフォントを試す（最も確実）
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
                self.japanese_font = 'HeiseiKakuGo-W5'
                print("内蔵日本語フォント使用: HeiseiKakuGo-W5 (ゴシック体)")
                return
            except Exception as cid_error:
                print(f"CIDフォントHeiseiKakuGo-W5登録失敗: {cid_error}")
                
            # 2. 別のCIDフォントを試す
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                self.japanese_font = 'HeiseiMin-W3'
                print("内蔵日本語フォント使用: HeiseiMin-W3 (明朝体)")
                return
            except Exception as cid_error:
                print(f"CIDフォントHeiseiMin-W3登録失敗: {cid_error}")
            
            # 3. 外部TTFフォントを試す（フォールバック）
            print("内蔵CIDフォントが使用できないため、外部フォントを探します...")
            
            # macOSの日本語フォントを探す
            font_paths = [
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
                "/Library/Fonts/Arial Unicode MS.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf",
            ]
            
            # まずはmacOSの標準フォントを試す
            for font_path in font_paths:
                if Path(font_path).exists():
                    try:
                        # TrueTypeフォントの場合
                        if font_path.endswith('.ttf'):
                            pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))
                            self.japanese_font = 'JapaneseFont'
                            print(f"TTF日本語フォント登録成功: {font_path}")
                            return
                        # TrueTypeコレクション(.ttc)の場合は最初のフォントを使用
                        elif font_path.endswith('.ttc'):
                            pdfmetrics.registerFont(TTFont('JapaneseFont', font_path, subfontIndex=0))
                            self.japanese_font = 'JapaneseFont'
                            print(f"TTC日本語フォント登録成功: {font_path}")
                            return
                    except Exception as font_error:
                        print(f"フォント登録失敗 {font_path}: {font_error}")
                        continue
            
            # macOSフォントが見つからない場合、追加のmacOSフォントとLinuxの日本語フォントを試す
            additional_font_paths = [
                # macOS追加フォント
                "/System/Library/AssetsV2/com_apple_MobileAsset_Font6/0d58d0348f8e86a29a23e6e9e8d0ecb3ea4d3e23.asset/AssetData/NotoSansCJK-Regular.ttc",
                "/System/Library/Fonts/Supplemental/NotoSansCJK.ttc",
                "/Library/Fonts/NotoSansCJK-Regular.ttc",
                # Linux フォント
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
            
            for font_path in additional_font_paths:
                if Path(font_path).exists():
                    try:
                        if font_path.endswith('.ttf'):
                            pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))
                        elif font_path.endswith('.ttc'):
                            pdfmetrics.registerFont(TTFont('JapaneseFont', font_path, subfontIndex=0))
                        self.japanese_font = 'JapaneseFont'
                        print(f"追加日本語フォント登録成功: {font_path}")
                        return
                    except Exception as font_error:
                        print(f"フォント登録失敗 {font_path}: {font_error}")
                        continue
            
            print(f"使用フォント: {self.japanese_font}")
            
        except Exception as e:
            print(f"日本語フォント設定エラー: {e}")
            self.japanese_font = 'Helvetica'
    
    def _setup_styles(self):
        """PDFスタイルの設定"""
        # タイトルスタイル
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # サブタイトルスタイル
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#374151'),
            spaceBefore=20,
            spaceAfter=15
        ))
        
        # セクションヘッダースタイル
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#4b5563'),
            spaceBefore=15,
            spaceAfter=10
        ))
        
        # 本文スタイル
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#4b5563'),
            alignment=TA_JUSTIFY
        ))
        
        # 日本語用スタイル
        if self.japanese_font != 'Helvetica':
            for style_name in ['CustomTitle', 'CustomSubtitle', 'SectionHeader', 'CustomBody']:
                self.styles[style_name].fontName = self.japanese_font
            print(f"スタイルに日本語フォント適用: {self.japanese_font}")
        else:
            # Helveticaの場合もUTF-8エンコーディングを有効にして可能な限り表示
            print("警告: 専用の日本語フォントが見つかりません。Helveticaで日本語表示を試行します。")
            # UTF-8エンコーディングでの文字描画を有効にする
            try:
                for style_name in ['CustomTitle', 'CustomSubtitle', 'SectionHeader', 'CustomBody']:
                    self.styles[style_name].encoding = 'utf-8'
            except AttributeError:
                # encodingプロパティがない場合はスキップ
                pass
    
    def generate_report(self, analysis_results: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
        """
        分析結果からPDFレポートを生成
        
        Args:
            analysis_results: 分析結果データ
            output_path: 出力ファイルパス（指定しない場合はbytesで返す）
            
        Returns:
            PDFデータ（bytes）
        """
        # 出力先の設定
        if output_path:
            pdf_buffer = output_path
        else:
            pdf_buffer = io.BytesIO()
        
        # PDFドキュメントの作成
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            encoding='utf-8'
        )
        
        # ストーリー（PDFの内容）を構築
        story = []
        
        # タイトルページ
        story.extend(self._create_title_page(analysis_results))
        story.append(PageBreak())
        
        # サマリーセクション
        if 'summary' in analysis_results:
            story.extend(self._create_summary_section(analysis_results['summary']))
            story.append(Spacer(1, 0.3*inch))
        
        # 最終投資判断セクション
        if 'final_decision' in analysis_results:
            story.extend(self._create_decision_section(analysis_results['final_decision']))
            story.append(Spacer(1, 0.3*inch))
        
        # トレーダー計画セクション
        if 'trader_plan' in analysis_results:
            story.extend(self._create_trader_plan_section(analysis_results['trader_plan']))
            story.append(PageBreak())
        
        # 投資計画セクション
        if 'investment_plan' in analysis_results:
            story.extend(self._create_investment_plan_section(analysis_results['investment_plan']))
            story.append(Spacer(1, 0.3*inch))
        
        # 市場分析セクション
        if 'market_analysis' in analysis_results:
            story.extend(self._create_market_analysis_section(analysis_results['market_analysis']))
            story.append(PageBreak())
        
        # ファンダメンタル分析セクション
        if 'fundamental_analysis' in analysis_results:
            story.extend(self._create_fundamental_section(analysis_results['fundamental_analysis']))
            story.append(PageBreak())
        
        # ニュース分析セクション
        if 'news_analysis' in analysis_results:
            story.extend(self._create_news_section(analysis_results['news_analysis']))
            story.append(Spacer(1, 0.3*inch))
        
        # センチメント分析セクション
        if 'sentiment_analysis' in analysis_results:
            story.extend(self._create_sentiment_section(analysis_results['sentiment_analysis']))
        
        # PDFをビルド
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        # バイトデータを返す
        if not output_path:
            pdf_buffer.seek(0)
            return pdf_buffer.read()
        
        return None
    
    def _create_title_page(self, analysis_results: Dict[str, Any]) -> list:
        """タイトルページの作成"""
        story = []
        
        # タイトル
        title = Paragraph(
            "TradingAgents 分析レポート",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # 基本情報テーブル
        ticker = analysis_results.get('ticker', 'N/A')
        analysis_date = analysis_results.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        generation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        info_data = [
            ['ティッカー:', ticker],
            ['分析基準日:', analysis_date],
            ['レポート生成日時:', generation_date],
            ['分析深度:', analysis_results.get('research_depth', 'N/A')],
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.japanese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 1*inch))
        
        # 使用モデル情報
        models_data = [
            ['LLMプロバイダー:', analysis_results.get('llm_provider', 'N/A')],
            ['軽量思考モデル:', analysis_results.get('shallow_model', 'N/A')],
            ['高性能思考モデル:', analysis_results.get('deep_model', 'N/A')],
        ]
        
        models_table = Table(models_data, colWidths=[3*inch, 3*inch])
        models_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.japanese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(models_table)
        
        return story
    
    def _create_summary_section(self, summary: str) -> list:
        """サマリーセクションの作成"""
        story = []
        
        # 日本語文字を安全にエンコード
        title = "📋 サマリー" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Summary"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # サマリーテキストを段落に分割
        paragraphs = summary.split('\n')
        for para in paragraphs:
            if para.strip():
                # 日本語フォントが利用できない場合は英数字のみを保持
                safe_text = self._make_text_safe(para)
                story.append(Paragraph(safe_text, self.styles['CustomBody']))
                story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _make_text_safe(self, text: str) -> str:
        """テキストを安全にPDF用に変換"""
        # CIDフォントまたはTTFフォントがある場合は日本語をそのまま使用
        if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont']:
            return text
        else:
            # Helveticaの場合もUTF-8エンコーディングで適切に処理
            try:
                # UTF-8エンコーディングで文字列を処理
                if isinstance(text, str):
                    return text
                else:
                    return str(text)
            except Exception:
                # 最後の手段としてASCII文字のみを保持
                import re
                safe_text = re.sub(r'[^\x00-\x7F]', '?', str(text))
                return safe_text if safe_text.strip() else "[Japanese content]"
    
    def _create_decision_section(self, decision: str) -> list:
        """最終投資判断セクションの作成"""
        story = []
        
        title = "🎯 最終投資判断" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Final Decision"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # 判断を強調表示
        decision_style = ParagraphStyle(
            name='Decision',
            parent=self.styles['CustomBody'],
            fontSize=14,
            textColor=colors.HexColor('#dc2626'),
            alignment=TA_CENTER,
            fontName=self.japanese_font
        )
        
        safe_decision = self._make_text_safe(decision)
        story.append(Paragraph(safe_decision, decision_style))
        story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_trader_plan_section(self, plan: str) -> list:
        """トレーダー計画セクションの作成"""
        story = []
        
        title = "💼 トレーダー計画" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Trader Plan"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # 計画内容を解析して整形
        lines = plan.split('\n')
        for line in lines:
            if line.strip():
                safe_line = self._make_text_safe(line)
                story.append(Paragraph(safe_line, self.styles['CustomBody']))
                story.append(Spacer(1, 0.05*inch))
        
        return story
    
    def _create_investment_plan_section(self, plan: str) -> list:
        """投資計画セクションの作成"""
        story = []
        
        title = "📈 投資計画" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Investment Plan"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # 投資計画の詳細を整形
        lines = plan.split('\n')
        for line in lines:
            if line.strip():
                safe_line = self._make_text_safe(line)
                story.append(Paragraph(safe_line, self.styles['CustomBody']))
                story.append(Spacer(1, 0.05*inch))
        
        return story
    
    def _create_market_analysis_section(self, analysis: str) -> list:
        """市場分析セクションの作成"""
        story = []
        
        title = "📊 市場分析" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Market Analysis"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # 市場分析の内容を整形
        paragraphs = analysis.split('\n\n')
        for para in paragraphs:
            if para.strip():
                safe_para = self._make_text_safe(para.replace('\n', '<br/>'))
                story.append(Paragraph(safe_para, self.styles['CustomBody']))
                story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_fundamental_section(self, analysis: str) -> list:
        """ファンダメンタル分析セクションの作成"""
        story = []
        
        title = "💰 ファンダメンタル分析" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Fundamental Analysis"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # ファンダメンタル分析の内容を整形
        paragraphs = analysis.split('\n\n')
        for para in paragraphs:
            if para.strip():
                safe_para = self._make_text_safe(para.replace('\n', '<br/>'))
                story.append(Paragraph(safe_para, self.styles['CustomBody']))
                story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_news_section(self, analysis: str) -> list:
        """ニュース分析セクションの作成"""
        story = []
        
        title = "📰 ニュース分析" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "News Analysis"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # ニュース分析の内容を整形
        paragraphs = analysis.split('\n\n')
        for para in paragraphs:
            if para.strip():
                safe_para = self._make_text_safe(para.replace('\n', '<br/>'))
                story.append(Paragraph(safe_para, self.styles['CustomBody']))
                story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _create_sentiment_section(self, analysis: str) -> list:
        """センチメント分析セクションの作成"""
        story = []
        
        title = "💬 センチメント分析" if self.japanese_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'JapaneseFont'] else "Sentiment Analysis"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 0.2*inch))
        
        # センチメント分析の内容を整形
        paragraphs = analysis.split('\n\n')
        for para in paragraphs:
            if para.strip():
                safe_para = self._make_text_safe(para.replace('\n', '<br/>'))
                story.append(Paragraph(safe_para, self.styles['CustomBody']))
                story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _add_header_footer(self, canvas_obj, doc):
        """ヘッダーとフッターの追加"""
        canvas_obj.saveState()
        
        try:
            # ヘッダー
            font_name = self.japanese_font if self.japanese_font != 'Helvetica' else 'Helvetica'
            canvas_obj.setFont(font_name, 9)
            canvas_obj.setFillColor(colors.HexColor('#9ca3af'))
            
            # ASCII文字のみを使用（文字化け回避）
            canvas_obj.drawString(inch, self.page_size[1] - 0.5*inch, "TradingAgents Analysis Report")
            canvas_obj.drawRightString(self.page_size[0] - inch, self.page_size[1] - 0.5*inch, 
                                      datetime.now().strftime('%Y-%m-%d'))
            
            # フッター
            canvas_obj.drawString(inch, 0.5*inch, "Generated by TradingAgents")
            page_num = canvas_obj.getPageNumber()
            canvas_obj.drawRightString(self.page_size[0] - inch, 0.5*inch, f"Page {page_num}")
            
        except Exception as e:
            print(f"ヘッダー・フッター描画エラー: {e}")
            # フォールバック: 基本フォントを使用
            canvas_obj.setFont('Helvetica', 9)
            canvas_obj.drawString(inch, self.page_size[1] - 0.5*inch, "TradingAgents Report")
            canvas_obj.drawRightString(self.page_size[0] - inch, 0.5*inch, f"Page {canvas_obj.getPageNumber()}")
        
        canvas_obj.restoreState()