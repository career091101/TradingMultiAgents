"""
PDF レポート生成モジュール（改善版）
読みやすさを大幅に向上させたバージョン
"""

from datetime import datetime
from pathlib import Path
import tempfile
from typing import Dict, Any, Optional, List, Tuple
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
    HRFlowable,
    FrameBreak,
    Indenter,
    ListFlowable,
    ListItem,
    CondPageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultEncoding
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.validators import Auto
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.widgets.markers import makeMarker


class ColorScheme:
    """統一されたカラースキーム"""
    # メインカラー
    PRIMARY = colors.HexColor('#1e40af')      # 濃青
    SECONDARY = colors.HexColor('#059669')    # 緑
    WARNING = colors.HexColor('#dc2626')      # 赤
    CAUTION = colors.HexColor('#f59e0b')      # 橙
    NEUTRAL = colors.HexColor('#6b7280')      # 灰
    
    # 背景色
    BG_SECTION = colors.HexColor('#f3f4f6')   # セクション背景
    BG_HIGHLIGHT = colors.HexColor('#fef3c7') # ハイライト
    BG_TABLE_EVEN = colors.HexColor('#f9fafb') # テーブル偶数行
    
    # テキスト色
    TEXT_PRIMARY = colors.HexColor('#111827')   # 主要テキスト
    TEXT_SECONDARY = colors.HexColor('#374151') # 副次テキスト
    TEXT_MUTED = colors.HexColor('#6b7280')     # 薄いテキスト
    
    # その他
    BORDER = colors.HexColor('#e5e7eb')        # 境界線
    SUCCESS = colors.HexColor('#10b981')       # 成功
    INFO = colors.HexColor('#3b82f6')          # 情報


class ImprovedPDFReportGenerator:
    """TradingAgents分析レポートのPDF生成クラス（改善版）"""
    
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self.colors = ColorScheme()
        self._setup_japanese_font()
        self._setup_styles()
        self.toc = TableOfContents()
        self.toc_entries = []  # 目次エントリを保存
        self.current_page = 1
        
    def _setup_japanese_font(self):
        """日本語フォントの設定（改善版）"""
        self.japanese_font = 'Helvetica'
        self.japanese_font_bold = 'Helvetica-Bold'
        
        try:
            # CIDフォントを試す
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                self.japanese_font = 'HeiseiKakuGo-W5'      # ゴシック
                self.japanese_font_bold = 'HeiseiKakuGo-W5' # ゴシック太字の代替
                self.japanese_font_mincho = 'HeiseiMin-W3'  # 明朝
                print("内蔵日本語フォント使用: HeiseiKakuGo-W5 (ゴシック), HeiseiMin-W3 (明朝)")
                return
            except Exception as e:
                print(f"CIDフォント登録失敗: {e}")
            
            # TTFフォントを探す
            font_paths = [
                ("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 0),
                ("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", 0),
                ("/System/Library/Fonts/ヒラギノ明朝 ProN.ttc", 0),
                ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
                ("/Library/Fonts/Arial Unicode MS.ttf", None),
            ]
            
            for font_path, index in font_paths:
                if Path(font_path).exists():
                    try:
                        if index is not None:
                            pdfmetrics.registerFont(TTFont('JapaneseGothic', font_path, subfontIndex=index))
                            self.japanese_font = 'JapaneseGothic'
                        else:
                            pdfmetrics.registerFont(TTFont('JapaneseGothic', font_path))
                            self.japanese_font = 'JapaneseGothic'
                        
                        # 太字フォントも登録
                        if "W6" in font_path or "Bold" in font_path:
                            self.japanese_font_bold = self.japanese_font
                        else:
                            self.japanese_font_bold = self.japanese_font
                            
                        print(f"日本語フォント登録成功: {font_path}")
                        return
                    except Exception as e:
                        print(f"フォント登録失敗 {font_path}: {e}")
                        
        except Exception as e:
            print(f"フォント設定エラー: {e}")
    
    def _setup_styles(self):
        """スタイルの設定（改善版）"""
        # タイトルスタイル（32pt）
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=32,
            leading=40,
            textColor=self.colors.TEXT_PRIMARY,
            spaceAfter=36,
            alignment=TA_CENTER,
            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
        ))
        
        # サブタイトルスタイル（22pt）
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            leading=28,
            textColor=self.colors.TEXT_PRIMARY,
            spaceBefore=24,
            spaceAfter=18,
            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
        ))
        
        # セクションヘッダースタイル（16pt）
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            leading=20,
            textColor=self.colors.PRIMARY,
            spaceBefore=18,
            spaceAfter=12,
            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
        ))
        
        # サブセクションヘッダー（14pt）
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            leading=18,
            textColor=self.colors.TEXT_SECONDARY,
            spaceBefore=12,
            spaceAfter=8,
            fontName=self.japanese_font
        ))
        
        # 本文スタイル（11pt）
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=16,  # 1.45倍
            textColor=self.colors.TEXT_SECONDARY,
            alignment=TA_JUSTIFY,
            fontName=self.japanese_font
        ))
        
        # キャプションスタイル（9pt）
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['BodyText'],
            fontSize=9,
            leading=12,
            textColor=self.colors.TEXT_MUTED,
            alignment=TA_CENTER,
            fontName=self.japanese_font
        ))
        
        # 強調スタイル
        self.styles.add(ParagraphStyle(
            name='Emphasis',
            parent=self.styles['CustomBody'],
            textColor=self.colors.PRIMARY,
            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
        ))
        
        # 引用スタイル
        self.styles.add(ParagraphStyle(
            name='Quote',
            parent=self.styles['CustomBody'],
            leftIndent=24,
            rightIndent=24,
            textColor=self.colors.TEXT_MUTED,
            fontName=self.japanese_font,
            borderColor=self.colors.BORDER,
            borderWidth=1,
            borderPadding=8,
            backColor=self.colors.BG_HIGHLIGHT
        ))
        
        # リストアイテムスタイル
        self.styles.add(ParagraphStyle(
            name='ListItem',
            parent=self.styles['CustomBody'],
            leftIndent=20,
            bulletIndent=10,
            fontName=self.japanese_font
        ))
    
    def _create_info_box(self, content: str, box_type: str = "info", title: str = None) -> List:
        """情報ボックスの作成"""
        # ボックスタイプ別の色設定
        box_colors = {
            "info": (self.colors.INFO, self.colors.BG_SECTION),
            "warning": (self.colors.WARNING, colors.HexColor('#fee2e2')),
            "success": (self.colors.SUCCESS, colors.HexColor('#d1fae5')),
            "caution": (self.colors.CAUTION, colors.HexColor('#fef3c7'))
        }
        
        border_color, bg_color = box_colors.get(box_type, box_colors["info"])
        
        # ボックスコンテンツ
        box_content = []
        
        if title:
            title_style = ParagraphStyle(
                name='BoxTitle',
                parent=self.styles['SubsectionHeader'],
                textColor=border_color,
                fontSize=12,
                leading=16,
                fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
            )
            box_content.append(Paragraph(title, title_style))
            box_content.append(Spacer(1, 0.1*inch))
        
        content_style = ParagraphStyle(
            name='BoxContent',
            parent=self.styles['CustomBody'],
            fontSize=10,
            leading=14,
            fontName=self.japanese_font
        )
        box_content.append(Paragraph(content, content_style))
        
        # テーブルでボックスを作成
        box_table = Table([box_content], colWidths=[self.page_size[0] - 180])
        box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BORDER', (0, 0), (-1, -1), 2, border_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return [box_table, Spacer(1, 0.2*inch)]
    
    def _create_enhanced_table(self, data: List[List], headers: List[str] = None, 
                             col_widths: List[float] = None, highlight_rows: List[int] = None) -> Table:
        """改善されたテーブルデザイン"""
        # ヘッダーがある場合は追加
        if headers:
            data = [headers] + data
        
        # カラム幅の自動計算
        if not col_widths:
            num_cols = len(data[0]) if data else 1
            available_width = self.page_size[0] - 180  # マージンを考慮
            col_widths = [available_width / num_cols] * num_cols
        
        table = Table(data, colWidths=col_widths)
        
        # 基本スタイル
        style = [
            ('FONTNAME', (0, 0), (-1, -1), self.japanese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEADING', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors.BORDER),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        # ヘッダー行のスタイル
        if headers:
            style.extend([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors.PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ])
        
        # 交互背景色（ゼブラストライプ）
        start_row = 1 if headers else 0
        for i in range(start_row, len(data)):
            if (i - start_row) % 2 == 1:
                style.append(('BACKGROUND', (0, i), (-1, i), self.colors.BG_TABLE_EVEN))
        
        # ハイライト行
        if highlight_rows:
            for row in highlight_rows:
                style.append(('BACKGROUND', (0, row), (-1, row), self.colors.BG_HIGHLIGHT))
        
        table.setStyle(TableStyle(style))
        return table
    
    def _add_to_toc(self, text: str, level: int = 0):
        """目次にエントリを追加"""
        self.toc_entries.append({
            'text': text,
            'level': level,
            'page': self.current_page
        })
    
    def _create_table_of_contents(self) -> List:
        """目次ページの作成"""
        story = []
        
        # 目次タイトル
        story.append(Paragraph("目次", self.styles['CustomTitle']))
        story.append(HRFlowable(width="100%", thickness=2, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.5*inch))
        
        # 目次エントリ
        for entry in self.toc_entries:
            indent = entry['level'] * 20
            
            # ドットリーダーとページ番号を含むエントリ
            text = entry['text']
            page = entry['page']
            
            # レベルに応じたスタイル
            if entry['level'] == 0:
                style = ParagraphStyle(
                    name='TOCLevel0',
                    parent=self.styles['CustomBody'],
                    fontSize=12,
                    leading=18,
                    textColor=self.colors.PRIMARY,
                    fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font,
                    leftIndent=indent
                )
            else:
                style = ParagraphStyle(
                    name=f'TOCLevel{entry["level"]}',
                    parent=self.styles['CustomBody'],
                    fontSize=11,
                    leading=16,
                    textColor=self.colors.TEXT_SECONDARY,
                    fontName=self.japanese_font,
                    leftIndent=indent
                )
            
            # ドットリーダーを含むフォーマット
            dots = '.' * (80 - len(text) - len(str(page)) - entry['level'] * 4)
            toc_line = f"{text} {dots} {page}"
            
            story.append(Paragraph(toc_line, style))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(PageBreak())
        return story
    
    def _add_header_footer(self, canvas_obj, doc):
        """ヘッダーとフッターの追加（改善版）"""
        canvas_obj.saveState()
        
        # ヘッダー
        # 左上: ドキュメントタイトル
        canvas_obj.setFont(self.japanese_font, 9)
        canvas_obj.setFillColor(self.colors.TEXT_MUTED)
        canvas_obj.drawString(90, self.page_size[1] - 50, "TradingAgents 分析レポート")
        
        # 右上: 生成日時
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        canvas_obj.drawRightString(self.page_size[0] - 90, self.page_size[1] - 50, now)
        
        # ヘッダーライン
        canvas_obj.setStrokeColor(self.colors.BORDER)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(90, self.page_size[1] - 60, self.page_size[0] - 90, self.page_size[1] - 60)
        
        # フッター
        # 中央下: ページ番号
        canvas_obj.setFont(self.japanese_font, 10)
        canvas_obj.drawCentredString(self.page_size[0] / 2, 50, f"- {self.current_page} -")
        
        # フッターライン
        canvas_obj.line(90, 70, self.page_size[0] - 90, 70)
        
        self.current_page += 1
        canvas_obj.restoreState()
    
    def _create_executive_summary(self, analysis_results: Dict[str, Any]) -> List:
        """エグゼクティブサマリーの作成"""
        story = []
        
        # タイトル
        story.append(Paragraph("エグゼクティブサマリー", self.styles['CustomTitle']))
        story.append(HRFlowable(width="100%", thickness=2, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # 主要情報を4象限で表示
        summary_data = []
        
        # 投資判断
        decision = analysis_results.get('final_decision', 'N/A')
        decision_color = self.colors.SUCCESS if decision == 'BUY' else self.colors.WARNING if decision == 'SELL' else self.colors.NEUTRAL
        
        summary_data.append([
            self._create_summary_box("投資判断", decision, decision_color),
            self._create_summary_box("信頼度", "85%", self.colors.INFO)
        ])
        
        summary_data.append([
            self._create_summary_box("目標株価", "$195", self.colors.SECONDARY),
            self._create_summary_box("リスクレベル", "中", self.colors.CAUTION)
        ])
        
        summary_table = Table(summary_data, colWidths=[(self.page_size[0] - 180) / 2] * 2)
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 主要ポイント
        if analysis_results.get('summary'):
            story.extend(self._create_info_box(
                analysis_results['summary'],
                "info",
                "分析サマリー"
            ))
        
        story.append(PageBreak())
        return story
    
    def _create_summary_box(self, label: str, value: str, color: colors.Color) -> Table:
        """サマリーボックスの作成"""
        data = [
            [Paragraph(label, ParagraphStyle(
                name='SummaryLabel',
                parent=self.styles['Caption'],
                fontSize=10,
                textColor=self.colors.TEXT_MUTED,
                fontName=self.japanese_font
            ))],
            [Paragraph(value, ParagraphStyle(
                name='SummaryValue',
                parent=self.styles['CustomSubtitle'],
                fontSize=24,
                textColor=color,
                alignment=TA_CENTER,
                fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
            ))]
        ]
        
        box = Table(data, colWidths=[(self.page_size[0] - 200) / 4])
        box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BORDER', (0, 0), (-1, -1), 1, self.colors.BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return box
    
    def _make_text_safe(self, text: str) -> str:
        """テキストを安全な形式に変換"""
        if not text:
            return ""
        
        # XML特殊文字のエスケープ
        text = str(text).replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        return text
    
    def generate_report(self, analysis_results: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
        """
        分析結果からPDFレポートを生成（改善版）
        """
        # 出力先の設定
        if output_path:
            pdf_buffer = output_path
        else:
            pdf_buffer = io.BytesIO()
        
        # PDFドキュメントの作成（マージン拡大）
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=self.page_size,
            rightMargin=85,
            leftMargin=85,
            topMargin=90,
            bottomMargin=90,
            encoding='utf-8'
        )
        
        # ストーリー（PDFの内容）を構築
        story = []
        self.current_page = 1
        self.toc_entries = []
        
        # タイトルページ
        self._add_to_toc("表紙", 0)
        story.extend(self._create_title_page(analysis_results))
        story.append(PageBreak())
        
        # エグゼクティブサマリー
        self._add_to_toc("エグゼクティブサマリー", 0)
        story.extend(self._create_executive_summary(analysis_results))
        
        # 目次ページ（後で挿入するためのプレースホルダー）
        toc_placeholder = Spacer(1, 1)
        story.append(toc_placeholder)
        
        # メインコンテンツ
        self._add_to_toc("分析結果詳細", 0)
        
        # 最終投資判断セクション
        if 'final_decision' in analysis_results:
            self._add_to_toc("最終投資判断", 1)
            story.extend(self._create_decision_section(analysis_results['final_decision']))
            story.append(Spacer(1, 0.4*inch))
        
        # トレーダー計画セクション
        if 'trader_plan' in analysis_results:
            self._add_to_toc("トレーディング戦略", 1)
            story.extend(self._create_trader_plan_section(analysis_results['trader_plan']))
            story.append(PageBreak())
        
        # 市場分析セクション
        if 'market_analysis' in analysis_results:
            self._add_to_toc("市場分析", 1)
            story.extend(self._create_market_analysis_section(analysis_results['market_analysis']))
            story.append(PageBreak())
        
        # ファンダメンタル分析セクション
        if 'fundamental_analysis' in analysis_results:
            self._add_to_toc("ファンダメンタル分析", 1)
            story.extend(self._create_fundamental_section(analysis_results['fundamental_analysis']))
            story.append(PageBreak())
        
        # 議論記録セクション
        if 'debate_transcript' in analysis_results and analysis_results['debate_transcript']:
            self._add_to_toc("投資戦略議論", 1)
            story.extend(self._create_debate_transcript_section(analysis_results['debate_transcript']))
            story.append(PageBreak())
        
        # リスク管理議論セクション
        if 'risk_discussion' in analysis_results and analysis_results['risk_discussion']:
            self._add_to_toc("リスク管理議論", 1)
            story.extend(self._create_risk_discussion_section(analysis_results['risk_discussion']))
            story.append(PageBreak())
        
        # 主要指標サマリーセクション
        if 'key_metrics' in analysis_results and analysis_results['key_metrics']:
            self._add_to_toc("主要指標サマリー", 1)
            story.extend(self._create_key_metrics_section(analysis_results['key_metrics']))
            story.append(PageBreak())
        
        # アクション項目セクション
        if 'action_items' in analysis_results and analysis_results['action_items']:
            self._add_to_toc("推奨アクション", 1)
            story.extend(self._create_action_items_section(analysis_results['action_items']))
        
        # PDFをビルド
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        # バイトデータを返す
        if not output_path:
            pdf_buffer.seek(0)
            return pdf_buffer.read()
        
        return None
    
    def _create_title_page(self, analysis_results: Dict[str, Any]) -> list:
        """タイトルページの作成（改善版）"""
        story = []
        
        # スペーサー
        story.append(Spacer(1, 2*inch))
        
        # メインタイトル
        title = f"TradingAgents 投資分析レポート"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        
        # 銘柄名
        ticker = analysis_results.get('ticker', 'N/A')
        subtitle = f"<font size='28'>{ticker}</font>"
        subtitle_style = ParagraphStyle(
            name='TickerTitle',
            parent=self.styles['CustomSubtitle'],
            fontSize=28,
            textColor=self.colors.PRIMARY,
            alignment=TA_CENTER,
            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
        )
        story.append(Paragraph(subtitle, subtitle_style))
        
        story.append(Spacer(1, 1*inch))
        
        # 分析日
        analysis_date = analysis_results.get('analysis_date', 'N/A')
        date_text = f"分析日: {analysis_date}"
        story.append(Paragraph(date_text, self.styles['CustomBody']))
        
        # 分析パラメータ
        params = []
        params.append(f"リサーチ深度: {analysis_results.get('research_depth', 'N/A')}")
        params.append(f"LLMプロバイダー: {analysis_results.get('llm_provider', 'N/A')}")
        params.append(f"モデル: {analysis_results.get('deep_model', 'N/A')}")
        
        for param in params:
            story.append(Paragraph(param, self.styles['Caption']))
            story.append(Spacer(1, 0.1*inch))
        
        # 生成日時
        story.append(Spacer(1, 2*inch))
        generated_at = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        story.append(Paragraph(f"レポート生成日時: {generated_at}", self.styles['Caption']))
        
        return story
    
    # 以下、各セクション作成メソッドも改善版として実装
    # （既存のメソッドを改善したバージョンを含む）
    
    def _create_decision_section(self, decision: str) -> list:
        """最終投資判断セクションの作成（改善版）"""
        story = []
        
        title = "📊 最終投資判断"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # 判断に応じた色とアイコン
        if decision.upper() == "BUY":
            box_type = "success"
            icon = "🟢"
        elif decision.upper() == "SELL":
            box_type = "warning"
            icon = "🔴"
        else:
            box_type = "info"
            icon = "🟡"
        
        decision_text = f"{icon} 推奨アクション: {decision.upper()}"
        story.extend(self._create_info_box(decision_text, box_type))
        
        return story
    
    def _create_trader_plan_section(self, plan: str) -> list:
        """トレーダー計画セクションの作成（改善版）"""
        story = []
        
        title = "📈 トレーディング戦略"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # 計画内容を整形
        lines = plan.split('\n')
        for line in lines:
            if line.strip():
                if line.startswith('#'):
                    # ヘッダー行
                    header_text = line.replace('#', '').strip()
                    story.append(Paragraph(header_text, self.styles['SectionHeader']))
                    story.append(Spacer(1, 0.1*inch))
                elif ':' in line:
                    # キー・バリューペア
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        # 重要な数値は強調
                        if any(keyword in key.lower() for keyword in ['entry', 'stop', 'target', 'risk']):
                            formatted_line = f"<b>{key}:</b> <font color='{self.colors.PRIMARY.hexval()}'>{value}</font>"
                        else:
                            formatted_line = f"<b>{key}:</b> {value}"
                        
                        story.append(Paragraph(formatted_line, self.styles['CustomBody']))
                        story.append(Spacer(1, 0.05*inch))
                else:
                    # 通常のテキスト
                    story.append(Paragraph(line, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.05*inch))
        
        return story
    
    def _create_market_analysis_section(self, analysis: str) -> list:
        """市場分析セクションの作成（改善版）"""
        story = []
        
        title = "📊 市場分析"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # セクションごとに処理
        sections = analysis.split('\n\n')
        for section in sections:
            if section.strip():
                lines = section.split('\n')
                
                if lines and lines[0].startswith('#'):
                    # セクションヘッダー
                    header = lines[0].replace('#', '').strip()
                    story.append(Paragraph(header, self.styles['SectionHeader']))
                    story.append(Spacer(1, 0.2*inch))
                    
                    # セクション内容
                    content_lines = lines[1:]
                    for line in content_lines:
                        if line.strip():
                            if line.strip().startswith('-'):
                                # リスト項目
                                item_text = line.strip()[1:].strip()
                                story.append(Paragraph(f"• {item_text}", self.styles['ListItem']))
                                story.append(Spacer(1, 0.05*inch))
                            else:
                                story.append(Paragraph(line, self.styles['CustomBody']))
                                story.append(Spacer(1, 0.1*inch))
                else:
                    # 通常のパラグラフ
                    for line in lines:
                        if line.strip():
                            story.append(Paragraph(line, self.styles['CustomBody']))
                            story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_fundamental_section(self, analysis: str) -> list:
        """ファンダメンタル分析セクションの作成（改善版）"""
        story = []
        
        title = "💰 ファンダメンタル分析"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # 財務指標をテーブル形式で表示できるよう解析
        lines = analysis.split('\n')
        current_section = None
        metrics_data = []
        
        for line in lines:
            if line.strip():
                if line.startswith('#'):
                    # 新しいセクション
                    if metrics_data and current_section:
                        # 前のセクションのデータをテーブル化
                        story.extend(self._create_metrics_table(metrics_data, current_section))
                        metrics_data = []
                    
                    current_section = line.replace('#', '').strip()
                    story.append(Paragraph(current_section, self.styles['SectionHeader']))
                    story.append(Spacer(1, 0.2*inch))
                
                elif ':' in line and line.startswith('-'):
                    # メトリクス項目
                    parts = line[1:].strip().split(':', 1)
                    if len(parts) == 2:
                        metric = parts[0].strip()
                        value = parts[1].strip()
                        metrics_data.append([metric, value])
                
                else:
                    # 通常のテキスト
                    story.append(Paragraph(line, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))
        
        # 最後のセクションのデータを処理
        if metrics_data and current_section:
            story.extend(self._create_metrics_table(metrics_data, current_section))
        
        return story
    
    def _create_metrics_table(self, data: List[List[str]], title: str = None) -> List:
        """メトリクステーブルの作成"""
        story = []
        
        if data:
            # テーブル作成
            table = self._create_enhanced_table(
                data,
                headers=["指標", "値"],
                col_widths=[(self.page_size[0] - 170) * 0.6, (self.page_size[0] - 170) * 0.4]
            )
            story.append(table)
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_debate_transcript_section(self, transcript: str) -> list:
        """議論記録セクションの作成（改善版）"""
        story = []
        
        title = "🗣️ 投資戦略議論"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # 議論の説明
        intro = "Bull ResearcherとBear Researcherによる投資戦略の議論記録です。"
        story.extend(self._create_info_box(intro, "info"))
        story.append(Spacer(1, 0.2*inch))
        
        # 議論内容を解析
        lines = transcript.split('\n')
        
        for line in lines:
            if line.strip():
                if line.startswith('**') and line.endswith('**'):
                    # 発言者
                    speaker = line.strip('*').replace(':', '')
                    
                    # 発言者に応じた色
                    if 'Bull' in speaker:
                        speaker_style = ParagraphStyle(
                            name='BullSpeaker',
                            parent=self.styles['SubsectionHeader'],
                            textColor=self.colors.SUCCESS,
                            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
                        )
                    elif 'Bear' in speaker:
                        speaker_style = ParagraphStyle(
                            name='BearSpeaker',
                            parent=self.styles['SubsectionHeader'],
                            textColor=self.colors.WARNING,
                            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
                        )
                    else:
                        speaker_style = ParagraphStyle(
                            name='ManagerSpeaker',
                            parent=self.styles['SubsectionHeader'],
                            textColor=self.colors.INFO,
                            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
                        )
                    
                    story.append(Paragraph(speaker, speaker_style))
                    story.append(Spacer(1, 0.1*inch))
                else:
                    # 発言内容
                    content_style = ParagraphStyle(
                        name='DebateContent',
                        parent=self.styles['CustomBody'],
                        leftIndent=20,
                        borderColor=self.colors.BORDER,
                        borderWidth=0,
                        borderLeftWidth=3,
                        borderPadding=8,
                        fontName=self.japanese_font
                    )
                    story.append(Paragraph(line, content_style))
                    story.append(Spacer(1, 0.15*inch))
        
        return story
    
    def _create_risk_discussion_section(self, discussion: str) -> list:
        """リスク管理議論セクションの作成（改善版）"""
        story = []
        
        title = "⚠️ リスク管理議論"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # リスク議論の説明
        intro = "アグレッシブ、コンサバティブ、ニュートラルの各アナリストによるリスク評価です。"
        story.extend(self._create_info_box(intro, "caution"))
        story.append(Spacer(1, 0.2*inch))
        
        # 議論内容を解析
        lines = discussion.split('\n')
        
        for line in lines:
            if line.strip():
                if line.startswith('**') and line.endswith('**'):
                    # アナリストタイプ
                    analyst = line.strip('*').replace(':', '')
                    
                    # アナリストタイプに応じた色とアイコン
                    if 'Aggressive' in analyst:
                        analyst_style = ParagraphStyle(
                            name='AggressiveAnalyst',
                            parent=self.styles['SubsectionHeader'],
                            textColor=self.colors.WARNING,
                            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
                        )
                        icon = "🔥"
                    elif 'Conservative' in analyst:
                        analyst_style = ParagraphStyle(
                            name='ConservativeAnalyst',
                            parent=self.styles['SubsectionHeader'],
                            textColor=self.colors.INFO,
                            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
                        )
                        icon = "🛡️"
                    else:
                        analyst_style = ParagraphStyle(
                            name='NeutralAnalyst',
                            parent=self.styles['SubsectionHeader'],
                            textColor=self.colors.NEUTRAL,
                            fontName=self.japanese_font_bold if hasattr(self, 'japanese_font_bold') else self.japanese_font
                        )
                        icon = "⚖️"
                    
                    story.append(Paragraph(f"{icon} {analyst}", analyst_style))
                    story.append(Spacer(1, 0.1*inch))
                else:
                    # 分析内容
                    story.append(Paragraph(line, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.15*inch))
        
        return story
    
    def _create_key_metrics_section(self, metrics: str) -> list:
        """主要指標サマリーセクションの作成（改善版）"""
        story = []
        
        title = "📊 主要指標サマリー"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # メトリクスを解析してテーブル化
        lines = metrics.split('\n')
        current_table_data = []
        current_headers = []
        
        for line in lines:
            if line.strip():
                if line.startswith('|'):
                    # テーブル行
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    
                    if all('-' in cell for cell in cells):
                        # セパレータ行はスキップ
                        continue
                    elif not current_headers:
                        # ヘッダー行
                        current_headers = cells
                    else:
                        # データ行
                        current_table_data.append(cells)
                
                elif current_table_data:
                    # テーブルが終了したので描画
                    table = self._create_enhanced_table(
                        current_table_data,
                        headers=current_headers
                    )
                    story.append(table)
                    story.append(Spacer(1, 0.3*inch))
                    current_table_data = []
                    current_headers = []
                
                if line.startswith('#'):
                    # セクションヘッダー
                    header = line.replace('#', '').strip()
                    story.append(Paragraph(header, self.styles['SectionHeader']))
                    story.append(Spacer(1, 0.2*inch))
                elif not line.startswith('|') and line.strip():
                    # 通常のテキスト
                    story.append(Paragraph(line, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))
        
        # 最後のテーブルがあれば描画
        if current_table_data:
            table = self._create_enhanced_table(
                current_table_data,
                headers=current_headers
            )
            story.append(table)
            story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_action_items_section(self, action_items: str) -> list:
        """アクション項目セクションの作成（改善版）"""
        story = []
        
        title = "✅ 推奨アクション"
        story.append(Paragraph(title, self.styles['CustomSubtitle']))
        story.append(HRFlowable(width="100%", thickness=1, color=self.colors.PRIMARY))
        story.append(Spacer(1, 0.3*inch))
        
        # アクション項目を優先度別に整理
        high_priority = []
        medium_priority = []
        low_priority = []
        
        sections = action_items.split('\n\n')
        current_priority = None
        
        for section in sections:
            if section.strip():
                lines = section.split('\n')
                
                if lines and lines[0].startswith('#'):
                    # 優先度セクション
                    header = lines[0].replace('#', '').strip()
                    if 'High' in header or '高' in header:
                        current_priority = 'high'
                    elif 'Medium' in header or '中' in header:
                        current_priority = 'medium'
                    elif 'Low' in header or '低' in header:
                        current_priority = 'low'
                    
                    # セクション内のアイテムを収集
                    for line in lines[1:]:
                        if line.strip() and line.strip()[0].isdigit():
                            # アクション項目
                            if current_priority == 'high':
                                high_priority.append(line.strip())
                            elif current_priority == 'medium':
                                medium_priority.append(line.strip())
                            elif current_priority == 'low':
                                low_priority.append(line.strip())
        
        # 優先度別に表示
        if high_priority:
            story.extend(self._create_priority_box("高優先度", high_priority, "warning"))
        
        if medium_priority:
            story.extend(self._create_priority_box("中優先度", medium_priority, "caution"))
        
        if low_priority:
            story.extend(self._create_priority_box("低優先度", low_priority, "info"))
        
        return story
    
    def _create_priority_box(self, title: str, items: List[str], box_type: str) -> List:
        """優先度別アクションボックスの作成"""
        story = []
        
        # ボックスタイトル
        story.append(Paragraph(title, self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        # アイテムリスト
        list_items = []
        for item in items:
            # チェックボックス風の表示
            item_text = f"☐ {item}"
            list_items.append(ListItem(
                Paragraph(item_text, self.styles['ListItem']),
                leftIndent=20,
                bulletColor=self.colors.PRIMARY
            ))
        
        # リストをボックス内に配置
        content = ListFlowable(list_items, bulletType='bullet')
        story.extend(self._create_info_box("", box_type))
        story[-2] = content  # ボックス内にリストを配置
        story.append(Spacer(1, 0.3*inch))
        
        return story