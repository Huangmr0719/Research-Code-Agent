# RCA Requirements

## Current Product Boundary

Research-Code-Agent is an OpenCode global Skill and project-local research experiment workspace.

RCA serves the Feishu + OpenCode research workflow, but RCA does not implement Feishu access. Feishu entry is handled by external tools such as `opencode-feishu` or botmux. RCA begins when OpenCode is already working inside the research project directory.

## Core User

The primary user is an individual researcher running deep learning experiments or paper reproduction experiments on a server.

Typical tasks:

- initialize a research code project for AI-assisted experiments;
- run baseline, ablation, training, and evaluation jobs;
- summarize results;
- compare experiment records;
- diagnose failed logs;
- organize paper reproduction tables.

## Must Have

- OpenCode global Skill at `skills/rca/SKILL.md`.
- Mechanical project initialization through `rca init`.
- Workspace validation through `rca check`.
- Project-local context in `RCA.md`.
- Structured project profile in `.rca/profile.json`.
- Experiment ledger in `.rca/experiments.json`.
- Standard wrapper at `.rca/scripts/run_experiment.sh`.
- Per-run records under `.rca/runs/<run_id>/`.
- Confirmation-gated experiment execution.
- Atomic and locked experiment ledger updates.

## Must Not Have

- No new Feishu bridge.
- No MCP server.
- No OpenCode plugin.
- No botmux integration.
- No dashboard.
- No complex MLOps queue.
- No multi-CLI abstraction.
- No automatic edits to user home config.
- No committed real secrets.

## Confirmation Rule

Only unconditional confirmation counts:

- 确认执行
- 开始运行
- 跑吧
- 执行这个计划
- 按这个计划运行

If confirmation words are combined with changes, questions, conditions, or reservations, it is not confirmation. The plan must be updated and confirmed again.

## Safety Boundary

RCA confirmation is the first boundary. OpenCode tool permission approval is the second boundary. `.rca/scripts/run_experiment.sh` should be configured as `ask` in OpenCode bash permissions, not unconditional `allow`.
