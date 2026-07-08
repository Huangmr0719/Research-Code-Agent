# Research-Code-Agent Context

This file is the main context file for AI coding agents working on research experiments in this project.

RCA does not replace OpenCode, Codex, Claude Code, or the project codebase. RCA only defines how an AI assistant should plan, run, record, summarize, compare, and diagnose experiments safely.

## Operating Rules

- Read this file before research experiment tasks.
- Propose an experiment plan before running any experiment.
- Wait for user confirmation before launching long-running experiments.
- Run long experiments through `.rca/scripts/run_experiment.sh`.
- Do not modify training, model, dataset, evaluation, or config code unless the user explicitly confirms the patch.
- Preserve logs, summaries, and experiment records.
- Update `.rca/experiments.json` after each experiment.
- Separate facts, inference, and recommendations in user-facing summaries.

## Project Profile

Fill this section during RCA init after reading the project README, training scripts, evaluation scripts, configs, data loading code, output code, and paper/reproduction materials.

- Project type:
- Main research task:
- Main model / method:
- Dataset(s):
- Metric(s):
- Training entrypoint(s):
- Evaluation entrypoint(s):
- Config mechanism:
- Output directory:
- Checkpoint directory:

## Code Structure

Record only the parts relevant to experiment planning and result extraction.

- Training code:
- Evaluation code:
- Dataset / dataloader:
- Model / method implementation:
- Config files:
- Scripts:
- Result files:

## Metrics And Result Extraction

Describe where reliable metrics come from.

- Preferred structured result files:
- Stable log patterns:
- Checkpoint / artifact naming:
- Known caveats:

## Paper / Reproduction Context

Put concise paper or reproduction context here when available. Do not create extra paper planning files unless the user asks.

- Paper / repo:
- Baseline target:
- Main table(s):
- Key ablation(s):
- Expected metric(s):
- Known reproduction gaps:

## Experiment Planning Rules

Before running an experiment, present a short plan with:

- Experiment purpose
- User initial note
- Command to execute
- Dataset / config / checkpoint
- Output directory
- Expected artifacts
- Resource and runtime risks
- Metric extraction method
- Failure diagnosis plan

## Experiment Recording Rules

Each run should create `.rca/runs/<run_id>/summary.json` and update `.rca/experiments.json`.

Each record should include:

- `run_id`
- `created_at`
- `status`
- `task_type`
- `user_note_initial`
- `ai_note_final`
- `command`
- `dataset`
- `config`
- `metrics`
- `artifacts`
- `conclusion`

## Current Issues

Track unresolved project-specific issues here.

- 
