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

if ! command -v python3 >/dev/null 2>&1; then
  printf 'python3 is required for RCA JSON record updates.\n' >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RCA_DIR="$PROJECT_DIR/.rca"
RUNS_DIR="$RCA_DIR/runs"
TMP_DIR="$RCA_DIR/tmp"
EXPERIMENTS_JSON="$RCA_DIR/experiments.json"
LOCK_FILE="$RCA_DIR/experiments.lock"
LOCK_DIR="$RCA_DIR/experiments.lockdir"

mkdir -p "$RUNS_DIR" "$RCA_DIR/plans" "$TMP_DIR"

sanitize_name() {
  printf '%s' "$1" | tr -cs 'A-Za-z0-9._-' '_' | sed 's/^_*//; s/_*$//'
}

SAFE_NAME="$(sanitize_name "$RUN_NAME")"
if [[ -z "$SAFE_NAME" ]]; then
  SAFE_NAME="run"
fi

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
RUN_ID="${TIMESTAMP}_${SAFE_NAME}"
RUN_DIR="$RUNS_DIR/$RUN_ID"
attempt=0
while ! mkdir "$RUN_DIR" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [[ "$attempt" -gt 20 ]]; then
    printf 'Failed to create unique run directory under %s\n' "$RUNS_DIR" >&2
    exit 1
  fi
  RANDOM_SUFFIX="$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')"
  RUN_ID="${TIMESTAMP}_${SAFE_NAME}_${RANDOM_SUFFIX}"
  RUN_DIR="$RUNS_DIR/$RUN_ID"
done

COMMAND_PATH="$RUN_DIR/command.sh"
STDOUT_PATH="$RUN_DIR/stdout.log"
STDERR_PATH="$RUN_DIR/stderr.log"
SUMMARY_PATH="$RUN_DIR/summary.json"
FAILURE_PATH="$RUN_DIR/failure.json"
ERROR_TAIL_PATH="$RUN_DIR/error_tail.txt"

COMMAND_DISPLAY="$(printf '%q ' "$@")"
WORKING_DIRECTORY="$(pwd)"
START_EPOCH="$(date +%s)"
START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  printf '#!/usr/bin/env bash\n'
  printf 'set -Eeuo pipefail\n'
  printf 'cd %q\n' "$WORKING_DIRECTORY"
  printf '%s\n' "$COMMAND_DISPLAY"
} > "$COMMAND_PATH.tmp"
mv "$COMMAND_PATH.tmp" "$COMMAND_PATH"
chmod +x "$COMMAND_PATH"

set +e
"$@" >"$STDOUT_PATH" 2>"$STDERR_PATH"
EXIT_CODE=$?
set -e

END_EPOCH="$(date +%s)"
END_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
DURATION_SECONDS="$((END_EPOCH - START_EPOCH))"
if [[ "$EXIT_CODE" -eq 0 ]]; then
  STATUS="success"
else
  STATUS="failed"
  tail -n 80 "$STDERR_PATH" > "$ERROR_TAIL_PATH" 2>/dev/null || true
fi

RCA_RUN_ID="$RUN_ID" \
RCA_STATUS="$STATUS" \
RCA_TASK_TYPE="$TASK_TYPE" \
RCA_USER_NOTE_INITIAL="$USER_NOTE_INITIAL" \
RCA_COMMAND="$COMMAND_DISPLAY" \
RCA_WORKING_DIRECTORY="$WORKING_DIRECTORY" \
RCA_START_TIME="$START_TIME" \
RCA_END_TIME="$END_TIME" \
RCA_DURATION_SECONDS="$DURATION_SECONDS" \
RCA_EXIT_CODE="$EXIT_CODE" \
RCA_STDOUT_PATH="$STDOUT_PATH" \
RCA_STDERR_PATH="$STDERR_PATH" \
RCA_COMMAND_PATH="$COMMAND_PATH" \
RCA_SUMMARY_PATH="$SUMMARY_PATH" \
RCA_DATASET="$DATASET" \
RCA_CONFIG="$CONFIG_PATH" \
RCA_FAILURE_PATH="$FAILURE_PATH" \
RCA_ERROR_TAIL_PATH="$ERROR_TAIL_PATH" \
python3 - <<'PY'
import json
import os
from pathlib import Path

summary_path = Path(os.environ["RCA_SUMMARY_PATH"])
status = os.environ["RCA_STATUS"]
summary = {
    "run_id": os.environ["RCA_RUN_ID"],
    "status": status,
    "task_type": os.environ.get("RCA_TASK_TYPE", ""),
    "user_note_initial": os.environ.get("RCA_USER_NOTE_INITIAL", ""),
    "ai_note_final": None,
    "command": os.environ.get("RCA_COMMAND", "").strip(),
    "working_directory": os.environ.get("RCA_WORKING_DIRECTORY", ""),
    "start_time": os.environ.get("RCA_START_TIME", ""),
    "end_time": os.environ.get("RCA_END_TIME", ""),
    "duration_seconds": int(os.environ.get("RCA_DURATION_SECONDS", "0")),
    "exit_code": int(os.environ.get("RCA_EXIT_CODE", "1")),
    "dataset": os.environ.get("RCA_DATASET", ""),
    "config": os.environ.get("RCA_CONFIG", ""),
    "metrics": {},
    "artifacts": {
        "stdout": os.environ["RCA_STDOUT_PATH"],
        "stderr": os.environ["RCA_STDERR_PATH"],
        "command": os.environ["RCA_COMMAND_PATH"],
        "summary": os.environ["RCA_SUMMARY_PATH"],
    },
    "conclusion": None,
}
if status != "success":
    summary["artifacts"]["failure"] = os.environ["RCA_FAILURE_PATH"]
    summary["artifacts"]["error_tail"] = os.environ["RCA_ERROR_TAIL_PATH"]
tmp_path = summary_path.with_name(summary_path.name + ".tmp")
tmp_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
json.loads(tmp_path.read_text(encoding="utf-8"))
tmp_path.replace(summary_path)
PY

if [[ "$STATUS" != "success" ]]; then
  RCA_FAILURE_STATUS="$STATUS" \
  RCA_EXIT_CODE="$EXIT_CODE" \
  RCA_ERROR_TAIL_PATH="$ERROR_TAIL_PATH" \
  RCA_FAILURE_PATH="$FAILURE_PATH" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

tail_path = Path(os.environ["RCA_ERROR_TAIL_PATH"])
failure = {
    "status": os.environ["RCA_FAILURE_STATUS"],
    "exit_code": int(os.environ["RCA_EXIT_CODE"]),
    "error_tail": tail_path.read_text(encoding="utf-8", errors="replace").splitlines() if tail_path.exists() else [],
}
path = Path(os.environ["RCA_FAILURE_PATH"])
tmp_path = path.with_name(path.name + ".tmp")
tmp_path.write_text(json.dumps(failure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
json.loads(tmp_path.read_text(encoding="utf-8"))
tmp_path.replace(path)
PY
fi

update_ledger() {
  python3 - "$EXPERIMENTS_JSON" "$SUMMARY_PATH" <<'PY'
import json
import sys
from pathlib import Path

ledger_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text(encoding="utf-8"))

if ledger_path.exists():
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
else:
    ledger = []
if not isinstance(ledger, list):
    raise SystemExit(".rca/experiments.json must be a JSON array")

record = {
    "run_id": summary["run_id"],
    "created_at": summary["start_time"],
    "status": summary["status"],
    "task_type": summary.get("task_type", ""),
    "user_note_initial": summary.get("user_note_initial", ""),
    "ai_note_final": summary.get("ai_note_final"),
    "command": summary.get("command", ""),
    "dataset": summary.get("dataset", ""),
    "config": summary.get("config", ""),
    "metrics": summary.get("metrics", {}),
    "artifacts": summary.get("artifacts", {}),
    "conclusion": summary.get("conclusion"),
}
ledger = [item for item in ledger if not isinstance(item, dict) or item.get("run_id") != record["run_id"]]
ledger.append(record)

tmp_path = ledger_path.with_name(ledger_path.name + ".tmp")
tmp_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
json.loads(tmp_path.read_text(encoding="utf-8"))
tmp_path.replace(ledger_path)
PY
}

if command -v flock >/dev/null 2>&1; then
  (
    flock -x 9
    update_ledger
  ) 9>"$LOCK_FILE"
else
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    sleep 1
  done
  trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT INT TERM
  update_ledger
  rmdir "$LOCK_DIR" 2>/dev/null || true
fi

printf 'RCA run recorded: %s\n' "$RUN_ID"
printf 'Summary: %s\n' "$SUMMARY_PATH"
printf 'Experiment ledger: %s\n' "$EXPERIMENTS_JSON"

exit "$EXIT_CODE"
