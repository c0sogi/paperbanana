---
description: Plan and generate a full set of figures for an academic paper with PaperBanana. It plans methodology diagrams from the paper's sections and statistical plots from result files, then packages them with figures.tex and captions.md. Also runs batch manifests of diagrams or plots. Use when the user wants all the figures for a paper, or many figures at once.
argument-hint: "<paper.pdf|paper.md|manifest.yaml> [results-dir]"
allowed-tools:
  - Read
  - Glob
  - mcp__plugin_paperbanana_paperbanana__orchestrate_figures
  - mcp__plugin_paperbanana_paperbanana__batch_diagrams
  - mcp__plugin_paperbanana_paperbanana__batch_plots
  - mcp__plugin_paperbanana_paperbanana__list_available_models
---

# Generate a paper's figure package

Arguments, if any: `$ARGUMENTS`

These runs make many paid generation calls, so plan first and get the user's go-ahead before generating.

## From a paper

1. **Plan, at no cost.** Call `orchestrate_figures` with `paper` (absolute path to a `.pdf`, `.md`, or `.txt` file) and `dry_run: true`. The planner finds sections from heading lines such as "3 Method" or "3.2 Training", so for a LaTeX paper pass the compiled PDF rather than the `.tex` source. Optional: `data_dir` (a folder of CSV or JSON results to plan plots from), `max_method_figures` (default 4), `max_plot_figures` (default 4), and `pdf_pages`. Planning reads the paper's structure and makes no API calls.
2. **Review the plan with the user.** Read `orchestration_plan.json` at the returned `orchestration_plan_path` and list each planned figure with its caption or intent. Estimate the cost: each diagram makes about one image call per refinement iteration (3 by default) plus a few VLM calls, and plots make VLM calls only. `list_available_models` has current prices; at the defaults, `gemini-3.1-flash-image` is about $0.10 per 2K image. Ask the user to confirm or trim the plan. They can also edit the plan file directly.
3. **Generate.** Call `orchestrate_figures` with `resume_orchestrate` set to the `orchestration_id` (or `orchestrate_dir`) from step 1. Don't pass `paper` again. Useful options: `iterations`, `optimize`, `venue` (`neurips`, `icml`, `acl`, `ieee`, or a user style pack), `concurrency` (figures generated in parallel), `vlm_model`, and `image_model`.
4. **Deliver.** The result gives `figure_package_path`, `figures_tex_path`, `captions_md_path`, `generated_count`, and any `failures`. Show the user the figures, point them to `figures.tex` (ready to `\input`) and `captions.md`, and offer to copy the figures into their paper repository. To retry failed figures, call `orchestrate_figures` again with the same `resume_orchestrate` and `retry_failed: true`.

## From a manifest

When the user already has a batch manifest, or wants exact control over each figure, call `batch_diagrams` (items with `input`, a text or PDF path, and `caption`) or `batch_plots` (items with `data` and `intent`). Paths inside a manifest resolve relative to the manifest file. A diagram manifest can add a `composite` section that stitches the panels into one labeled figure:

```yaml
composite:
  layout: "1x3"     # rows x cols, or "auto"
  labels: auto      # (a), (b), (c), ...
items:
  - input: encoder.txt
    caption: "Encoder architecture"
    id: panel_a
```

Batch results report `batch_dir`, `batch_report_path`, the status of each item, and `composite_path` when a composite was requested.
