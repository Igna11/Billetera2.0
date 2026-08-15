"""
Billeterapp 2.0 - v2.0 Mayo 2026
"""

import os
import sqlite3
from typing import Optional, Literal, Any, List

from src import DATAPATH
from src.models.opgroupsmodel import OperationGroups
from src.dbhandlers.dbutils import DatabaseConnection


class OperationGroupsDB:

    INSERT_QUERY = """
        INSERT INTO operation_groups (
              group_id, group_datetime, group_name, group_currency, original_amount,
              category, subcategory, description, status, created_at, updated_at
        ) VALUES (
              :group_id, :group_datetime, :group_name, :group_currency, :original_amount,
              :category, :subcategory, :description, :status, :created_at, :updated_at
        )
    """
    UPDATE_QUERY = """
        UPDATE
          operation_groups
        SET
          group_datetime = :group_datetime,
          group_name = :group_name,
          group_currency = :group_currency,
          original_amount = :original_amount,
          category = :category,
          subcategory = :subcategory,
          description = :description,
          status = :status,
          updated_at = :updated_at
        WHERE
          group_id = :group_id
    """

    def __init__(self, user_id: str, db_path: Optional[str] = None) -> None:
        path = os.path.join(DATAPATH, user_id, "accounts_database.db")
        self.db_path: str = db_path or os.getenv("ACC_DATABASE_NAME", path) or path
        self.db = DatabaseConnection(self.db_path, enforce_foreign_keys=True)

    def _connect(self) -> sqlite3.Connection:
        return self.db.connect(row_factory=sqlite3.Row)

    def create_group(self, group: OperationGroups) -> dict[str, Any]:
        group_data = group.to_dict()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(self.INSERT_QUERY, group_data)
            return group_data

    def get_group_by_id(self, group_id: str) -> sqlite3.Row:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM operation_groups WHERE group_id = ?", (group_id,))
            record = cur.fetchone()
            return record

    def get_groups_list(self, status: Optional[Literal["open", "closed"]] = None) -> List[sqlite3.Row]:
        """
        Returns a list of all existing groups, optionally filtered by status.

        Args:
            status: Optional filter for group status ('open', 'closed'). If None, returns all groups.

        Returns:
            List of sqlite3.Row objects representing the groups.
        """
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            if status == "open":
                cur.execute("SELECT * FROM operation_groups WHERE status = 'open' ORDER BY group_datetime DESC;")
            elif status == "closed":
                cur.execute("SELECT * FROM operation_groups WHERE status = 'closed' ORDER BY group_datetime DESC;")
            else:
                cur.execute("SELECT * FROM operation_groups ORDER BY group_datetime DESC;")

            records = cur.fetchall()
            return records

    def update_group(self, group: OperationGroups) -> None:
        group_data = group.to_dict()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(self.UPDATE_QUERY, group_data)

    def delete_group(self, group_id: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM operation_groups WHERE group_id = ?", (group_id,))
