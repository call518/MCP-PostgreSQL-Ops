import asyncpg
import logging
import os
from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime

# Logger configuration
logger = logging.getLogger(__name__)

# PostgreSQL connection configuration
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "database": os.getenv("POSTGRES_DB", "postgres"),
}


async def get_current_database_name(database: str = None) -> str:
    """Get the name of the currently connected database.
    
    Args:
        database: Database name to connect to. If None, uses default from config.
        
    Returns:
        Current database name as string
    """
    try:
        query = "SELECT current_database() as database_name"
        result = await execute_query(query, [], database=database)
        return result[0]['database_name'] if result else "unknown"
    except Exception as e:
        logger.error(f"Failed to get current database name: {e}")
        return "unknown"


async def get_db_connection(database: str = None) -> asyncpg.Connection:
    """Create PostgreSQL database connection.
    
    Args:
        database: Database name to connect to. If None, uses default from config.
    """
    try:
        config = POSTGRES_CONFIG.copy()
        if database:
            config["database"] = database
            
        conn = await asyncpg.connect(**config)
        logger.debug(f"Connected to PostgreSQL at {config['host']}:{config['port']}/{config['database']}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise


async def execute_query(query: str, params: Optional[List] = None, database: str = None) -> List[Dict[str, Any]]:
    """Execute query and return results.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        database: Database name to connect to. If None, uses default from config.
    """
    conn = None
    try:
        conn = await get_db_connection(database)
        if params:
            rows = await conn.fetch(query, *params)
        else:
            rows = await conn.fetch(query)
        
        # Convert Record to Dict
        result = []
        for row in rows:
            result.append(dict(row))
        
        logger.debug(f"Query executed successfully, returned {len(result)} rows")
        return result
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        logger.debug(f"Failed query: {query}")
        raise
    finally:
        if conn:
            await conn.close()


async def execute_single_query(query: str, params: Optional[List] = None, database: str = None) -> Optional[Dict[str, Any]]:
    """Execute query that returns a single result.
    
    Args:
        query: SQL query to execute
        params: Query parameters  
        database: Database name to connect to. If None, uses default from config.
    """
    results = await execute_query(query, params, database)
    return results[0] if results else None


def format_bytes(bytes_value: Union[int, float, None]) -> str:
    """Format byte values into human-readable format."""
    if bytes_value is None:
        return "N/A"
    
    bytes_value = float(bytes_value)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_duration(seconds: Union[int, float, None]) -> str:
    """Format seconds into human-readable format."""
    if seconds is None:
        return "N/A"
    
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        return f"{seconds/60:.2f}m"
    else:
        return f"{seconds/3600:.2f}h"


def format_table_data(data: List[Dict[str, Any]], title: str = "") -> str:
    """Convert table data into formatted string."""
    if not data:
        return f"No data found{' for ' + title if title else ''}"
    
    result = []
    if title:
        result.append(f"=== {title} ===\n")
    
    # Format as table
    if len(data) == 1:
        # Display single record as key-value pairs
        for key, value in data[0].items():
            if isinstance(value, (int, float)) and key.endswith(('_bytes', '_size')):
                value = format_bytes(value)
            elif isinstance(value, (int, float)) and key.endswith(('_time', '_duration')):
                value = format_duration(value)
            result.append(f"{key}: {value}")
    else:
        # Display multiple records as table format
        headers = list(data[0].keys())
        
        # Add headers
        result.append(" | ".join(headers))
        result.append("-" * (sum(len(h) for h in headers) + len(headers) * 3 - 1))
        
        # Add data rows
        for row in data:
            formatted_row = []
            for key, value in row.items():
                if isinstance(value, (int, float)) and key.endswith(('_bytes', '_size')):
                    formatted_row.append(format_bytes(value))
                elif isinstance(value, (int, float)) and key.endswith(('_time', '_duration')):
                    formatted_row.append(format_duration(value))
                else:
                    formatted_row.append(str(value) if value is not None else "NULL")
            result.append(" | ".join(formatted_row))
    
    return "\n".join(result)


async def get_server_version() -> str:
    """Return PostgreSQL server version."""
    try:
        result = await execute_single_query("SELECT version()")
        return result["version"] if result else "Unknown"
    except Exception as e:
        logger.error(f"Failed to get server version: {e}")
        return f"Error: {e}"


async def check_extension_exists(extension_name: str) -> bool:
    """Check if extension is installed."""
    try:
        query = "SELECT 1 FROM pg_extension WHERE extname = $1"
        result = await execute_single_query(query, [extension_name])
        return result is not None
    except Exception:
        return False


# pg_stat_statements related functions
async def get_pg_stat_statements_data(limit: int = 20, database: str = None) -> List[Dict[str, Any]]:
    """Get query statistics from pg_stat_statements.
    
    Args:
        limit: Maximum number of results to return
        database: Database name to query (uses default if omitted)
    """
    from .version_compat import get_pg_stat_statements_query
    
    try:
        # Get version-compatible query
        base_query = await get_pg_stat_statements_query(database)
        query = f"{base_query} LIMIT $1"
        
        return await execute_query(query, [limit], database=database)
    except Exception as e:
        logger.error(f"Failed to fetch pg_stat_statements data: {e}")
        raise Exception(f"Failed to fetch pg_stat_statements data: {e}")


# pg_stat_monitor related functions
async def get_pg_stat_monitor_data(limit: int = 20, database: str = None) -> List[Dict[str, Any]]:
    """Get query statistics from pg_stat_monitor.
    
    Args:
        limit: Maximum number of results to return
        database: Database name to query (uses default if omitted)
    """
    from .version_compat import get_pg_stat_monitor_query
    
    try:
        # Get version-compatible query
        base_query = await get_pg_stat_monitor_query(database)
        query = f"{base_query} LIMIT $1"
        
        return await execute_query(query, [limit], database=database)
    except Exception as e:
        logger.error(f"Failed to fetch pg_stat_monitor data: {e}")
        raise Exception(f"Failed to fetch pg_stat_monitor data: {e}")


def sanitize_connection_info() -> Dict[str, Any]:
    """Remove sensitive information from connection info."""
    config = POSTGRES_CONFIG.copy()
    config["password"] = "***"
    return config


def read_prompt_template(path: str) -> str:
    """
    Reads the MCP prompt template file and returns its content as a string.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_prompt_sections(template: str):
    """
    Parses the prompt template into section headings and sections.
    Returns (headings, sections).
    """
    lines = template.splitlines()
    sections = []
    current = []
    headings = []
    for line in lines:
        if line.startswith("## "):
            if current:
                sections.append("\n".join(current))
                current = []
            headings.append(line[3:].strip())
            current.append(line)
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current))
    return headings, sections

