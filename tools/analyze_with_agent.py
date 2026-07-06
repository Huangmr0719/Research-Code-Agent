#!/usr/bin/env python3
"""Append CLI-agent analysis to an experiment summary JSON file."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


UNAVAILABLE = "Agent analysis unavailable. See facts and log tail."


def unavailable_analysis() -> Dict[str, Any]:
    return {
        "concise_summary": UNAVAILABLE,
        "evidence": [],
        "possible_causes": [],
        "next_steps": [],
        "confidence": "low",
    }


def load_summary(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError("summary JSON must contain an object")
    return value


def extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        value = json.loads(fenced.group(1))
        if isinstance(value, dict):
            return value

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        value = json.loads(text[start : end + 1])
        if isinstance(value, dict):
            return value

    raise ValueError("agent output did not contain a JSON object")


def normalize_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_analysis(value: Dict[str, Any]) -> Dict[str, Any]:
    confidence = str(value.get("confidence", "low")).strip().lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"
    concise_summary = str(value.get("concise_summary", "")).strip() or UNAVAILABLE
    return {
        "concise_summary": concise_summary,
        "evidence": normalize_list(value.get("evidence")),
        "possible_causes": normalize_list(value.get("possible_causes")),
        "next_steps": normalize_list(value.get("next_steps")),
        "confidence": confidence,
    }


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def build_prompt(summary: Dict[str, Any]) -> str:
    facts = summary.get("facts") if isinstance(summary.get("facts"), dict) else {}
    metrics = summary.get("metrics") if isinstance(summary.get("metrics"), dict) else {}
    log_tail = summary.get("log_tail") if isinstance(summary.get("log_tail"), list) else []
    traceback = summary.get("traceback") if isinstance(summary.get("traceback"), list) else []
    status = str(facts.get("status", "unknown"))

    status_instruction = {
        "success": (
            "For success, analyze whether the result looks usable, whether metrics are worth keeping, "
            "and whether seed repeats, ablations, or metric stability checks are needed."
        ),
        "failed": (
            "For failed, classify the error type, identify possible causes from evidence only, "
            "and propose concrete debugging steps."
        ),
        "interrupted": (
            "For interrupted, only analyze whether the pre-interruption log shows anomalies. "
            "Do not present unverified interruption causes as facts."
        ),
    }.get(status, "Analyze conservatively from the provided facts only.")

    return f"""You are analyzing a research experiment run from structured facts.

Use only the provided facts, metrics, traceback snippet, and last 80 log lines.
Do not infer causes that are not supported by evidence. Do not request full logs unless needed.
Return strict JSON only, with exactly these keys:
{{
  "concise_summary": "one or two sentences",
  "evidence": ["short evidence bullets from facts/metrics/log_tail"],
  "possible_causes": ["hypotheses, or [] if not applicable"],
  "next_steps": ["concrete next actions"],
  "confidence": "low|medium|high"
}}

Status-specific instruction:
{status_instruction}

Facts:
{compact_json(facts)}

Metrics:
{compact_json(metrics)}

Traceback snippet if available:
{compact_json(traceback)}

Log tail, last 80 lines:
{compact_json(log_tail)}
"""


def run_opencode(prompt: str, timeout: int) -> str:
    if shutil.which("opencode") is None:
        raise FileNotFoundError("opencode CLI not found")
    completed = subprocess.run(
        ["opencode", "run", prompt],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "opencode failed")
    return completed.stdout


def write_summary(path: Path, summary: Dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    path = Path(args.summary)
    summary = load_summary(path)
    prompt = build_prompt(summary)

    try:
        output = run_opencode(prompt, args.timeout)
        analysis = normalize_analysis(extract_json_object(output))
    except Exception as exc:
        analysis = unavailable_analysis()
        summary["analysis_error"] = str(exc)

    summary["analysis"] = analysis
    write_summary(path, summary)
    print(f"Updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
