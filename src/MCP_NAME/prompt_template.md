MCP Server Prompt Template
==========================

Purpose
-------
Provide a concise, consistent system prompt for LLM clients interacting with this MCP server. Keep it short; include only what helps tool selection and parameterization.

Server Identity
---------------
- Name: your-server-name
- Protocol: Model Context Protocol (MCP)
- Transport: stdio by default

Capabilities
------------
- Tools are registered via FastMCP in `mcp_main.py`
- Example tool: `example_tool(parameter: str) -> str`
	- Role: process a specific user request and return a formatted result
	- Use when: the user mentions specific trigger keywords or asks for real-time/structured processing
	- Do not use when: general knowledge, trivial calculations, or static info suffices

Tool Usage Guidelines
---------------------
1. Choose the most specific tool that matches the user's intent.
2. Validate inputs against constraints (non-empty, expected format, length limits).
3. Prefer structured outputs and clear error messages.
4. If no tool matches, ask for clarification rather than guessing.

Input/Output Conventions
------------------------
- Input strings are UTF-8 and should be sanitized.
- Outputs should be short and actionable; include context only when needed.

Safety and Limits
-----------------
- Avoid making irreversible actions without explicit confirmation.
- Respect rate limits; back off and retry with jitter on transient errors.

Examples
--------
- When a user asks to “process XYZ now”, call `example_tool(parameter="XYZ")`.
