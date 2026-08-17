"""
Central database utility module for connection setup and adapter registration.

This module provides:
- SQLite adapter and converter registration for custom types
- Consistent database connection setup
- Context managers for database operations
- Foreign key enforcement configuration
"""

import sqlite3
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Callable
from contextlib import contextmanager


def register_sqlite_adapters() -> None:
    """
    Register custom SQLite adapters and converters for Python types.

    This function should be called once at application startup to ensure
    consistent type handling across all database operations.

    Adapters registered:
    - date: Converts to ISO format string
    - datetime: Converts to ISO format string
    - Decimal: Converts to string representation

    Converters registered:
    - DECIMAL: Converts string back to Decimal
    """
    # Custom sqlite3 adapters for date and datetime
    sqlite3.register_adapter(date, lambda val: val.isoformat())
    sqlite3.register_adapter(datetime, lambda val: val.isoformat())
    # Custom sqlite3 converters for date and datetime
    sqlite3.register_converter(
        "DATE", lambda val: datetime.fromisoformat(val.decode() if isinstance(val, bytes) else val)
    )
    sqlite3.register_converter(
        "DATETIME", lambda val: datetime.fromisoformat(val.decode() if isinstance(val, bytes) else val)
    )

    # Custom sqlite3 adapter for decimals
    sqlite3.register_adapter(Decimal, lambda val: str(val))
    # Custom sqlite3 converter for decimals, if val if bytes will decode them first, if not proceeds
    sqlite3.register_converter("DECIMAL", lambda val: Decimal(val.decode() if isinstance(val, bytes) else val))

    # Custom sqlite3 adapter for tuples converting them to a string with commas to store in the db
    sqlite3.register_adapter(tuple, lambda val: ",".join(val))
    # Custom sqlite3 converter for strings with commas to convert them as tuples
    sqlite3.register_converter("TUPLE", lambda val: tuple([v for v in val.split(b",") if v.strip()]))


# Register adapters when module is imported
register_sqlite_adapters()


def get_connection(
    db_path: str, enforce_foreign_keys: bool = True, row_factory: Optional[Callable] = None
) -> sqlite3.Connection:
    """
    Create and configure a SQLite database connection.

    Args:
        db_path: Path to the SQLite database file
        enforce_foreign_keys: Whether to enable foreign key constraints (default: True)
        row_factory: Optional row factory function (e.g., sqlite3.Row for dict-like access)

    Returns:
        Configured SQLite connection object

    Example:
        >>> conn = get_connection("database.db")
        >>> conn = get_connection("database.db", row_factory=sqlite3.Row)
    """
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    if enforce_foreign_keys:
        conn.execute("PRAGMA foreign_keys = ON;")

    if row_factory:
        conn.row_factory = row_factory

    return conn


@contextmanager
def get_connection_context(db_path: str, enforce_foreign_keys: bool = True, row_factory: Optional[Callable] = None):
    """
    Context manager for database connections that ensures proper cleanup.

    Args:
        db_path: Path to the SQLite database file
        enforce_foreign_keys: Whether to enable foreign key constraints (default: True)
        row_factory: Optional row factory function

    Yields:
        SQLite connection object

    Example:
        >>> with get_connection_context("database.db") as conn:
        ...     conn.execute("SELECT * FROM users")
    """
    conn = get_connection(db_path, enforce_foreign_keys, row_factory)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class DatabaseConnection:
    """
    reusable database connection manager class.

    This class provides a simple interface for managing database connections
    with consistent configuration across the application.

    Example:
        >>> db = DatabaseConnection("database.db")
        >>> with db.connect() as conn:
        ...     conn.execute("SELECT * FROM users")
    """

    def __init__(self, db_path: str, enforce_foreign_keys: bool = True, default_row_factory: Optional[Callable] = None):
        """
        Initialize database connection manager.

        Args:
            db_path: Path to the SQLite database file
            enforce_foreign_keys: Whether to enable foreign key constraints (default: True)
            default_row_factory: Optional default row factory for all connections
        """
        self.db_path = db_path
        self.enforce_foreign_keys = enforce_foreign_keys
        self.default_row_factory = default_row_factory

    def connect(
        self, row_factory: Optional[Callable] = None, enforce_foreign_keys: Optional[bool] = None
    ) -> sqlite3.Connection:
        """
        Create a new database connection.

        Args:
            row_factory: Optional row factory (overrides default if provided)
            enforce_foreign_keys: Optional foreign key setting (overrides default if provided)

        Returns:
            SQLite connection object
        """
        if enforce_foreign_keys is None:
            enforce_foreign_keys = self.enforce_foreign_keys

        if row_factory is None:
            row_factory = self.default_row_factory

        return get_connection(self.db_path, enforce_foreign_keys=enforce_foreign_keys, row_factory=row_factory)

    @contextmanager
    def connection_context(self, row_factory: Optional[Callable] = None, enforce_foreign_keys: Optional[bool] = None):
        """
        Context manager for database connections.

        Args:
            row_factory: Optional row factory (overrides default if provided)
            enforce_foreign_keys: Optional foreign key setting (overrides default if provided)

        Yields:
            SQLite connection object
        """
        conn = self.connect(row_factory, enforce_foreign_keys)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
