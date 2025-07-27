#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 09/06/2025 23:45

@author: igna
"""
import os
from math import ceil
from typing import List
from decimal import Decimal
from datetime import datetime

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.uic import loadUi
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMainWindow, QLabel

from src.queries.accqueries import ListAccountsQuery
from src.queries.opqueries import GetOperationByIDQuery, ListOperationsQuery

from src.models.opmodel import UserOperations
from src.ophandlers.deletehandler import DeletionHandler
from src.ophandlers.operationhandler import OperationHandler

from billeUI import UISPATH, operationscreen, currency_format, animatedlabel, headerfiltermixin

DATEFORMAT = "%A %d-%m-%Y %H:%M:%S"


class HeaderFilter(headerfiltermixin.HeaderFilterMixin):
    def __init__(self):
        super().__init__()


class PageLink(QLabel):
    """
    Label with the clickeable property to be used to change between pages of operations in an account.
    """

    clicked = pyqtSignal([str])

    def __init__(self, text, parent=None):
        super().__init__(text, parent=parent)
        self.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.setStyleSheet("color: blue;")
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignRight)
        # size of the laels
        width = self.fontMetrics().boundingRect(self.text()).width()
        height = self.fontMetrics().height()
        self.setFixedSize(width + 40, height + 2)
        # visibility
        self.setVisible(False)
        # stiles
        page_link_style = """
        QLabel {
            color: #007bff;
            font-weight: bold;
        }
        QLabel:hover {
            color: #0056b3;
            text-decoration: underline;
        }
        """
        self.setStyleSheet(page_link_style)

    def mousePressEvent(self, event):
        self.clicked.emit(self.text())
        return super().mousePressEvent(event)


class OperationBrowser(QMainWindow, headerfiltermixin.HeaderFilterMixin):
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

        self.column_widths = [135, 100, 90, 90, 100, 130, 400, 10]
        self.headers_list = [
            "Date & Time",
            "Cumulatives",
            "Amount",
            "Operation Type",
            "Category",
            "Subcategory",
            "Description",
            "Select",
        ]

        self.acc_id = ""
        self.operations_list = []
        self.current_account_index = -1  # flag index to avoid fetching operations unnecessarily
        self.active_filters = {}

        # Pagination
        self.pagination_index = 0
        self.page_label = QLabel()
        self.next_page_label = PageLink(">", parent=self)
        self.prev_page_label = PageLink("<", parent=self)

        self.HLablelLayout.addWidget(self.page_label)
        self.HLablelLayout.addWidget(self.prev_page_label)
        self.HLablelLayout.addWidget(self.next_page_label)

        self.next_page_label.clicked.connect(self.next_page)
        self.prev_page_label.clicked.connect(self.prev_page)

        # Pupulation of the tables with operations data
        self.set_table_data(self.accounts_comboBox.currentIndex())
        self.accounts_comboBox.currentIndexChanged.connect(self.set_table_data)

        # Filters
        self.init_header_filter(
            self.operation_table_widget,
            filterable_columns=[3, 4, 5],
            operations_list=self.filter_operations(self.operations_list),
        )
        self.set_filter_callback(lambda: self.set_table_data(self.accounts_comboBox.currentIndex()))

        # Activation of the save button on changes in data
        self.rows_changed = set()
        self.operation_table_widget.cellChanged.connect(self.cell_change)
        self.save_changes_button.clicked.connect(self.save_updated_row)

        # Delete operation button
        self.delete_op_button.setVisible(False)
        self.operation_table_widget.itemChanged.connect(self.handle_checkbox_change)
        self.delete_op_button.clicked.connect(self.delete_operations)

        # Go back to previus window
        self.back_button.clicked.connect(self.back)

    def next_page(self) -> None:
        try:
            self.pagination_index += 1
            self.set_table_data(self.accounts_comboBox.currentIndex())
        except IndexError:
            self.pagination_index = 0

    def prev_page(self) -> None:
        try:
            self.pagination_index -= 1
            self.set_table_data(self.accounts_comboBox.currentIndex())
        except IndexError:
            self.pagination_index = 0

    def handle_checkbox_change(self, item):
        """
        Sets the delete operation button visible whenever an operation has its checkbox checked
        and invisible when the checkbox is unchecked
        """
        if item.column() == self.operation_table_widget.columnCount() - 1:
            any_checked = any(
                self.operation_table_widget.item(row, self.operation_table_widget.columnCount() - 1).checkState()
                == Qt.Checked
                for row in range(self.operation_table_widget.rowCount())
            )
            self.delete_op_button.setVisible(any_checked)

    def get_operations_data(self, index: int) -> None:
        """Makes de query to fetch all operations from a given account"""
        self.acc_id = self.accounts_object[index].model_dump()["account_id"]
        self.operations_list = ListOperationsQuery(
            user_id=self.widget.user_object.user_id, account_id=self.acc_id
        ).execute(order_by_datetime="DESC")
        self.current_account_index = index

    def set_table_data(self, index: int) -> None:
        """
        Populates the table with the operations of the given account. The given account is selected with the index
        """
        # Disconnect the signal for the table so cellChanged.connect is not triggered while loading a new account
        self.operation_table_widget.blockSignals(True)

        # call the get_operations_data only when the account is changed and not when moving through pagination
        if self.current_account_index != index:
            self.get_operations_data(index)
            self.current_account_index = index
            self.pagination_index = 0

        self.operation_table_widget.setColumnCount(len(self.headers_list))
        self.operation_table_widget.setHorizontalHeaderLabels(self.headers_list)
        self.total_label.setText("<b>Total: Empty</b>")

        filtered_operations_list = self.filter_operations(self.operations_list)

        if self.operations_list and filtered_operations_list:
            pagination = 100
            print(f"{len(self.operations_list)=}, {len(filtered_operations_list)=}")

            cumulative_amount = currency_format(self.operations_list[0].cumulative_amount)
            self.total_label.setText(f"<b>Total: ${cumulative_amount}</b>")
            if len(filtered_operations_list) > pagination:
                pagination_left = self.pagination_index * pagination
                pagination_right = (self.pagination_index + 1) * pagination
                operations_page = filtered_operations_list[pagination_left:pagination_right]
                pages = ceil(len(filtered_operations_list) / pagination)
                current_page = self.pagination_index

                if current_page < 0:
                    current_page = 0
                elif current_page >= pages:
                    current_page = pages - 1
                self.pagination_index = current_page

                self.page_label.setText(f"Page {self.pagination_index + 1} of {pages}")

                self.prev_page_label.setVisible(current_page > 0)
                self.next_page_label.setVisible(current_page < pages - 1)

                self.prev_page_label.setText("◀ Prev")
                self.next_page_label.setText("Next ▶")
            else:
                self.pagination_index = 0
                operations_page = filtered_operations_list
                pages = 1
                self.prev_page_label.setVisible(False)
                self.next_page_label.setVisible(False)
                self.page_label.setText(f"Page {self.pagination_index + 1} of {pages}")

            self.operation_table_widget.setRowCount(len(operations_page))
            self.set_table_items(operations_page)
            # Reconnect the signal for the table
            self.operation_table_widget.blockSignals(False)
        else:
            self.operation_table_widget.clearContents()

    def set_table_items(self, current_operations_page: List[UserOperations]) -> None:
        """wrapper function to set the info into the table"""
        for row_index, operation in enumerate(current_operations_page):
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
            items[0].setData(QtCore.Qt.UserRole + 1, self.acc_id)

            checkbox = QtWidgets.QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            self.operation_table_widget.setItem(row_index, len(items), checkbox)

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
                self.operation_table_widget.setColumnWidth(column_index, self.column_widths[column_index])

    def filter_operations(self, operations_list):
        """Applies the active filters to the complete operations list of a given account"""
        if not hasattr(self, "active_filters") or not self.active_filters:
            return operations_list
        filtered = []
        for operation in operations_list:
            passed = True
            for col, vals in self.active_filters.items():
                value = None
                if col == 3:
                    value = operation.operation_type
                elif col == 4:
                    value = operation.category
                    if operation.category == "Compas":
                        print(operation)
                elif col == 5:
                    value = operation.subcategory
                if value not in vals:
                    passed = False
                    break
            if passed:
                filtered.append(operation)
        return filtered

    def cell_change(self, row, column) -> None:
        """detects when a cell in a row has a change"""
        checkbox_column: int = 7
        if column != checkbox_column:
            self.operation_table_widget.item(row, column)
            self.rows_changed.add(row)
            self.save_changes_button.setEnabled(True)
            self.status_label.setText("<font color='orange'>Changes to be saved.</font>")

    def save_updated_row(self):
        """Get all the new data in a row"""
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
                self.status_label.setText("<font color='green'>Change saved.</font>")
                animatedlabel.AnimatedLabel("Changes successfully saved ✅").display()
            except ValueError:
                animatedlabel.AnimatedLabel("Edition not allowed!!", message_type="error").display()
                self.status_label.setText(
                    "<font color='red'>Can not save this change because somewhere the cumulative amount becomes negative.</font>"
                )
        self.save_changes_button.setEnabled(False)
        # force update data in set_table by changing the self.current_account_index
        self.current_account_index = -1
        self.set_table_data(self.accounts_comboBox.currentIndex())
        self.rows_changed.clear()

    def delete_operations(self):
        """
        Method to delet operations. More than one operation can be deleted at the same time. A message will
        be desplayed before deleting the operation asking for permission for it.
        """
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete the selected operations?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            rows_to_delete = []
            for row in range(self.operation_table_widget.rowCount()):
                checkbox = self.operation_table_widget.item(row, self.operation_table_widget.columnCount() - 1)
                if checkbox and checkbox.checkState() == Qt.Checked:
                    op_id = self.operation_table_widget.item(row, 0).data(QtCore.Qt.UserRole)
                    acc_id = self.operation_table_widget.item(row, 0).data(QtCore.Qt.UserRole + 1)
                    rows_to_delete.append((op_id, acc_id))

            for op_id, acc_id in rows_to_delete:
                op = GetOperationByIDQuery(
                    user_id=self.widget.user_object.user_id, account_id=acc_id, operation_id=op_id
                ).execute()
                deletion = DeletionHandler(**op.model_dump())
                deletion.set_account_total()
                cml = deletion.set_cumulatives()
                deletion.save(cml)

            # QTimer used to deffer slightly the generation of the label to next iteration of the event loop, so the main
            # window get of focus again. Otherwise it will not appear.
            QTimer.singleShot(1, lambda: animatedlabel.AnimatedLabel("Operations deleted successfully ✅").display())
            self.status_label.setText(f"<font color='green'>{len(rows_to_delete)} operations deleted.</font>")
            self.current_account_index = -1  # fuerza recarga
            self.set_table_data(self.accounts_comboBox.currentIndex())
            self.delete_op_button.setVisible(False)

    def copy_selected_cells(self):
        """Gets all text from items in the selected range of cells, then join them in a string with new lines and tabs"""
        selection = self.operation_table_widget.selectedRanges()
        if selection:
            selected = selection[0]
            text_data = ""
            for row in range(selected.topRow(), selected.bottomRow() + 1):
                row_data = []
                for col in range(selected.leftColumn(), selected.rightColumn() + 1):
                    item = self.operation_table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                text_data += "\t".join(row_data) + "\n"
            QtWidgets.QApplication.clipboard().setText(text_data)

    def back(self) -> None:
        """Returns to the OperationScreen Menu"""
        operation_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(operation_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the OperationScreen Menu when Esc key is pressed."""
        if e.matches(QtGui.QKeySequence.Copy):
            self.copy_selected_cells()
        elif e.key() == QtCore.Qt.Key_Escape:
            operation_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(operation_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
