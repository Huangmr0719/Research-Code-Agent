# Experiment Summary

Use this as an OpenCode action template when the user asks about recent or specific experiment results.

- Do not ask the user to type this command name.
- Prefer existing `experiments/summaries/*.summary.json` and `.summary.md`.
- If no summary exists, use `tools/summarize_experiment.py` on the relevant project log.
- Read only project logs and summaries.
- Do not read `.env`, `feishu_bridge.env`, SSH keys, tokens, or credentials.
- Return concise status, metrics, log path, summary path, likely issue, and next step.
- Separate facts from inference. Say when evidence is insufficient.
