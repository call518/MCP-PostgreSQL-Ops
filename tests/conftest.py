"""Shared fixtures for MCP PostgreSQL Ops test suite."""
import os
import sys
import asyncio
import pytest
import asyncpg

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


def pg_dsn(port: int) -> str:
    return f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{port}/{PG_DB}"


def is_pg_available(port: int) -> bool:
    """Check if a PG instance is reachable (for skipping unavailable versions)."""
    import socket
    try:
        with socket.create_connection((PG_HOST, port), timeout=2):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def pg_version_id(val):
    """Generate readable test IDs like 'PG12', 'PG18'."""
    if isinstance(val, tuple) and len(val) == 2:
        return f"PG{val[0]}"
    return str(val)


@pytest.fixture(params=PG_VERSIONS, ids=[f"PG{v}" for v, _ in PG_VERSIONS])
def pg_config(request):
    """Parametrized fixture providing (major_version, port) for each PG version."""
    major, port = request.param
    if not is_pg_available(port):
        pytest.skip(f"PostgreSQL {major} not available on port {port}")
    return major, port


@pytest.fixture
async def pg_conn(pg_config):
    """Async fixture providing an asyncpg connection to the parametrized PG version."""
    major, port = pg_config
    conn = await asyncpg.connect(pg_dsn(port))
    yield conn
    await conn.close()


@pytest.fixture
def setup_env(pg_config):
    """Set environment variables so MCP tools connect to the right PG instance."""
    major, port = pg_config
    old_env = {}
    env_vars = {
        "POSTGRES_HOST": PG_HOST,
        "POSTGRES_PORT": str(port),
        "POSTGRES_USER": PG_USER,
        "POSTGRES_PASSWORD": PG_PASSWORD,
        "POSTGRES_DB": PG_DB,
    }
    for key, val in env_vars.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = val

    # Clear the version cache so it re-detects for this PG instance
    import mcp_postgresql_ops.version_compat as vc
    vc._cached_version = None

    # Reload functions module to pick up new env vars
    import mcp_postgresql_ops.functions as fn
    fn.POSTGRES_CONFIG = {
        "host": PG_HOST,
        "port": port,
        "user": PG_USER,
        "password": PG_PASSWORD,
        "database": PG_DB,
    }

    yield major, port

    # Restore env
    for key, val in old_env.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val
    vc._cached_version = None
