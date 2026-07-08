# RCA Implementation Plan

## Why Skill, Not Plugin Or MCP

RCA is mostly workflow policy and project-local records. It does not need a runtime server, protocol, callback channel, or long-running process.

An OpenCode global Skill is the smallest stable surface:

- it teaches OpenCode when to use RCA;
- it defines confirmation and safety rules;
- it points OpenCode to project-local files;
- it avoids building another agent runtime.

OpenCode Plugin or MCP should be considered only if RCA later needs a shared service, remote state, cross-project search, or explicit tool protocol that cannot be handled by shell/Python scripts.

## Global Skill vs Project Workspace

Global Skill:

- `skills/rca/SKILL.md`;
- general rules, confirmation policy, and safety constraints;
- no project-specific facts.

Project workspace:

- `RCA.md`;
- `.rca/profile.json`;
- `.rca/experiments.json`;
- `.rca/scripts/run_experiment.sh`;
- `.rca/runs/`;
- `.rca/plans/`.

The Skill tells OpenCode how to behave. The project workspace stores local facts and experiment artifacts.

## rca init

`rca init` is mechanical. It creates:

- `RCA.md`;
- `.rca/README.md`;
- `.rca/profile.json`;
- `.rca/experiments.json`;
- `.rca/scripts/run_experiment.sh`;
- `.rca/runs/`;
- `.rca/plans/`.

It does not scan deeply, modify source code, write secrets, or edit user home config. OpenCode should then perform the deep initialization by reading project files and filling `RCA.md` and `.rca/profile.json`.

## rca check

`rca check` validates:

- required files and directories;
- JSON validity;
- `.rca/experiments.json` top-level array shape;
- run directories missing from the ledger;
- ledger records with missing summaries.

It prints `PASS`, `WARN`, and `FAIL`.

## run_experiment.sh

The wrapper:

- requires `--confirm`;
- creates a unique `run_id` using atomic `mkdir`;
- saves `command.sh`, `stdout.log`, and `stderr.log`;
- records timing and exit code;
- writes `summary.json` atomically;
- writes `failure.json` and `error_tail.txt` on failure;
- updates `.rca/experiments.json` under a lock;
- uses Python standard library for JSON.

Ledger updates use `flock` when available and an atomic `mkdir` lock fallback when `flock` is unavailable.

## Experiments Ledger

`.rca/experiments.json` is a JSON array. It is the first source for experiment history, comparisons, and paper table drafting.

OpenCode may enrich `ai_note_final`, `metrics`, and `conclusion` after reading logs and results, but it must keep JSON valid and rerun `rca check` if consistency is unclear.

## Wrapper Relationship

`.rca/scripts/run_experiment.sh` is the only standard experiment execution entrypoint.

Legacy scripts in `tools/` are retained for compatibility and optional notifications. They must not become a second experiment ledger. New RCA workflow should write every experiment into `.rca/runs/` and `.rca/experiments.json`.

## OpenCode Permission Advice

Configure `.rca/scripts/run_experiment.sh` as `ask` in `opencode.json` bash permission rules. Do not set it to unconditional `allow`.

## Optional Integrations

Feishu, `opencode-feishu`, botmux, systemd, tmux, and the legacy Python bridge are optional entry/runtime layers. They are not RCA core.
