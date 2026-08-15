"""
Mayo 2026
operation_details table: A table destined to store details for a given operation, like a photo of a receipt.
The operations table will store operations, some of which will need to have one or more details, so one operation
could be related to one or more entries in the details table:
So there is a relation one to one or many from operations to operations_details.
"""

import os
import sqlite3

from src import DATAPATH


def initialize_details_table(user_id: str, database_name: str = "accounts_database.db") -> None:
    db_path = os.path.join(DATAPATH, user_id, database_name)
    with sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS operation_details (
              detail_id TEXT PRIMARY KEY,
              operation_id TEXT NOT NULL,
              account_id TEXT NOT NULL,
              details BLOB NOT NULL,
              created_at DATETIME,
              updated_at DATETIME,
              FOREIGN KEY (operation_id) REFERENCES operations (operation_id) ON DELETE CASCADE,
              FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE SET NULL
            )"""
        )
