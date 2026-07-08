# .rca

This directory stores Research-Code-Agent project metadata, experiment records, scripts, and run artifacts.

It is local workflow state. Do not commit it unless the user explicitly decides to publish selected records.

Contents:

- `profile.json`: structured project profile for AI assistants.
- `experiments.json`: experiment ledger. It is a JSON array and is the first source for summaries, comparisons, and paper tables.
- `scripts/run_experiment.sh`: the only standard experiment execution entrypoint.
- `runs/`: per-run directories containing `command.sh`, `stdout.log`, `stderr.log`, `summary.json`, and failure artifacts when needed.
- `plans/`: optional saved experiment plans.

RCA is intentionally light. It is not an experiment database, dashboard, queue, or MLOps platform.

Do not manually corrupt or partially rewrite `experiments.json`. Use `.rca/scripts/run_experiment.sh` for experiment runs. If `experiments.json` and `runs/` disagree, run:

```bash
rca check
```
