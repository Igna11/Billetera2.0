"""
Billeterapp 2.0 - v2.0 Marzo 2026
"""

import os
import sqlite3
from typing import Optional, Any

from src import DATAPATH
from src.models.accmodel import Accounts
from src.dbhandlers.dbutils import DatabaseConnection


class AccountsDB:

    INSERT_QUERY = """
        INSERT INTO accounts (
          account_id, user_id, account_name, account_currency,
          account_total, is_active, tags, created_at, updated_at
        )
        VALUES (
          :account_id, :user_id, :account_name, :account_currency,
          :account_total, :is_active, :tags, :created_at, :updated_at
        )
    """
    UPDATE_QUERY = """
        UPDATE
          accounts
        SET
          account_name = :account_name,
          account_currency = :account_currency,
          account_total = :account_total,
          is_active = :is_active,
          tags = :tags,
          updated_at = :updated_at
        WHERE
          account_id = :account_id
       """

    def __init__(self, user_id: str, db_path: Optional[str] = None) -> None:
        path = os.path.join(DATAPATH, user_id, "accounts_database.db")
        self.db_path: str = db_path or os.getenv("ACC_DATABASE_NAME", path) or path
        self.db = DatabaseConnection(self.db_path, enforce_foreign_keys=False)

    def _connect(self) -> sqlite3.Connection:
        return self.db.connect(row_factory=sqlite3.Row)

    def create_account(self, account: Accounts) -> dict[str, Any]:
        acc_data = account.to_dict()
        # insert new account operations table name into accounts table
        with self._connect() as conn:
            conn.execute(self.INSERT_QUERY, acc_data)
            return acc_data

    def get_account_by_id(self, account_id: str) -> sqlite3.Row:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
            record = cur.fetchone()
            return record

    def get_account_by_name_and_currency(self, acc_name: str, acc_currency: str) -> sqlite3.Row:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM accounts WHERE account_name = ? AND account_currency = ?",
                (
                    acc_name,
                    acc_currency,
                ),
            )
            record = cur.fetchone()
            return record

    def get_accounts_lists(self, **kwargs: int | str | tuple[str, ...]) -> list[sqlite3.Row]:
        """tags are case-insensitive"""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            select_query = "SELECT * FROM accounts"

            query_conditions = []
            query_parameters = []

            if kwargs:
                if "is_active" in kwargs and kwargs["is_active"] is not None:
                    query_conditions.append("is_active = ?")
                    query_parameters.append(kwargs["is_active"])  # type: ignore[arg-type]
                if "currency" in kwargs and kwargs["currency"] is not None:
                    query_conditions.append("account_currency = ?")
                    query_parameters.append(kwargs["currency"])  # type: ignore[arg-type]
                if "tags" in kwargs and kwargs["tags"] is not None:
                    tags = kwargs["tags"]
                    tag_conditions = " OR ".join(["tags LIKE ?"] * len(tags))  # type: ignore[arg-type, union-attr]
                    query_conditions.append(f"({tag_conditions})")
                    query_parameters.extend([f"%{tag}%" for tag in tags])  # type: ignore[arg-type]
                if query_conditions:
                    select_query += " WHERE " + " AND ".join(query_conditions)

            cur = conn.cursor()
            cur.execute(select_query, query_parameters)

            records = cur.fetchall()
            return records

    def update_account(self, account: Accounts) -> None:
        acc_data = account.to_dict()
        with self._connect() as conn:
            conn.execute(self.UPDATE_QUERY, acc_data)

    def delete_account(self, account_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM accounts WHERE account_id = ?", (account_id,))
