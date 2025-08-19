#!/usr/bin/env bash
set -euo pipefail

# Concise template renamer for MCP servers.
# Usage:
#   ./scripts/rename-template.sh \
#     --name "my-mcp-server" --author "Your Name" --email "you@example.com" --version "0.1.0" [--desc "..."] [--no-sync]

err() { echo "[rename-template] $*" >&2; }
die() { err "error: $*"; exit 1; }
log() { echo "[rename-template] $*"; }

cd "$(dirname "$0")/.."

# Args
DIST_NAME=""; AUTHOR_NAME=""; AUTHOR_EMAIL=""; VERSION=""; DESC="Add your description here"; DO_SYNC=1
while [[ $# -gt 0 ]]; do case "$1" in
  --name) DIST_NAME="$2"; shift 2;;
  --author) AUTHOR_NAME="$2"; shift 2;;
  --email) AUTHOR_EMAIL="$2"; shift 2;;
  --version) VERSION="$2"; shift 2;;
  --desc) DESC="$2"; shift 2;;
  --no-sync) DO_SYNC=0; shift;;
  -h|--help) sed -n '1,40p' "$0" | sed 's/^# //;tx;d;:x'; exit 0;;
  *) die "unknown arg: $1";; esac; done

[[ -n "$DIST_NAME" && -n "$AUTHOR_NAME" && -n "$AUTHOR_EMAIL" && -n "$VERSION" ]] || \
  die "--name/--author/--email/--version are required"

# Names
PKG_NAME=$(echo "$DIST_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/(^_+|_+$)//g; s/_+/_/g')
DIST_NAME=$(echo "$DIST_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/(^-+|-+$)//g; s/-+/-/g')
log "dist: $DIST_NAME  pkg: $PKG_NAME"

[[ -d src ]] || die "src not found"
[[ -d src/MCP_NAME || -d src/$PKG_NAME ]] || die "src/MCP_NAME not found"
if [[ -d src/MCP_NAME && ! -d src/$PKG_NAME ]]; then mv src/MCP_NAME "src/$PKG_NAME"; fi

# Replace placeholders across tracked files
FILES=$(git ls-files 2>/dev/null || find . -type f)
for f in $FILES; do
  [[ -f "$f" ]] || continue
  case "$f" in ./.git/*|./.venv/*|./dist/*|./build/*|./.ruff_cache/*|./.pytest_cache/*|./.mypy_cache/*|./uv.lock|./scripts/rename-template.sh) continue;; esac
  grep -qE 'MCP_NAME|MCP-NAME|your-server-name' "$f" 2>/dev/null || continue
  sed -i -e "s/MCP_NAME/${PKG_NAME}/g" -e "s/MCP-NAME/${DIST_NAME}/g" -e "s/your-server-name/${DIST_NAME}/g" "$f" || true
done

# pyproject.toml
[[ -f pyproject.toml ]] && cp pyproject.toml pyproject.toml.bak
cat > pyproject.toml <<PY
[project]
name = "${DIST_NAME}"
version = "${VERSION}"
description = "${DESC}"
readme = "README.md"
requires-python = ">=3.11"
authors = [{ name = "${AUTHOR_NAME}", email = "${AUTHOR_EMAIL}" }]
dependencies = [
    "fastmcp>=2.11.1"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0"
]

[project.scripts]
${DIST_NAME} = "${PKG_NAME}.mcp_main:main"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"
PY

# No need to add CLI function since main() already exists and handles CLI arguments
log "Using existing main() function as CLI entrypoint"

# Optional sync
if [[ $DO_SYNC -eq 1 ]] && command -v uv >/dev/null 2>&1; then
  uv sync || log "uv sync failed; run manually if needed"
fi

cat <<EOM
[rename-template] Done
- dist: ${DIST_NAME}
- pkg : ${PKG_NAME}
Backup: pyproject.toml.bak (if existed)
Next: edit src/${PKG_NAME}/mcp_main.py and src/${PKG_NAME}/functions.py
EOM
