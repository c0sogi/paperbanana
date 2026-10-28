---
description: Generate a publication-ready methodology or architecture diagram for an academic paper from method text, a LaTeX/Markdown section, or a PDF, using the PaperBanana multi-agent pipeline (retriever, planner, stylist, visualizer, critic). Use when the user asks for a method figure, framework overview, model architecture, or pipeline diagram for a paper.
argument-hint: "[method.txt|section.tex|paper.pdf] [caption]"
allowed-tools:
  - Read
  - Glob
  - mcp__plugin_paperbanana_paperbanana__generate_diagram
  - mcp__plugin_paperbanana_paperbanana__start_diagram_session
  - mcp__plugin_paperbanana_paperbanana__get_figure_session
  - mcp__plugin_paperbanana_paperbanana__preview_figure_session
  - mcp__plugin_paperbanana_paperbanana__list_figure_sessions
  - mcp__plugin_paperbanana_paperbanana__cancel_figure_session
  - mcp__plugin_paperbanana_paperbanana__list_available_models
---

# Generate a methodology diagram

Arguments, if any: `$ARGUMENTS`

## 1. Collect the inputs

- **Source context**: the method description the diagram must be faithful to.
  - A `.txt`, `.md`, or `.tex` file: read it and pass the method section as `source_context`. Leave out unrelated sections such as related work and experiments; focused text gives a better plan.
  - A PDF: read only the pages that describe the method and pass that text.
  - Text in the conversation: use it as is.
- **Caption**: what the figure must communicate, passed as `caption`. Use the user's caption. If they gave none, draft one in the paper's voice ("Overview of X: ...") and state it. Ask only when the source could support several different figures and the user's goal is unclear.
- **Sketches**: if the user has a hand-drawn sketch, a whiteboard photo, or an earlier version of the figure, pass absolute paths in `input_images`. The planner follows their layout and content.

## 2. Pick options

Keep the defaults unless the user asks for something else or the input calls for it.

| Option | Default | When to change it |
|---|---|---|
| `iterations` | 3 | More rounds for dense diagrams, 1 for a quick draft |
| `auto_refine` | false | true lets the critic loop until it is satisfied (up to 30 rounds); slower and costlier |
| `optimize` | false | true restructures rough notes and sharpens the caption before planning |
| `aspect_ratio` | landscape | `16:9` or `21:9` for a full-width figure in a two-column paper, `4:3` or `1:1` for one column; also `2:3`, `3:2`, `3:4`, `9:16` |
| `vlm_model`, `image_model` | configured defaults (`gemini-3.7-flash`, `gemini-3.1-flash-image`) | Exact IDs only. VLM: `gemini-3.7-flash`, `gpt-5.2`. Image: `gemini-3.1-flash-image`, `gemini-3-pro-image` (higher quality), `gpt-image-1.5`, `gpt-image-2`. `list_available_models` gives prices |

## 3. Run it

- **Normal runs** (no `auto_refine`, a handful of iterations): call `generate_diagram`. It returns the final image when the run finishes, usually after a few minutes.
- **Long or watched runs** (`auto_refine`, many iterations, or the user wants to follow progress or be able to stop it): call `start_diagram_session`. It returns at once with a `session_id`, `run_id`, and `run_dir`. `get_figure_session` reports `status`, `progress_event`, and `current_iteration`; `preview_figure_session` returns the newest iteration image; `cancel_figure_session` stops the run. Check progress when the user asks or between other work, not in a tight loop. Use a session whenever a run could take more than about 30 minutes, because Claude Code aborts a silent tool call after that long. Sessions live in the MCP server process and are lost if it restarts, but files already written stay in `run_dir`.

## 4. Report the result

- Each run writes a folder `outputs/run_<timestamp>_<id>/` in the project directory with `final_output.png`, one `iter_<n>/` folder per refinement round, `run_input.json`, and `metadata.json`. After `generate_diagram`, the newest `outputs/run_*` folder is the run you just made.
- Look at the image yourself and compare it with the source: missing or invented components, wrong data flow, garbled or misspelled labels. Tell the user what you see.
- Give the user the path to `final_output.png` and the run ID, and offer a refinement round with concrete feedback. `/paperbanana:refine-figure` continues the same run without re-planning.

## If something fails

- No PaperBanana tools are available: the bundled MCP server didn't start. Run `/paperbanana:setup`.
- An error about a missing or invalid API key: run `/paperbanana:setup`. Never ask the user to paste a key into the chat.
