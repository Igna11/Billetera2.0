"""
Abril 2026
"""

import os
import sqlite3

from src import DATAPATH


def initialize_operations_table(user_id: str, database_name: str = "accounts_database.db") -> None:
    db_path = os.path.join(DATAPATH, user_id, database_name)
    with sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS operations (
              operation_id TEXT PRIMARY KEY,
              account_id TEXT NOT NULL,
              operation_datetime DATETIME NOT NULL,
              cumulative_amount DECIMAL NOT NULL,
              amount DECIMAL NOT NULL,
              operation_type TEXT NOT NULL,
              category TEXT,
              subcategory TEXT,
              description TEXT,
              tags TUPLE,
              group_id TEXT,
              detail_id TEXT,
              transfer_id TEXT,
              created_at DATETIME,
              updated_at DATETIME,
              FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE SET NULL,
              FOREIGN KEY (detail_id) REFERENCES operation_details (detail_id) ON DELETE SET NULL,
              FOREIGN KEY (group_id) REFERENCES operation_groups (group_id) ON DELETE SET NULL
            )"""
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_operation_account_id 
            ON operations(account_id);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_operation_datetime 
            ON operations(operation_datetime);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_operation_operations_account_datetime_op_id
            ON operations(account_id, operation_datetime, operation_id);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_operation_type 
            ON operations(operation_type);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_operation_transfer_id 
            ON operations(transfer_id);
            """
        )
