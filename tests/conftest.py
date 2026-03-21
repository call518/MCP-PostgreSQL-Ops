"""Shared fixtures for MCP PostgreSQL Ops test suite."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

DOCKER_COMPOSE_FILE = str(
    Path(__file__).parent / "docker" / "docker-compose.test.yml"
)

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

WAIT_TIMEOUT_SEC = 120


def _is_pg_available(port: int) -> bool:
    """TCP-level check: PostgreSQL is listening."""
    try:
        with socket.create_connection((PG_HOST, port), timeout=2):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def _is_pg_initialized(port: int) -> bool:
    """SQL-level check: init-test-db.sql has finished (sales.customers table exists)."""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=PG_HOST,
            port=port,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB,
            connect_timeout=2,
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='sales' AND table_name='customers'"
            )
            found = cur.fetchone() is not None
        conn.close()
        return found
    except Exception:
        return False


def _all_pg_initialized() -> bool:
    """Return True if every PG instance is already fully initialized."""
    return all(_is_pg_initialized(port) for _, port in PG_VERSIONS)


def _wait_for_all_pg(timeout: int = WAIT_TIMEOUT_SEC) -> None:
    """Poll until every PG container is fully initialized (schema + data ready)."""
    deadline = time.monotonic() + timeout
    pending = list(PG_VERSIONS)
    while pending and time.monotonic() < deadline:
        still_pending = []
        for major, port in pending:
            if _is_pg_initialized(port):
                print(f"  [ready] PG{major} (port {port})")
            else:
                still_pending.append((major, port))
        pending = still_pending
        if pending:
            time.sleep(2)
    if pending:
        versions = ", ".join(f"PG{v}" for v, _ in pending)
        raise RuntimeError(
            f"Timed out after {timeout}s waiting for: {versions}"
        )


@pytest.fixture(scope="session", autouse=True)
def docker_compose_pg():
    """Start test PostgreSQL containers and tear them down after the session.

    Automatically detects if containers are already running (e.g. in CI)
    and skips Docker lifecycle management in that case.
    """
    if _all_pg_initialized():
        print("\n[conftest] Containers already running — skipping Docker lifecycle.")
        yield
        return

    print("\n[conftest] Starting test PostgreSQL containers (PG 12-18)...")
    subprocess.run(
        ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d"],
        check=True,
    )
    try:
        print(
            f"[conftest] Waiting for all instances "
            f"(timeout: {WAIT_TIMEOUT_SEC}s)..."
        )
        _wait_for_all_pg()
        print("[conftest] All PostgreSQL instances ready.\n")
        yield
    finally:
        print("\n[conftest] Tearing down test containers and volumes...")
        subprocess.run(
            ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down", "-v"],
            check=False,
        )
        print("[conftest] Cleanup complete.")


def is_pg_available(port: int) -> bool:
    """Check if a PG instance is reachable (for skipping unavailable versions)."""
    return _is_pg_available(port)


@pytest.fixture(params=PG_VERSIONS, ids=[f"PG{v}" for v, _ in PG_VERSIONS])
def pg_config(request: pytest.FixtureRequest):
    """Parametrized fixture providing (major_version, port) for each PG version."""
    major, port = request.param
    if not is_pg_available(port):
        pytest.skip(f"PostgreSQL {major} not available on port {port}")
    return major, port


@pytest.fixture
def setup_env(monkeypatch: pytest.MonkeyPatch, pg_config):
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

    monkeypatch.setattr(
        fn,
        "POSTGRES_CONFIG",
        {
            "host": PG_HOST,
            "port": port,
            "user": PG_USER,
            "password": PG_PASSWORD,
            "database": PG_DB,
        },
    )

    yield major, port
