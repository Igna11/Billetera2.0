"""
Billeterapp 2.0 - v2.0 Abril 2026
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Any, List, Dict

from src import DATAPATH
from src.models.opmodel import Operations
from src.dbhandlers.dbutils import DatabaseConnection


class OperationsDB:

    INSERT_QUERY = """
        INSERT INTO operations (
          operation_id, account_id, operation_datetime, cumulative_amount, amount, operation_type,
          category, subcategory, description, tags, group_id, detail_id, transfer_id,
          created_at, updated_at
        ) VALUES (
          :operation_id, :account_id, :operation_datetime, :cumulative_amount, :amount, :operation_type,
          :category, :subcategory, :description, :tags, :group_id, :detail_id, :transfer_id,
          :created_at, :updated_at
        )
    """
    UPDATE_QUERY = """
        UPDATE 
          operations
        SET
          account_id = :account_id,
          operation_datetime = :operation_datetime,
          cumulative_amount = :cumulative_amount,
          amount = :amount,
          operation_type = :operation_type,
          category = :category,
          subcategory = :subcategory,
          description = :description,
          tags = :tags,
          group_id = :group_id,
          detail_id = :detail_id,
          transfer_id = :transfer_id,
          updated_at = :updated_at
        WHERE
          operation_id = :operation_id
    """

    def __init__(self, user_id: str, db_path: Optional[str] = None) -> None:
        path = os.path.join(DATAPATH, user_id, "accounts_database.db")
        self.db_path: str = db_path or os.getenv("ACC_DATABASE_NAME", path) or path
        self.db = DatabaseConnection(self.db_path, enforce_foreign_keys=True)

    def _connect(self) -> sqlite3.Connection:
        return self.db.connect(row_factory=sqlite3.Row)

    def create_operation(self, operation: Operations) -> Dict[str, Any]:
        operation_data = operation.to_dict()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(self.INSERT_QUERY, operation_data)
            # Update account total if provided (check for None, not falsy)
            if operation.account_total is not None:
                cur.execute(
                    """
                    UPDATE accounts SET account_total = :account_total, updated_at = :updated_at 
                    WHERE account_id = :account_id
                    """,
                    operation_data,
                )
            return operation_data

    def get_operation_by_id(self, operation_id: str) -> sqlite3.Row:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM operations WHERE operation_id = ?", (operation_id,))
            record = cur.fetchone()
            return record

    def get_all_operations(
        self, account_id: Optional[str] = None, **kwargs: str | tuple[str, ...]
    ) -> List[sqlite3.Row]:
        # Join with accounts table to get currency
        select_query = """
            SELECT 
                o.operation_id, o.account_id, o.operation_datetime, o.cumulative_amount, o.amount, o.operation_type, 
                o.category, o.subcategory, o.description, o.tags, o.group_id, o.detail_id, o.transfer_id,
                o.created_at, o.updated_at,
                a.account_currency AS operation_currency, a.account_name as account_name
            FROM operations o
            LEFT JOIN accounts a ON o.account_id = a.account_id
        """

        query_conditions = []
        query_parameters = []

        if account_id:
            query_conditions.append("o.account_id = ?")
            query_parameters.append(account_id)

        if kwargs:
            if "currency" in kwargs and kwargs["currency"] is not None:
                query_conditions.append("a.account_currency = ?")
                query_parameters.append(kwargs["currency"])  # type: ignore[arg-type]

            if "category" in kwargs and kwargs["category"] is not None:
                query_conditions.append("o.category = ?")
                query_parameters.append(kwargs["category"])  # type: ignore[arg-type]

            if "subcategory" in kwargs and kwargs["subcategory"] is not None:
                query_conditions.append("o.subcategory = ?")
                query_parameters.append(kwargs["subcategory"])  # type: ignore[arg-type]

            if "description" in kwargs and kwargs["description"] is not None:
                descriptions = kwargs["description"]
                desc_condition = " OR ".join(["o.description LIKE ?"] * len(descriptions))
                query_conditions.append(f"({desc_condition})")
                query_parameters.extend([f"%{kword}%" for kword in descriptions])  # type: ignore[arg-type]

            if "group_id" in kwargs and kwargs["group_id"] is not None:
                query_conditions.append("o.group_id = ?")
                query_parameters.append(kwargs["group_id"])  # type: ignore[arg-type]

            if "tags" in kwargs and kwargs["tags"] is not None:
                tags = kwargs["tags"]
                tag_conditions = " OR ".join(["o.tags LIKE ?"] * len(tags))
                query_conditions.append(f"({tag_conditions})")
                query_parameters.extend([f"%{tag}%" for tag in tags])  # type: ignore[arg-type]

            if "operation_type" in kwargs and kwargs["operation_type"] is not None:
                query_conditions.append("o.operation_type = ?")
                query_parameters.append(kwargs["operation_type"])  # type: ignore[arg-type]

            if "from_dt" in kwargs and kwargs["from_dt"] is not None:
                query_conditions.append("o.operation_datetime >= ?")
                query_parameters.append(kwargs["from_dt"])  # type: ignore[arg-type]

            if "to_dt" in kwargs and kwargs["to_dt"] is not None:
                query_conditions.append("o.operation_datetime <= ?")
                query_parameters.append(kwargs["to_dt"])  # type: ignore[arg-type]

            if "is_active" in kwargs and kwargs["is_active"] is not None:
                query_conditions.append("a.is_active = ?")
                query_parameters.append(kwargs["is_active"])  # type: ignore[arg-type]

        if query_conditions:
            select_query += " WHERE " + " AND ".join(query_conditions)

        if kwargs and "order" in kwargs and kwargs["order"]:
            order = kwargs["order"]
            if order in ["ASC", "DESC"]:
                select_query += f" ORDER BY o.operation_datetime {order}, o.operation_id {order}"

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(select_query, query_parameters)
            records = cur.fetchall()
            return records

    def get_transfer_operations_by_id(self, transfer_id: str) -> List[sqlite3.Row]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                    SELECT * FROM operations 
                    WHERE transfer_id = ? 
                    ORDER BY CASE operation_type
                      WHEN 'transfer_in' THEN 1
                      WHEN 'transfer_out' THEN 2
                    END ASC;
                """,
                (transfer_id,),
            )
            records = cur.fetchall()
            return records

    def get_operations_for_net_analysis(
        self,
        from_dt: datetime,
        to_dt: datetime,
        currency: str,
        is_active: Optional[bool] = True,
    ) -> List[sqlite3.Row]:
        """
        Gets operations for net analysis by category in a given time window.

        This method:
        1. Gets all operations where group_id is not null in the time window
        2. Groups by group_id and sums amounts (income adds, expense subtracts)
        3. Determines net operation_type based on final sum (positive=expense, negative=income)
        4. Joins with operation_groups table to get category, subcategory, description
        5. Gets all operations where group_id is null and operation_type is income/expense
        6. Returns both results in a single query

        Args:
            from_dt: Start datetime for the time window
            to_dt: End datetime for the time window
            currency: Currency filter to avoid mixing currencies
            operation_type: Optional filter for 'income' or 'expense'

        Returns:
            List of sqlite3.Row with the net analysis results
        """
        grouped_query = """
            SELECT
              ABS(
                SUM(
                  CASE
                    WHEN o.operation_type = 'income' THEN o.amount
                    WHEN o.operation_type = 'expense' THEN -o.amount
                    ELSE 0
                  END
                )
              ) AS amount,
              CASE
                WHEN SUM(
                  CASE
                    WHEN o.operation_type = 'income' THEN o.amount
                    WHEN o.operation_type = 'expense' THEN -o.amount
                    ELSE 0
                  END
                ) >= 0 THEN 'income'
                ELSE 'expense'
              END AS operation_type,
              g.category,
              g.subcategory,
              g.description,
              a.account_currency
            FROM operations o
            LEFT JOIN operation_groups g ON o.group_id = g.group_id
            LEFT JOIN accounts a ON o.account_id = a.account_id
            WHERE o.operation_datetime >= ? 
              AND o.operation_datetime <= ?
              AND o.group_id IS NOT NULL
              AND a.account_currency = ?
              AND a.is_active = ?
            GROUP BY o.group_id
        """
        ungrouped_query = """
            SELECT
              o.amount,
              o.operation_type,
              o.category,
              o.subcategory,
              o.description,
              a.account_currency
            FROM operations o
            LEFT JOIN accounts a ON o.account_id = a.account_id
            WHERE o.operation_datetime >= ? 
              AND o.operation_datetime <= ?
              AND o.group_id IS NULL
              AND o.operation_type IN ('income', 'expense')
              AND a.account_currency = ? 
              AND a.is_active = ?
        """
        # Combine both queries with UNION ALL
        combined_query = f"""
            {grouped_query}
            UNION ALL
            {ungrouped_query}
        """

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(combined_query, (from_dt, to_dt, currency, is_active, from_dt, to_dt, currency, is_active))
            records = cur.fetchall()
            return records

    def get_unique_categories(self) -> List[sqlite3.Row]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT category FROM operations")
            category_records = cur.fetchall()
            return category_records

    def get_unique_subcategories(self, category: Optional[str] = None) -> List[sqlite3.Row]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if category:
                rows = cur.execute("SELECT DISTINCT subcategory FROM operations WHERE category = ?", (category,))
            else:
                rows = cur.execute("SELECT DISTINCT subcategory FROM operations")
            subcat_records = rows.fetchall()
            return subcat_records

    def get_operations_list_from_datetime(self, account_id: str, operation_datetime: datetime) -> List[sqlite3.Row]:
        """
        Fetches all operations with datetimes greater than the input datetime and the first operation before, sorted
        by date in ascending order: {date(op_0) < date(op_1) < ... < date(op_N)}.
        If the operation_datetime provided is identical to other operation datetime, that operation will be the first.
        If the operation_datetime provided is identical to several operations datetime, all those operations will be
        ignored but the last one (newer id), which will be the first on the returned list.
        """
        dict_data = {"account_id": account_id, "operation_datetime": operation_datetime}
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                WITH previous_row AS (
                  SELECT * FROM operations
                  WHERE account_id = :account_id AND operation_datetime <= :operation_datetime
                  ORDER BY operation_datetime DESC, operation_id DESC
                  LIMIT 1
                )
                SELECT * FROM operations
                WHERE account_id = :account_id AND operation_datetime > :operation_datetime
                UNION ALL
                SELECT * FROM previous_row
                ORDER BY operation_datetime ASC, operation_id ASC;
                """,
                dict_data,
            )
            records = cur.fetchall()
            return records

    def get_operations_list_from_id(self, account_id: str, operation_id: str) -> List[sqlite3.Row]:
        """
        Fetches all operations from db with a datetime grater than the datetime of the operation with given id, and the
        first operation before, sorted by date in ascending order: {date(op_0) < date(op_1) < ... < date(op_N)}.
        """
        dict_data = {"account_id": account_id, "operation_id": operation_id}
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                WITH row_number_table AS (
                  SELECT *, row_number() over (ORDER BY operation_datetime, operation_id) AS row_number FROM operations
                  WHERE account_id = :account_id AND operation_datetime <= (
                    SELECT operation_datetime FROM operations
                    WHERE account_id = :account_id AND operation_id = :operation_id
                  )
                )
                SELECT 
                  operation_id, account_id, operation_datetime, cumulative_amount, amount, operation_type, 
                  category, subcategory, description, tags, group_id, detail_id, transfer_id, created_at, updated_at 
                FROM row_number_table WHERE row_number = (
                  SELECT row_number-1 FROM row_number_table
                  WHERE operation_id = :operation_id
                )
                UNION
                SELECT * FROM operations WHERE account_id = :account_id AND operation_id = :operation_id
                UNION
                SELECT * FROM operations WHERE account_id = :account_id AND operation_datetime >= (
                  SELECT operation_datetime FROM operations
                  WHERE operation_id = :operation_id
                )
                ORDER BY operation_datetime, operation_id;
                """,
                dict_data,
            )

            records = cur.fetchall()
            return records

    def update_operation(self, operation: Operations) -> None:
        operation_data = operation.to_dict()
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(self.UPDATE_QUERY, operation_data)
            # Update account total if provided
            if operation.account_total is not None:
                cur.execute(
                    """
                    UPDATE accounts SET account_total = :account_total, updated_at = :updated_at 
                    WHERE account_id = :account_id
                    """,
                    operation_data,
                )

    def update_several_operations(
        self, operation: Operations, operations_list: List[Operations], edit_flag: bool = False
    ) -> Dict[str, Any]:
        """
        Edits all affected operations by the 'self' operation: could be an insert or an update. So, it also creates a
        new operations if edit_flag = False
        edit_flag = True means that self operation has been edited instead of created.

        args:
            operations_list (list of dicts): list of OperationModel.to_dict() with the information to update the db.
            edit_flag (bool): True if there is a self edition involved.
        """
        with self._connect() as conn:
            oper_dicts = [Operations.to_dict(oper) for oper in operations_list]
            cur = conn.cursor()
            cur.executemany(self.UPDATE_QUERY, oper_dicts)
            if not edit_flag:
                operation_data = operation.to_dict()
                cur.execute(self.INSERT_QUERY, operation_data)
            else:
                operation_data = oper_dicts[-1]
            if operation.account_total is not None:
                cur.execute(
                    "UPDATE accounts SET account_total = ?, updated_at = ? WHERE account_id = ?",
                    (
                        operation.account_total,
                        operation.updated_at,
                        operation.account_id,
                    ),
                )
            return operation_data

    def delete_operation(self, operation: Operations, operations_list: List[Operations]) -> None:
        """
        Deletes one operation and edits all necessary operations affected by the deletion.

        args:
            operations_list (list): list of Operations objects with the information to update the database.
        """
        oper_dicts = [Operations.to_dict(oper) for oper in operations_list]
        with self._connect() as conn:
            cur = conn.cursor()
            cur.executemany(
                self.UPDATE_QUERY,
                oper_dicts,
            )

            # Delete the operation
            cur.execute("DELETE FROM operations WHERE operation_id = ?", (operation.operation_id,))
            # Update the account total
            if operation.account_total is not None:
                cur.execute(
                    "UPDATE accounts SET account_total = ?, updated_at = ? WHERE account_id = ?",
                    (
                        operation.account_total,
                        operation.updated_at,
                        operation.account_id,
                    ),
                )
