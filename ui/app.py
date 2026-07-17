#!/usr/bin/env python3
"""GEO Brand Audit — Streamlit Web Interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# Add scripts to path
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))


# Page configuration
st.set_page_config(
    page_title="GEO Brand Audit",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_report(report_path: Path) -> dict:
    """Load and parse report JSON."""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading report: {e}")
        return {}


def render_score_gauge(score: float, title: str):
    """Render a score gauge chart."""
    import plotly.graph_objects as go
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "red"},
                {'range': [40, 60], 'color': "yellow"},
                {'range': [60, 80], 'color': "lightgreen"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_radar_chart(data: dict, title: str):
    """Render a radar chart for multi-dimensional scores."""
    import plotly.graph_objects as go
    
    categories = list(data.keys())
    values = list(data.values())
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=title
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


def render_bar_chart(data: dict, title: str, x_label: str, y_label: str):
    """Render a bar chart."""
    import plotly.express as px
    import pandas as pd
    
    df = pd.DataFrame(list(data.items()), columns=[x_label, y_label])
    fig = px.bar(df, x=x_label, y=y_label, title=title)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main Streamlit app."""
    
    # Sidebar
    with st.sidebar:
        st.title("🔍 GEO Brand Audit")
        st.markdown("---")
        
        # File upload
        st.subheader("Upload Report")
        uploaded_file = st.file_uploader(
            "Choose a report JSON file",
            type=["json"],
            help="Upload a GEO Brand Audit report file"
        )
        
        # Demo mode
        st.markdown("---")
        st.subheader("Demo Mode")
        if st.button("Load Demo Report"):
            demo_path = ROOT / "dist" / "demo-runs" / "geo_offline_demo_00000001" / "output" / "report.json"
            if demo_path.exists():
                st.session_state.report = load_report(demo_path)
            else:
                st.warning("Demo report not found. Run the offline demo first.")
        
        # API Configuration
        st.markdown("---")
        st.subheader("API Configuration")
        st.info("Set API keys in environment variables:\n"
                "- OPENAI_API_KEY\n"
                "- ANTHROPIC_API_KEY\n"
                "- GOOGLE_API_KEY\n"
                "- PERPLEXITY_API_KEY")
    
    # Main content
    if uploaded_file is not None:
        try:
            report = json.load(uploaded_file)
            st.session_state.report = report
        except Exception as e:
            st.error(f"Error parsing report: {e}")
            return
    
    if "report" not in st.session_state:
        st.session_state.report = {}
    
    report = st.session_state.report
    
    if not report:
        st.info("Upload a report file or load the demo report to get started.")
        return
    
    # Report header
    metadata = report.get("metadata", {})
    st.title(f"GEO Brand Audit: {metadata.get('brand_name', 'Unknown')}")
    st.caption(f"Generated: {metadata.get('generated_at', 'N/A')}")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Metrics", "🎯 Opportunities", "📜 History", "📄 Export"])
    
    with tab1:
        render_overview(report)
    
    with tab2:
        render_metrics(report)
    
    with tab3:
        render_opportunities(report)
    
    with tab4:
        render_historical_trends()
    
    with tab5:
        render_export_section(report)


def render_overview(report: dict):
    """Render overview tab."""
    metrics = report.get("metrics", {})
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        geo_score = metrics.get("geo_score", {}).get("score", 0)
        render_score_gauge(geo_score, "GEO Score")
    
    with col2:
        mention_rate = metrics.get("mention_rate", {}).get("rate", 0) or 0
        render_score_gauge(mention_rate * 100, "Mention Rate")
    
    with col3:
        rec_rate = metrics.get("recommendation_rate", {}).get("rate", 0) or 0
        render_score_gauge(rec_rate * 100, "Recommendation Rate")
    
    with col4:
        accuracy = metrics.get("accuracy_score", {}).get("score", 0) or 0
        render_score_gauge(accuracy * 100, "Accuracy Score")
    
    # Sentiment and Trust
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        sentiment = metrics.get("sentiment_index", {}).get("score", 0) or 0
        st.metric("Sentiment Index", f"{sentiment:.1f}")
    
    with col2:
        trust = metrics.get("trust_stack", {})
        if trust:
            st.metric("Trust Grade", trust.get("grade", "N/A"))
    
    # Execution Summary
    st.markdown("---")
    st.subheader("Execution Summary")
    execution = report.get("execution_summary", {})
    if execution:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", execution.get("question_count", 0))
        with col2:
            st.metric("Search Success Rate", f"{execution.get('search_success_rate', 0):.1%}")
        with col3:
            st.metric("Duration", execution.get("duration", "N/A"))


def render_metrics(report: dict):
    """Render metrics tab."""
    metrics = report.get("metrics", {})
    
    # GEO Score Breakdown
    st.subheader("GEO Score Breakdown")
    geo_score = metrics.get("geo_score", {})
    if geo_score:
        breakdown = geo_score.get("breakdown", {})
        if breakdown:
            render_radar_chart(breakdown, "GEO Score Components")
    
    # Recommendation Type Distribution
    st.markdown("---")
    st.subheader("Recommendation Type Distribution")
    rec_dist = metrics.get("recommendation_type_distribution", {})
    if rec_dist:
        render_bar_chart(rec_dist, "Recommendation Types", "Type", "Count")
    
    # Citation Analysis
    st.markdown("---")
    st.subheader("Citation Analysis")
    citation_map = metrics.get("platform_citation_map", {})
    if citation_map:
        st.json(citation_map)
    
    # All Metrics
    st.markdown("---")
    st.subheader("All Metrics")
    with st.expander("View all metrics"):
        st.json(metrics)


def render_opportunities(report: dict):
    """Render opportunities tab."""
    opportunities = report.get("opportunities", [])
    
    if not opportunities:
        st.info("No opportunities identified.")
        return
    
    st.subheader(f"Top {len(opportunities)} Opportunities")
    
    for i, opp in enumerate(opportunities, 1):
        with st.expander(f"{i}. {opp.get('title', 'Untitled')} (Score: {opp.get('score', 0):.1f})"):
            st.markdown(f"**Type:** {opp.get('type', 'N/A')}")
            st.markdown(f"**Priority:** {opp.get('priority', 'N/A')}")
            st.markdown(f"**Description:** {opp.get('description', 'N/A')}")
            
            if opp.get("action_items"):
                st.markdown("**Action Items:**")
                for item in opp["action_items"]:
                    st.markdown(f"- {item}")


def render_historical_trends():
    """Render historical trends tab."""
    import plotly.graph_objects as go
    import pandas as pd
    from datetime import datetime, timedelta
    
    st.subheader("Historical Trends")
    
    # Load metrics history
    run_dir = ROOT / "geo-audit-runs"
    history_file = run_dir / "metrics_history.jsonl"
    
    if not history_file.exists():
        st.info("No historical data available. Run multiple audits to see trends.")
        return
    
    # Parse history
    history = []
    cutoff = datetime.now() - timedelta(days=30)
    
    with open(history_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= cutoff:
                    history.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue
    
    if not history:
        st.info("No historical data in the last 30 days.")
        return
    
    # Prepare dataframe
    df = pd.DataFrame([
        {
            "date": entry["timestamp"][:10],
            "geo_score": entry.get("metrics", {}).get("geo_score", {}).get("score", 0),
            "mention_rate": entry.get("metrics", {}).get("mention_rate", {}).get("rate", 0),
            "recommendation_rate": entry.get("metrics", {}).get("recommendation_rate", {}).get("rate", 0),
            "sentiment_index": entry.get("metrics", {}).get("sentiment_index", {}).get("score", 0),
        }
        for entry in history
    ])
    
    # GEO Score trend
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["geo_score"],
        mode='lines+markers',
        name='GEO Score',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(
        title="GEO Score Trend",
        xaxis_title="Date",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Multi-metric trend
    col1, col2 = st.columns(2)
    
    with col1:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df["date"], y=df["mention_rate"],
            mode='lines', name='Mention Rate',
            line=dict(color='#2ca02c')
        ))
        fig2.add_trace(go.Scatter(
            x=df["date"], y=df["recommendation_rate"],
            mode='lines', name='Recommendation Rate',
            line=dict(color='#ff7f0e')
        ))
        fig2.update_layout(
            title="Mention & Recommendation Rates",
            xaxis_title="Date",
            yaxis_title="Rate",
            height=350
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df["date"], y=df["sentiment_index"],
            mode='lines+markers',
            name='Sentiment Index',
            line=dict(color='#d62728')
        ))
        fig3.update_layout(
            title="Sentiment Index Trend",
            xaxis_title="Date",
            yaxis_title="Score",
            height=350
        )
        st.plotly_chart(fig3, use_container_width=True)


def render_export_section(report: dict):
    """Render export section with JSON and PDF download."""
    st.subheader("Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### JSON Export")
        st.download_button(
            label="📥 Download Report JSON",
            data=json.dumps(report, indent=2),
            file_name="geo_audit_report.json",
            mime="application/json"
        )
    
    with col2:
        st.markdown("#### PDF Export")
        try:
            from scripts.pdf_export import PDFExporter
            import tempfile
            
            exporter = PDFExporter(report)
            
            # Create temp PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            if exporter.export(tmp_path):
                with open(tmp_path, "rb") as f:
                    pdf_data = f.read()
                
                st.download_button(
                    label="📥 Download Report PDF",
                    data=pdf_data,
                    file_name="geo_audit_report.pdf",
                    mime="application/pdf"
                )
                
                # Cleanup
                tmp_path.unlink(missing_ok=True)
            else:
                st.error("PDF generation failed")
        except ImportError:
            st.warning("Install reportlab for PDF export: `pip install reportlab`")
        except Exception as e:
            st.error(f"PDF export error: {e}")
    
    # Alerts section
    st.markdown("---")
    st.subheader("Recent Alerts")
    
    alerts_file = ROOT / "geo-audit-runs" / "alerts.json"
    if alerts_file.exists():
        try:
            with open(alerts_file, "r", encoding="utf-8") as f:
                alerts = json.load(f)
            
            if alerts:
                for alert in alerts[-5:]:  # Show last 5 alerts
                    severity = alert.get("severity", "info")
                    if severity == "critical":
                        st.error(f"[{alert.get('triggered_at', '')[:16]}] {alert.get('message', '')}")
                    elif severity == "warning":
                        st.warning(f"[{alert.get('triggered_at', '')[:16]}] {alert.get('message', '')}")
                    else:
                        st.info(f"[{alert.get('triggered_at', '')[:16]}] {alert.get('message', '')}")
            else:
                st.info("No alerts triggered.")
        except Exception:
            st.info("No alerts available.")
    else:
        st.info("No alerts file found.")


if __name__ == "__main__":
    main()