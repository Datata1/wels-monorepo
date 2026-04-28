"""
DuckDB utility for backend — read-only connection and query helpers.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import duckdb

from backend.config import settings


def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a read-only DuckDB connection using the configured path.
    """
    db_path = Path(settings.duckdb_path)
    return duckdb.connect(str(db_path), read_only=True)


def query_duckdb(query: str, params: list[Any] | None = None) -> Iterator[dict[str, Any]]:
    """
    Executes a query and yields rows as dicts.
    """
    with get_duckdb_connection() as conn:
        cursor = conn.execute(query, params or [])
        cols = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            yield dict(zip(cols, row, strict=True))
