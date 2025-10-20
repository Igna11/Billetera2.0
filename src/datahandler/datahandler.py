"""
billeterapp 2.0 - Junio 2025                                                                                        120

This module handles the data stored in the operation tables.
"""

import os
import sqlite3
from typing import List, Dict
from string import Template
from decimal import Decimal
from datetime import datetime
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
        """Calculates the User total of all accounts for every currency if specify in kwargs."""
        accounts_list = UserAccounts.get_all_accounts(user_id=user_id, **kwargs)
        total = Decimal(0)
        for account in accounts_list:
            try:
                total += account.account_total
            except TypeError as e:
                print(f"Error captured during execution: {e}")  # debugging and developing purposes
                total += 0
        return total

    @classmethod
    def get_user_totals_by_period(
        cls, user_id: str, from_datetime: datetime, to_datetime: datetime, operation_type: str, **kwargs: int | str
    ) -> Decimal:
        """
        Calculates the User income/expense total of all accounts for a given period of time for a given currency
        Args:
            user_id (str): The unique identifier for the user
            from_datetime (datetime): initial datetime
            to_datetime (datetime): final datetime
            operation_type (str): 'income'/'expense'
            **kwargs (int | str): 'is_active', 'currency'
        Returns:
            total (Decimal): The total value
        """
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
    def categorize_flow_operations(
        cls,
        user_id: str,
        from_datetime: datetime,
        to_datetime: datetime,
        operation_type: str,
        data_type: str,
        **kwargs: int | str,
    ) -> List[Dict]:
        """
        Gathers all operations for all active accounts with the same currency in a given period of time
        and groups them by category or by category and subcategory adding their amounts.
        This method does not discriminate for group of operations.
        Args:
            user_id (str): The unique identifier for the user
            from_datetime (datetime): initial datetime
            to_datetime (datetime): final datetime
            operation_type (str): 'income'/'expense'
            data_type (str): 'category'/'subcategory'
            **kwargs (int | str): 'is_active', 'currency'
        Returns:
             category_data (List[Dict]): e.g.: [{'category': <category_name>, 'total': total}, ...]
             subcategory_data (List[Dict]):
                e.g.: [{'category': <category_name>, 'subcategory': <subcat_name>, 'total': total}, ...]
        """
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

    @classmethod
    def categorize_net_operations(
        cls,
        user_id: str,
        from_datetime: datetime,
        to_datetime: datetime,
        operation_type: str,
        data_type: str,
        **kwargs: int | str,
    ) -> List[Dict]:
        """
        Gathers all operations for all active accounts with the same currency in a given period of time
        and groups them by category or by category and subcategory adding their amounts.
        This method does discriminate for group of operations: operations belonging to any group will be grouped and
        all their values will be summed in order to determine if its total is an net income or a net expense.
        Args:
            user_id (str): The unique identifier for the user
            from_datetime (datetime): initial datetime
            to_datetime (datetime): final datetime
            operation_type (str): 'income'/'expense'
            data_type (str): 'category'/'subcategory'
            **kwargs (int | str): 'is_active', 'currency'
        Returns:
             category_data (List[Dict]): e.g.: [{'category': <category_name>, 'total': total}, ...]
             subcategory_data (List[Dict]):
                e.g.: [{'category': <category_name>, 'subcategory': <subcat_name>, 'total': total}, ...]
        """

        accounts_list = UserAccounts.get_all_accounts(user_id=user_id, **kwargs)

        db_path = os.path.join("data", user_id, "accounts_database.db")

        conn = sqlite3.connect(os.getenv("ACC_DATABASE_NAME", db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # A query for listing all existing groups created inside the time window
        cur.execute("SELECT * FROM operation_groups WHERE created_at BETWEEN ? AND ?", (from_datetime, to_datetime))
        groups_list = [dict(group)["group_id"] for group in cur.fetchall()]

        # Generate a query for every account table in the time window
        operation_select_for_all_accounts = Template(
            "SELECT * FROM $acc_table WHERE operation_datetime BETWEEN '$from_dttime' AND '$to_dttime'"
        )

        operations_selects_list = []
        for account in accounts_list:
            table_name = f"{account.account_name}_{account.account_currency}"
            operations_selects_list.append(
                operation_select_for_all_accounts.substitute(
                    acc_table=table_name, from_dttime=from_datetime, to_dttime=to_datetime
                )
            )

        # join all queries for every table with a UNION ALL
        operation_select_union = " UNION ALL ".join(operations_selects_list)

        # Generate the part of the query that takes care of filtering by group id
        group_ids = ", ".join([f"'{gid}'" for gid in groups_list])

        grouped_operations_query = (
            f"SELECT * FROM ({operation_select_union}) AS all_operations WHERE group_id IN ({group_ids})"
        )
        # Another part of the query that takes care of fetching all operations that don't have groups
        ungrouped_operations_query = f"""
            SELECT
              amount,
              operation_type,
              category,
              subcategory,
              description,
              group_id
            FROM 
              ({operation_select_union})
            WHERE 
              group_id IS NULL"""

        # For the query of grouped operations, their amounts are added
        sum_query = f"""
            SELECT
            ABS(
              SUM(
              CASE
                  WHEN operation_type = 'income' THEN amount
                  WHEN operation_type = 'expense' THEN - amount
                  ELSE 0
              END
              )
            ) AS amount,
            CASE
              WHEN SUM(
              CASE
                  WHEN operation_type = 'income' THEN amount
                  WHEN operation_type = 'expense' THEN - amount
                  ELSE 0
              END
              ) >= 0 THEN 'income'
              ELSE 'expense'
            END AS operation_type,
            category,
            subcategory,
            group_id
            FROM
            ({grouped_operations_query})
            GROUP BY group_id
        """
        join_query = f"""
            SELECT 
              sum_table.amount,
              sum_table.operation_type,
              op_gp.category,
              op_gp.subcategory,
              op_gp.description,
              op_gp.group_id
            FROM
              operation_groups as op_gp
            LEFT JOIN
              ({sum_query}) as sum_table
            ON op_gp.group_id = sum_table.group_id
            """

        category_query = f"""
            SELECT 
              category,
              SUM(amount) AS total
            FROM 
              ({join_query}
            UNION ALL 
              {ungrouped_operations_query})
            WHERE 
              operation_type = '{operation_type}'
            GROUP BY category;"""

        subcategory_query = f"""
            SELECT
              category,
              subcategory,
              SUM(amount) AS total
            FROM 
              ({join_query}
            UNION ALL
              {ungrouped_operations_query})
            WHERE
              operation_type = '{operation_type}'
            GROUP BY category, subcategory;"""

        if data_type == "category":
            cur.execute(category_query)
            data = cur.fetchall()
            return list(map(dict, data))
        elif data_type == "subcategory":
            cur.execute(subcategory_query)
            data = cur.fetchall()
            return list(map(dict, data))


class OperationDataAnalizer(UserOperations):
    pass
