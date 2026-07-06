# Agent Instructions

This repository uses the Research-Code-Agent workflow.

## Experiment Execution

- All long-running experiments must go through: `tools/run_with_feishu_notify.sh`
- Do not bypass Feishu notification.
- Do not redesign the Feishu card. Pass structured data to `feishu_notify.py`; card layout is maintained by Research-Code-Agent.
- After initializing a new project, run: `./tools/test_feishu_notify.sh`

## Project Results Adapter

- After entering a new baseline project, first check how that project outputs metrics.
- Adapt `tools/project_results_adapter.py` to the project's actual output format.
- Priority:
  1. Reuse the project's existing `metrics.json` / `result.json` / `results.json` / `eval_results.json`
  2. Reuse CSV / wandb / tensorboard exports
  3. Extract from a stable log format
  4. LAST RESORT: minimal change to `train.py` / `eval.py` to write structured output
- Do NOT force all projects to output a single fixed results schema.
- Do NOT refactor training code at scale.
- Do NOT commit experiment outputs to Git.

## Experiment Comparison

- When comparing experiments, prefer `tools/compare_experiments.py`.
- Base comparisons on structured metrics in `experiments/summaries/*.summary.json`.
- Do not read large full logs directly for experiment comparison.
- If metrics are missing, check `tools/project_results_adapter.py` before expanding log parsing.
- Compare output is an experiment artifact and should not be committed unless the user explicitly asks.

## Do Not Commit

- `papers/`
- `PAPER_CONTEXT.md`
- `logs/`
- `outputs/`
- `experiments/`
- `checkpoints/`
- `datasets/`
- `weights/`
- `models/`
- `wandb/`
- `tensorboard/`
- `secrets/`, `token/`, `credentials/`, `.env`

## Do Not Write Secrets

- Do not write Feishu credentials, webhooks, or tokens into code or commit them to Git.

## Do Not Introduce

- gateway
- MCP
- Hermes
- botmux
- Feishu bidirectional control
- Auto `/next` / `/fix` / `/run` control systems

## Keep

- `analyze_with_agent.py` on-demand OpenCode analysis is allowed.
- Do not add a persistent OpenCode daemon or command listener.

## Escalation

- If the same bug fails after 2-3 attempts, suggest escalating to CodeX or a stronger review workflow.
- If the task touches core method implementation, deadline-critical experiments, or rebuttal experiments, suggest escalating before making risky changes.

## Standard Command Pattern

Use:

```bash
./tools/run_with_feishu_notify.sh --name baseline_default -- python train.py --config configs/default.yaml
```

Avoid:

```bash
python train.py --config configs/default.yaml
```
