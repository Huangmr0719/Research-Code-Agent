# RCA Final Convergence

This document records the current product boundary for Research-Code-Agent.

## Definition

Research-Code-Agent is a research experiment workflow package for AI coding assistants.

It helps OpenCode, Codex, Claude Code, or similar coding CLIs safely plan, run, record, summarize, compare, and diagnose experiments inside an existing research code project.

RCA is not a Feishu bot, bridge, multi-agent platform, web terminal, agent runtime, LLM provider manager, permission system, or MLOps platform.

## Primary User

The first user is an individual researcher running deep learning experiments or paper reproduction experiments on a server.

Typical tasks:

- train a model;
- run a baseline;
- run ablations;
- tune configs;
- inspect loss / accuracy / F1 / UF1 / UAR;
- reproduce an open-source paper baseline;
- organize experiment results into tables.

## Recommended Flow

```text
existing research code project
  -> OpenCode init
  -> RCA init
  -> AI reads README, train/eval scripts, configs, data flow, outputs, paper materials
  -> AI fills RCA.md and .rca/profile.json
  -> user asks for an experiment in natural language
  -> RCA proposes an experiment plan
  -> user confirms
  -> RCA runs .rca/scripts/run_experiment.sh
  -> RCA updates .rca/experiments.json
  -> AI summarizes results in the conversation
```

RCA init is intentionally a scaffold step, not a complex scanner. The AI assistant should do the project-specific reading and fill the context files.

## Final MVP Structure

```text
project-root/
  AGENTS.md
  RCA.md
  .rca/
    README.md
    profile.json
    experiments.json
    scripts/
      run_experiment.sh
    runs/
    plans/
```

`AGENTS.md` stays at the project root because AI coding tools are most likely to read it automatically. RCA init appends a short RCA section if `AGENTS.md` already exists.

`RCA.md` is the main project context for AI agents. It should contain project profile, code structure, training/evaluation entrypoints, data flow, metrics, paper/reproduction context, experiment planning rules, and unresolved issues.

`.rca/` stores local structured RCA state and runtime artifacts. It should not be committed by default.

## Experiment Plan Rule

RCA is semi-automatic. It must not launch a long experiment immediately after a vague user request.

Before running an experiment, the AI assistant should present:

- experiment purpose;
- user initial note;
- command;
- dataset / config / checkpoint;
- output directory;
- expected artifacts;
- resource and runtime risks;
- metric extraction method;
- failure diagnosis plan.

Only after user confirmation should it run the experiment.

## Experiment Record Rule

Every run should create:

- `.rca/runs/<run_id>/summary.json`
- an entry in `.rca/experiments.json`

The global experiment index is the first local source for later experiment comparison, result lookup, and paper table drafting.

## Out Of Scope

RCA does not own:

- Feishu connection logic;
- message cards;
- WebSocket bridge;
- multi-bot orchestration;
- web terminal;
- agent runtime;
- LLM provider management;
- complex permission systems;
- heavy MLOps dashboards;
- experiment queues;
- GPU monitoring platforms.

These can be handled by external tools such as OpenCode, Codex, Claude Code, opencode-feishu, botmux, tmux, or systemd.

## Relationship To Existing Optional Tools

Existing `tools/` scripts remain useful implementation helpers:

- `tools/run_with_feishu_notify.sh` captures logs, summaries, notifications, and exit status.
- `tools/summarize_experiment.py` extracts factual summary data.
- `tools/compare_experiments.py` compares summary records.
- `tools/project_results_adapter.py` adapts project-specific metric extraction.

The converged RCA entrypoint is `.rca/scripts/run_experiment.sh`, which can reuse these tools without making Feishu or bridge functionality part of the product core.
