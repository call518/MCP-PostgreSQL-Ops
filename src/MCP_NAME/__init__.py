"""MCP Server package.

This module exposes the `mcp` FastMCP instance for convenience.
Importing this package will not start the server; use the CLI entrypoint or
call `mcp.run()` explicitly in your own launcher if needed.
"""

from .mcp_main import mcp  # noqa: F401

__all__ = ["mcp"]

