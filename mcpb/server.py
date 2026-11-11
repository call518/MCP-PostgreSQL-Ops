"""MCPB entry point: run MCP-PostgreSQL-Ops over stdio."""

from mcp_postgresql_ops.mcp_main import main


if __name__ == "__main__":
    main(["--type", "stdio"])
