# Experiment Run

Use this as an OpenCode action template when the user naturally asks to run an experiment.

- Do not ask the user to type this command name.
- Do not run naked long tasks such as `python train.py` or `bash train.sh`.
- Use `tools/run_with_feishu_notify.sh` for long experiments.
- If `opencode-pty` is available and the task may run long, start a controlled background session.
- Keep the command inside the current project.
- After completion, report exit code, log path, summary path, key metrics, and next step.

Example pattern:

```bash
./tools/run_with_feishu_notify.sh --name <experiment_name> -- <project command>
```
