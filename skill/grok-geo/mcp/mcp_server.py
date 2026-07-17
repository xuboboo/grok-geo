#!/usr/bin/env python3
"""GEO Brand Audit MCP Server.

Exposes GEO audit capabilities as MCP tools for Cursor/Claude integration.

Usage:
  # As stdio MCP server (for Cursor)
  python mcp_server.py

  # Or configure in .cursor/mcp.json:
  {
    "mcpServers": {
      "grok-geo": {
        "command": "python",
        "args": ["skill/grok-geo/mcp/mcp_server.py"],
        "cwd": "/path/to/project"
      }
    }
  }
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add scripts/ to path
SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from core.constants import SKILL_NAME, SKILL_VERSION
from core.io_utils import read_json, write_json, read_jsonl
from core.path_utils import default_runs_base_dir, ensure_run_dirs, generate_run_id, load_manifest


class MCPServer:
    """Minimal MCP stdio server for GEO Brand Audit."""

    def __init__(self):
        self.base_dir = default_runs_base_dir()
        self.schedules_path = self.base_dir / "schedules.json"

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        if method == "initialize":
            return self._response(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SKILL_NAME, "version": SKILL_VERSION},
            })
        elif method == "tools/list":
            return self._response(req_id, {"tools": self._list_tools()})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            return self._response(req_id, self._call_tool(tool_name, arguments))
        elif method == "notifications/initialized":
            return None  # No response for notifications
        else:
            return self._error(req_id, -32601, f"Method not found: {method}")

    def _response(self, req_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _error(self, req_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def _list_tools(self) -> List[Dict[str, Any]]:
        manifest_path = SKILL_ROOT / "mcp" / "manifest.json"
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            return manifest.get("tools", [])
        return []

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "geo_audit_run": self._tool_audit_run,
            "geo_audit_status": self._tool_audit_status,
            "geo_audit_report": self._tool_audit_report,
            "geo_audit_metrics": self._tool_audit_metrics,
            "geo_schedule_add": self._tool_schedule_add,
            "geo_schedule_list": self._tool_schedule_list,
            "geo_schedule_run": self._tool_schedule_run,
        }
        handler = handlers.get(name)
        if not handler:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
        try:
            return handler(args)
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}

    def _tool_audit_run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new audit run and return run_id."""
        run_id = generate_run_id()
        mode = args.get("mode", "standard")
        run_dir = self.base_dir / run_id
        ensure_run_dirs(run_dir)

        # Write brand config
        brand_config = {
            "brand_name": args["brand_name"],
            "website": args["website"],
            "industry": args["industry"],
            "target_customer": args["target_customer"],
            "target_region": args.get("target_region", "global"),
            "competitors": args.get("competitors", []),
        }
        write_json(run_dir / "input" / "brand.json", brand_config)

        # Initialize manifest
        from core.hashing import sha256_json
        from core.path_utils import new_manifest
        manifest = new_manifest(run_id, mode, sha256_json(brand_config))
        write_json(run_dir / "output" / "manifest.json", manifest)

        return {
            "content": [{
                "type": "text",
                "text": (
                    f"Audit initialized.\n"
                    f"Run ID: {run_id}\n"
                    f"Mode: {mode}\n"
                    f"Run directory: {run_dir}\n\n"
                    f"To execute the audit, run:\n"
                    f"  python {SCRIPTS_DIR / 'initialize_run.py'} --input {run_dir / 'input' / 'brand.json'} --base-dir {self.base_dir}\n\n"
                    f"Then follow the SKILL.md pipeline (Phase 2-11)."
                ),
            }],
        }

    def _tool_audit_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check audit run status."""
        run_id = args["run_id"]
        run_dir = self.base_dir / run_id
        try:
            manifest = load_manifest(run_dir)
        except FileNotFoundError:
            return {"content": [{"type": "text", "text": f"Run not found: {run_id}"}], "isError": True}

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "run_id": manifest.get("run_id"),
                    "status": manifest.get("status"),
                    "mode": manifest.get("mode"),
                    "started_at": manifest.get("started_at"),
                    "updated_at": manifest.get("updated_at"),
                    "completed_at": manifest.get("completed_at"),
                    "question_count": manifest.get("question_count"),
                    "search_result_count": manifest.get("search_result_count"),
                    "successful_result_count": manifest.get("successful_result_count"),
                    "warnings": manifest.get("warnings", []),
                    "errors": manifest.get("errors", []),
                }, indent=2, ensure_ascii=False),
            }],
        }

    def _tool_audit_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get audit report."""
        run_id = args["run_id"]
        fmt = args.get("format", "markdown")
        run_dir = self.base_dir / run_id

        ext = "md" if fmt == "markdown" else "json"
        report_path = run_dir / "output" / f"report.{ext}"
        if not report_path.exists():
            return {"content": [{"type": "text", "text": f"Report not found: {report_path}"}], "isError": True}

        content = report_path.read_text(encoding="utf-8")
        return {"content": [{"type": "text", "text": content}]}

    def _tool_audit_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get computed metrics, optionally filtered by tier."""
        run_id = args["run_id"]
        tier_filter = args.get("tier", "all")
        run_dir = self.base_dir / run_id
        metrics_path = run_dir / "intermediate" / "metrics.json"

        if not metrics_path.exists():
            return {"content": [{"type": "text", "text": "Metrics not found. Run calculate_metrics.py first."}], "isError": True}

        metrics = read_json(metrics_path)

        if tier_filter != "all":
            # Tier mapping for v5.0 ceiling metrics
            tier_map = {
                "multimodal_score": "T3",
                "predict_30d": "T3",
                "predict_90d": "T3",
                "predict_confidence": "T3",
                "agentic_engine_status": "T3",
                "agentic_cycle_count": "T3",
                "agentic_conversion_rate": "T2",
                "agent_ready_score": "T2",
                "a2a_score": "T2",
                "hallucinations_detected": "T2",
                "entity_kg_score": "T2",
                "i18n_score": "T2",
            }
            # Default T1 for metrics not in tier_map
            filtered = {}
            for k, v in metrics.items():
                metric_tier = tier_map.get(k, "T1")
                if metric_tier == tier_filter:
                    filtered[k] = v
            metrics = filtered

        return {"content": [{"type": "text", "text": json.dumps(metrics, indent=2, ensure_ascii=False)}]}

    def _tool_schedule_add(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a scheduled audit."""
        from scheduler import Scheduler
        scheduler = Scheduler(self.schedules_path)
        schedule = scheduler.add_schedule(
            name=args["name"],
            brand_config=args["brand_config"],
            cron_expression=args.get("cron", "0 2 * * 1"),
            mode=args.get("mode", "standard"),
        )
        return {"content": [{"type": "text", "text": f"Schedule '{schedule['name']}' added. Cron: {schedule['cron']}"}]}

    def _tool_schedule_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all schedules."""
        from scheduler import Scheduler
        scheduler = Scheduler(self.schedules_path)
        schedules = scheduler.list_schedules()
        return {"content": [{"type": "text", "text": json.dumps(schedules, indent=2, ensure_ascii=False)}]}

    def _tool_schedule_run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific schedule."""
        from scheduler import Scheduler
        scheduler = Scheduler(self.schedules_path)
        result = scheduler.run_schedule(args["name"])
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]}


def main():
    """Stdio MCP server loop."""
    server = MCPServer()
    # MCP uses newline-delimited JSON over stdio
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = server.handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()