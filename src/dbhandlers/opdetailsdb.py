"""
Billeterapp 2.0 - v2.0 Mayo 2026
"""

import os
import sqlite3
from typing import Optional, Any, List

from src import DATAPATH
from src.models.opdetmodel import OperationDetails
from src.dbhandlers.dbutils import DatabaseConnection


class OperationDetailsDB:

    INSERT_QUERY = """
        INSERT INTO operation_details (
              detail_id, operation_id, account_id, details, created_at, updated_at
        ) VALUES (
              :detail_id, :operation_id, :account_id, :details, :created_at, :updated_at
        )
    """
    UPDATE_QUERY = """
        UPDATE
          operation_details
        SET
          operation_id = :operation_id,
          account_id = :account_id,
          details = :details,
          updated_at = :updated_at
        WHERE
          detail_id = :detail_id
    """

    def __init__(self, user_id: str, db_path: Optional[str] = None) -> None:
        path = os.path.join(DATAPATH, user_id, "accounts_database.db")
        self.db_path: str = db_path or os.getenv("ACC_DATABASE_NAME", path) or path
        self.db = DatabaseConnection(self.db_path, enforce_foreign_keys=True)

    def _connect(self) -> sqlite3.Connection:
        return self.db.connect(row_factory=sqlite3.Row)

    def create_detail(self, detail: OperationDetails) -> dict[str, Any]:
        detail_data = detail.to_dict()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(self.INSERT_QUERY, detail_data)
            return detail_data

    def get_detail_by_id(self, detail_id: str) -> sqlite3.Row:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM operation_details WHERE detail_id = ?", (detail_id,))
            record = cur.fetchone()
            return record

    def get_detail_by_operation_id(self, operation_id: str) -> sqlite3.Row:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM operation_details WHERE operation_id = ?", (operation_id,))
            record = cur.fetchone()
            return record

    def get_details_by_account_id(self, account_id: str) -> List[sqlite3.Row]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM operation_details WHERE account_id = ? ORDER BY created_at DESC;", (account_id,))
            records = cur.fetchall()
            return records

    def update_detail(self, detail: OperationDetails) -> None:
        """
        Updates an existing operation detail in the database.

        Args:
            detail: OperationDetails object with the updated data.
        """
        detail_data = detail.to_dict()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(self.UPDATE_QUERY, detail_data)

    def delete_detail(self, detail_id: str) -> None:
        """
        Deletes an operation detail from the database.

        Note: Due to the foreign key constraint in the operations table with ON DELETE CASCADE,
        if an operation is deleted, its associated details will be automatically deleted.

        Args:
            detail_id: The unique identifier of the detail to delete.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM operation_details WHERE detail_id = ?", (detail_id,))
