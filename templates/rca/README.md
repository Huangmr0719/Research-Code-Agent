# .rca

This directory stores Research-Code-Agent project metadata, experiment records, scripts, and run artifacts.

It is local workflow state. Do not commit it unless the user explicitly decides to publish selected records.

Contents:

- `profile.json`: structured project profile for AI assistants.
- `experiments.json`: append-only experiment index used for summaries, comparisons, and paper tables.
- `scripts/run_experiment.sh`: standard experiment launcher.
- `runs/`: per-run summaries and logs.
- `plans/`: optional saved experiment plans.

RCA is intentionally light. It is not an experiment database, dashboard, queue, or MLOps platform.
