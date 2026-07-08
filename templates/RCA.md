# Research-Code-Agent Context

This is the AI-readable research README for this project. It is not meant to be a polished human-facing README.

## 1. RCA Operating Rules

- Read this file before research experiment tasks.
- Use `.rca/profile.json` as the structured project profile.
- Use `.rca/experiments.json` as the experiment ledger.
- Before running any experiment, present a plan and wait for explicit confirmation.
- Run experiments only through `.rca/scripts/run_experiment.sh --confirm`.
- Do not modify original source code unless explicitly approved.
- Do not edit `.rca/experiments.json` concurrently by hand; the wrapper uses locking and atomic writes.

## 2. Project Summary

TODO: Fill after reading README, setup docs, package files, and repository structure.

## 3. Research Goal

TODO: Describe the main research problem, target task, and expected outcome.

## 4. Code Structure

TODO: Record only experiment-relevant source layout.

- Training code:
- Evaluation code:
- Model / method code:
- Dataset / dataloader:
- Config files:
- Scripts:
- Result output code:

## 5. Training Entry Points

TODO: List train commands, required arguments, configs, and known defaults.

## 6. Evaluation Entry Points

TODO: List evaluation commands, metric scripts, checkpoints, and output files.

## 7. Dataset and Data Flow

TODO: Describe dataset name, paths, split protocol, preprocessing, dataloaders, and generated files.

## 8. Metrics and Result Extraction

TODO: Define primary metrics, where they appear, and stable extraction rules.

- Primary metrics:
- Structured result files:
- Stable log patterns:
- Known metric caveats:

## 9. Paper / Reproduction Context

TODO: Summarize paper or reproduction context when available.

- Paper / repo:
- Target baseline:
- Main table(s):
- Expected metric(s):
- Known reproduction gaps:

## 10. Baselines and Ablations

TODO: Record baseline configs, ablation factors, target comparisons, and table mapping.

## 11. Output and Artifact Paths

TODO: Record logs, checkpoints, results, temporary outputs, and artifacts.

## 12. Experiment Planning Rules

Every experiment plan must include:

- experiment purpose;
- proposed command;
- dataset / config / checkpoint;
- output directory;
- expected artifacts;
- risk and resource cost;
- success metric extraction method;
- failure diagnosis method;
- `user_note_initial` in Chinese.

Only unconditional confirmation counts. If the user adds changes, questions, conditions, or reservations, update the plan and wait for confirmation again.

## 13. Experiment Ledger Rules

Every run must create `.rca/runs/<run_id>/summary.json` and update `.rca/experiments.json`.

The ledger is a JSON array. Use `rca check` if ledger records and run directories disagree.

## 14. Known Risks and Open Questions

TODO: Track unresolved project-specific risks.

-
