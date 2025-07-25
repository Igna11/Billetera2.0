"""
billeterapp 2.0 - Junio 2024

This module handles the model of accounts.
Creation of one dedicated directory and database for every user created and
their corresponding accounts table and a new table for each user account.

This module is intended to be used by the module commands and not directly.
"""

import os
import sqlite3
import datetime
from typing import Optional, List

from pydantic import BaseModel

# custom sqlite3 adapter for date and datetime
sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())
sqlite3.register_adapter(datetime.datetime, lambda val: val.isoformat())


class OperationDetailsNotFoundError(Exception):
    pass


class OperationsDetails(BaseModel, validate_assignment=True):

    user_id: Optional[str] = None
    account_id: Optional[str] = None
    operation_id: Optional[str] = None
    account_name: Optional[str] = None
    details: Optional[bytes] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    @classmethod
    def get_details_by_operation_id(cls, user_id: str, operation_id: str) -> "OperationsDetails":
        """
        Fetches operation details info from db and returns an OperationDetails object that matches the id provided.

        Args:
            user_id (str): The unique identifier for the user generated by the library ULID.
            operation_id (str): The unique identifier for the operation generated by the library ULID.
        Returns:
            OperationDetails: An OperationDetails object with that operation data.
        """
        db_path = os.path.join("data", user_id, "accounts_database.db")

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT * FROM operation_details WHERE operation_id = ?", (operation_id,))

        record = cur.fetchone()
        conn.close()

        if not record:
            raise OperationDetailsNotFoundError

        record = dict(record)
        record["user_id"] = user_id

        details = cls(**record)

        return details

    @classmethod
    def get_all_operation_details_by_account_id(cls, user_id: str, account_id: str) -> List["OperationsDetails"]:
        """
        Fetches all operation details of one account from db and returns a list of OperationDetails objects.

        Returns:
            List[OperationDetails]: A list of OperationDetails objects.
        """
        db_path = os.path.join("data", user_id, "accounts_database.db")
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT * FROM operation_details WHERE account_id = ?", (account_id,))

        records = cur.fetchall()
        conn.close()

        details = [cls(**record) for record in records]

        return details

    def create(self, database_name="accounts_database.db") -> "OperationsDetails":
        """
        Creates the details of an operation in the database as a binary (BLOB).

        Args:
            self (OperationDetails): An OperationDetails object.
        Returns:
            self (OperationDetails): An OperationDetails object.
        """
        db_path = os.path.join("data", self.user_id, database_name)

        self.created_at = self.updated_at = datetime.datetime.now(datetime.UTC)

        with sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path)) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO operation_details
                  (operation_id, account_id, details, created_at, updated_at)
                VALUES
                  (?, ?, ?, ?, ?)
                """,
                (
                    self.operation_id,
                    self.account_id,
                    self.details,
                    self.created_at,
                    self.updated_at,
                ),
            )
            conn.commit()
        conn.close()
        return self

    def save(self) -> "OperationsDetails":
        """
        Saves changes into the details of an operation in the database as a binary (BLOB).

        Args:
            self (OperationDetails): An OperationDetails object.
        Returns:
            self (OperationDetails): An OperationDetails object.
        """
        db_path = os.path.join("data", self.user_id, "accounts_database.db")

        self.updated_at = datetime.datetime.now(datetime.UTC)

        with sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path)) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE operation_details
                  SET details = ?, updated_at = ?
                WHERE operation_id = ?
                """,
                (self.details, self.updated_at, self.operation_id),
            )
            conn.commit()
        conn.close()
        return self

    def delete(self) -> None:
        """
        Deletes operation details from db using the operation_id for matching.

        Args:
            self (OperationDetails): The unique identifier for the user generated by the library ULID.
        """
        db_path = os.path.join("data", self.user_id, "accounts_database.db")

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path))
        cur = conn.cursor()

        cur.execute("DELETE FROM operation_details WHERE operation_id = ?", (self.operation_id,))
        conn.commit()
        conn.close()

    @classmethod
    def create_operation_details_table(cls, user_id: str, database_name: str = "accounts_database.db") -> None:
        """
        Creates the operation_details table where extra information about operations will be stored, such as pictures
        or pdfs in their binary form
        Args:
            user_id (str): Unique identifier of the user
            database_name (str, optional): The name of the database, default to 'accounts_database.db'
        """
        acc_table_query = """
            CREATE TABLE IF NOT EXISTS operation_details (
              operation_id TEXT NOT NULL,
              account_id TEXT NOT NULL,
              details BLOB NOT NULL,
              created_at DATETIME,
              updated_at DATETIME
            )"""
        db_path = os.path.join("data", user_id, database_name)

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(acc_table_query)
        conn.commit()
        conn.close()
