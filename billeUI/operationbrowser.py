#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 09/06/2025 23:45

@author: igna
"""
import os
from decimal import Decimal
from datetime import datetime, UTC

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QDate, QTime, QDateTime

from src.queries.accqueries import ListAccountsQuery
from src.queries.opqueries import GetOperationByIDQuery, ListOperationsQuery, ListOperationsByDatetime

from src.ophandlers.operationhandler import OperationHandler

from billeUI import operationscreen, currency_format
from billeUI import UISPATH

DATEFORMAT = "%A %d-%m-%Y %H:%M:%S"


class OperationBrowser(QMainWindow):
    """
    Screen where inputs for the operations are managed
    """

    def __init__(self, parent=None, widget=None):
        super(OperationBrowser, self).__init__(parent)
        operation_browser_screen = os.path.join(UISPATH, "operation_browser_screen.ui")
        loadUi(operation_browser_screen, self)
        self.widget = widget

        self.accounts_object = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()

        self.acc_list = [f"{acc.account_name} ({acc.account_currency})" for acc in self.accounts_object]
        self.accounts_comboBox.addItems(self.acc_list)
        self.accounts_comboBox.currentIndexChanged.connect(self.set_table_data)

        self.sort_type = "DESC"
        self.operation_table_widget.horizontalHeader().sectionClicked.connect(self.header_clicked_sort)

        self.set_table_data(self.accounts_comboBox.currentIndex())
        self.back_button.clicked.connect(self.back)

        self.rows_changed = set()
        self.columns_changed = {}
        self.operation_table_widget.cellChanged.connect(self.cell_change)
        self.save_changes_button.clicked.connect(self.save_updated_row)

        # self.status_label
        # self.total_label

    def header_clicked_sort(self, index):
        if index == 0:
            if self.sort_type == "DESC":
                self.sort_type = "ASC"
            elif self.sort_type == "ASC":
                self.sort_type = "DESC"
            self.set_table_data(self.accounts_comboBox.currentIndex())

    def set_table_data(self, index: int) -> None:
        # Disconnect the signal for the table so cellChanged.connect is not triggered while loading a new account
        self.operation_table_widget.blockSignals(True)
        acc_id = self.accounts_object[index].model_dump()["account_id"]
        operations_list = ListOperationsQuery(user_id=self.widget.user_object.user_id, account_id=acc_id).execute(
            order_by_datetime=self.sort_type
        )

        headers_list = [
            "Date & Time",
            "Cumulatives",
            "Amount",
            "Operation Type",
            "Category",
            "Subcategory",
            "Description",
        ]
        column_widths = [135, 100, 90, 90, 100, 130, 900]
        self.operation_table_widget.setRowCount(len(operations_list))
        self.operation_table_widget.setColumnCount(len(headers_list))
        self.operation_table_widget.setHorizontalHeaderLabels(headers_list)
        self.total_label.setText(f"<b>Total: Empty</b>")

        if operations_list:
            cumulative_amount = currency_format(operations_list[0].cumulative_amount)
            self.total_label.setText(f"<b>Total: ${cumulative_amount}</b>")
            tablerow = 0
            for row_index, operation in enumerate(operations_list):
                # arrow = "\u2197" if operation.operation_type == "income" or operation.operation_type == "transfer_in" else "\u2198"
                items = [
                    QtWidgets.QTableWidgetItem(operation.operation_datetime.strftime(DATEFORMAT)),
                    QtWidgets.QTableWidgetItem(f"{currency_format(operation.cumulative_amount)}"),
                    QtWidgets.QTableWidgetItem(f"{currency_format(operation.amount)}"),
                    QtWidgets.QTableWidgetItem(operation.operation_type),
                    QtWidgets.QTableWidgetItem(operation.category),
                    QtWidgets.QTableWidgetItem(operation.subcategory),
                    QtWidgets.QTableWidgetItem(operation.description),
                ]
                # save the account_id and operation_id to be retrieved later
                items[0].setData(QtCore.Qt.UserRole, operation.operation_id)
                items[0].setData(QtCore.Qt.UserRole + 1, acc_id)

                # colors
                if operation.operation_type == "income":
                    background_color = QColor(200, 255, 200)
                elif operation.operation_type == "transfer_in":
                    background_color = QColor(190, 235, 255)
                elif operation.operation_type == "expense":
                    background_color = QColor(255, 200, 200)
                elif operation.operation_type == "transfer_out":
                    background_color = QColor(255, 230, 180)
                else:
                    background_color = QColor(255, 255, 255)

                for column_index, item in enumerate(items):
                    item.setBackground(background_color)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                    self.operation_table_widget.setItem(row_index, column_index, item)
                    self.operation_table_widget.setColumnWidth(column_index, column_widths[column_index])
            # Reconnect the signal for the table
            self.operation_table_widget.blockSignals(False)

    def cell_change(self, row, column):
        """detects when a cell in a row has a change"""
        item = self.operation_table_widget.item(row, column)
        new_value = item.text()
        self.rows_changed.add(row)
        self.save_changes_button.setEnabled(True)
        self.status_label.setText(f"<font color='orange'>Changes to be saved.</font>")

    def save_updated_row(self):
        """Get all the new data in a row"""
        updated_data = []
        for row_idx in self.rows_changed:
            user_id = self.widget.user_object.user_id
            account_id = self.operation_table_widget.item(row_idx, 0).data(QtCore.Qt.UserRole + 1)
            operation_id = self.operation_table_widget.item(row_idx, 0).data(QtCore.Qt.UserRole)
            # original operation used for edition
            original_op = GetOperationByIDQuery(
                user_id=user_id, account_id=account_id, operation_id=operation_id
            ).execute()
            # dictionary to create the OperationHandler object
            row_data = {
                "user_id": user_id,
                "account_id": account_id,
                "operation_id": operation_id,
                "operation_datetime": datetime.strptime(
                    self.operation_table_widget.item(row_idx, 0).text() + "+00:00", DATEFORMAT + "%z"
                ),
                "cumulative_amount": Decimal(
                    currency_format(self.operation_table_widget.item(row_idx, 1).text(), to_numeric=True)
                ),
                "amount": Decimal(
                    currency_format(self.operation_table_widget.item(row_idx, 2).text(), to_numeric=True)
                ),
                "operation_type": self.operation_table_widget.item(row_idx, 3).text(),
                "category": self.operation_table_widget.item(row_idx, 4).text(),
                "subcategory": self.operation_table_widget.item(row_idx, 5).text(),
                "description": self.operation_table_widget.item(row_idx, 6).text(),
            }

            edited_op = OperationHandler(**row_data)
            edited_op.set_account_total(edit_flag=True, original_operation=original_op)
            try:
                cml = edited_op.set_cumulatives(edit_flag=True, original_operation=original_op)
                edited_op.save(cml)
                self.status_label.setText(f"<font color='green'>Change saved.</font>")
            except ValueError as e:
                self.status_label.setText(
                    f"<font color='red'><b>Can not save this change because somewhere the cumulative amount becomes negative.</b></font>"
                )
                print(e)
        self.save_changes_button.setEnabled(False)
        self.set_table_data(self.accounts_comboBox.currentIndex())
        self.rows_changed.clear()

    def back(self) -> None:
        """Returns to the OperationScreen Menu"""
        operation_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(operation_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the OperationScreen Menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            operation_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(operation_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
