"""Server instructions reach clients, and no MCP prompts are exposed.

Claude Code truncates server instructions beyond 4,096 characters, so the file
must stay under that limit. Offline: no database needed.

The installed FastMCP Client has no discover mode, so instructions are read
from ``initialize_result`` only.
"""
import asyncio

from fastmcp import Client

from mcp_postgresql_ops.mcp_main import SERVER_INSTRUCTIONS, mcp

CLAUDE_CODE_INSTRUCTIONS_LIMIT = 4096


def test_instructions_non_empty_and_within_limit():
    assert SERVER_INSTRUCTIONS.strip()
    assert len(SERVER_INSTRUCTIONS) <= CLAUDE_CODE_INSTRUCTIONS_LIMIT


def test_client_receives_instructions_and_no_prompts():
    async def collect():
        async with Client(mcp) as client:
            return client.initialize_result.instructions, await client.list_prompts()

    instructions, prompts = asyncio.run(collect())
    assert instructions == SERVER_INSTRUCTIONS
    assert prompts == []
