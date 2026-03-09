# Integration & Unit Test Suite Design

**Goal:** Comprehensive test coverage for all 38 MCP tools across PostgreSQL 12-18.

**Architecture:** Docker Compose stack with 7 PG instances running simultaneously. pytest suite with parametrized tests across all versions. GitHub Actions CI on PRs and pushes to main.

**Tech Stack:** pytest, pytest-asyncio, asyncpg, Docker Compose, GitHub Actions

---

## Test Layers

### 1. Unit Tests (test_version_compat.py)
- Test every `PostgreSQLVersion` property for PG 12-18
- Test query generators produce valid SQL (no trailing commas, correct columns)
- No database required

### 2. Integration Tests (test_tools_integration.py)
- Call every MCP tool function directly (no MCP protocol overhead)
- Parametrized across all 7 PG versions
- Verify: no exceptions, returns string, contains expected data markers
- Version-gated tools tested for graceful fallback on unsupported versions

### 3. Test Data (init-test-db.sql)
- pg_stat_statements extension
- 2 schemas, 5 tables with foreign keys and indexes
- ~100 rows of sample data
- Warm stats views with queries

## Docker Compose

7 services: pg12-pg18 on ports 5412-5418. All use `postgres:XX-alpine` images (PG 18 uses beta image). Shared init script, health checks, `shared_preload_libraries=pg_stat_statements`.

## CI/CD

GitHub Actions workflow on PR and push to main. Single job: docker compose up → wait for health → pytest → docker compose down.

## Out of Scope
- MCP protocol transport testing
- Authentication/auth token testing
- Docker deployment config testing
- Prompt template tool testing
