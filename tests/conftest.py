"""Shared fixtures for MCP PostgreSQL Ops test suite."""
import os
import sys
import pytest

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# PG version configs: (major_version, port)
PG_VERSIONS = [
    (12, 5412),
    (13, 5413),
    (14, 5414),
    (15, 5415),
    (16, 5416),
    (17, 5417),
    (18, 5418),
]

PG_USER = "postgres"
PG_PASSWORD = "testpass"
PG_DB = "testdb"
PG_HOST = "localhost"


def is_pg_available(port: int) -> bool:
    """Check if a PG instance is reachable (for skipping unavailable versions)."""
    import socket
    try:
        with socket.create_connection((PG_HOST, port), timeout=2):
            return True
    except (ConnectionRefusedError, OSError):
        return False


@pytest.fixture(params=PG_VERSIONS, ids=[f"PG{v}" for v, _ in PG_VERSIONS])
def pg_config(request):
    """Parametrized fixture providing (major_version, port) for each PG version."""
    major, port = request.param
    if not is_pg_available(port):
        pytest.skip(f"PostgreSQL {major} not available on port {port}")
    return major, port


@pytest.fixture
def setup_env(monkeypatch, pg_config):
    """Set environment variables so MCP tools connect to the right PG instance."""
    major, port = pg_config

    monkeypatch.setenv("POSTGRES_HOST", PG_HOST)
    monkeypatch.setenv("POSTGRES_PORT", str(port))
    monkeypatch.setenv("POSTGRES_USER", PG_USER)
    monkeypatch.setenv("POSTGRES_PASSWORD", PG_PASSWORD)
    monkeypatch.setenv("POSTGRES_DB", PG_DB)

    # Clear the version cache so it re-detects for this PG instance
    import mcp_postgresql_ops.version_compat as vc
    monkeypatch.setattr(vc, "_cached_version", None)

    # Reload functions module to pick up new env vars
    import mcp_postgresql_ops.functions as fn
    monkeypatch.setattr(fn, "POSTGRES_CONFIG", {
        "host": PG_HOST,
        "port": port,
        "user": PG_USER,
        "password": PG_PASSWORD,
        "database": PG_DB,
    })

    yield major, port
