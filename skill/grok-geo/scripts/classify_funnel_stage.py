#!/usr/bin/env python3
"""Classify questions by funnel stage based on intent and keyword patterns.

v1.7 — Adds funnel_stage field to each question: awareness/consideration/conversion/retention.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Allow import from scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import INTENT_TO_FUNNEL, read_json, write_json

# Keyword patterns for fallback classification when intent is unknown
AWARENESS_KEYWORDS = [
    r"什么|哪些|什么是|有哪些|推荐.*软件|推荐.*工具|最好.*软件|最好.*工具",
    r"what are|what is|best .* tools|best .* software|top .* tools",
]
CONSIDERATION_KEYWORDS = [
    r"vs|对比|比较|哪个好|区别|优劣|选择",
    r"vs\.?|compare|comparison|better than|which .* better|alternative",
]
CONVERSION_KEYWORDS = [
    r"购买|买|订阅|开通|注册|价格.*多少|多少钱",
    r"buy|purchase|subscribe|sign up|pricing|how much",
]
RETENTION_KEYWORDS = [
    r"怎么用|如何使用|教程|使用方法|导出|设置|配置|故障|问题",
    r"how to use|tutorial|export|configure|setup|troubleshoot|error",
]


def classify_question_stage(question: dict) -> str:
    """Classify a single question by funnel stage.

    Priority: intent mapping > keyword pattern matching > default 'awareness'.
    """
    intent = question.get("intent", "")
    if intent in INTENT_TO_FUNNEL:
        return INTENT_TO_FUNNEL[intent]

    text = question.get("text", "")
    if text:
        for pattern in CONVERSION_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return "conversion"
        for pattern in CONSIDERATION_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return "consideration"
        for pattern in RETENTION_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return "retention"
        for pattern in AWARENESS_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return "awareness"

    return "awareness"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify questions by funnel stage (v1.7)"
    )
    parser.add_argument(
        "--questions", required=True, help="Path to questions.json"
    )
    parser.add_argument(
        "--output", required=True, help="Output path (can be same as --questions)"
    )
    args = parser.parse_args()

    questions = read_json(args.questions)
    if not isinstance(questions, list):
        print("Error: questions.json must be a JSON array", file=sys.stderr)
        raise SystemExit(1)

    stage_counts: Counter = Counter()
    for q in questions:
        stage = classify_question_stage(q)
        q["funnel_stage"] = stage
        stage_counts[stage] += 1

    summary = {
        "total_questions": len(questions),
        "stage_distribution": dict(stage_counts),
    }

    output_data = {"questions": questions, "summary": summary}
    write_json(args.output, output_data)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()