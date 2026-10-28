---
description: Check and fix the PaperBanana plugin setup, covering uv, the bundled MCP server, API keys, and the optional reference dataset. Use when PaperBanana tools are missing, when they fail with missing-key or authentication errors, or before first use.
allowed-tools:
  - Bash(uv --version)
  - PowerShell(uv --version)
  - mcp__plugin_paperbanana_paperbanana__check_setup
---

# PaperBanana setup check

Keep this short. `check_setup` reports what the server sees, so don't read the plugin's source code or inspect the user's environment variables yourself.

1. **Ask the server.** Call `check_setup`. It returns which API keys are set and where each came from, the default models, whether PDF input works, the output folder, and whether the full reference set is cached. It never returns key values.
2. **If the tool doesn't exist**, the MCP server didn't start. Run `uv --version`:
   - uv is missing: the plugin starts its server with `uvx`, so the user needs to install uv (https://docs.astral.sh/uv/getting-started/installation/) and restart Claude Code. The server's first start downloads its Python dependencies and can take a minute.
   - uv is present: ask the user to open `/mcp`, select `plugin:paperbanana:paperbanana`, and share the error it shows.
3. **API keys.** The default models need `GOOGLE_API_KEY`; OpenAI models (`gpt-5.2`, `gpt-image-1.5`, `gpt-image-2`) need `OPENAI_API_KEY`. If a key the user needs isn't set, explain where it can come from, highest precedence first, and never ask the user to paste a key into the chat:
   1. The plugin's options, kept in the system keychain: `/plugin configure paperbanana@paperbanana` in Claude Code. A terminal install (`claude plugin install`) doesn't ask for them, so they are often still empty.
   2. `GOOGLE_API_KEY` or `OPENAI_API_KEY` in the environment Claude Code starts from.
   3. A `.env` file in the project directory.

   After a key changes, the user runs `/reload-plugins` (or restarts Claude Code) so the server picks it up.
4. **Reference set (optional).** If `expanded_reference_set.cached` is false, mention that diagram retrieval currently uses the small built-in reference set and that the full PaperBananaBench set (about 254 MB) gives it more examples. Call `download_references` only if the user asks for it.

Finish with a short status list, then suggest `/paperbanana:generate-diagram` or `/paperbanana:generate-plot`.
