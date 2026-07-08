#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./.rca/scripts/run_experiment.sh --name RUN_NAME --note "中文实验备注" --confirm [options] -- COMMAND [ARGS...]

Options:
  --name NAME        Short experiment name, for example baseline_default
  --note NOTE        Required user initial note in Chinese
  --task-type TYPE   Optional task type, for example baseline or ablation
  --dataset NAME     Optional dataset name
  --config PATH      Optional config path
  --confirm          Required after the user explicitly confirms the experiment plan

Example:
  ./.rca/scripts/run_experiment.sh \
    --name baseline_default \
    --note "跑一次原始 baseline，后面做消融对照" \
    --confirm \
    --task-type baseline \
    --config configs/default.yaml \
    -- python train.py --config configs/default.yaml
EOF
}

RUN_NAME=""
USER_NOTE_INITIAL=""
TASK_TYPE=""
DATASET=""
CONFIG_PATH=""
CONFIRMED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      RUN_NAME="${2:-}"
      shift 2
      ;;
    --note)
      USER_NOTE_INITIAL="${2:-}"
      shift 2
      ;;
    --task-type)
      TASK_TYPE="${2:-}"
      shift 2
      ;;
    --dataset)
      DATASET="${2:-}"
      shift 2
      ;;
    --config)
      CONFIG_PATH="${2:-}"
      shift 2
      ;;
    --confirm)
      CONFIRMED=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$RUN_NAME" || -z "$USER_NOTE_INITIAL" || "$CONFIRMED" -ne 1 || $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXPERIMENTS_JSON="$PROJECT_DIR/.rca/experiments.json"
LEGACY_WRAPPER="$PROJECT_DIR/tools/run_with_feishu_notify.sh"
LOCK_DIR="$PROJECT_DIR/.rca/run.lock"

mkdir -p "$PROJECT_DIR/.rca/runs" "$PROJECT_DIR/.rca/plans" "$PROJECT_DIR/.rca/tmp"

cleanup_lock() {
  if [[ -n "${LOCK_ACQUIRED:-}" ]]; then
    rmdir "$LOCK_DIR" 2>/dev/null || true
  fi
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  printf 'Another RCA experiment is already running. Lock: %s\n' "$LOCK_DIR" >&2
  exit 1
fi
LOCK_ACQUIRED=1
trap cleanup_lock EXIT INT TERM

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
RUN_ID="${TIMESTAMP}_${RUN_NAME}"
RUN_DIR="$PROJECT_DIR/.rca/runs/$RUN_ID"
SUMMARY_JSON="$PROJECT_DIR/experiments/summaries/${RUN_ID}.summary.json"
mkdir -p "$RUN_DIR"

if [[ ! -x "$LEGACY_WRAPPER" ]]; then
  printf 'Missing executable wrapper: %s\n' "$LEGACY_WRAPPER" >&2
  exit 1
fi

COMMAND_DISPLAY="$(printf '%q ' "$@")"

set +e
"$LEGACY_WRAPPER" --name "$RUN_ID" --note "$USER_NOTE_INITIAL" -- "$@"
EXIT_CODE=$?
set -e

if [[ -f "$SUMMARY_JSON" ]]; then
  cp "$SUMMARY_JSON" "$RUN_DIR/summary.json.tmp"
else
  printf '{"experiment_name":"%s","note":"%s","status":"failed","metrics":{},"facts":{"command":"%s"}}\n' \
    "$RUN_ID" "$USER_NOTE_INITIAL" "$COMMAND_DISPLAY" > "$RUN_DIR/summary.json.tmp"
fi
mv "$RUN_DIR/summary.json.tmp" "$RUN_DIR/summary.json"

RCA_RUN_ID="$RUN_ID" \
RCA_TASK_TYPE="$TASK_TYPE" \
RCA_DATASET="$DATASET" \
RCA_CONFIG="$CONFIG_PATH" \
RCA_USER_NOTE_INITIAL="$USER_NOTE_INITIAL" \
RCA_COMMAND="$COMMAND_DISPLAY" \
RCA_EXIT_CODE="$EXIT_CODE" \
python3 - "$EXPERIMENTS_JSON" "$RUN_DIR/summary.json" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

index_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])

try:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
except Exception:
    summary = {}

if index_path.exists():
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        index = {"schema_version": 1, "experiments": []}
else:
    index = {"schema_version": 1, "experiments": []}

experiments = index.setdefault("experiments", [])
run_id = os.environ["RCA_RUN_ID"]
facts = summary.get("facts") if isinstance(summary.get("facts"), dict) else {}
metrics = summary.get("metrics") if isinstance(summary.get("metrics"), dict) else {}
status = summary.get("status") or ("success" if os.environ.get("RCA_EXIT_CODE") == "0" else "failed")
command = facts.get("command") or os.environ.get("RCA_COMMAND", "").strip()
log_path = facts.get("log_path", "")

record = {
    "run_id": run_id,
    "created_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    "status": status,
    "task_type": os.environ.get("RCA_TASK_TYPE", ""),
    "user_note_initial": os.environ.get("RCA_USER_NOTE_INITIAL", ""),
    "ai_note_final": "",
    "command": command,
    "dataset": os.environ.get("RCA_DATASET", ""),
    "config": os.environ.get("RCA_CONFIG", ""),
    "metrics": metrics,
    "artifacts": {
        "summary": str(summary_path),
        "stdout": log_path,
        "stderr": log_path,
        "checkpoint": "",
    },
    "conclusion": "",
}

experiments[:] = [item for item in experiments if item.get("run_id") != run_id]
experiments.append(record)
index_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = index_path.with_name(index_path.name + ".tmp")
tmp_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
tmp_path.replace(index_path)
PY

printf 'RCA run recorded: %s\n' "$RUN_ID"
printf 'Summary: %s\n' "$RUN_DIR/summary.json"
printf 'Experiment index: %s\n' "$EXPERIMENTS_JSON"

exit "$EXIT_CODE"
