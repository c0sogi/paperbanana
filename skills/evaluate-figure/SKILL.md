---
description: Compare a generated diagram or plot with a human-made reference figure using PaperBanana's VLM-as-judge, which scores faithfulness, conciseness, readability, and aesthetics. Use when the user wants to benchmark a generated figure against a reference or judge which of two figures is better.
argument-hint: "<generated-image> <reference-image>"
allowed-tools:
  - Read
  - mcp__plugin_paperbanana_paperbanana__evaluate_diagram
  - mcp__plugin_paperbanana_paperbanana__evaluate_plot
---

# Evaluate a figure against a reference

Arguments, if any: `$ARGUMENTS`

1. Get absolute paths for the generated image and the human reference image.
2. Gather what the judge needs for the figure type. If the generated image came from a PaperBanana run, its `run_input.json` holds the original inputs (`source_context`, `communicative_intent`, and `raw_data` for plots).
   - **Methodology diagram**: call `evaluate_diagram` with `context` (the method text the diagram depicts; read it from a file if the user gives one) and `caption`.
   - **Statistical plot**: call `evaluate_plot` with `data_json` (the source data as a JSON string) and `intent`.
3. Present the result. For each dimension, say which figure won and why. Faithfulness and readability are the primary dimensions; conciseness and aesthetics only decide ties, following the hierarchical aggregation in the PaperBanana paper. End with the overall winner and the concrete weaknesses worth fixing in the generated figure.
