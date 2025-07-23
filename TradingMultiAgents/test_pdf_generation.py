#!/usr/bin/env python3
"""
Test PDF generation with all sections implemented
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from webui.utils.pdf_generator import PDFReportGenerator

def test_pdf_generation():
    """Test PDF generation with sample data"""
    
    # Create PDF generator
    pdf_gen = PDFReportGenerator()
    
    # Sample data with all sections in the expected format
    sample_data = {
        "ticker": "AAPL",
        "analysis_date": "2025-07-17",
        "research_depth": 3,
        "llm_provider": "openai",
        "shallow_model": "gpt-4o-mini",
        "deep_model": "o4-mini-2025-04-16",
        
        # Summary
        "summary": """最終投資判断: BUY
信頼度: 85%

主要ポジティブ要因:
1. 強力なファンダメンタルズ（FCF $95B）
2. AI機能による製品差別化
3. サービス収益の二桁成長
4. 技術的ブレイクアウトパターン
5. ポジティブな市場センチメント

主要リスク要因:
1. バリュエーションの高さ（P/E 28.5）
2. マクロ経済の逆風
3. 中国市場の規制リスク
4. 金利上昇圧力
5. 競争激化""",
        
        # Decision and plans
        "final_decision": "BUY",
        "trader_plan": """# Trading Strategy
## Position: LONG
### Entry: $185
### Stop Loss: $180
### Take Profit: $195
### Risk/Reward: 1:2""",
        
        "investment_plan": """# Investment Recommendation
## Recommendation: BUY
### Rationale
- Strong fundamentals
- Positive market sentiment
- Technical breakout pattern
### Target Price: $195""",
        
        "market_analysis": """# Market Analysis Report
## Stock: AAPL
### Key Findings
- Strong upward trend in the past quarter
- Technical indicators showing bullish signals
- RSI at 65, indicating moderate momentum
### Market Conditions
- Overall market sentiment is positive
- Technology sector outperforming""",
        
        "fundamental_analysis": """# Fundamental Analysis
## Financial Metrics
- P/E Ratio: 28.5
- EPS Growth: 12% YoY
- Revenue: $385B (up 8%)
- Free Cash Flow: $95B""",
        
        "news_analysis": """# News Analysis
## Recent Headlines
1. Apple announces new AI features
2. Strong iPhone sales in China
3. Services revenue hits record high""",
        
        "sentiment_analysis": """# Sentiment Analysis
## Social Media Sentiment: Positive
- Twitter mentions up 45% this week
- Reddit discussions largely bullish
- Analyst upgrades from 3 major firms""",
        
        # Additional detailed sections
        "debate_transcript": """# Bull vs Bear Debate

**Bull Researcher**: The fundamentals are extremely strong. Apple's services revenue continues to grow at double digits, and the new AI features will drive iPhone upgrade cycles.

**Bear Researcher**: While I acknowledge the strong fundamentals, the valuation is stretched at current levels. A P/E of 28.5 is high even for Apple.

**Bull Researcher**: But consider the free cash flow generation - $95B annually! The company can easily support this valuation through buybacks and dividends.

**Bear Researcher**: True, but we're also facing macroeconomic headwinds. Interest rates remain elevated, which could pressure valuations across tech.

**Research Manager**: Both perspectives have merit. The consensus leans bullish given the strong cash flows and product pipeline, but we should monitor valuation metrics closely.""",
            
            "risk_discussion": """# Risk Management Discussion

**Conservative Analyst**: We need to consider the concentration risk. Apple represents a significant portion of the S&P 500, and any disappointment could have market-wide implications.

**Aggressive Analyst**: The risk is overblown. Apple has proven resilient through multiple cycles. The ecosystem lock-in provides a competitive moat.

**Neutral Analyst**: I see both sides. While Apple has defensive qualities, the current valuation does leave limited margin for error. A position size of 3-5% of portfolio seems prudent.

**Risk Manager**: Agreed on position sizing. Also recommend setting stop losses at $180 to protect downside while allowing for normal volatility.""",
        
        "key_metrics": """# Key Performance Metrics

| Metric | Value | Industry Avg | Rating |
|--------|--------|--------------|---------|
| P/E Ratio | 28.5 | 22.3 | Above Average |
| ROE | 147% | 25% | Exceptional |
| Debt/Equity | 1.95 | 0.85 | High |
| Gross Margin | 43.3% | 35.2% | Strong |
| Revenue Growth | 8% | 5% | Good |
| EPS Growth | 12% | 7% | Strong |

## Technical Indicators
- RSI (14): 65
- MACD: Bullish crossover
- 50-day MA: $182
- 200-day MA: $175
- Support: $180
- Resistance: $190""",
        
        "action_items": """# Action Items & Next Steps

## High Priority
1. **Execute Buy Order**: Place limit order for 100 shares at $185 or better
2. **Set Risk Parameters**: Configure stop loss at $180 and take profit at $195
3. **Monitor Earnings**: Q2 earnings release on July 25th - prepare for volatility

## Medium Priority
4. **Sector Analysis**: Review technology sector allocation - currently at 35% of portfolio
5. **Hedging Strategy**: Consider buying protective puts if position exceeds 5% of portfolio
6. **News Monitoring**: Set alerts for Apple regulatory news, particularly in EU and China

## Low Priority
7. **Long-term Planning**: Research Apple's AI roadmap for investment thesis update
8. **Dividend Tracking**: Note ex-dividend date (August 5th) for income planning
9. **Peer Comparison**: Analyze relative performance vs. MSFT, GOOGL for sector rotation"""
    }
    
    # Generate PDF
    try:
        # Specify output path
        output_path = "test_analysis_report.pdf"
        pdf_gen.generate_report(sample_data, output_path)
        print(f"✅ PDF generated successfully: {output_path}")
        
        # Check file size to ensure content was written
        file_size = Path(output_path).stat().st_size
        print(f"📄 File size: {file_size:,} bytes")
        
        if file_size > 10000:  # Should be at least 10KB with all content
            print("✅ All sections appear to be included")
        else:
            print("⚠️  File seems too small, some sections might be missing")
            
        return output_path
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 Testing PDF generation with all sections...")
    pdf_path = test_pdf_generation()
    
    if pdf_path:
        print(f"\n📍 PDF location: {pdf_path}")
        print("🎯 You can open this file to verify all sections are present")