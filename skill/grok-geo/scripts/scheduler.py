#!/usr/bin/env python3
"""Scheduled audit execution for GEO brand audit."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class Scheduler:
    """Manage scheduled audits."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("./schedules.json")
        self.schedules: List[Dict[str, Any]] = self._load_schedules()
    
    def _load_schedules(self) -> List[Dict[str, Any]]:
        """Load schedule configurations."""
        if not self.config_path.exists():
            return []
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_schedules(self):
        """Save schedules to config file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.schedules, f, indent=2)
    
    def add_schedule(
        self,
        name: str,
        brand_config: Dict[str, Any],
        cron_expression: str = "0 2 * * *",
        engines: Optional[List[str]] = None,
        mode: str = "standard"
    ) -> Dict[str, Any]:
        """Add a new scheduled audit."""
        schedule = {
            "name": name,
            "brand_config": brand_config,
            "cron": cron_expression,
            "engines": engines or [],
            "mode": mode,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "last_status": None,
            "next_run": None
        }
        
        # Check if schedule already exists
        existing_idx = next((i for i, s in enumerate(self.schedules) if s["name"] == name), None)
        if existing_idx is not None:
            self.schedules[existing_idx] = schedule
        else:
            self.schedules.append(schedule)
        
        self._save_schedules()
        return schedule
    
    def remove_schedule(self, name: str) -> bool:
        """Remove a scheduled audit."""
        original_len = len(self.schedules)
        self.schedules = [s for s in self.schedules if s["name"] != name]
        if len(self.schedules) < original_len:
            self._save_schedules()
            return True
        return False
    
    def enable_schedule(self, name: str) -> bool:
        """Enable a scheduled audit."""
        for schedule in self.schedules:
            if schedule["name"] == name:
                schedule["enabled"] = True
                self._save_schedules()
                return True
        return False
    
    def disable_schedule(self, name: str) -> bool:
        """Disable a scheduled audit."""
        for schedule in self.schedules:
            if schedule["name"] == name:
                schedule["enabled"] = False
                self._save_schedules()
                return True
        return False
    
    def run_schedule(self, name: str) -> Dict[str, Any]:
        """Execute a scheduled audit."""
        schedule = next((s for s in self.schedules if s["name"] == name), None)
        if not schedule:
            return {"success": False, "error": f"Schedule '{name}' not found"}
        
        if not schedule["enabled"]:
            return {"success": False, "error": f"Schedule '{name}' is disabled"}
        
        try:
            # Prepare input file
            input_file = self.config_path.parent / f"schedule_input_{name}.json"
            with open(input_file, "w", encoding="utf-8") as f:
                json.dump(schedule["brand_config"], f)
            
            # Build command
            cmd = [
                sys.executable,
                str(Path(__file__).parent / "initialize_run.py"),
                "--input", str(input_file),
                "--mode", schedule.get("mode", "standard")
            ]
            
            if schedule.get("engines"):
                cmd.extend(["--engines", ",".join(schedule["engines"])])
            
            # Execute
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Update schedule status
            schedule["last_run"] = datetime.now().isoformat()
            schedule["last_status"] = "success" if result.returncode == 0 else "failed"
            self._save_schedules()
            
            # Cleanup
            input_file.unlink(missing_ok=True)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            schedule["last_run"] = datetime.now().isoformat()
            schedule["last_status"] = "timeout"
            self._save_schedules()
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            schedule["last_run"] = datetime.now().isoformat()
            schedule["last_status"] = "error"
            self._save_schedules()
            return {"success": False, "error": str(e)}
    
    def run_all_enabled(self) -> Dict[str, Dict[str, Any]]:
        """Run all enabled schedules."""
        results = {}
        for schedule in self.schedules:
            if schedule["enabled"]:
                results[schedule["name"]] = self.run_schedule(schedule["name"])
        return results
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all schedules."""
        return self.schedules
    
    def get_schedule(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific schedule."""
        return next((s for s in self.schedules if s["name"] == name), None)


def generate_cron_command(schedule_name: str, script_path: Path, cron: str = "0 2 * * *") -> str:
    """Generate crontab command for a schedule."""
    python_path = sys.executable
    return f"{cron} cd {script_path.parent.parent} && {python_path} {script_path} --run {schedule_name}"


def generate_windows_task_command(schedule_name: str, script_path: Path, time: str = "02:00") -> str:
    """Generate Windows Task Scheduler command."""
    python_path = sys.executable
    return f'schtasks /create /tn "GEOAudit_{schedule_name}" /tr "{python_path} {script_path} --run {schedule_name}" /sc daily /st {time}'


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GEO Brand Audit Scheduler")
    parser.add_argument("--config", type=str, default="./schedules.json", help="Schedule config file")
    parser.add_argument("--run", type=str, help="Run a specific schedule")
    parser.add_argument("--run-all", action="store_true", help="Run all enabled schedules")
    parser.add_argument("--list", action="store_true", help="List all schedules")
    parser.add_argument("--add", type=str, help="Add a new schedule (name)")
    parser.add_argument("--brand-config", type=str, help="Brand config JSON file for --add")
    parser.add_argument("--cron", type=str, default="0 2 * * *", help="Cron expression for --add")
    parser.add_argument("--remove", type=str, help="Remove a schedule")
    parser.add_argument("--enable", type=str, help="Enable a schedule")
    parser.add_argument("--disable", type=str, help="Disable a schedule")
    
    args = parser.parse_args()
    
    scheduler = Scheduler(Path(args.config))
    
    if args.list:
        schedules = scheduler.list_schedules()
        if not schedules:
            print("No schedules configured.")
        else:
            for s in schedules:
                status = "enabled" if s["enabled"] else "disabled"
                print(f"  {s['name']} [{status}] cron={s['cron']} last_run={s['last_run'] or 'never'}")
    
    elif args.run:
        result = scheduler.run_schedule(args.run)
        print(f"Schedule '{args.run}': {'SUCCESS' if result['success'] else 'FAILED'}")
        if result.get("stdout"):
            print(result["stdout"])
        if result.get("stderr"):
            print(result["stderr"], file=sys.stderr)
    
    elif args.run_all:
        results = scheduler.run_all_enabled()
        for name, result in results.items():
            print(f"  {name}: {'SUCCESS' if result['success'] else 'FAILED'}")
    
    elif args.add:
        if not args.brand_config:
            print("Error: --brand-config required for --add")
            sys.exit(1)
        with open(args.brand_config, "r") as f:
            brand_config = json.load(f)
        schedule = scheduler.add_schedule(args.add, brand_config, args.cron)
        print(f"Added schedule '{schedule['name']}' with cron '{schedule['cron']}'")
    
    elif args.remove:
        if scheduler.remove_schedule(args.remove):
            print(f"Removed schedule '{args.remove}'")
        else:
            print(f"Schedule '{args.remove}' not found")
    
    elif args.enable:
        if scheduler.enable_schedule(args.enable):
            print(f"Enabled schedule '{args.enable}'")
        else:
            print(f"Schedule '{args.enable}' not found")
    
    elif args.disable:
        if scheduler.disable_schedule(args.disable):
            print(f"Disabled schedule '{args.disable}'")
        else:
            print(f"Schedule '{args.disable}' not found")
    
    else:
        parser.print_help()