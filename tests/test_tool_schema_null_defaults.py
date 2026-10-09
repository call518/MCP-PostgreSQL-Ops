"""Every tool argument that defaults to null must also accept null.

FastMCP advertises `"default": null` for an argument written as
`x: str = None`, but types it `"type": "string"`, so a client that sends the
advertised default back (some agent frameworks fill in every optional
argument) fails validation before the tool runs. Offline: no database needed.
"""
import asyncio

from fastmcp import Client

from mcp_postgresql_ops.mcp_main import mcp


def _null_default_args_rejecting_null():
    async def collect():
        async with Client(mcp) as client:
            tools = await client.list_tools()
        bad = []
        for tool in tools:
            for name, prop in tool.inputSchema.get("properties", {}).items():
                if "default" not in prop or prop["default"] is not None:
                    continue
                types = [prop.get("type")] + [s.get("type") for s in prop.get("anyOf", [])]
                if "null" not in types:
                    bad.append(f"{tool.name}.{name}")
        return bad

    return asyncio.run(collect())


def test_null_default_arguments_accept_null():
    assert _null_default_args_rejecting_null() == []
