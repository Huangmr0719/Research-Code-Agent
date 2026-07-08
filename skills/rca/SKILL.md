---
name: rca
description: Use for research code experiments in OpenCode: project profiling, experiment planning, confirmation-gated execution, wrapper-based runs, structured experiment ledger, result summarization, comparison, and failure diagnosis.
---

# Research-Code-Agent Skill

Research-Code-Agent is an OpenCode global Skill and project-local research experiment workspace.

Use RCA for research code projects when the user asks to initialize a project, run training or evaluation, reproduce a paper baseline, run ablations, summarize results, compare experiments, diagnose failed logs, or organize experiment tables.

RCA does not implement Feishu access, bridges, MCP, OpenCode plugins, botmux, dashboards, LLM provider management, or MLOps infrastructure. Feishu + OpenCode can be the user entry route, but RCA begins after OpenCode is inside the project directory.

## Project Files

RCA uses these project-local files:

- `RCA.md`: AI-readable research README for the current project.
- `.rca/profile.json`: structured project profile.
- `.rca/experiments.json`: experiment ledger. It must be a JSON array.
- `.rca/scripts/run_experiment.sh`: the only standard experiment execution entrypoint.
- `.rca/runs/<run_id>/summary.json`: per-run experiment record.
- `.rca/plans/`: optional saved experiment plans.

## RCA Init

When the user says “帮这个项目做 RCA 初始化” or equivalent:

1. Run `rca init` to create the mechanical workspace.
2. Read the project README, training scripts, evaluation scripts, config files, data loading logic, result output logic, paper PDF / `paper.md` / reproduction notes if present.
3. Generate or complete `RCA.md`.
4. Generate or complete `.rca/profile.json`.
5. Output a concise project understanding summary.
6. Wait for the user to confirm whether the project understanding is correct.
7. Do not run experiments before project understanding is confirmed.

Do not modify original project source code during RCA init. If source changes seem necessary, present a patch/diff and rationale, then wait for explicit user approval.

## Experiment Planning

When the user asks to run an experiment, do not run it immediately.

First present an experiment plan. The plan can remain in the conversation and does not have to be saved unless useful. It must include:

- experiment purpose;
- command to execute;
- dataset / config / checkpoint;
- output directory;
- expected artifacts;
- resource and runtime risks;
- how metrics will be extracted after success;
- how failure will be diagnosed;
- user initial Chinese note as `user_note_initial`.

## Confirmation Gate

Only unconditional confirmation counts as approval to run:

- 确认执行
- 开始运行
- 跑吧
- 执行这个计划
- 按这个计划运行

These do not count as confirmation:

- 基本可以，不过……
- 是不是先……
- 要不要……
- 可以吗？
- 先看看……
- 确认执行，不过 output 目录改一下
- 跑吧，但 batch size 改成 16

If a confirmation phrase appears together with any requested change, condition, question, or reservation, it is not confirmation. Update the plan, show the revised plan, and wait for confirmation again. Do not run first and patch the plan afterward.

After valid confirmation, run only through:

```bash
.rca/scripts/run_experiment.sh --name <name> --note "<中文备注>" --confirm -- <command>
```

## Tool Safety

- Never run long training/evaluation commands naked.
- Do not bypass `.rca/scripts/run_experiment.sh`.
- Do not run `rm -rf`, recursive `chmod`, `scp` uploads, `curl` uploads, or `git push` unless the user explicitly requests it and OpenCode permission rules allow it.
- Do not read or expose secrets, `.env`, `feishu.json`, SSH keys, tokens, credentials, or secret-like directories.
- Do not modify original source code unless the user explicitly approves the patch.
- If code changes are needed, present the proposed patch/diff and the reason first.

## OpenCode Permission Boundary

Configure OpenCode permissions so `.rca/scripts/run_experiment.sh` is `ask`, not unconditional `allow`.

RCA confirmation is the first safety boundary. OpenCode tool execution approval is the second boundary.

## Success And Failure Handling

On success:

- ensure `.rca/runs/<run_id>/summary.json` exists;
- ensure `.rca/experiments.json` is updated;
- summarize facts, metrics, conclusion, and next steps in the conversation.

On failure:

- preserve `stdout.log` and `stderr.log`;
- preserve `failure.json` or an error tail;
- record exit code and run metadata;
- explain the failed stage, likely causes, and concrete debugging steps;
- do not invent facts not supported by logs or summary records.

## Comparison And Diagnosis

For experiment history, read `.rca/experiments.json` first.

For a single run, read `.rca/runs/<run_id>/summary.json`, `stdout.log`, and `stderr.log` only as needed.

If ledger and run directories disagree, run `rca check`.
