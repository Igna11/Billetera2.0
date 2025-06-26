"""
Enero 2025
"""

import os
import sqlite3
import csv
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta, UTC

from src.models.usrmodel import User
from src.models.accmodel import UserAccounts
from src.models.opmodel import OperationNotFoundError
from src.ophandlers.operationhandler import OperationHandler


class CSVtoSQLiteMapper:
    def __init__(self, user: User, account: UserAccounts, table_name: str):
        """
        Initialize the mapper with the SQLite database path.
        """
        self.db_path = os.path.join("data", user.user_id, "accounts_database.db")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.table_name = table_name
        self.user_id = user.user_id
        self.account_id = account.account_id

    def close(self):
        """
        Close the database connection.
        """
        self.connection.close()

    def load_csv(self, csv_path, delimiter):
        """
        Load the CSV file and return its headers and rows.
        """
        with open(csv_path, "r") as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            headers = reader.fieldnames
            rows = list(reader)
        return headers, rows

    def initialize_operation(self, user: User, account: UserAccounts, db_row: dict) -> OperationHandler:
        """
        Creates the operation object whose values will be extracted to be saved into the database

        Arg:
            db_row: Dictionary with the structured information needed by the OperationsModel object
        Return:
            OperationHandler object
        """
        db_row["user_id"] = self.user_id
        db_row["account_id"] = self.account_id
        db_row["cumulative_amount"] = db_row["amount"]
        db_row["created_at"] = db_row["updated_at"] = datetime.now(UTC)
        return OperationHandler(**db_row)

    def map_and_insert(self, user: User, account: UserAccounts, rows) -> dict:
        """
        Map CSV columns to database fields and insert rows into the database.

        :param rows: List of rows from the CSV file.
        :param mapping: Dictionary mapping CSV columns to database fields.
        """
        tzBSAS = ZoneInfo("America/Argentina/Buenos_Aires")
        for i, row in enumerate(rows):
            print(f"\rFila: {i+1} de {len(rows)}", end="")
            db_row = {}
            row["datetime"] = datetime.strptime(row["Date"] + " " + row["Time"], "%d-%m-%Y %H:%M:%S")
            db_row["operation_datetime"] = row["datetime"].replace(tzinfo=tzBSAS).astimezone(UTC)
            db_row["category"] = row["Category"]
            db_row["subcategory"] = row["Subcategory"]
            db_row["description"] = row["Description"]
            if float(row["Expenses"]) > 0 or float(row["Extractions"]) > 0 and row["Category"] != "Transferencia":
                db_row["operation_type"] = "expense"
                db_row["amount"] = max(row["Expenses"], row["Extractions"])
            if float(row["Incomes"]) > 0 and row["Category"] != "Transferencia":
                db_row["operation_type"] = "income"
                db_row["amount"] = row["Incomes"]
            if row["Category"] == "Transferencia" and row["Subcategory"] == "Transferencia de salida":
                db_row["operation_type"] = "transfer_out"
                db_row["amount"] = row["Extractions"]
            elif row["Category"] == "Transferencia" and row["Subcategory"] == "Transferencia de entrada":
                db_row["operation_type"] = "transfer_in"
                db_row["amount"] = row["Incomes"]

            # Insert into database
            oper4db = self.initialize_operation(user, account, db_row)
            self.insert_row(oper4db)

    def insert_row(self, operation: OperationHandler):
        """
        Insert a single row into the database.
        """
        insert_query = f"""
        INSERT INTO {self.table_name} (
            operation_id,
            operation_datetime,
            amount,
            cumulative_amount,
            operation_type,
            category,
            subcategory,
            description,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        values = (
            operation.operation_id,
            operation.operation_datetime,
            operation.amount,
            operation.cumulative_amount,
            operation.operation_type,
            operation.category,
            operation.subcategory,
            operation.description,
            operation.created_at,
            operation.updated_at,
        )
        self.cursor.execute(insert_query, values)
        self.connection.commit()

    def sanitizer(self):
        """
        Corrects the cumulative amounts and the account_total
        """
        self.cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY ROWID ASC LIMIT 1;")

        record = self.cursor.fetchone()
        self.connection.close()

        if not record:
            raise OperationNotFoundError

        record = dict(record)
        record["user_id"] = self.user_id
        record["account_id"] = self.account_id

        first_operation = OperationHandler(**record)
        cml_corrected_list = first_operation.set_cumulatives(edit_flag=True, original_operation=first_operation)
        # the first operation is added at the end of the list
        cml_corrected_list_without_first = cml_corrected_list[:-1]
        # the account total must be the same as the last cumulative amount
        try:
            # or the same as the amount if there is only one income
            first_operation.account_total = cml_corrected_list_without_first[-1].cumulative_amount
        except IndexError:
            first_operation.account_total = first_operation.amount
        # save the changes
        first_operation.save(existing_operations=cml_corrected_list)
