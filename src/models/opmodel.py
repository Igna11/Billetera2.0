"""
billeterapp 2.0 - Junio 2024

This module handles the model of accounts.

Creation of one dedicated directory and database for every user created and
their corresponding accounts table and a new table for each user account.

This module is intended to be used by the module commands and not directly.
"""

import os
import re
import sqlite3
from datetime import datetime, date, UTC
from decimal import Decimal
from string import Template
from typing import Optional, Literal, List, Sequence

from ulid import ULID
from pydantic import BaseModel, Field, field_validator
from pydantic_extra_types.currency_code import ISO4217

# custom sqlite3 adapter for date and datetime
sqlite3.register_adapter(date, lambda val: val.isoformat())
sqlite3.register_adapter(datetime, lambda val: val.isoformat())

INSERT_INTO_QUERY = Template(
    """
    INSERT INTO 
      $table_name
      (operation_id,
      operation_datetime,
      cumulative_amount,
      amount,
      operation_type,
      category,
      subcategory,
      description,
      tags,
      group_id,
      detail_id,
      created_at,
      updated_at)
    VALUES
      (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
)
UPDATE_OPERATIONS_QUERY = Template(
    """
    UPDATE
      $table_name
    SET
      operation_datetime = ?,
      cumulative_amount = ?,
      amount = ?,
      operation_type = ?,
      category = ?,
      subcategory = ?,
      description = ?,
      tags = ?,
      group_id = ?,
      detail_id = ?,
      updated_at = ?
    WHERE
      operation_id = ?
    """
)
UPDATE_ACC_TOTAL_QUERY = """
    UPDATE
      accounts
    SET
      account_total = ?,
      updated_at = ?
    WHERE
      account_id = ?
    """


class OperationNotFoundError(Exception):
    pass


class InvalidAccountNameError(Exception):
    pass


class OperationsModel(BaseModel, validate_assignment=True):
    """
    OperationsModel: Abstract class to handle the lower level operations of each account that an user can have.

    Args:
        user_id (str): The unique identifier for the user.
        account_id (str): The unique identifier for the account.
        operation_id (str): The unique identifier for the operation.
        account_name (str, optional): Name of the account.
        account_total (float, optional): Total amount of funds in the account.
        operation_datetime (datetime, optional): Date and time of a given operation. If not provided uses now.
        amount (float): Amount of the operation.
        operation_type (str): Type of the operation (income, expense, transfer).
        category (str, optional): Category name of the operation.
        subcategory (str, optional): Subcategory name of the operation.
        description (str, optional): Description of the operation.
        tags (str, optional): Tags of the operation to be used for filtering.
        group_id (str, optional): The unique identifier of an entry in the operation_groups table.
        details_id (str, optional): The unique identifier of an entry in the operation_details table.
        created_at (datetime, optional): UTC datetime. Optional because it should not be user provided.
        updated_at (datetime, optional): UTC datetime. Optional because it should not be user provided.
    """

    user_id: Optional[str] = None
    account_id: Optional[str] = None
    operation_id: str = Field(default_factory=lambda: "op_" + str(ULID()))
    account_name: Optional[str] = None
    account_total: Optional[Decimal] = None
    operation_datetime: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))
    cumulative_amount: Optional[Decimal] = Field(ge=0, default=None)
    amount: Decimal = Field(gt=0)
    operation_type: Literal["income", "expense", "transfer_in", "transfer_out"]
    operation_currency: Optional[ISO4217] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    group_id: Optional[str] = None
    detail_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def __db_path(user_id) -> str:
        """Stablished the path for the accounts_database.db"""
        return os.path.join("data", user_id, "accounts_database.db")

    @field_validator("account_name")
    @classmethod
    def __name_validator(cls, acc_name) -> str | None:
        """
        Validates names of the account or the table if they have only alphanumeric chars and underscores for
        security reasons.

        Args:
            acc_name (str): Name of the account.

        Returns:
            str: Name of the account.
        """
        if acc_name is None:
            return acc_name
        if not re.match(r"^[a-zA-Z0-9_]*$", acc_name):
            raise InvalidAccountNameError
        return acc_name


class UserOperations(OperationsModel):
    """
    UserOperations model: Handle the lower level operations of each account that an user can have.

    Args:
        Inherited from OperationModel.
    """

    @classmethod
    def get_operation_by_id(cls, user_id: str, account_id: str, operation_id: str) -> "UserOperations":
        """
        Fetches operation info from db and returns an UserOperation object that matches the id provided.

        Args:
            user_id (str): The unique identifier for the user.
            account_id (str): The uique identifier for the account.
            operation_id (str): The unique identifier for the operation.
        Returns:
            UserOperation: An UserOperation object with that operation data.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (account_id,))
        table_name = cur.fetchone()[0]
        cur.execute(f"SELECT * FROM {table_name} WHERE operation_id = ?", (operation_id,))

        record = cur.fetchone()
        conn.close()

        if not record:
            raise OperationNotFoundError

        record = dict(record)
        record["user_id"] = user_id
        record["account_id"] = account_id

        operation = cls(**record)

        return operation

    @classmethod
    def get_last_chronological_operation(cls, user_id: str, account_id: str) -> "UserOperations":
        """
        Fetches operation info from db and returns an UserOperation object that has the latest datetime.

        Args:
            user_id (str): The unique identifier for the user.
            account_id (str): The unique identifier for the account.

        Returns:
            UserOperation: An UserOperation object with the last operation datetime.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (account_id,))
        table_name = cur.fetchone()[0]
        cur.execute(f"SELECT * FROM {table_name} ORDER BY operation_datetime DESC LIMIT 1;")

        record = cur.fetchone()
        conn.close()

        if not record:
            raise OperationNotFoundError

        record = dict(record)
        record["user_id"] = user_id
        record["account_id"] = account_id

        operation = cls(**record)

        return operation

    @classmethod
    def get_operations_list(
        cls, user_id: str, account_id: str, order_by_datetime: str | None = None
    ) -> List["UserOperations"]:
        """
        Fetches all operations from db and returns a list of UserOperation objects.

        Args:
            user_id (str): The unique identifier for the user
            account_id (str): The unique identifier for the account
        Returns:
            list[UserOperation]: A list of UserOperation objects for a given account.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (account_id,))
        table_name = cur.fetchone()[0]

        select_op_query = f"SELECT * FROM {table_name}"
        if order_by_datetime == "ASC":
            select_op_query += " ORDER BY operation_datetime ASC;"
        elif order_by_datetime == "DESC":
            select_op_query += " ORDER BY operation_datetime DESC"

        cur.execute(select_op_query)

        records = cur.fetchall()
        conn.close()

        records = [dict(record, user_id=user_id, account_id=account_id) for record in records]

        operations = [cls(**record) for record in records]

        return operations

    @classmethod
    def get_operations_list_by_tags(cls, user_id: str, account_id: str, tags: Sequence) -> List["UserOperations"]:
        """
        Fetches all operations from db that contains certain tags and returns a list of UserOperation objects.

        Args:
            user_id (str): The unique identifier for the user
            account_id (str): The unique identifier for the account
            tags (tuple): A tuple of tags
        Returns:
            list[UserOperation]: A list of UserOperation objects for a given account with given tags.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (account_id,))
        table_name = cur.fetchone()[0]

        like_clause = f"SELECT * FROM {table_name} WHERE tags LIKE ? " + "OR tags LIKE ? " * (len(tags) - 1)
        tup_tags = tuple(f"%{tag}%" for tag in tags)
        cur.execute(like_clause, tup_tags)

        records = cur.fetchall()
        conn.close()

        operations = [cls(**record) for record in records]

        return operations

    @classmethod
    def get_operations_list_from_datetime(
        cls, user_id: str, account_id: str, operation_datetime: datetime
    ) -> List["UserOperations"]:
        """
        Fetches all operations from db with datetime after the input datetime and the first operation before, sorted
        by date (from older dates to newer dates).
        If the operation_datetime provided is identical to other operation datetime, that operation will be the first.
        If the operation_datetime provided is identical to several operations datetime, all those operations will be
        ignored but the last one, which will be the first on the returned list.

        Args:
            user_id (str): The unique identifier for the user
            account_id (str): The unique identifier for the account
            operation_datetime (datetime): the datetime to use as filter
        Returns:
            list[UserOperations]: A list of sorted UserOperation objects for a given account with given datetimes.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (account_id,))
        table_name = cur.fetchone()[0]

        cur.execute(
            f"""
            WITH previus_row AS (
              SELECT *
              FROM {table_name}
              WHERE operation_datetime <= ?
              ORDER BY operation_datetime DESC, created_at DESC
              LIMIT 1
            )
            SELECT *
            FROM {table_name}
            WHERE operation_datetime > ?
            UNION ALL
            SELECT *
            FROM previus_row
            ORDER BY operation_datetime ASC;
            """,
            (operation_datetime, operation_datetime),
        )

        records = cur.fetchall()
        conn.close()

        operations = [cls(**record) for record in records]

        return operations

    @classmethod
    def get_operations_list_from_id(cls, user_id: str, account_id: str, operation_id: str) -> List["UserOperations"]:
        """
        Fetches all operations from db with a datetime after the datetime of the operation with given id, and the first
        operation before, sorted by date (from older dates to newer dates).

        Args:
            user_id (str): The unique identifier for the user
            account_id (str): The unique identifier for the account
            operation_id (str): The unique identifier for the operation
        Returns:
            list[UserOperations]: A list of sorted UserOperation objects for a given account with given datetimes.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))
        conn.row_factory = sqlite3.Row

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (account_id,))
        table_name = cur.fetchone()[0]
        cur.execute(
            f"""
            WITH row_number_table AS (
              SELECT *, row_number()
              over (ORDER BY operation_datetime, created_at ASC)
              AS row_number
              FROM {table_name}
              WHERE operation_datetime <= (
                SELECT operation_datetime
                FROM {table_name}
                WHERE operation_id = ?
                )
            )
            SELECT operation_id,
              operation_datetime,
              cumulative_amount,
              amount,
              operation_type,
              category,
              subcategory,
              description,
              tags,
              group_id,
              detail_id,
              created_at,
              updated_at
            FROM row_number_table
            WHERE row_number = (
              SELECT row_number-1
              FROM row_number_table
              WHERE operation_id=?
            )
            UNION
            SELECT * FROM {table_name}
            WHERE operation_id = ?
            UNION
            SELECT * FROM {table_name}
            WHERE operation_datetime >= (
              SELECT operation_datetime FROM {table_name}
              WHERE operation_id = ?
            )
            ORDER BY operation_datetime, created_at;
            """,
            (
                operation_id,
                operation_id,
                operation_id,
                operation_id,
            ),
        )

        records = cur.fetchall()
        conn.close()

        operations = [cls(**record) for record in records]

        return operations

    @classmethod
    def get_unique_categories(cls, user_id: str) -> List[str]:
        """
        Retrieves all the different categories exiting in all accounts:

        Args:
            user_id (str): The unique identifier for the user
        Returns:
            list[str]: A list of strings (categories)
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts;")
        table_name_list = [table_name[0] for table_name in cur.fetchall()]
        categories = []
        for table_name in table_name_list:
            cur.execute(f"SELECT DISTINCT category FROM {table_name};")
            categories.extend(cur.fetchall())
        conn.close()

        categories = list(set(categories))
        return categories

    @classmethod
    def get_unique_subcategories(cls, user_id: str, category: str = None) -> List[str]:
        """
        Retrieves all the different subcategories exiting in all accounts

        Args:
            user_id (str): The unique identifier for the user
            category (str): main category to only retrieve unique values for a given category
        Returns:
            list[str]: A list of strings (subcategories)
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(user_id)))

        cur = conn.cursor()
        cur.execute("SELECT table_name FROM accounts;")
        table_name_list = [table_name[0] for table_name in cur.fetchall()]
        subcategories = []
        if category:
            for table_name in table_name_list:
                cur.execute(f"SELECT DISTINCT subcategory FROM {table_name} WHERE category = ?", (category,))
                subcategories.extend(cur.fetchall())
        else:
            for table_name in table_name_list:
                cur.execute(f"SELECT DISTINCT subcategory FROM {table_name};")
                subcategories.extend(cur.fetchall())
        conn.close()

        subcategories = list(set(subcategories))

        return subcategories

    def create(self) -> "UserOperations":
        """
        creates a new operation entry in the database in the given table (account).

        args:
            self (useroperations): an useroperations object.
        returns:
            self (useroperations): an useroperations object.
        """
        self.created_at = self.updated_at = datetime.now(UTC)

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(self.user_id)))
        cur = conn.cursor()
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (self.account_id,))
            table_name = cur.fetchone()[0]
            cur.execute(
                INSERT_INTO_QUERY.substitute(table_name=table_name),
                (
                    self.operation_id,
                    self.operation_datetime,
                    self.cumulative_amount,
                    self.amount,
                    self.operation_type,
                    self.category,
                    self.subcategory,
                    self.description,
                    self.tags,
                    self.group_id,
                    self.detail_id,
                    self.created_at,
                    self.updated_at,
                ),
            )
            # if self.account_total: doesn't work well with account_total=0, since 0==False but (not None==0)==True
            if self.account_total is not None:
                cur.execute(
                    UPDATE_ACC_TOTAL_QUERY,
                    (
                        self.account_total,
                        self.updated_at,
                        self.account_id,
                    ),
                )
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
        finally:
            conn.close()
        return self

    def save(self) -> "UserOperations":
        """
        Saves modifications to operation entry data in the database. Uses operation_id for matching.

        Args:
            self (UserOperations): An UserOperations object.
        Returns:
            self (UserOperations): An UserOperations object.
        """
        self.updated_at = datetime.now(UTC)

        with sqlite3.connect(
            (os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(self.user_id)))
        ) as conn:
            cur = conn.cursor()
            cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (self.account_id,))

            table_name = cur.fetchone()[0]

            cur.execute(
                UPDATE_OPERATIONS_QUERY.substitute(table_name=table_name),
                (
                    self.operation_datetime,
                    self.cumulative_amount,
                    self.amount,
                    self.operation_type,
                    self.category,
                    self.subcategory,
                    self.description,
                    self.tags,
                    self.group_id,
                    self.detail_id,
                    self.updated_at,
                    self.operation_id,
                ),
            )
            if self.account_total is not None:
                cur.execute(
                    UPDATE_ACC_TOTAL_QUERY,
                    (
                        self.account_total,
                        self.updated_at,
                        self.account_id,
                    ),
                )
            conn.commit()

        conn.close()
        return self

    def massive_save(self, operations_list: list, edit_flag: bool = False) -> None:
        """
        Edits several operations in the database in the given table (account).

        args:
            self (useroperations): an useroperations object.
            operations_list (list): list of OperationModel objects with the information to update the database.
            edit_flag (bool): True if there is a self edition involved.
        returns:
            self (useroperations): an useroperations object.
        """
        self.created_at = self.updated_at = datetime.now(UTC)

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(self.user_id)))
        cur = conn.cursor()
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (self.account_id,))
            table_name = cur.fetchone()[0]
            for oper in operations_list:
                cur.execute(
                    UPDATE_OPERATIONS_QUERY.substitute(table_name=table_name),
                    (
                        oper.operation_datetime,
                        oper.cumulative_amount,
                        oper.amount,
                        oper.operation_type,
                        oper.category,
                        oper.subcategory,
                        oper.description,
                        oper.tags,
                        oper.group_id,
                        oper.detail_id,
                        self.updated_at,
                        oper.operation_id,
                    ),
                )
            if not edit_flag:
                cur.execute(
                    INSERT_INTO_QUERY.substitute(table_name=table_name),
                    (
                        self.operation_id,
                        self.operation_datetime,
                        self.cumulative_amount,
                        self.amount,
                        self.operation_type,
                        self.category,
                        self.subcategory,
                        self.description,
                        self.tags,
                        self.group_id,
                        self.detail_id,
                        self.created_at,
                        self.updated_at,
                    ),
                )
            if self.account_total is not None:
                cur.execute(
                    UPDATE_ACC_TOTAL_QUERY,
                    (
                        self.account_total,
                        self.updated_at,
                        self.account_id,
                    ),
                )
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            raise sqlite3.Error
        finally:
            conn.close()
        return self

    def delete_n_massive_save(self, operations_list: list) -> None:
        """
        Deletes the self operation and edits all operations affected by the deletion in a give table.

        args:
            self (useroperations): an useroperations object.
            operations_list (list): list of OperationModel objects with the information to update the database.
        returns:
            self (useroperations): an useroperations object.
        """
        self.updated_at = datetime.now(UTC)

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(self.user_id)))
        cur = conn.cursor()
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (self.account_id,))
            table_name = cur.fetchone()[0]
            for oper in operations_list:
                cur.execute(
                    f"""
                    UPDATE
                      {table_name}
                    SET
                      cumulative_amount = ?,
                      updated_at = ?
                    WHERE operation_id = ?
                    """,
                    (
                        oper.cumulative_amount,
                        self.updated_at,
                        oper.operation_id,
                    ),
                )

            # Delete de operation
            cur.execute(f"DELETE FROM {table_name} WHERE operation_id = ?", (self.operation_id,))
            # Update the account total
            if self.account_total is not None:
                cur.execute(
                    UPDATE_ACC_TOTAL_QUERY,
                    (
                        self.account_total,
                        self.updated_at,
                        self.account_id,
                    ),
                )
            conn.commit()
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
        finally:
            conn.close()
        return self

    def delete(self) -> None:
        """
        Deletes operation entry data in the database. Uses operation_id for matching.

        Args:
            self (UserOperations): An UserOperations object.
        """
        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", UserOperations._OperationsModel__db_path(self.user_id)))
        cur = conn.cursor()
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("SELECT table_name FROM accounts WHERE account_id = ?", (self.account_id,))
            table_name = cur.fetchone()[0]

            cur.execute(f"DELETE FROM {table_name} WHERE operation_id = ?", (self.operation_id,))
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
        finally:
            conn.close()
