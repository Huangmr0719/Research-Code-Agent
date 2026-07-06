# research-agent-template

A small reusable template for initializing research projects with:

- a single experiment wrapper
- Feishu notification hooks
- log capture
- simple experiment summaries
- Agent workflow constraints

This first version is intentionally plain bash plus Python standard library. It does not store Feishu credentials.

## Install Once

Keep this repository somewhere stable, for example:

```bash
~/research-agent-template
```

Make scripts executable:

```bash
chmod +x ~/research-agent-template/init_research_project.sh
chmod +x ~/research-agent-template/tools/*.sh
chmod +x ~/research-agent-template/tools/*.py
chmod +x ~/research-agent-template/examples/*.sh
```

## Initialize A Research Project

From any research project root:

```bash
~/research-agent-template/init_research_project.sh
```

The init script creates:

```text
tools/
  run_with_feishu_notify.sh
  feishu_notify.py
  summarize_experiment.py
logs/
outputs/
experiments/
  summaries/
  runs/
examples/
  toy_success.sh
  toy_failed.sh
AGENTS.md
README_AGENT_WORKFLOW.md
```

If `tools/`, `AGENTS.md`, `README_AGENT_WORKFLOW.md`, or the toy example files already exist, existing paths are moved to `.bak.<timestamp>` before new files are copied.

## Run An Experiment

Original command:

```bash
python train.py --config configs/default.yaml
```

Use:

```bash
./tools/run_with_feishu_notify.sh --name baseline_default -- python train.py --config configs/default.yaml
```

The wrapper records start time, end time, duration, host, git commit, stdout/stderr log path, exit code, metrics, and a summary.

## Toy Tests

After initializing a project that has the `examples/` directory, run:

```bash
./tools/run_with_feishu_notify.sh --name toy_success -- bash examples/toy_success.sh
```

```bash
./tools/run_with_feishu_notify.sh --name toy_failed -- bash examples/toy_failed.sh
```

Interrupt test:

```bash
./tools/run_with_feishu_notify.sh --name toy_interrupt -- bash -c "sleep 60"
```

Then press `Ctrl+C`. You should receive an `interrupted` notification if Feishu CLI is configured.

## Feishu Configuration

`tools/feishu_notify.py` first tries to detect installed `feishu` or `lark` CLI binaries with common send commands.

If your CLI uses a different command format, set:

```bash
export FEISHU_CLI_SEND_COMMAND="feishu send --text"
```

The configured command should accept the notification text as its final argument. No Feishu credential should be written into this repository.

If Feishu sending fails, the script prints the notification content to stdout and exits non-zero. The experiment wrapper does not fail the experiment just because notification delivery failed.

## Summary Files

`tools/summarize_experiment.py` writes:

```text
experiments/summaries/<experiment_name>.summary.json
experiments/summaries/<experiment_name>.summary.md
```

If `metrics.json` or `result.json` exists, JSON metrics are preferred. Otherwise the script extracts common metrics from logs:

- `accuracy`
- `acc`
- `F1`
- `UF1`
- `UAR`
- `loss`
- `val_loss`
- `best_epoch`

## Agent Rule

Long-running experiments must go through:

```bash
./tools/run_with_feishu_notify.sh --name <experiment_name> -- <command>
```

Do not directly run `python train.py` or `bash train.sh` for long tasks, and do not bypass Feishu notification.
