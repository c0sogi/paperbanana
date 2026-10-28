---
description: Refine a figure from an earlier PaperBanana run by continuing that run with the user's feedback (more visualizer and critic rounds, no re-planning). Use when the user wants changes to a generated diagram or plot, such as "make the arrows thicker", "rename the encoder block", or "use a colorblind-safe palette".
argument-hint: "[run_id] [feedback]"
allowed-tools:
  - Read
  - Glob
  - mcp__plugin_paperbanana_paperbanana__continue_diagram
  - mcp__plugin_paperbanana_paperbanana__continue_plot
---

# Refine a generated figure

Arguments, if any: `$ARGUMENTS`

1. **Find the run.** Use the run ID or folder from the arguments or the conversation. Otherwise take the newest `outputs/run_*` folder and confirm with the user that it holds the figure they mean. Read its `run_input.json`: a `diagram_type` of `methodology` needs `continue_diagram`, and `statistical_plot` needs `continue_plot`.
2. **Write the feedback for the critic.** Say exactly what to change and where, and what must stay as it is. "Rename the 'Enc' block to 'Visual Encoder'; keep the layout and colors" works better than "fix the labels". Add any problems you saw in the last image yourself.
3. **Continue the run.** Pass `run_id`, `feedback`, and `iterations` (1 or 2 is usually enough for a targeted edit). If the run folder is not under `outputs/` in the project directory, pass its parent folder as `output_dir`. `venue` applies a venue style guide (`neurips`, `icml`, `acl`, `ieee`, or a user style pack). Model options work as they do for generation.
4. **Show the result.** The tool returns JSON with `final_image_path`, `run_dir`, and `new_iteration_count`, or `error` with `strict_success: false`. Read `final_image_path` to check the change landed, then give the user the path. Earlier iterations stay in `run_dir` in case they prefer a previous version.
