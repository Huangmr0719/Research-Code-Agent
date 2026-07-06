# Agent Instructions

This repository uses the research agent workflow initialized by `research-agent-template`.

## Experiment Execution

- All long-running experiments in this project must be executed through `tools/run_with_feishu_notify.sh`.
- Do not directly run long tasks such as `python train.py`, `bash train.sh`, or equivalent training/evaluation commands.
- Do not bypass Feishu notification.
- The Agent does not need to monitor training continuously. The wrapper decides `success`, `failed`, or `interrupted` from the command exit code.

## Safety Rules

- Do not write Feishu credentials into code, scripts, logs, or documentation.
- Do not introduce MCP, Hermes, or botmux into this project.
- Do not automatically modify the main repository's core training logic unless the user explicitly asks for that change.

## Escalation

- If the same bug fails to be fixed after 2-3 consecutive attempts, suggest escalating to CodeX or a stronger review workflow.
- If the task touches core method implementation, deadline-critical experiments, or rebuttal experiments, suggest escalating to CodeX or a stronger review workflow before making risky changes.

## Standard Command Pattern

Use:

```bash
./tools/run_with_feishu_notify.sh --name baseline_default -- python train.py --config configs/default.yaml
```

Avoid:

```bash
python train.py --config configs/default.yaml
```
