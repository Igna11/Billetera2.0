"""
billeterapp 2.0 - v2.0 Marzo 2026
"""

import os
import sqlite3
from typing import Optional, List, Any, Callable

from src import DATAPATH
from src.models.usersmodel import Users
from src.dbhandlers.dbutils import DatabaseConnection


class UsersDB:
    def __init__(self, db_path: Optional[str] = None) -> None:
        path = os.path.join(DATAPATH, "database.db")
        self.db_path: str = db_path or os.getenv("DATABASE_NAME", path) or path
        self.db = DatabaseConnection(self.db_path, enforce_foreign_keys=False)

    def _connect(self, row_factory: Optional[Callable] = sqlite3.Row) -> sqlite3.Connection:
        return self.db.connect(row_factory=row_factory)

    def create_user(self, user: Users, hashed_password: str) -> dict[str, Any]:
        data = user.to_dict()
        data.update({"password": hashed_password})
        with self._connect(row_factory=None) as conn:
            conn.execute(
                """
                INSERT INTO users
                  (user_id, first_name, last_name, birthdate,
                   gender, region, email, password, created_at, updated_at)
                VALUES
                  (:user_id, :first_name, :last_name, :birthdate,
                   :gender, :region, :email, :password, :created_at, :updated_at)
                """,
                data,
            )
            return user.to_dict()

    def get_user_by_id(self, user_id: str) -> sqlite3.Row:
        with self._connect(row_factory=sqlite3.Row) as conn:
            cur = conn.execute(
                """
                SELECT
                  user_id, first_name, last_name, birthdate,
                  gender, region, email, created_at, updated_at
                FROM
                  users
                WHERE
                  user_id = ?
                """,
                (user_id,),
            )
            record = cur.fetchone()
            return record

    def get_user_by_email(self, user_email: str) -> sqlite3.Row:
        with self._connect(row_factory=sqlite3.Row) as conn:
            cur = conn.execute(
                """
                SELECT
                  user_id, first_name, last_name, birthdate,
                  gender, region, email, created_at, updated_at
                FROM
                  users
                WHERE
                  email = ?
                """,
                (user_email,),
            )

            record = cur.fetchone()
            return record

    def get_user_with_password(self, email: str) -> sqlite3.Row:
        with self._connect(row_factory=sqlite3.Row) as conn:
            cur = conn.execute(
                """
                SELECT *
                FROM
                  users
                WHERE
                  email = ?
                """,
                (email,),
            )

            record = cur.fetchone()
            return record

    def get_all_users(self) -> List[sqlite3.Row]:
        with self._connect(row_factory=sqlite3.Row) as conn:
            cur = conn.execute(
                """
                SELECT
                  user_id, first_name, last_name, birthdate,
                  gender, region, email, created_at, updated_at
                FROM
                  users
                """
            )

            records = cur.fetchall()
            return records

    def update_user(self, user: Users) -> None:
        data = user.to_dict()
        with self._connect(row_factory=None) as conn:
            conn.execute(
                """
                UPDATE
                  users
                SET
                  first_name = :first_name, last_name = :last_name, birthdate = :birthdate,
                  gender = :gender, region = :region, email = :email, updated_at = :updated_at
                WHERE
                  user_id = :user_id
                """,
                data,
            )

    def delete_user(self, user_id: str) -> None:
        with self._connect(row_factory=None) as conn:
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
