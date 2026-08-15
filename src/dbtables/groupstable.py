"""
Mayo 2026
operations_group table: A table destined to store one group per row.
The operations table will store operations, some of which will be related to one group of the operations_group table.
So there is a relation many to one from operations to operations_group.
"""

import os
import sqlite3

from src import DATAPATH


def initialize_groups_table(user_id: str, database_name: str = "accounts_database.db") -> None:
    db_path = os.path.join(DATAPATH, user_id, database_name)
    with sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS operation_groups (
              group_id TEXT PRIMARY KEY,
              group_datetime DATETIME NOT NULL,
              group_name TEXT NOT NULL,
              group_currency TEXT NOT NULL,
              original_amount DECIMAL,
              category TEXT,
              subcategory TEXT,
              description TEXT,
              status TEXT NOT NULL,
              created_at DATETIME,
              updated_at DATETIME
              )
            """
        )
