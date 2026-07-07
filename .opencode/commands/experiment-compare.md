# Experiment Compare

Use this as an OpenCode action template when the user asks to compare experiments.

- Do not ask the user to type this command name.
- Prefer structured summaries under `experiments/summaries/`.
- Use `tools/compare_experiments.py` before reading logs.
- Do not read large full logs unless summaries are missing and the user accepts the cost.
- Explain metric changes, failures, and concrete next steps.

Example pattern:

```bash
python3 tools/compare_experiments.py --summaries experiments/summaries
```
