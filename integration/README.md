# Integration Tests

Snapshot-based regression tests for the MCP protocol surface. A golden cassette records the `initialize` handshake and all tool schemas via `tools/list`. CI verifies that every PR still matches. If a tool is renamed, removed, or has its schema changed, the diff shows exactly what broke.

Uses [mcp-recorder](https://github.com/devhelmhq/mcp-recorder) for recording and verification.

## What's tested

| Cassette | What it guards |
|---|---|
| `protocol_and_schemas.json` | Protocol version, server capabilities, all 35 tool names and input schemas |

## Setup

```bash
pip install -r integration/requirements.txt
```

## Verify locally

```bash
mcp-recorder verify \
  --cassette integration/cassettes/protocol_and_schemas.json \
  --target-stdio "mcp-postgresql-ops"
```

All interactions should pass. The MCP server is spawned as a subprocess automatically. No running PostgreSQL needed -- `initialize` and `tools/list` don't query the database.

## Update cassettes after intentional changes

When you've changed a tool schema, added a new tool, or removed one:

```bash
mcp-recorder verify \
  --cassette integration/cassettes/protocol_and_schemas.json \
  --target-stdio "mcp-postgresql-ops" \
  --update
```

This replays the recorded requests, accepts the new responses, and writes them back to the cassette. Commit the updated cassette with your PR -- the diff makes the schema change visible in review.

## Re-record from scratch

```bash
mcp-recorder record-scenarios integration/scenarios.yml \
  --output-dir integration/cassettes
```

See the [mcp-recorder docs](https://github.com/devhelmhq/mcp-recorder) for more options.
