#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$(pwd)"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"

TEST_FEISHU=0
UPDATE_TOOLS=0

log() {
  printf '[research-init] %s\n' "$*"
}

backup_if_exists() {
  local path="$1"
  if [[ -e "$path" ]]; then
    local backup="${path}.bak.${TIMESTAMP}"
    mv "$path" "$backup"
    log "Backed up existing ${path#$TARGET_DIR/} -> ${backup#$TARGET_DIR/}"
  fi
}

copy_file() {
  local src="$1"
  local dst="$2"
  backup_if_exists "$dst"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  log "Created ${dst#$TARGET_DIR/}"
}

copy_file_if_missing() {
  local src="$1"
  local dst="$2"
  if [[ -e "$dst" ]]; then
    log "Skipped ${dst#$TARGET_DIR/} (already exists)"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  log "Created ${dst#$TARGET_DIR/}"
}

install_agents_file() {
  local section="$SCRIPT_DIR/templates/AGENTS_RCA_SECTION.md"
  local dst="$TARGET_DIR/AGENTS.md"
  if [[ ! -f "$dst" ]]; then
    cp "$section" "$dst"
    log "Created AGENTS.md"
    return
  fi
  if grep -q "## Research-Code-Agent" "$dst"; then
    log "Skipped AGENTS.md (Research-Code-Agent section already exists)"
    return
  fi
  {
    printf '\n'
    cat "$section"
  } >> "$dst"
  log "Appended Research-Code-Agent section to AGENTS.md"
}

ensure_dir() {
  local dir="$1"
  mkdir -p "$dir"
  log "Ensured directory ${dir#$TARGET_DIR/}"
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    printf 'Missing template file: %s\n' "$path" >&2
    exit 1
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --test-feishu)
        TEST_FEISHU=1
        shift
        ;;
      --update-tools)
        UPDATE_TOOLS=1
        shift
        ;;
      -h|--help)
        cat <<'EOF'
Usage:
  bash init_research_project.sh [--test-feishu] [--update-tools]

Options:
  --test-feishu   Run Feishu smoke test after initialization
  --update-tools  Update generic tools only; do not touch project adapters or outputs
EOF
        exit 0
        ;;
      *)
        printf 'Unknown argument: %s\n' "$1" >&2
        exit 1
        ;;
    esac
  done
}

copy_generic_tools() {
  copy_file "$SCRIPT_DIR/tools/run_with_feishu_notify.sh" "$TARGET_DIR/tools/run_with_feishu_notify.sh"
  copy_file "$SCRIPT_DIR/tools/feishu_notify.py" "$TARGET_DIR/tools/feishu_notify.py"
  copy_file "$SCRIPT_DIR/tools/summarize_experiment.py" "$TARGET_DIR/tools/summarize_experiment.py"
  copy_file "$SCRIPT_DIR/tools/analyze_with_agent.py" "$TARGET_DIR/tools/analyze_with_agent.py"
  copy_file "$SCRIPT_DIR/tools/compare_experiments.py" "$TARGET_DIR/tools/compare_experiments.py"
  copy_file "$SCRIPT_DIR/tools/test_feishu_notify.sh" "$TARGET_DIR/tools/test_feishu_notify.sh"
  copy_file "$SCRIPT_DIR/tools/init_paper_context.sh" "$TARGET_DIR/tools/init_paper_context.sh"
  copy_file "$SCRIPT_DIR/tools/feishu_opencode_bridge.py" "$TARGET_DIR/tools/feishu_opencode_bridge.py"
  copy_file "$SCRIPT_DIR/tools/feishu_card_renderer.py" "$TARGET_DIR/tools/feishu_card_renderer.py"
  copy_file "$SCRIPT_DIR/tools/test_feishu_opencode_bridge.py" "$TARGET_DIR/tools/test_feishu_opencode_bridge.py"

  chmod +x "$TARGET_DIR/tools/run_with_feishu_notify.sh"
  chmod +x "$TARGET_DIR/tools/feishu_notify.py"
  chmod +x "$TARGET_DIR/tools/summarize_experiment.py"
  chmod +x "$TARGET_DIR/tools/analyze_with_agent.py"
  chmod +x "$TARGET_DIR/tools/compare_experiments.py"
  chmod +x "$TARGET_DIR/tools/test_feishu_notify.sh"
  chmod +x "$TARGET_DIR/tools/init_paper_context.sh"
  chmod +x "$TARGET_DIR/tools/feishu_opencode_bridge.py"
  chmod +x "$TARGET_DIR/tools/feishu_card_renderer.py"
  chmod +x "$TARGET_DIR/tools/test_feishu_opencode_bridge.py"
}

main() {
  parse_args "$@"

  log "Initializing Research-Code-Agent workflow in $TARGET_DIR"

  require_file "$SCRIPT_DIR/tools/run_with_feishu_notify.sh"
  require_file "$SCRIPT_DIR/tools/feishu_notify.py"
  require_file "$SCRIPT_DIR/tools/summarize_experiment.py"
  require_file "$SCRIPT_DIR/tools/analyze_with_agent.py"
  require_file "$SCRIPT_DIR/tools/compare_experiments.py"
  require_file "$SCRIPT_DIR/tools/project_results_adapter.py"
  require_file "$SCRIPT_DIR/tools/test_feishu_notify.sh"
  require_file "$SCRIPT_DIR/tools/init_paper_context.sh"
  require_file "$SCRIPT_DIR/tools/feishu_opencode_bridge.py"
  require_file "$SCRIPT_DIR/tools/feishu_card_renderer.py"
  require_file "$SCRIPT_DIR/tools/test_feishu_opencode_bridge.py"
  require_file "$SCRIPT_DIR/bin/rca"
  require_file "$SCRIPT_DIR/skills/rca/SKILL.md"
  require_file "$SCRIPT_DIR/templates/AGENTS.md"
  require_file "$SCRIPT_DIR/templates/AGENTS_RCA_SECTION.md"
  require_file "$SCRIPT_DIR/templates/RCA.md"
  require_file "$SCRIPT_DIR/templates/README_AGENT_WORKFLOW.md"
  require_file "$SCRIPT_DIR/templates/PAPER_CONTEXT_TEMPLATE.md"
  require_file "$SCRIPT_DIR/templates/rca/README.md"
  require_file "$SCRIPT_DIR/templates/rca/profile.template.json"
  require_file "$SCRIPT_DIR/templates/rca/experiments.template.json"
  require_file "$SCRIPT_DIR/templates/rca/RCA_INIT_PROMPT.md"
  require_file "$SCRIPT_DIR/templates/rca/run_experiment.sh"
  require_file "$SCRIPT_DIR/templates/feishu_bridge.env.example"
  require_file "$SCRIPT_DIR/templates/opencode-feishu.plugin.example.json"
  require_file "$SCRIPT_DIR/templates/feishu.plugin.example.json"
  require_file "$SCRIPT_DIR/templates/opencode.remote.example.json"
  require_file "$SCRIPT_DIR/templates/systemd/opencode-serve.service"
  require_file "$SCRIPT_DIR/templates/systemd/rca-feishu-opencode-bridge.service"
  require_file "$SCRIPT_DIR/docs/opencode-feishu-adoption.md"
  require_file "$SCRIPT_DIR/docs/opencode-feishu-throwaway-test.md"
  require_file "$SCRIPT_DIR/docs/rca-final-convergence.md"
  require_file "$SCRIPT_DIR/.opencode/commands/experiment-run.md"
  require_file "$SCRIPT_DIR/.opencode/commands/experiment-summary.md"
  require_file "$SCRIPT_DIR/.opencode/commands/experiment-compare.md"
  require_file "$SCRIPT_DIR/.opencode/commands/log-tail.md"
  require_file "$SCRIPT_DIR/examples/toy_success.sh"
  require_file "$SCRIPT_DIR/examples/toy_failed.sh"

  if [[ "$UPDATE_TOOLS" -eq 1 ]]; then
    log "Updating generic tools only."
    copy_generic_tools
    log "Skipped tools/project_results_adapter.py, PAPER_CONTEXT.md, papers/, logs/, outputs/, experiments/, and project code."
    log "Done."
    exit 0
  fi

  backup_if_exists "$TARGET_DIR/README_AGENT_WORKFLOW.md"

  ensure_dir "$TARGET_DIR/papers"
  ensure_dir "$TARGET_DIR/.rca"
  ensure_dir "$TARGET_DIR/.rca/scripts"
  ensure_dir "$TARGET_DIR/.rca/runs"
  ensure_dir "$TARGET_DIR/.rca/plans"
  ensure_dir "$TARGET_DIR/logs"
  ensure_dir "$TARGET_DIR/outputs"
  ensure_dir "$TARGET_DIR/experiments"
  ensure_dir "$TARGET_DIR/experiments/summaries"
  ensure_dir "$TARGET_DIR/experiments/runs"
  ensure_dir "$TARGET_DIR/examples"
  ensure_dir "$TARGET_DIR/bin"
  ensure_dir "$TARGET_DIR/docs"
  ensure_dir "$TARGET_DIR/.opencode/commands"

  copy_generic_tools
  if [[ -f "$TARGET_DIR/tools/project_results_adapter.py" ]]; then
    log "Skipped tools/project_results_adapter.py (already exists, not overwriting project-specific adapter)"
  else
    copy_file "$SCRIPT_DIR/tools/project_results_adapter.py" "$TARGET_DIR/tools/project_results_adapter.py"
  fi
  copy_file "$SCRIPT_DIR/bin/rca" "$TARGET_DIR/bin/rca"
  chmod +x "$TARGET_DIR/bin/rca"
  copy_file "$SCRIPT_DIR/templates/RCA.md" "$TARGET_DIR/templates/RCA.md"
  copy_file "$SCRIPT_DIR/templates/rca/README.md" "$TARGET_DIR/templates/rca/README.md"
  copy_file "$SCRIPT_DIR/templates/rca/profile.template.json" "$TARGET_DIR/templates/rca/profile.template.json"
  copy_file "$SCRIPT_DIR/templates/rca/experiments.template.json" "$TARGET_DIR/templates/rca/experiments.template.json"
  copy_file "$SCRIPT_DIR/templates/rca/RCA_INIT_PROMPT.md" "$TARGET_DIR/templates/rca/RCA_INIT_PROMPT.md"
  copy_file "$SCRIPT_DIR/templates/rca/run_experiment.sh" "$TARGET_DIR/templates/rca/run_experiment.sh"
  install_agents_file
  copy_file_if_missing "$SCRIPT_DIR/templates/RCA.md" "$TARGET_DIR/RCA.md"
  copy_file_if_missing "$SCRIPT_DIR/templates/rca/README.md" "$TARGET_DIR/.rca/README.md"
  copy_file_if_missing "$SCRIPT_DIR/templates/rca/profile.template.json" "$TARGET_DIR/.rca/profile.json"
  copy_file_if_missing "$SCRIPT_DIR/templates/rca/experiments.template.json" "$TARGET_DIR/.rca/experiments.json"
  copy_file_if_missing "$SCRIPT_DIR/templates/rca/RCA_INIT_PROMPT.md" "$TARGET_DIR/.rca/RCA_INIT_PROMPT.md"
  copy_file_if_missing "$SCRIPT_DIR/templates/rca/run_experiment.sh" "$TARGET_DIR/.rca/scripts/run_experiment.sh"
  copy_file "$SCRIPT_DIR/templates/README_AGENT_WORKFLOW.md" "$TARGET_DIR/README_AGENT_WORKFLOW.md"
  copy_file "$SCRIPT_DIR/templates/PAPER_CONTEXT_TEMPLATE.md" "$TARGET_DIR/templates/PAPER_CONTEXT_TEMPLATE.md"
  copy_file "$SCRIPT_DIR/templates/feishu_bridge.env.example" "$TARGET_DIR/templates/feishu_bridge.env.example"
  copy_file "$SCRIPT_DIR/templates/opencode-feishu.plugin.example.json" "$TARGET_DIR/templates/opencode-feishu.plugin.example.json"
  copy_file "$SCRIPT_DIR/templates/feishu.plugin.example.json" "$TARGET_DIR/templates/feishu.plugin.example.json"
  copy_file "$SCRIPT_DIR/templates/opencode.remote.example.json" "$TARGET_DIR/templates/opencode.remote.example.json"
  copy_file "$SCRIPT_DIR/templates/systemd/opencode-serve.service" "$TARGET_DIR/templates/systemd/opencode-serve.service"
  copy_file "$SCRIPT_DIR/templates/systemd/rca-feishu-opencode-bridge.service" "$TARGET_DIR/templates/systemd/rca-feishu-opencode-bridge.service"
  copy_file "$SCRIPT_DIR/docs/opencode-feishu-adoption.md" "$TARGET_DIR/docs/opencode-feishu-adoption.md"
  copy_file "$SCRIPT_DIR/docs/opencode-feishu-throwaway-test.md" "$TARGET_DIR/docs/opencode-feishu-throwaway-test.md"
  copy_file "$SCRIPT_DIR/docs/rca-final-convergence.md" "$TARGET_DIR/docs/rca-final-convergence.md"
  copy_file "$SCRIPT_DIR/.opencode/commands/experiment-run.md" "$TARGET_DIR/.opencode/commands/experiment-run.md"
  copy_file "$SCRIPT_DIR/.opencode/commands/experiment-summary.md" "$TARGET_DIR/.opencode/commands/experiment-summary.md"
  copy_file "$SCRIPT_DIR/.opencode/commands/experiment-compare.md" "$TARGET_DIR/.opencode/commands/experiment-compare.md"
  copy_file "$SCRIPT_DIR/.opencode/commands/log-tail.md" "$TARGET_DIR/.opencode/commands/log-tail.md"
  copy_file "$SCRIPT_DIR/examples/toy_success.sh" "$TARGET_DIR/examples/toy_success.sh"
  copy_file "$SCRIPT_DIR/examples/toy_failed.sh" "$TARGET_DIR/examples/toy_failed.sh"

  chmod +x "$TARGET_DIR/tools/project_results_adapter.py"
  chmod +x "$TARGET_DIR/.rca/scripts/run_experiment.sh"
  chmod +x "$TARGET_DIR/examples/toy_success.sh"
  chmod +x "$TARGET_DIR/examples/toy_failed.sh"
  chmod 700 "$TARGET_DIR/.rca"

  log "Done."

  if [[ "$TEST_FEISHU" -eq 1 ]]; then
    log "Running Feishu smoke test..."
    "$TARGET_DIR/tools/test_feishu_notify.sh" || true
  else
    cat <<'EOF'

Next step: ask your AI coding assistant to read RCA.md and fill the project profile.

RCA commands:
  ./bin/rca init
  ./bin/rca check

Primary RCA experiment launcher:
  ./.rca/scripts/run_experiment.sh --name toy_success --note "跑一次 toy success，验证 RCA 记录流程" --confirm -- bash examples/toy_success.sh

Optional: run ./tools/test_feishu_notify.sh to verify Feishu notification.

Optional paper context:
  1. Put the paper PDF under papers/
  2. Run ./tools/init_paper_context.sh
  3. Ask your Agent to fill PAPER_CONTEXT.md based on the paper, README, and code.

Toy test commands:
  ./.rca/scripts/run_experiment.sh --name toy_success --note "跑一次 toy success，验证 RCA 记录流程" --confirm -- bash examples/toy_success.sh
  ./tools/run_with_feishu_notify.sh --name toy_success --note "toy success notification check" -- bash examples/toy_success.sh
  ./tools/run_with_feishu_notify.sh --name toy_failed -- bash examples/toy_failed.sh
  ./tools/run_with_feishu_notify.sh --name toy_interrupt -- bash -c "sleep 60"

For Feishu delivery, configure an installed Feishu CLI or set FEISHU_CLI_SEND_COMMAND.

Recommended Feishu remote entry:
  See docs/opencode-feishu-adoption.md and templates/opencode-feishu.plugin.example.json.

Legacy Python Feishu-OpenCode Bridge fallback:
  See README.md and templates/feishu_bridge.env.example.
EOF
  fi
}

main "$@"
