#!/usr/bin/env python3
"""Analytics Integration — GSC + GA4 AI Referrer 分析。

用法:
  python analyze_ai_referrers.py --ga4-property <property_id> --gsc-site <site_url> \
    --period 30 --output <output.json>

  # 仅分析 GA4 数据（不需要 GSC）
  python analyze_ai_referrers.py --ga4-property <property_id> --output <output.json>
"""

from __future__ import annotations
import argparse, json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_common import write_json, utc_now_iso, print_json

# AI referrer domains
AI_REFERRERS = {
    "chatgpt.com": "ChatGPT",
    "perplexity.ai": "Perplexity",
    "claude.ai": "Claude",
    "gemini.google.com": "Gemini",
    "copilot.microsoft.com": "Copilot",
    "you.com": "You.com",
    "search.brave.com": "Brave Search",
    "poe.com": "Poe",
}


def query_ga4_ai_traffic(
    property_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Query GA4 for AI referrer traffic."""
    api_key = os.environ.get("GOOGLE_ANALYTICS_API_KEY", "")
    creds_path = os.environ.get("GOOGLE_ANALYTICS_CREDENTIALS", "")

    if not api_key and not creds_path:
        return {
            "status": "unavailable",
            "reason": "GOOGLE_ANALYTICS_API_KEY or GOOGLE_ANALYTICS_CREDENTIALS not set",
            "ai_referrers": {},
        }

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter,
        )

        client = BetaAnalyticsDataClient()

        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="landingPage"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="engagementRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate"),
                Metric(name="conversions"),
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionSource",
                    in_list_filter=Filter.InListFilter(
                        values=list(AI_REFERRERS.keys()),
                    ),
                )
            ),
            limit=10000,
        )

        response = client.run_report(request)

        # Process results
        ai_data: Dict[str, Dict[str, Any]] = {}
        total_sessions = 0

        for row in response.rows:
            source = row.dimension_values[0].value
            landing = row.dimension_values[1].value
            sessions = int(row.metric_values[0].value)
            engagement = float(row.metric_values[1].value)
            duration = float(row.metric_values[2].value)
            bounce = float(row.metric_values[3].value)
            conversions = float(row.metric_values[4].value)

            if source not in ai_data:
                ai_data[source] = {
                    "sessions": 0,
                    "engagement_rate": [],
                    "avg_duration": [],
                    "bounce_rate": [],
                    "conversions": 0,
                    "top_pages": {},
                }

            ai_data[source]["sessions"] += sessions
            ai_data[source]["engagement_rate"].append(engagement)
            ai_data[source]["avg_duration"].append(duration)
            ai_data[source]["bounce_rate"].append(bounce)
            ai_data[source]["conversions"] += conversions
            ai_data[source]["top_pages"][landing] = ai_data[source]["top_pages"].get(landing, 0) + sessions
            total_sessions += sessions

        # Aggregate
        result: Dict[str, Any] = {}
        for source, data in ai_data.items():
            eng_rates = data["engagement_rate"]
            result[source] = {
                "sessions": data["sessions"],
                "share": round(data["sessions"] / total_sessions, 4) if total_sessions else 0,
                "engagement_rate": round(sum(eng_rates) / len(eng_rates), 4) if eng_rates else 0,
                "avg_duration_sec": round(sum(data["avg_duration"]) / len(data["avg_duration"]), 1) if data["avg_duration"] else 0,
                "bounce_rate": round(sum(data["bounce_rate"]) / len(data["bounce_rate"]), 4) if data["bounce_rate"] else 0,
                "conversions": int(data["conversions"]),
                "top_pages": sorted(data["top_pages"].items(), key=lambda x: x[1], reverse=True)[:10],
            }

        return {
            "status": "success",
            "total_ai_sessions": total_sessions,
            "ai_referrers": result,
        }

    except ImportError:
        return {"status": "unavailable", "reason": "google-analytics-data-v1beta not installed"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def query_gsc_ai_queries(
    site_url: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Query GSC for AI-related search queries."""
    creds_path = os.environ.get("GOOGLE_SEARCH_CONSOLE_CREDENTIALS", "")

    if not creds_path:
        return {
            "status": "unavailable",
            "reason": "GOOGLE_SEARCH_CONSOLE_CREDENTIALS not set",
        }

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=credentials)

        request_body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query", "page"],
            "rowLimit": 1000,
            "dataState": "final",
        }

        response = service.searchanalytics().query(
            siteUrl=site_url, body=request_body
        ).execute()

        rows = response.get("rows", [])
        queries = []
        for row in rows:
            queries.append({
                "query": row["keys"][0],
                "page": row["keys"][1],
                "impressions": row.get("impressions", 0),
                "clicks": row.get("clicks", 0),
                "ctr": round(row.get("ctr", 0), 4),
                "position": round(row.get("position", 0), 1),
            })

        return {
            "status": "success",
            "total_queries": len(queries),
            "top_queries": sorted(queries, key=lambda x: x["impressions"], reverse=True)[:50],
        }

    except ImportError:
        return {"status": "unavailable", "reason": "google-api-python-client not installed"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def build_report(
    ga4_data: Dict[str, Any],
    gsc_data: Dict[str, Any],
    period_days: int,
) -> Dict[str, Any]:
    """Build comprehensive AI analytics report."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=period_days)

    ai_traffic = ga4_data.get("ai_referrers", {})
    total_ai = ga4_data.get("total_ai_sessions", 0)

    # Compute aggregates
    total_conversions = sum(d.get("conversions", 0) for d in ai_traffic.values())
    avg_engagement = (
        sum(d.get("engagement_rate", 0) * d.get("sessions", 0) for d in ai_traffic.values()) / total_ai
        if total_ai > 0 else 0
    )

    # Determine trend (placeholder — real trend needs historical data)
    trend = "stable"
    if ga4_data.get("status") == "success":
        trend = "growing" if total_ai > 0 else "no_data"

    return {
        "schema_version": "2.4.0",
        "generated_at": utc_now_iso(),
        "period": {
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "days": period_days,
        },
        "ai_traffic_overview": {
            "total_sessions": total_ai,
            "ai_share": None,  # Need total traffic data
            "trend": trend,
        },
        "ai_sources": ai_traffic,
        "ai_user_behavior": {
            "avg_engagement_rate": round(avg_engagement, 4),
            "total_conversions": total_conversions,
        },
        "gsc_insights": gsc_data,
        "data_sources": {
            "ga4": ga4_data.get("status", "unavailable"),
            "gsc": gsc_data.get("status", "unavailable"),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description="AI Referrer Analytics")
    p.add_argument("--ga4-property", help="GA4 property ID")
    p.add_argument("--gsc-site", help="GSC site URL")
    p.add_argument("--period", type=int, default=30, help="Analysis period in days")
    p.add_argument("--output", help="Output path")
    args = p.parse_args()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.period)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    ga4_data = {"status": "skipped", "ai_referrers": {}}
    gsc_data = {"status": "skipped"}

    if args.ga4_property:
        ga4_data = query_ga4_ai_traffic(args.ga4_property, start_str, end_str)

    if args.gsc_site:
        gsc_data = query_gsc_ai_queries(args.gsc_site, start_str, end_str)

    report = build_report(ga4_data, gsc_data, args.period)

    if args.output:
        write_json(args.output, report)
        print(f"AI analytics report: {report['ai_traffic_overview']['total_sessions']} AI sessions")
    else:
        print_json(report)

if __name__ == "__main__":
    main()