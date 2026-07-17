#!/usr/bin/env python3
"""PDF report generation for GEO brand audit."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class PDFExporter:
    """Export GEO audit reports to PDF."""
    
    def __init__(self, report_data: Dict[str, Any]):
        self.report = report_data
        if HAS_REPORTLAB:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='BrandTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor('#1a1a2e')
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#16213e')
        ))
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#0f3460')
        ))
    
    def export(self, output_path: Path) -> bool:
        """Export report to PDF."""
        if not HAS_REPORTLAB:
            print("Error: reportlab is required. Install with: pip install reportlab")
            return False
        
        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            story.extend(self._build_title_page())
            story.extend(self._build_executive_summary())
            story.extend(self._build_metrics_section())
            story.extend(self._build_opportunities_section())
            story.extend(self._build_limitations_section())
            
            doc.build(story)
            return True
        except Exception as e:
            print(f"PDF export failed: {e}")
            return False
    
    def _build_title_page(self) -> list:
        """Build title page."""
        story = []
        
        # Title
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("grok-geo Report", self.styles['BrandTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Brand info
        metadata = self.report.get("metadata", {})
        brand_name = metadata.get("brand_name", "Unknown Brand")
        story.append(Paragraph(f"Brand: {brand_name}", self.styles['Heading1']))
        story.append(Spacer(1, 0.3*inch))
        
        # Generated date
        generated_at = metadata.get("generated_at", datetime.now().isoformat())
        story.append(Paragraph(f"Generated: {generated_at}", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Mode
        mode = metadata.get("mode", "standard")
        story.append(Paragraph(f"Mode: {mode}", self.styles['Normal']))
        
        story.append(PageBreak())
        return story
    
    def _build_executive_summary(self) -> list:
        """Build executive summary section."""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))
        
        metrics = self.report.get("metrics", {})
        
        # Key findings
        geo_score = metrics.get("geo_score", {}).get("score", 0)
        mention_rate = metrics.get("mention_rate", {}).get("rate", 0)
        rec_rate = metrics.get("recommendation_rate", {}).get("rate", 0)
        
        summary_data = [
            ["Metric", "Score", "Status"],
            ["GEO Score", f"{geo_score:.1f}", self._get_status(geo_score)],
            ["Mention Rate", f"{mention_rate:.1%}", self._get_status(mention_rate * 100)],
            ["Recommendation Rate", f"{rec_rate:.1%}", self._get_status(rec_rate * 100)],
        ]
        
        table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f8f8')])
        ]))
        story.append(table)
        
        return story
    
    def _build_metrics_section(self) -> list:
        """Build detailed metrics section."""
        story = []
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Detailed Metrics", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))
        
        metrics = self.report.get("metrics", {})
        
        # Sentiment
        sentiment = metrics.get("sentiment_index", {})
        if sentiment:
            story.append(Paragraph("Sentiment Analysis", self.styles['SubHeader']))
            story.append(Paragraph(f"Sentiment Index: {sentiment.get('score', 0):.1f}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Trust Stack
        trust = metrics.get("trust_stack", {})
        if trust:
            story.append(Paragraph("Trust Stack", self.styles['SubHeader']))
            story.append(Paragraph(f"Trust Grade: {trust.get('grade', 'N/A')}", self.styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Accuracy
        accuracy = metrics.get("accuracy_score", {})
        if accuracy:
            story.append(Paragraph("Claim Accuracy", self.styles['SubHeader']))
            story.append(Paragraph(
                f"Accuracy: {accuracy.get('score', 0):.1%} "
                f"(Correct: {accuracy.get('correct_count', 0)}, "
                f"Partial: {accuracy.get('partially_correct_count', 0)})",
                self.styles['Normal']
            ))
        
        return story
    
    def _build_opportunities_section(self) -> list:
        """Build opportunities section."""
        story = []
        
        opportunities = self.report.get("opportunities", [])
        if not opportunities:
            return story
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Top Opportunities", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))
        
        for i, opp in enumerate(opportunities[:10], 1):
            title = opp.get("title", "Untitled")
            score = opp.get("score", 0)
            opp_type = opp.get("type", "N/A")
            
            story.append(Paragraph(
                f"{i}. {title} (Score: {score:.1f}, Type: {opp_type})",
                self.styles['Normal']
            ))
            
            description = opp.get("description", "")
            if description:
                story.append(Paragraph(f"   {description}", self.styles['Normal']))
            
            story.append(Spacer(1, 0.1*inch))
        
        return story
    
    def _build_limitations_section(self) -> list:
        """Build limitations section."""
        story = []
        
        limitations = self.report.get("limitations", [])
        if not limitations:
            return story
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Limitations", self.styles['SectionHeader']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.2*inch))
        
        for limitation in limitations:
            story.append(Paragraph(f"• {limitation}", self.styles['Normal']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Paragraph(
            "Generated by grok-geo Skill v5.0.0",
            ParagraphStyle(name='Footer', parent=self.styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
        ))
        
        return story
    
    def _get_status(self, score: float) -> str:
        """Get status text based on score."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Needs Work"
        else:
            return "Critical"


def export_report_to_pdf(report_path: Path, output_path: Path) -> bool:
    """Export a report JSON file to PDF."""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        
        exporter = PDFExporter(report_data)
        return exporter.export(output_path)
    except Exception as e:
        print(f"Failed to export PDF: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export GEO audit report to PDF")
    parser.add_argument("report", help="Path to report JSON file")
    parser.add_argument("--output", "-o", help="Output PDF path (default: report.pdf)")
    
    args = parser.parse_args()
    
    report_path = Path(args.report)
    output_path = Path(args.output) if args.output else report_path.with_suffix(".pdf")
    
    if not report_path.exists():
        print(f"Error: Report file not found: {report_path}")
        sys.exit(1)
    
    success = export_report_to_pdf(report_path, output_path)
    if success:
        print(f"PDF exported to: {output_path}")
    else:
        print("PDF export failed")
        sys.exit(1)