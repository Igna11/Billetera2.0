"""
billeterapp 2.0 - Junio 2025

This module handles the data stored in the operation tables.
"""

import os
import sqlite3
from typing import List, Dict
from string import Template
from decimal import Decimal
from datetime import datetime, UTC
from collections import defaultdict

from src.models.accmodel import UserAccounts
from src.models.opmodel import UserOperations


SELECT_QUERY = Template(
    """
    SELECT  
      operation_id,
      operation_datetime,
      amount,
      operation_type,
      category,
      subcategory,
      description,
      tags
    FROM
      $table_name
    WHERE 
      operation_datetime >= ?
    AND
      operation_datetime <= ?
    AND
      operation_type = ?
    """
)

TOTAL_QUERY = Template(
    """
    SELECT
      SUM(amount)
    FROM
      $table_name
    WHERE
      operation_datetime >= ?
    AND
      operation_datetime <= ?
    AND
      operation_type = ?
    """
)


class AccountDataAnalyzer(UserAccounts):

    @classmethod
    def get_user_totals(cls, user_id: str, **kwargs: int | str) -> Decimal:
        """User totals of all accounts"""
        accounts_list = UserAccounts.get_all_accounts(user_id=user_id, **kwargs)
        total = Decimal(0)
        for account in accounts_list:
            try:
                total += account.account_total
            except TypeError as e:
                print(e)  # debugging and develop purposes
                total += 0
        return total

    @classmethod
    def get_user_totals_by_period(
        cls, user_id: str, from_datetime: datetime, to_datetime: datetime, operation_type: str, **kwargs: int | str
    ) -> Decimal:
        accounts_list = UserAccounts.get_all_accounts(user_id=user_id, **kwargs)

        db_path = os.path.join("data", user_id, "accounts_database.db")

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        total = Decimal(0)

        for account in accounts_list:
            try:
                table_name = f"{account.account_name}_{account.account_currency}"
                cur.execute(
                    TOTAL_QUERY.substitute(table_name=table_name),
                    (
                        from_datetime,
                        to_datetime,
                        operation_type,
                    ),
                )
                parcial = cur.fetchone()["SUM(amount)"]
                if parcial:
                    total += Decimal(parcial)

            except sqlite3.OperationalError as e:
                print(e)  # debugging and develop purposes

        return total

    @classmethod
    def group_operations(
        cls,
        user_id: str,
        from_datetime: datetime,
        to_datetime: datetime,
        operation_type: str,
        data_type: str,
        **kwargs: int | str,
    ) -> List[Dict]:
        """Gathers all operations for all active accounts with the same currency in a given period of time"""
        accounts_list = UserAccounts.get_all_accounts(user_id=user_id, **kwargs)
        all_operations = []

        db_path = os.path.join("data", user_id, "accounts_database.db")

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        for account in accounts_list:
            try:
                table_name = f"{account.account_name}_{account.account_currency}"
                cur.execute(
                    SELECT_QUERY.substitute(table_name=table_name),
                    (
                        from_datetime,
                        to_datetime,
                        operation_type,
                    ),
                )
                operations = cur.fetchall()
                all_operations.extend(operations)
            except sqlite3.OperationalError as e:
                print(e)  # debugging and develop purposes

        operation_objects = []
        for operation in all_operations:
            operation_objects.append(UserOperations(**operation))

        # operation_objects.sort(key=lambda operation_objects: operation_objects.operation_datetime)
        # Grouping
        if data_type == "category":
            category_group = defaultdict(Decimal)
            for operation in operation_objects:
                if operation.amount is None:
                    raise ValueError
                # category = operation.category if operation.category is not None else "-"
                # category_group[category] += operation.amount
                category_group[operation.category] += operation.amount
            category_data = [
                {"category": cat, "total": Decimal(total)} for cat, total in sorted(category_group.items())
            ]
            return category_data

        elif data_type == "subcategory":
            subcategory_group = defaultdict(Decimal)
            for operation in operation_objects:
                if operation.amount is None:
                    raise ValueError
                key = (operation.category, operation.subcategory)
                subcategory_group[key] += operation.amount
            subcategory_data = [
                {"category": category, "subcategory": subcategory, "total": Decimal(total)}
                for (category, subcategory), total in sorted(subcategory_group.items())
            ]
            return subcategory_data


class OperationDataAnalizer(UserOperations):
    pass
