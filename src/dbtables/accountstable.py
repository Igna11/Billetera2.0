"""
Marzo 2026
"""

import os
import sqlite3

from src import DATAPATH


def initialize_accounts_table(user_id: str, database_name: str = "accounts_database.db") -> None:
    db_path = os.path.join(DATAPATH, user_id, database_name)
    with sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
              account_id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              account_name TEXT NOT NULL,
              account_currency TEXT NOT NULL,
              account_unique_name TEXT GENERATED ALWAYS AS (account_name || '_' || account_currency) VIRTUAL UNIQUE,
              account_total DECIMAL,
              is_active BOOLEAN NOT NULL CHECK (is_active IN (0, 1)),
              tags TUPLE,
              created_at DATETIME,
              updated_at DATETIME
            )"""
        )
