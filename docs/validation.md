# Validation Records

Records of checks actually run against this repository. Each entry states what
was verified and what was not.

## 2026-11-13: Server instructions replace the prompt template (local tests)

- **Base commit**: `17cee21`, with the uncommitted changes that remove
  `prompt_template.md` and add `server_instructions.md`
- **Environment**: Python 3.12 via `uv`, FastMCP 3.4.10, Docker for the
  PostgreSQL 12-18 integration containers
- **Change under test**: the server passes `server_instructions.md` to
  `FastMCP(instructions=...)`; the `prompt_template_full`,
  `prompt_template_headings`, and `prompt_template_section` prompts and the
  `get_prompt_template` tool are removed

| Command | Result |
|---|---|
| `uv run pytest tests --ignore=tests/test_tools_integration.py` | 210 passed / 210 |
| `uv run pytest` (unit + integration, PostgreSQL 12-18) | 546 passed, 35 skipped / 581 (all skips are PG 17+/18+ version gates) |

New test scope (`tests/test_server_instructions.py`):

- Instructions are non-empty and at most 4,096 characters.
- An in-process `fastmcp.Client` receives the instructions in
  `initialize_result.instructions`, and `list_prompts()` returns an empty list.
  FastMCP 3.4.10 has no discover mode, so only the initialize path was tested.

Not verified:

- Behavior in real MCP clients (Claude Code, Claude Desktop, OpenWebUI).
- A wheel or mcpb package built after `server_instructions.md` is tracked by
  Git. setuptools-scm packages only tracked files, so the file must be
  committed for the server to start from a built package.
