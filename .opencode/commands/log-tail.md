# Log Tail

Use this as an OpenCode action template when the user asks what happened in a run or why it failed.

- Do not ask the user to type this command name.
- Read only project logs under `logs/` or experiment artifacts under `experiments/`.
- Prefer the last relevant lines instead of full logs.
- Do not read `.env`, `feishu_bridge.env`, secrets, SSH keys, tokens, or credentials.
- Redact token/key-like content in the final answer.
- Return the error type, evidence, affected log path, and next diagnostic step.
