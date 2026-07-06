#!/usr/bin/env python3
"""
Project-level metrics adapter for Research-Code-Agent.

This is a DEFAULT TEMPLATE. Agents should adapt this file to each baseline
project's actual metric output format.  Do NOT commit project-specific logic
back into the mother template repository.

Adapter priority (recommended):
  1. Reuse the project's existing metrics.json / result.json / results.json / eval_results.json
  2. Reuse CSV / wandb / tensorboard exports
  3. Extract from a stable log format
  4. LAST RESORT: minimal change to train.py / eval.py to write structured output

Usage from summarize_experiment.py:
    from project_results_adapter import extract_metrics
    result = extract_metrics(project_root, log_path, output_dir)
    # result["metrics"], result["metrics_source"], result["warnings"]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

RESULT_FILENAMES = [
    "metrics.json",
    "result.json",
    "results.json",
    "eval_results.json",
]

SEARCH_DIRS = [
    "",           # project_root itself
    "outputs",
    "results",
    "runs",
    "experiments/runs",
]


def _is_simple_value(value: Any) -> bool:
    return isinstance(value, (int, float, str, bool, type(None)))


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return data


def _extract_simple_metrics(obj: Dict[str, Any]) -> Dict[str, Any]:
    if not obj:
        return {}

    metrics_dict = obj.get("metrics") if isinstance(obj.get("metrics"), dict) else obj

    result = {}
    for key, value in metrics_dict.items():
        if _is_simple_value(value):
            result[str(key)] = value
    return result


def extract_metrics(
    project_root: str,
    log_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract metrics from structured result files in the project.

    Returns:
        {
            "metrics": {...},
            "metrics_source": "adapter" | "none",
            "warnings": [...]
        }
    """
    warnings: List[str] = []
    root = Path(project_root)

    search_paths: List[Path] = []
    if output_dir:
        search_paths.append(Path(output_dir))
    for subdir in SEARCH_DIRS:
        search_paths.append(root / subdir)

    for search_dir in search_paths:
        for filename in RESULT_FILENAMES:
            candidate = search_dir / filename
            if not candidate.is_file():
                continue
            try:
                data = _load_json(candidate)
                metrics = _extract_simple_metrics(data)
                if metrics:
                    return {
                        "metrics": metrics,
                        "metrics_source": "adapter",
                        "warnings": warnings,
                    }
            except Exception as exc:
                warnings.append(f"Failed to read {candidate}: {exc}")

    warnings.append("No structured metrics file found by project_results_adapter.py")
    return {
        "metrics": {},
        "metrics_source": "none",
        "warnings": warnings,
    }


if __name__ == "__main__":
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    result = extract_metrics(root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
