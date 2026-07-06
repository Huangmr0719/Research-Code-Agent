#!/usr/bin/env python3
"""Create a simple experiment summary from logs and optional JSON results."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional


METRIC_PATTERNS = {
    "accuracy": re.compile(r"(?i)\baccuracy\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "acc": re.compile(r"(?i)\bacc\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "F1": re.compile(r"(?i)\bF1\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "UF1": re.compile(r"(?i)\bUF1\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "UAR": re.compile(r"(?i)\bUAR\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "loss": re.compile(r"(?i)\bloss\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "val_loss": re.compile(r"(?i)\bval_loss\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
    "best_epoch": re.compile(r"(?i)\bbest_epoch\b\s*[:=]\s*(-?\d+(?:\.\d+)?)"),
}


def load_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def read_log(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def extract_metrics_from_json(*objects: Dict[str, Any]) -> Dict[str, Any]:
    metrics = {}  # type: Dict[str, Any]
    keys = set(METRIC_PATTERNS)
    for obj in objects:
        if not obj:
            continue
        source = obj.get("metrics") if isinstance(obj.get("metrics"), dict) else obj
        for key, value in source.items():
            if key in keys or key.lower() in {k.lower() for k in keys}:
                metrics[key] = value
    return metrics


def extract_metrics_from_log(log_text: str) -> Dict[str, Any]:
    metrics = {}  # type: Dict[str, Any]
    for key, pattern in METRIC_PATTERNS.items():
        matches = pattern.findall(log_text)
        if matches:
            value = matches[-1]
            metrics[key] = float(value) if "." in value else int(value)
    return metrics


def find_failure_summary(log_text: str, status: str) -> str:
    if status == "success":
        return ""
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    keywords = ("error", "exception", "failed", "traceback", "cuda out of memory", "out of memory", "interrupted")
    selected = [line for line in lines if any(keyword in line.lower() for keyword in keywords)]
    if selected:
        return "\n".join(selected[-12:])
    return "\n".join(lines[-12:])


def format_duration(seconds: Any) -> str:
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "unknown"
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def write_markdown(path: Path, summary: Dict[str, Any]) -> None:
    metrics = summary.get("metrics") or {}
    failure_summary = summary.get("failure_summary") or ""
    metric_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(metrics.items())) or "- none"

    content = f"""# Experiment Summary: {summary['experiment_name']}

## Run

- Experiment: {summary['experiment_name']}
- Status: {summary['status']}
- Command: `{summary.get('command', 'unknown')}`
- Host: {summary.get('host', 'unknown')}
- Git commit: {summary.get('git_commit', 'unknown')}
- Start time: {summary.get('start_time', 'unknown')}
- End time: {summary.get('end_time', 'unknown')}
- Duration: {format_duration(summary.get('duration_seconds'))}
- Log path: {summary.get('log_path', 'unknown')}

## Core Metrics

{metric_lines}

## Failure Summary

{failure_summary or 'none'}

## Next Steps

- TODO: Record the next action after reviewing this run.
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--metrics-json")
    parser.add_argument("--result-json")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_json(args.result_json)
    metrics_json = load_json(args.metrics_json)
    log_text = read_log(args.log)
    metrics = extract_metrics_from_json(metrics_json, metadata)
    if not metrics:
        metrics = extract_metrics_from_log(log_text)

    summary = {
        "experiment_name": args.name,
        "status": args.status,
        "command": metadata.get("command", "unknown"),
        "host": metadata.get("host", "unknown"),
        "git_commit": metadata.get("git_commit", "unknown"),
        "start_time": metadata.get("start_time", "unknown"),
        "end_time": metadata.get("end_time", "unknown"),
        "duration_seconds": metadata.get("duration_seconds"),
        "log_path": metadata.get("log_path", args.log),
        "metrics": metrics,
        "failure_summary": find_failure_summary(log_text, args.status),
    }

    json_path = output_dir / f"{args.name}.summary.json"
    md_path = output_dir / f"{args.name}.summary.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, summary)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
