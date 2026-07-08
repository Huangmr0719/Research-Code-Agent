## Research-Code-Agent

This project uses Research-Code-Agent for research experiment workflow.

- For research experiment tasks, read `RCA.md` first.
- Before running an experiment, propose a short plan and wait for user confirmation.
- Long experiments must run through `.rca/scripts/run_experiment.sh`.
- Do not run naked long training commands such as `python train.py` or `bash train.sh`.
- Every experiment must preserve logs and update `.rca/experiments.json`.
- Do not modify core training, model, dataset, or config code unless the user explicitly confirms the patch.
- Do not read or expose secrets such as `.env`, `feishu.json`, `feishu_bridge.env`, SSH keys, tokens, or credentials.
