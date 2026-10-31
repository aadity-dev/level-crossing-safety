"""SQLite database connection and migration management."""

import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager

from level_crossing.common.exceptions import DatabaseError
from level_crossing.common.logger import get_logger
from level_crossing.database.schema import V3_1_SCHEMA

logger = get_logger("database")


class DatabaseManager:
    """Manages SQLite connections, migrations, and transactional integrity."""

    def __init__(self, db_path: str | Path = "data/level_crossing.sqlite3"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back due to error: {e}")
            raise DatabaseError(f"Database transaction failure: {e}") from e
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Executes V3.1 schema migrations."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.executescript(V3_1_SCHEMA)
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
                ("3.1.0",),
            )
            conn.commit()
        logger.info(f"Database initialized and schema 3.1.0 verified at {self.db_path}")
