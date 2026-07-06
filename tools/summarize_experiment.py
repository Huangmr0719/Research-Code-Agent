#!/usr/bin/env python3
"""Extract factual experiment summary data from logs and optional JSON results."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _try_adapter(project_root: str, log_path: Optional[str], output_dir: Optional[str]) -> Dict[str, Any]:
    """Try to load project_results_adapter.py and call extract_metrics."""
    script_dir = Path(__file__).parent
    adapter_path = script_dir / "project_results_adapter.py"
    if not adapter_path.is_file():
        return {"metrics": {}, "metrics_source": "none", "adapter_status": "skip", "warnings": []}

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("project_results_adapter", adapter_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.extract_metrics(project_root, log_path=log_path, output_dir=output_dir)
        metrics = result.get("metrics", {})
        source = result.get("metrics_source", "none")
        warnings = result.get("warnings", [])
        if metrics:
            return {"metrics": metrics, "metrics_source": source, "adapter_status": "ok", "adapter_warnings": warnings}
        return {"metrics": {}, "metrics_source": source, "adapter_status": "empty", "adapter_warnings": warnings}
    except Exception as exc:
        return {"metrics": {}, "metrics_source": "none", "adapter_status": "error", "adapter_error": str(exc), "adapter_warnings": []}


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

MAX_LOG_TAIL_LINES = 80
MAX_LOG_TAIL_LINE_CHARS = 300


def load_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def read_log(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def extract_metrics_from_json(*objects: Dict[str, Any]) -> Dict[str, Any]:
    metrics = {}  # type: Dict[str, Any]
    canonical = {key.lower(): key for key in METRIC_PATTERNS}
    for obj in objects:
        if not obj:
            continue
        source = obj.get("metrics") if isinstance(obj.get("metrics"), dict) else obj
        for key, value in source.items():
            canonical_key = canonical.get(str(key).lower())
            if canonical_key:
                metrics[canonical_key] = value
    return metrics


def extract_metrics_from_log(log_text: str) -> Dict[str, Any]:
    metrics = {}  # type: Dict[str, Any]
    for key, pattern in METRIC_PATTERNS.items():
        matches = pattern.findall(log_text)
        if matches:
            value = matches[-1]
            metrics[key] = float(value) if "." in value else int(value)
    return metrics


def truncate_line(line: str) -> str:
    if len(line) <= MAX_LOG_TAIL_LINE_CHARS:
        return line
    return line[: MAX_LOG_TAIL_LINE_CHARS - 18].rstrip() + " ... [truncated]"


def extract_log_tail(log_text: str) -> List[str]:
    lines = log_text.splitlines()[-MAX_LOG_TAIL_LINES:]
    return [truncate_line(line) for line in lines]


def extract_traceback(log_text: str) -> List[str]:
    lines = log_text.splitlines()
    lower_lines = [line.lower() for line in lines]
    markers = ("traceback", "exception", "error", "cuda out of memory", "out of memory")
    indices = [idx for idx, line in enumerate(lower_lines) if any(marker in line for marker in markers)]
    if not indices:
        return []
    start = max(0, indices[-1] - 20)
    end = min(len(lines), indices[-1] + 40)
    return [truncate_line(line) for line in lines[start:end]][-80:]


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


def default_signal(status: str, exit_code: Any, metadata: Dict[str, Any]) -> str:
    signal = metadata.get("signal")
    if signal:
        return str(signal)
    try:
        code = int(exit_code)
    except (TypeError, ValueError):
        code = -1
    if status == "interrupted":
        if code == 130:
            return "SIGINT"
        if code == 143:
            return "SIGTERM"
    return "unknown"


def write_markdown(path: Path, summary: Dict[str, Any]) -> None:
    facts = summary["facts"]
    metrics = summary.get("metrics") or {}
    analysis = summary.get("analysis") or {}
    metric_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(metrics.items())) or "- No metrics found"
    tail_lines = "\n".join(summary.get("log_tail") or [])
    analysis_summary = analysis.get("concise_summary", "Agent 分析待生成。")
    note = summary.get("note") or "未填写"

    content = f"""# Experiment Summary: {summary['experiment_name']}

## Note

{note}

## Facts

- Status: {summary.get('status', 'unknown')}
- Exit code: {facts.get('exit_code', 'unknown')}
- Signal: {facts.get('signal', 'unknown')}
- Command: `{facts.get('command', 'unknown')}`
- Host: {facts.get('host', 'unknown')}
- Git commit: {facts.get('git_commit', 'unknown')}
- Start time: {facts.get('start_time', 'unknown')}
- End time: {facts.get('end_time', 'unknown')}
- Duration: {facts.get('duration', 'unknown')}
- Log path: {facts.get('log_path', 'unknown')}

## Metrics

{metric_lines}

## Agent Analysis

{analysis_summary}

## Log Tail

```text
{tail_lines}
```
"""
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--log", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--metrics-json")
    parser.add_argument("--result-json")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_json(args.result_json)
    metrics_json = load_json(args.metrics_json)
    log_text = read_log(args.log)

    adapter_result = _try_adapter(args.project_root, args.log, args.output_dir)
    adapter_status = adapter_result.get("adapter_status", "skip")
    adapter_error = adapter_result.get("adapter_error")
    adapter_warnings = adapter_result.get("adapter_warnings", [])
    metrics_source = adapter_result.get("metrics_source", "none")

    if adapter_status == "ok" and adapter_result.get("metrics"):
        metrics = adapter_result["metrics"]
        metrics_source = adapter_result.get("metrics_source", "adapter")
    else:
        metrics = extract_metrics_from_json(metrics_json, metadata)
        if metrics:
            metrics_source = "json"
        else:
            metrics = extract_metrics_from_log(log_text)
            if metrics:
                metrics_source = "log_regex"
            else:
                metrics_source = "none"

    exit_code = metadata.get("exit_code", "unknown")
    facts = {
        "exit_code": exit_code,
        "signal": default_signal(args.status, exit_code, metadata),
        "command": metadata.get("command", "unknown"),
        "host": metadata.get("host", "unknown"),
        "git_commit": metadata.get("git_commit", "unknown"),
        "start_time": metadata.get("start_time", "unknown"),
        "end_time": metadata.get("end_time", "unknown"),
        "duration_seconds": metadata.get("duration_seconds"),
        "duration": format_duration(metadata.get("duration_seconds")),
        "log_path": metadata.get("log_path", args.log),
    }

    summary = {
        "experiment_name": args.name,
        "note": args.note or metadata.get("note", ""),
        "status": args.status,
        "facts": facts,
        "metrics": metrics,
        "metrics_source": metrics_source,
        "adapter_status": adapter_status,
        "log_tail": extract_log_tail(log_text),
        "traceback": extract_traceback(log_text),
        "analysis": {
            "concise_summary": "Agent 分析待生成。",
            "evidence": [],
            "possible_causes": [],
            "next_steps": [],
            "confidence": "unknown",
        },
    }

    if adapter_error:
        summary["adapter_error"] = adapter_error
    if adapter_warnings:
        summary["adapter_warnings"] = adapter_warnings

    json_path = output_dir / f"{args.name}.summary.json"
    md_path = output_dir / f"{args.name}.summary.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, summary)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
