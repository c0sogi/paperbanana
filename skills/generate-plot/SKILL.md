---
description: Generate a publication-ready statistical plot (bar, line, scatter, heatmap, and similar) for an academic paper from CSV or JSON results or a table in the conversation. PaperBanana writes matplotlib code, renders it, and refines it with a critic. Use when the user wants a results chart, comparison plot, or ablation figure for a paper.
argument-hint: "[results.csv|data.json] [intent]"
allowed-tools:
  - Read
  - Glob
  - mcp__plugin_paperbanana_paperbanana__generate_plot
  - mcp__plugin_paperbanana_paperbanana__batch_plots
---

# Generate a statistical plot

Arguments, if any: `$ARGUMENTS`

## 1. Collect the inputs

- **Data**: a CSV or JSON file, or values or a table in the conversation.
- **Intent**: what the plot should show, for example "Grouped bar chart of accuracy per benchmark, one bar per model, with error bars". Use the user's words. If they gave none, propose an intent from the data's columns and state it.

## 2. Run it

**Small data** (up to a few hundred values): call `generate_plot` with

- `data_json`: the data as a JSON **string**. Convert a CSV to a list of row objects (`[{"model": "A", "accuracy": 0.91}, ...]`), the same shape `paperbanana plot` uses. Pass a JSON file's content unchanged.
- `intent`: the description from step 1.
- Optional: `iterations` (default 3), `auto_refine`, `optimize`, `aspect_ratio` (`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `9:16`, `16:9`, `21:9`), `vlm_model` (`gemini-3.7-flash` or `gpt-5.2`).

**Large files**: don't pass the data through the tool call. Write a one-item manifest under `outputs/` and call `batch_plots` with its absolute `manifest_path`. The server reads the data file itself.

```yaml
items:
  - data: C:/path/to/results.csv   # absolute, or relative to the manifest
    intent: "Line plot of validation loss vs. step for each model"
    id: fig_loss
    aspect_ratio: "16:9"           # optional
```

`batch_plots` returns JSON with `batch_dir`, `batch_report_path`, and per-item output paths.

Plots are drawn by matplotlib code that the VLM writes, so only the VLM provider's key is needed: Google for Gemini, OpenAI for `gpt-5.2`. No image-generation model is used.

## 3. Report the result

- Look at the plot and check it against the data: values, axis labels and units, legend entries, and whether the chart type suits the intent.
- Give the user the output path: `final_output.png` in the newest `outputs/run_*` folder, or the paths in the batch report.
- Each plot run keeps the matplotlib script for every iteration as a `.py` file in its run folder. Tell the user, so they can tweak or regenerate the figure by hand.
- Offer a refinement round with concrete feedback. `/paperbanana:refine-figure` continues the same run.
