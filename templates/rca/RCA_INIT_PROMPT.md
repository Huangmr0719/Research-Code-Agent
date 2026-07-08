# RCA Deep Initialization Prompt

Use this after `rca init` has completed mechanical project setup.

Read the current project carefully:

- README and setup notes;
- training scripts;
- evaluation scripts;
- config files;
- dataset and dataloader logic;
- logging and result output logic;
- checkpoint/output conventions;
- paper PDF, `paper.md`, reproduction notes, or baseline documentation when available.

Then update:

- `RCA.md`;
- `.rca/profile.json`.

Do not modify original project source code during RCA initialization.

After updating context, output a concise project understanding summary:

- project type and research goal;
- training/evaluation entrypoints;
- dataset and data flow;
- metrics and where they are extracted;
- output/checkpoint/log paths;
- known reproduction risks and open questions.

Wait for the user to confirm this project understanding. Do not run experiments before the user confirms the project understanding and then confirms a specific experiment plan.
