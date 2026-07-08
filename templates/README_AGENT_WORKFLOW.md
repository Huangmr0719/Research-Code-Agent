# Research-Code-Agent Workflow

This project uses Research-Code-Agent for long-running experiments in a Feishu + OpenCode research workflow. RCA requires an experiment plan and explicit user confirmation before running long experiments. The RCA launcher records logs, creates a summary, updates `.rca/experiments.json`, and can send a Feishu notification when the command exits.

## Run Experiments

Original command:

```bash
python train.py --config configs/default.yaml
```

Run it as:

```bash
./.rca/scripts/run_experiment.sh \
  --name baseline_default \
  --note "跑一次默认 baseline，作为后续实验对照" \
  --confirm \
  --task-type baseline \
  --config configs/default.yaml \
  -- python train.py --config configs/default.yaml
```

Add a short experiment note when the run has a specific intent:

```bash
./.rca/scripts/run_experiment.sh \
  --name exp_042 \
  --note "去除 region mask 模块，验证该模块对 UF1/UAR 的贡献" \
  --confirm \
  --task-type ablation \
  -- python train.py --config configs/exp_042.yaml
```

`--confirm` means the user already approved the experiment plan. Do not add it before user confirmation.

## Feishu Smoke Test

After initializing the project, verify Feishu notification:

```bash
./tools/test_feishu_notify.sh
```

## Outputs

- `logs/` stores complete stdout/stderr logs.
- `experiments/summaries/` stores `.summary.json` and `.summary.md` files for each experiment name.
- `.rca/runs/<run_id>/summary.json` stores the RCA per-run summary.
- `.rca/experiments.json` stores the global experiment index for later comparison and table drafting.
- Feishu receives `success`, `failed`, or `interrupted` notifications.
- `summary.json` stores the user-provided `note`, top-level `status`, factual fields, metrics, log tail, and separate `analysis`.

The RCA launcher uses `.rca/run.lock` and atomic replacement for `.rca/runs/<run_id>/summary.json` and `.rca/experiments.json`, so concurrent runs or interruptions do not leave partial JSON.

The first version does not require modifying `train.py`. If later experiments need more stable metric parsing, make `train.py` write `metrics.json` or `result.json`; the summary script will prefer JSON metrics over regex log extraction.

`summarize_experiment.py` only extracts facts, metrics, traceback snippets, and the last 80 log lines. `analyze_with_agent.py` calls OpenCode with the note and those limited inputs, then writes concise Chinese Agent Analysis back into `summary.json`.

## Feishu CLI

No Feishu credential is stored in this repository. Configure your existing Feishu CLI, or set:

```bash
export FEISHU_CLI_CARD_COMMAND="feishu send --card"
export FEISHU_CLI_TEXT_COMMAND="feishu send --text"
```

The command prefix should accept the message body as its final argument. For `lark-cli`, set `FEISHU_CHAT_ID` or `FEISHU_USER_ID`; `lark-cli` will be auto-detected when available.
