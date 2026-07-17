#!/usr/bin/env python3
"""Multi-Engine Query — 多引擎真实 AI 搜索查询。

支持 8 个 AI 引擎的统一查询接口。

用法:
  # 列出可用引擎
  python multi_engine_query.py list-engines

  # 单引擎查询
  python multi_engine_query.py query --engine chatgpt --question "best PM tools"

  # 批量查询（从问题队列）
  python multi_engine_query.py batch --run-dir <RUN> --engines chatgpt,perplexity,claude

  # 引擎健康检查
  python multi_engine_query.py health-check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    read_json,
    read_jsonl,
    write_json,
    append_jsonl,
    utc_now_iso,
    clamp,
    print_json,
)


# ─── Engine Response ────────────────────────────────────────────────────

def new_engine_response(
    engine: str,
    question_id: str,
    question_text: str,
    status: str = "success",
) -> Dict[str, Any]:
    return {
        "engine": engine,
        "model": "",
        "question_id": question_id,
        "question_text": question_text,
        "answer_text": "",
        "citations": [],
        "sources": [],
        "response_metadata": {
            "tokens_used": 0,
            "latency_ms": 0,
            "has_inline_citations": False,
            "response_format": "unknown",
            "list_detected": False,
            "table_detected": False,
        },
        "query_timestamp": utc_now_iso(),
        "status": status,
        "error": None,
        "fallback": None,
    }


# ─── Engine Adapters ────────────────────────────────────────────────────

class EngineAdapter(ABC):
    """统一的 AI 引擎查询基类。"""
    
    engine_name: str = ""
    requires_api_key: bool = True
    supports_citations: bool = True
    max_batch_size: int = 5
    rate_limit_rpm: int = 60
    api_key_env: str = ""

    def __init__(self) -> None:
        self._api_key = os.environ.get(self.api_key_env, "")

    def is_available(self) -> bool:
        if self.requires_api_key and not self._api_key:
            return False
        return True

    @abstractmethod
    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        ...

    def health_check(self) -> Dict[str, Any]:
        return {
            "engine": self.engine_name,
            "available": self.is_available(),
            "api_key_set": bool(self._api_key),
            "requires_api_key": self.requires_api_key,
        }


class ChatGPTAdapter(EngineAdapter):
    """ChatGPT Search via OpenAI API."""
    engine_name = "chatgpt"
    requires_api_key = True
    supports_citations = True
    api_key_env = "OPENAI_API_KEY"
    rate_limit_rpm = 60

    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        resp = new_engine_response("chatgpt", question_id, question)
        resp["model"] = "gpt-4o-search-preview"

        if not self._api_key:
            resp["status"] = "error"
            resp["error"] = "OPENAI_API_KEY not set"
            resp["fallback"] = "web_search"
            return resp

        try:
            import urllib.request
            import urllib.error

            body = json.dumps({
                "model": "gpt-4o-search-preview",
                "messages": [{"role": "user", "content": question}],
                "web_search_options": {"search_context_size": "medium"},
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )

            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            elapsed = int((time.monotonic() - start) * 1000)

            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                resp["answer_text"] = msg.get("content", "")
                # Extract citations from annotations
                for ann in msg.get("annotations", []):
                    if ann.get("type") == "url_citation":
                        uc = ann.get("url_citation", {})
                        resp["citations"].append({
                            "title": uc.get("title", ""),
                            "url": uc.get("url", ""),
                            "domain": uc.get("url", "").split("/")[2] if "/" in uc.get("url", "") else "",
                            "snippet": uc.get("snippet", ""),
                        })
                resp["sources"] = list({c["domain"] for c in resp["citations"] if c["domain"]})

            resp["response_metadata"]["latency_ms"] = elapsed
            resp["response_metadata"]["tokens_used"] = data.get("usage", {}).get("total_tokens", 0)
            resp["response_metadata"]["has_inline_citations"] = len(resp["citations"]) > 0

        except Exception as e:
            resp["status"] = "error"
            resp["error"] = str(e)
            resp["fallback"] = "web_search"

        return resp


class PerplexityEngineAdapter(EngineAdapter):
    """Perplexity via sonar API."""
    engine_name = "perplexity"
    requires_api_key = True
    supports_citations = True
    api_key_env = "PERPLEXITY_API_KEY"
    rate_limit_rpm = 50

    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        resp = new_engine_response("perplexity", question_id, question)
        resp["model"] = "sonar-pro"

        if not self._api_key:
            resp["status"] = "error"
            resp["error"] = "PERPLEXITY_API_KEY not set"
            resp["fallback"] = "web_search"
            return resp

        try:
            import urllib.request

            body = json.dumps({
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": question}],
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.perplexity.ai/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )

            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            elapsed = int((time.monotonic() - start) * 1000)

            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                resp["answer_text"] = msg.get("content", "")

            # Perplexity returns citations at top level
            for cit in data.get("citations", []):
                if isinstance(cit, str):
                    resp["citations"].append({"url": cit, "domain": cit.split("/")[2] if "/" in cit else "", "title": "", "snippet": ""})
                elif isinstance(cit, dict):
                    resp["citations"].append(cit)

            resp["sources"] = list({c.get("domain", "") for c in resp["citations"] if c.get("domain")})
            resp["response_metadata"]["latency_ms"] = elapsed
            resp["response_metadata"]["has_inline_citations"] = len(resp["citations"]) > 0

        except Exception as e:
            resp["status"] = "error"
            resp["error"] = str(e)
            resp["fallback"] = "web_search"

        return resp


class ClaudeSearchAdapter(EngineAdapter):
    """Claude with web search tool."""
    engine_name = "claude"
    requires_api_key = True
    supports_citations = True
    api_key_env = "ANTHROPIC_API_KEY"
    rate_limit_rpm = 50

    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        resp = new_engine_response("claude", question_id, question)
        resp["model"] = "claude-sonnet-4-20250514"

        if not self._api_key:
            resp["status"] = "error"
            resp["error"] = "ANTHROPIC_API_KEY not set"
            resp["fallback"] = "web_search"
            return resp

        try:
            import urllib.request

            body = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": question}],
                "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
            )

            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            elapsed = int((time.monotonic() - start) * 1000)

            # Extract text content
            for block in data.get("content", []):
                if block.get("type") == "text":
                    resp["answer_text"] += block.get("text", "")
                elif block.get("type") == "web_search_tool_result":
                    for result in block.get("content", []):
                        resp["citations"].append({
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "domain": result.get("url", "").split("/")[2] if "/" in result.get("url", "") else "",
                            "snippet": result.get("encrypted_content", "")[:200],
                        })

            resp["sources"] = list({c["domain"] for c in resp["citations"] if c["domain"]})
            resp["response_metadata"]["latency_ms"] = elapsed
            resp["response_metadata"]["has_inline_citations"] = len(resp["citations"]) > 0

        except Exception as e:
            resp["status"] = "error"
            resp["error"] = str(e)
            resp["fallback"] = "web_search"

        return resp


class GeminiAdapter(EngineAdapter):
    """Gemini via Google AI API."""
    engine_name = "gemini"
    requires_api_key = True
    supports_citations = True
    api_key_env = "GOOGLE_API_KEY"
    rate_limit_rpm = 60

    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        resp = new_engine_response("gemini", question_id, question)
        resp["model"] = "gemini-2.5-pro"

        if not self._api_key:
            resp["status"] = "error"
            resp["error"] = "GOOGLE_API_KEY not set"
            resp["fallback"] = "web_search"
            return resp

        try:
            import urllib.request

            body = json.dumps({
                "contents": [{"parts": [{"text": question}]}],
                "tools": [{"googleSearch": {}}],
            }).encode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={self._api_key}"
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
            )

            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            elapsed = int((time.monotonic() - start) * 1000)

            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if part.get("text"):
                        resp["answer_text"] += part["text"]
                    # Extract grounding metadata
                    grounding = part.get("groundingMetadata", {})
                    for chunk in grounding.get("groundingChunks", []):
                        web = chunk.get("web", {})
                        if web:
                            resp["citations"].append({
                                "title": web.get("title", ""),
                                "url": web.get("uri", ""),
                                "domain": web.get("uri", "").split("/")[2] if "/" in web.get("uri", "") else "",
                                "snippet": "",
                            })

            resp["sources"] = list({c["domain"] for c in resp["citations"] if c["domain"]})
            resp["response_metadata"]["latency_ms"] = elapsed
            resp["response_metadata"]["has_inline_citations"] = len(resp["citations"]) > 0

        except Exception as e:
            resp["status"] = "error"
            resp["error"] = str(e)
            resp["fallback"] = "web_search"

        return resp


class GrokAdapter(EngineAdapter):
    """Grok via xAI API."""
    engine_name = "grok"
    requires_api_key = True
    supports_citations = False
    api_key_env = "XAI_API_KEY"
    rate_limit_rpm = 60

    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        resp = new_engine_response("grok", question_id, question)
        resp["model"] = "grok-3"

        if not self._api_key:
            resp["status"] = "error"
            resp["error"] = "XAI_API_KEY not set"
            resp["fallback"] = "web_search"
            return resp

        try:
            import urllib.request

            body = json.dumps({
                "model": "grok-3",
                "messages": [{"role": "user", "content": question}],
                "search_parameters": {"mode": "auto"},
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.x.ai/v1/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )

            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            elapsed = int((time.monotonic() - start) * 1000)

            choices = data.get("choices", [])
            if choices:
                resp["answer_text"] = choices[0].get("message", {}).get("content", "")

            resp["response_metadata"]["latency_ms"] = elapsed

        except Exception as e:
            resp["status"] = "error"
            resp["error"] = str(e)
            resp["fallback"] = "web_search"

        return resp


class DeepSeekAdapter(EngineAdapter):
    """DeepSeek via DeepSeek API."""
    engine_name = "deepseek"
    requires_api_key = True
    supports_citations = False
    api_key_env = "DEEPSEEK_API_KEY"
    rate_limit_rpm = 60

    def query(self, question: str, question_id: str = "", **kwargs) -> Dict[str, Any]:
        resp = new_engine_response("deepseek", question_id, question)
        resp["model"] = "deepseek-chat"

        if not self._api_key:
            resp["status"] = "error"
            resp["error"] = "DEEPSEEK_API_KEY not set"
            resp["fallback"] = "web_search"
            return resp

        try:
            import urllib.request

            body = json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": question}],
                "web_search": True,
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )

            start = time.monotonic()
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            elapsed = int((time.monotonic() - start) * 1000)

            choices = data.get("choices", [])
            if choices:
                resp["answer_text"] = choices[0].get("message", {}).get("content", "")

            resp["response_metadata"]["latency_ms"] = elapsed

        except Exception as e:
            resp["status"] = "error"
            resp["error"] = str(e)
            resp["fallback"] = "web_search"

        return resp


# ─── Engine Registry ────────────────────────────────────────────────────

ENGINES: Dict[str, EngineAdapter] = {
    "chatgpt": ChatGPTAdapter(),
    "perplexity": PerplexityEngineAdapter(),
    "claude": ClaudeSearchAdapter(),
    "gemini": GeminiAdapter(),
    "grok": GrokAdapter(),
    "deepseek": DeepSeekAdapter(),
}

# Engine priority for query distribution
ENGINE_PRIORITY = ["chatgpt", "perplexity", "claude", "gemini", "grok", "deepseek"]

# Distribution ratios for standard mode
STANDARD_DISTRIBUTION = {
    "chatgpt": 0.30,
    "perplexity": 0.25,
    "claude": 0.20,
    "gemini": 0.15,
    "grok": 0.05,
    "deepseek": 0.05,
}

# Distribution ratios for quick mode
QUICK_DISTRIBUTION = {
    "chatgpt": 0.40,
    "perplexity": 0.30,
    "claude": 0.20,
    "gemini": 0.10,
}


# ─── Query Router ───────────────────────────────────────────────────────

def select_engines(
    requested_engines: Optional[List[str]] = None,
    mode: str = "standard",
) -> List[str]:
    """Select available engines based on request and mode."""
    if requested_engines:
        selected = [e for e in requested_engines if e in ENGINES]
    else:
        dist = STANDARD_DISTRIBUTION if mode == "standard" else QUICK_DISTRIBUTION
        selected = [e for e in dist.keys() if e in ENGINES]
    
    # Filter to available engines
    available = [e for e in selected if ENGINES[e].is_available()]
    
    if not available:
        # Fallback: return all engines (will use web_search fallback)
        available = ["chatgpt"]  # Minimum fallback
    
    return available


def distribute_questions(
    questions: List[Dict[str, Any]],
    engines: List[str],
    mode: str = "standard",
) -> Dict[str, List[Dict[str, Any]]]:
    """Distribute questions across engines based on distribution ratios."""
    dist = STANDARD_DISTRIBUTION if mode == "standard" else QUICK_DISTRIBUTION
    total = len(questions)
    
    allocation: Dict[str, List[Dict[str, Any]]] = {e: [] for e in engines}
    
    # Calculate per-engine counts
    counts: Dict[str, int] = {}
    remaining = total
    for engine in engines:
        ratio = dist.get(engine, 1.0 / len(engines))
        count = max(1, round(total * ratio))
        count = min(count, remaining)
        counts[engine] = count
        remaining -= count
    
    # Adjust if we over/under allocated
    if remaining > 0:
        for engine in engines:
            if remaining <= 0:
                break
            counts[engine] += 1
            remaining -= 1
    elif remaining < 0:
        for engine in reversed(engines):
            if remaining >= 0:
                break
            counts[engine] = max(1, counts[engine] - 1)
            remaining += 1
    
    # Assign questions
    idx = 0
    for engine in engines:
        count = counts.get(engine, 0)
        allocation[engine] = questions[idx:idx + count]
        idx += count
    
    return allocation


def route_queries(
    questions: List[Dict[str, Any]],
    engines: Optional[List[str]] = None,
    mode: str = "standard",
) -> List[Dict[str, Any]]:
    """Route questions to engines and collect responses."""
    selected = select_engines(engines, mode)
    allocation = distribute_questions(questions, selected, mode)
    
    all_responses: List[Dict[str, Any]] = []
    
    for engine_name, engine_questions in allocation.items():
        adapter = ENGINES.get(engine_name)
        if not adapter:
            continue
        
        for q in engine_questions:
            qid = q.get("id", q.get("question_id", ""))
            qtext = q.get("text", q.get("question_text", ""))
            
            response = adapter.query(qtext, question_id=qid)
            
            # Detect response format features
            answer = response.get("answer_text", "")
            response["response_metadata"]["list_detected"] = any(
                line.strip().startswith(("- ", "* ", "1. ", "2. "))
                for line in answer.split("\n")
            )
            response["response_metadata"]["table_detected"] = "|" in answer and "---" in answer
            response["response_metadata"]["response_format"] = (
                "list" if response["response_metadata"]["list_detected"]
                else "table" if response["response_metadata"]["table_detected"]
                else "narrative"
            )
            
            all_responses.append(response)
            
            # Rate limiting
            time.sleep(60.0 / adapter.rate_limit_rpm)
    
    return all_responses


# ─── Cross-Engine Analysis ──────────────────────────────────────────────

def compute_cross_engine_metrics(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute cross-engine aggregation metrics."""
    if not responses:
        return {}
    
    # Per-engine stats
    by_engine: Dict[str, List[Dict[str, Any]]] = {}
    for r in responses:
        engine = r.get("engine", "unknown")
        by_engine.setdefault(engine, []).append(r)
    
    engine_stats: Dict[str, Dict[str, Any]] = {}
    all_domains: List[set] = []
    
    for engine, engine_responses in by_engine.items():
        total = len(engine_responses)
        success = sum(1 for r in engine_responses if r["status"] == "success")
        with_citations = sum(1 for r in engine_responses if r.get("citations"))
        all_cited_domains: set = set()
        for r in engine_responses:
            domains = set(r.get("sources", []))
            all_cited_domains.update(domains)
            all_domains.append(domains)
        
        engine_stats[engine] = {
            "total_queries": total,
            "success_count": success,
            "success_rate": round(success / total, 4) if total else 0,
            "citation_count": with_citations,
            "citation_rate": round(with_citations / total, 4) if total else 0,
            "unique_domains_cited": len(all_cited_domains),
        }
    
    # Cross-engine citation consistency
    if len(all_domains) >= 2:
        union_domains: set = set()
        for d_set in all_domains:
            union_domains.update(d_set)
        intersection_domains = all_domains[0].copy()
        for d_set in all_domains[1:]:
            intersection_domains &= d_set
        cec = round(len(intersection_domains) / len(union_domains), 4) if union_domains else 0
    else:
        cec = None
    
    return {
        "engine_stats": engine_stats,
        "cross_engine_citation_consistency": cec,
        "total_queries": len(responses),
        "total_successful": sum(1 for r in responses if r["status"] == "success"),
        "engines_used": list(by_engine.keys()),
    }


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Engine Query — 多引擎 AI 搜索")
    sub = parser.add_subparsers(dest="command")

    # list-engines
    sub.add_parser("list-engines", help="列出所有引擎及可用状态")

    # health-check
    sub.add_parser("health-check", help="检查所有引擎健康状态")

    # query
    q = sub.add_parser("query", help="单引擎查询")
    q.add_argument("--engine", required=True, help="引擎名称")
    q.add_argument("--question", required=True, help="查询问题")
    q.add_argument("--question-id", default="q_001", help="问题 ID")

    # batch
    b = sub.add_parser("batch", help="批量查询")
    b.add_argument("--run-dir", required=True, help="运行目录")
    b.add_argument("--engines", help="逗号分隔的引擎列表（默认自动分配）")
    b.add_argument("--mode", default="standard", choices=["standard", "quick"], help="查询模式")
    b.add_argument("--output", help="输出路径（默认 <run-dir>/raw/engine_responses.jsonl）")

    args = parser.parse_args()

    if args.command == "list-engines":
        for name, adapter in ENGINES.items():
            status = "✓" if adapter.is_available() else "✗ (API key missing)"
            print(f"  {name:15s} {status}")
        return

    if args.command == "health-check":
        results = [adapter.health_check() for adapter in ENGINES.values()]
        print_json(results)
        return

    if args.command == "query":
        adapter = ENGINES.get(args.engine)
        if not adapter:
            print(f"Unknown engine: {args.engine}")
            print(f"Available: {', '.join(ENGINES.keys())}")
            sys.exit(1)
        response = adapter.query(args.question, question_id=args.question_id)
        print_json(response)
        return

    if args.command == "batch":
        run_dir = Path(args.run_dir)
        questions_path = run_dir / "intermediate" / "questions.json"
        if not questions_path.exists():
            print(f"Questions file not found: {questions_path}")
            sys.exit(1)

        questions_data = read_json(questions_path)
        questions = questions_data if isinstance(questions_data, list) else questions_data.get("questions", [])

        engines = args.engines.split(",") if args.engines else None
        responses = route_queries(questions, engines=engines, mode=args.mode)

        # Save responses
        output_path = Path(args.output) if args.output else run_dir / "raw" / "engine_responses.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        for resp in responses:
            append_jsonl(output_path, resp)

        # Compute and save cross-engine metrics
        metrics = compute_cross_engine_metrics(responses)
        metrics_path = run_dir / "intermediate" / "cross_engine_metrics.json"
        write_json(metrics_path, metrics)

        print(f"Queried {len(responses)} questions across {len(metrics.get('engines_used', []))} engines")
        print(f"Success rate: {metrics.get('total_successful', 0)}/{metrics.get('total_queries', 0)}")
        print(f"Responses: {output_path}")
        print(f"Metrics: {metrics_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()