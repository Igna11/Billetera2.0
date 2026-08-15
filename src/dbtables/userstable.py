"""
Marzo 2026
"""

import os
import sqlite3

from src import DATAPATH


def initialize_users_table(database_name: str = "database.db") -> None:
    db_path = os.path.join(DATAPATH, database_name)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                birthdate DATE,
                gender TEXT,
                region TEXT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at DATETIME,
                updated_at DATETIME
            )"""
        )
