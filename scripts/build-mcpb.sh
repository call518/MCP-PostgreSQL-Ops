#!/bin/bash
# Build the Claude Desktop MCP Bundle (.mcpb) from an explicit file allowlist.
# Usage: scripts/build-mcpb.sh <version> [output-dir]
set -euo pipefail

VERSION="${1:?usage: scripts/build-mcpb.sh <version> [output-dir]}"
OUT_DIR="${2:-dist}"
MCPB_CLI="@anthropic-ai/mcpb@2.1.2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp "$ROOT/mcpb/server.py" "$ROOT/pyproject.toml" "$ROOT/uv.lock" \
   "$ROOT/README.md" "$ROOT/LICENSE" "$STAGE/"
mkdir -p "$STAGE/src"
cp -R "$ROOT/src/mcp_postgresql_ops" "$STAGE/src/"
find "$STAGE/src" -name '__pycache__' -type d -prune -exec rm -rf {} +

# The bundle has no Git metadata, so provide its release version to setuptools-scm.
python3 - "$ROOT/mcpb/manifest.json" "$STAGE/manifest.json" "$VERSION" <<'EOF'
import json
import sys

source, target, version = sys.argv[1:]
with open(source, encoding="utf-8") as source_file:
    manifest = json.load(source_file)
manifest["version"] = version
manifest["server"]["mcp_config"]["env"]["SETUPTOOLS_SCM_PRETEND_VERSION"] = version
with open(target, "w", encoding="utf-8") as target_file:
    json.dump(manifest, target_file, indent=2)
EOF

mkdir -p "$OUT_DIR"
OUTPUT="$(cd "$OUT_DIR" && pwd)/mcp-postgresql-ops-$VERSION.mcpb"
npx -y "$MCPB_CLI" validate "$STAGE/manifest.json"
npx -y "$MCPB_CLI" pack "$STAGE" "$OUTPUT"
echo "Built $OUTPUT"
