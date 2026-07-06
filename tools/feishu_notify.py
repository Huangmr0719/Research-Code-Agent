#!/usr/bin/env python3
"""Send a research experiment notification through a local Feishu CLI."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


TITLES = {
    "success": "✅ 实验完成",
    "failed": "❌ 实验失败",
    "interrupted": "⚠️ 实验中断",
}

COLORS = {
    "success": "green",
    "failed": "red",
    "interrupted": "orange",
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
    except json.JSONDecodeError as exc:
        print(f"Warning: failed to parse JSON {path}: {exc}", file=sys.stderr)
        return {}


def read_text(path: Optional[str]) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


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


def flatten_metrics(metrics: Any) -> Dict[str, Any]:
    if not isinstance(metrics, dict):
        return {}
    if isinstance(metrics.get("metrics"), dict):
        return metrics["metrics"]
    return metrics


def build_message(args: argparse.Namespace) -> str:
    metadata = load_json(args.metadata)
    summary = load_json(args.summary)
    metrics = flatten_metrics(summary.get("metrics") or metadata.get("metrics"))
    tail_log = read_text(args.tail_log).strip()

    status = args.status
    title = TITLES.get(status, f"Experiment {status}")
    lines = [
        title,
        "",
        f"experiment name: {args.name}",
        f"status: {status}",
        f"host: {metadata.get('host', 'unknown')}",
        f"git commit: {metadata.get('git_commit', 'unknown')}",
        f"command: {metadata.get('command', 'unknown')}",
        f"start time: {metadata.get('start_time', 'unknown')}",
        f"end time: {metadata.get('end_time', 'unknown')}",
        f"duration: {format_duration(metadata.get('duration_seconds'))}",
        f"log path: {metadata.get('log_path', 'unknown')}",
    ]

    if metrics:
        lines.append("")
        lines.append("metrics:")
        for key in sorted(metrics):
            lines.append(f"- {key}: {metrics[key]}")
    else:
        lines.append("metrics: none")

    if tail_log and status in {"failed", "interrupted"}:
        lines.append("")
        lines.append("last 80 log lines:")
        lines.append(tail_log)

    return "\n".join(lines)


def build_card_payload(args: argparse.Namespace, message: str) -> str:
    title = TITLES.get(args.status, f"Experiment {args.status}")
    color = COLORS.get(args.status, "blue")
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": message},
                }
            ],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def candidate_commands() -> List[List[str]]:
    explicit = os.environ.get("FEISHU_CLI_SEND_COMMAND", "").strip()
    if explicit:
        return [shlex.split(explicit)]

    candidates = []  # type: List[List[str]]
    for binary in ("feishu", "lark"):
        if shutil.which(binary):
            candidates.extend(
                [
                    [binary, "send", "--text"],
                    [binary, "message", "send", "--text"],
                    [binary, "notify", "--text"],
                ]
            )
    return candidates


def run_command(command_prefix: List[str], message: str, card_payload: str) -> int:
    payload = card_payload if "--card" in command_prefix else message
    command = command_prefix + [payload]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return 127
    except OSError as exc:
        print(f"Failed to run Feishu CLI: {exc}", file=sys.stderr)
        return 1

    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr.strip(), file=sys.stderr)
        if completed.stdout:
            print(completed.stdout.strip(), file=sys.stderr)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", required=True, choices=("success", "failed", "interrupted"))
    parser.add_argument("--name", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--tail-log")
    args = parser.parse_args()

    message = build_message(args)
    card_payload = build_card_payload(args, message)
    commands = candidate_commands()

    if not commands:
        print("No Feishu CLI command detected.", file=sys.stderr)
        print("Set FEISHU_CLI_SEND_COMMAND, for example:", file=sys.stderr)
        print('  export FEISHU_CLI_SEND_COMMAND="feishu send --text"', file=sys.stderr)
        print("\nNotification content:\n")
        print(message)
        return 1

    last_code = 1
    for command in commands:
        last_code = run_command(command, message, card_payload)
        if last_code == 0:
            return 0

    print("\nFeishu CLI send failed. Notification content:\n")
    print(message)
    return last_code or 1


if __name__ == "__main__":
    raise SystemExit(main())
