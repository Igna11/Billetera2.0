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
from PyQt5.QtWidgets import QMainWindow, QLabel, QStyledItemDelegate, QComboBox, QCompleter, QMessageBox

from pydantic import ValidationError

from src.queries.accqueries import ListAccountsQuery
from src.queries.opqueries import GetOperationByIDQuery, ListOperationsQuery

from src.models.opmodel import Operations
from src.queries.groupqueries import ListGroupsQuery, GetGroupByIDQuery
from src.commands.groupcommands import CreateOperationGroupCommand
from src.ophandlers.deletehandler import DeletionHandler
from src.ophandlers.operationhandler import OperationHandler, NegativeAccountTotalError

from billeUI import UISPATH, operationscreen, currency_format, animatedlabel, headerfiltermixin
from billeUI.utils import clean_tags

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


class GroupComboBoxDelegate(QStyledItemDelegate):
    """Custom delegate for group column with combo box"""

    def __init__(self, groups_list, user_id, accounts_dict, parent=None):
        super().__init__(parent)
        self.groups_list = groups_list  # List of (group_id, group_name) tuples
        self.user_id = user_id
        self.accounts_dict = accounts_dict  # Mapping of account_id -> account_currency
        self.parent_browser = parent  # Reference to parent OperationBrowser for refreshing

    def createEditor(self, parent, option, index):
        """Create the combo box editor with search functionality and limit to 10 items"""
        editor = QComboBox(parent)
        editor.setEditable(True)  # Allow typing to search

        # Add "N/A" option
        editor.addItem("N/A", None)

        for i, (group_id, group_name) in enumerate(self.groups_list):
            editor.addItem(group_name, group_id)

        # Add completer for search functionality
        completer = QCompleter(editor)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setModel(editor.model())
        editor.setCompleter(completer)

        return editor

    def setEditorData(self, editor, index):
        """Set the current value in the editor"""
        current_text = index.model().data(index, Qt.DisplayRole)
        if current_text == "N/A":
            editor.setCurrentIndex(0)
        else:
            # Find the index of the current group name in the dropdown
            found = False
            for i in range(1, editor.count()):
                if editor.itemText(i) == current_text:
                    editor.setCurrentIndex(i)
                    found = True
                    break

            # If not found in the dropdown (because it's beyond the first 10),
            # set it as the text directly
            if not found:
                editor.setEditText(current_text)

    def setModelData(self, editor, model, index):
        """Save the data from the editor back to the model"""
        current_text = editor.currentText()

        if current_text == "N/A" or editor.currentIndex() == 0:
            # "N/A" selected - remove group
            model.setData(index, "N/A", Qt.DisplayRole)
            model.setData(index, None, Qt.UserRole)  # Store group_id in UserRole
        else:
            # Group selected or typed
            group_name = current_text
            group_id = editor.currentData()

            # If group_id is None (user typed a group not in dropdown),
            # search for it in the full groups_list
            if group_id is None:
                for gid, gname in self.groups_list:
                    if gname == group_name:
                        group_id = gid
                        break

            # If still not found, ask to create a new group
            if group_id is None and group_name and group_name.strip():
                # Get account_id from the first column (stored in UserRole + 1)
                account_id = model.data(index.sibling(index.row(), 0), Qt.UserRole + 1)

                if account_id and account_id in self.accounts_dict:
                    account_currency = self.accounts_dict[account_id]

                    # Ask user if they want to create the group
                    reply = QMessageBox.question(
                        None,
                        "Create Group",
                        f"Group '{group_name}' does not exist. Do you want to create it with currency {account_currency}?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes,
                    )

                    if reply == QMessageBox.Yes:
                        new_group = CreateOperationGroupCommand(
                            user_id=self.user_id,
                            group_name=group_name,
                            group_currency=account_currency,
                            status="open",
                        ).execute()
                        # new_group.create()
                        group_id = new_group.group_id

                        # Refresh the groups list in the parent browser
                        if self.parent_browser:
                            self.parent_browser.refresh_groups_list()
                    else:
                        # User cancelled, revert to N/A
                        model.setData(index, "N/A", Qt.DisplayRole)
                        model.setData(index, None, Qt.UserRole)
                        return
                else:
                    # No account_id found, revert to N/A
                    model.setData(index, "N/A", Qt.DisplayRole)
                    model.setData(index, None, Qt.UserRole)
                    return

            model.setData(index, group_name, Qt.DisplayRole)
            model.setData(index, group_id, Qt.UserRole)  # Store group_id in UserRole


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
        self.acc_list.extend(["All"])
        self.accounts_comboBox.addItems(self.acc_list)

        # Create accounts dictionary for delegate (account_id -> account_currency)
        self.accounts_dict = {acc.account_id: acc.account_currency for acc in self.accounts_object}

        # Load groups for the combo box delegate
        self.groups_list = []
        self.groups_dict = {}
        try:
            groups = ListGroupsQuery(user_id=self.widget.user_object.user_id, status="open").execute()
            self.groups_list = [(group.group_id, group.group_name) for group in groups]
            self.groups_dict = {group_id: group_name for group_id, group_name in self.groups_list}
        except Exception:
            self.groups_list = []
            self.groups_dict = {}

        self.column_widths = [135, 100, 90, 90, 100, 130, 400, 150, 200, 40]
        self.headers_list = [
            "Date & Time",
            "Cumulatives",
            "Amount",
            "Operation Type",
            "Category",
            "Subcategory",
            "Description",
            "Group",
            "Tags",
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

        self.HLabelLayout.addWidget(self.page_label)
        self.HLabelLayout.addWidget(self.prev_page_label)
        self.HLabelLayout.addWidget(self.next_page_label)

        self.next_page_label.clicked.connect(self.next_page)
        self.prev_page_label.clicked.connect(self.prev_page)

        # Set up the group column delegate
        self.group_delegate = GroupComboBoxDelegate(
            self.groups_list, self.widget.user_object.user_id, self.accounts_dict, self
        )

        # Pupulation of the tables with operations data
        self.set_table_data(self.accounts_comboBox.currentIndex())
        self.accounts_comboBox.currentIndexChanged.connect(self.set_table_data)

        # Filters
        # Create groups dictionary for header filter (group_id -> group_name)
        groups_dict = {group_id: group_name for group_id, group_name in self.groups_list}
        self.init_header_filter(
            self.operation_table_widget,
            filterable_columns=(
                [0, 3, 4, 5, 6, 7, 8] if self.accounts_comboBox.currentText() != "All" else [0, 3, 4, 5, 6, 7, 8, 9]
            ),
            operations_list=self.filter_operations(self.operations_list),
            groups_dict=groups_dict,
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

    def add_account_column(self) -> None:
        if "Account Name" not in self.headers_list:
            self.column_widths.insert(-1, 200)
            self.headers_list.insert(-1, "Account Name")

    def remove_account_column(self) -> None:
        if "Account Name" in self.headers_list:
            self.column_widths.pop(-2)
            self.headers_list.remove("Account Name")

    def add_tags_column(self) -> None:
        if "Tags" not in self.headers_list:
            self.column_widths.insert(-1, 200)
            self.headers_list.insert(-1, "Tags")

    def remove_tags_column(self) -> None:
        if "Tags" in self.headers_list:
            self.column_widths.pop(-2)
            self.headers_list.remove("Tags")

    def view_all_operations(self) -> None:
        self.add_account_column()
        self.set_table_data(self.accounts_comboBox.currentIndex())

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

    def get_all_operations_data(self) -> List:
        """Makes the query to fetch ALL operations in ALL accounts"""
        all_operations = ListOperationsQuery(user_id=self.widget.user_object.user_id).execute(order="DESC")
        self.add_account_column()
        return all_operations

    def get_operations_data(self, index: int) -> None:
        """Makes the query to fetch all operations from a given account"""
        if index == len(self.accounts_object):
            self.operations_list = ListOperationsQuery(user_id=self.widget.user_object.user_id).execute(order="DESC")
        else:
            self.acc_id = self.accounts_object[index].to_dict().get("account_id")
            self.operations_list = ListOperationsQuery(user_id=self.widget.user_object.user_id).execute(
                account_id=self.acc_id, order="DESC"
            )
        self.current_account_index = index

    def set_table_data(self, index: int) -> None:
        """
        Populates the table with the operations of the given account. The given account is selected with the index
        """
        # Disconnect the signal for the table so cellChanged.connect is not triggered while loading a new account
        self.operation_table_widget.blockSignals(True)

        if self.accounts_comboBox.itemText(index) == "All":
            self.operations_list = self.get_all_operations_data()
        else:
            self.remove_account_column()

        # call the get_operations_data only when the account is changed and not when moving through pagination
        if self.current_account_index != index:
            self.get_operations_data(index)
            self.current_account_index = index
            self.pagination_index = 0

        self.operation_table_widget.setColumnCount(len(self.headers_list))
        self.operation_table_widget.setHorizontalHeaderLabels(self.headers_list)

        # Set the delegate for the group column (column 7)
        self.operation_table_widget.setItemDelegateForColumn(7, self.group_delegate)

        self.total_label.setText("<b>Total: Empty</b>")

        filtered_operations_list = self.filter_operations(self.operations_list)

        # Update the header filter mixin with the current operations list
        self.update_operations_list(self.operations_list)

        if self.operations_list and filtered_operations_list:
            pagination = 100

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

    def set_table_items(self, current_operations_page: List[Operations]) -> None:
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
            items[0].setData(QtCore.Qt.UserRole + 1, operation.account_id)

            # Add group name
            group_name = "N/A"
            if operation.group_id:
                try:
                    group = GetGroupByIDQuery(
                        user_id=self.widget.user_object.user_id, group_id=operation.group_id
                    ).execute()
                    # group = OperationGroups.get_group_by_id(self.widget.user_object.user_id, operation.group_id)
                    group_name = group.group_name
                except Exception:
                    group_name = "N/A"
            group_item = QtWidgets.QTableWidgetItem(group_name)
            group_item.setData(QtCore.Qt.UserRole, operation.group_id)  # Store group_id for later use
            items.append(group_item)

            # Add tags as text for now (will be displayed as TagContainer later)
            tags_text = ",".join(operation.tags) if operation.tags else ""
            tags_item = QtWidgets.QTableWidgetItem(tags_text)
            tags_item.setData(QtCore.Qt.UserRole, operation.tags)  # Store tags tuple for later use
            items.append(tags_item)

            if self.accounts_comboBox.currentText() == "All":
                items.insert(len(items), QtWidgets.QTableWidgetItem(operation.account_name))

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
        # Create groups dictionary for group name lookup
        groups_dict = {group_id: group_name for group_id, group_name in self.groups_list}

        for operation in operations_list:
            passed = True
            for col, filter_value in self.active_filters.items():
                if col == 0:
                    # Date column - check if operation date is within range
                    if isinstance(filter_value, dict) and "initial" in filter_value and "final" in filter_value:
                        op_date = operation.operation_datetime.date()
                        initial_date = filter_value["initial"]
                        final_date = filter_value["final"]
                        if not (initial_date <= op_date <= final_date):
                            passed = False
                            break
                elif col == 3:
                    # Operation type column
                    if operation.operation_type not in filter_value:
                        passed = False
                        break
                elif col == 4:
                    # Category column
                    if operation.category not in filter_value:
                        passed = False
                        break
                elif col == 5:
                    # Subcategory column
                    if operation.subcategory not in filter_value:
                        passed = False
                        break
                elif col == 6:
                    # Description column - check if search term is in description (case insensitive)
                    if not (operation.description and filter_value.lower() in operation.description.lower()):
                        passed = False
                        break
                elif col == 7:
                    # Group column - use group_name for comparison (filter uses group names)
                    group_name = (
                        groups_dict.get(operation.group_id, operation.group_id) if operation.group_id else "N/A"
                    )
                    if group_name not in filter_value:
                        passed = False
                        break
                elif col == 8:
                    # Tags column - check if any of the operation's tags match any of the filter values (case insensitive)
                    if operation.tags:
                        # Convert filter values to lowercase for case-insensitive comparison
                        vals_lower = {val.lower() for val in filter_value}
                        # Check if any operation tag (lowercase) is in the filter values
                        if not any(tag.lower() in vals_lower for tag in operation.tags):
                            passed = False
                            break
                    else:
                        # Operation has no tags, filter it out if tags are being filtered
                        passed = False
                        break
            if passed:
                filtered.append(operation)
        return filtered

    def cell_change(self, row, column) -> None:
        """detects when a cell in a row has a change"""
        checkbox_column: int = self.operation_table_widget.columnCount() - 1
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

            # Get tags from the tags column (column 8)
            tags_text = self.operation_table_widget.item(row_idx, 8).text()
            cleaned_tags = clean_tags(tags_text)

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
                "group_id": self.operation_table_widget.item(row_idx, 7).data(
                    QtCore.Qt.UserRole
                ),  # Get the edited group_id
                "tags": cleaned_tags,  # Add cleaned tags
            }

            edited_op = OperationHandler(**row_data)
            try:
                edited_op.set_account_total(edit_flag=True, original_operation=original_op)
                cml = edited_op.set_cumulatives(edit_flag=True, original_operation=original_op)
                edited_op.save(cml)
                self.status_label.setText("<font color='green'>Change saved.</font>")
                animatedlabel.AnimatedLabel("Changes successfully saved ✅").display()
            except (ValueError, NegativeAccountTotalError):
                animatedlabel.AnimatedLabel("Edition not allowed!!", message_type="error").display()
                self.status_label.setText(
                    """<font color='red'>
                    Can not save this change because somewhere the cumulative amount becomes negative.
                    </font>"""
                )
        self.save_changes_button.setEnabled(False)
        # force update data in set_table by changing the self.current_account_index
        self.current_account_index = -1

        if self.accounts_comboBox.currentText() == "All":
            # self.set_True_all_operations_flag()
            self.operations_list = self.get_all_operations_data()

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
        error_flag = False
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
                try:
                    deletion = DeletionHandler(**op.model_dump())
                    deletion.set_account_total()
                    cml = deletion.set_cumulatives()
                    deletion.save(cml)
                except ValidationError as err_info:
                    print(err_info)
                    QTimer.singleShot(
                        1,
                        lambda: animatedlabel.AnimatedLabel(
                            "Could not delete operation: {op.operation_datetime}: {op.operation_type} - {op.amount}",
                            message_type="error",
                        ).display(),
                    )
                    self.status_label.setText(
                        """<font color='red'>
                        Can not delete this operation because the account total would become negative.
                        </font>"""
                    )
                    error_flag = True

            # QTimer used to deffer slightly the generation of the label to next iteration of the event loop, so the main
            # window get of focus again. Otherwise it will not appear.
            if not error_flag:
                QTimer.singleShot(
                    1, lambda: animatedlabel.AnimatedLabel("Operations deleted successfully ✅").display()
                )
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

    def refresh_groups_list(self) -> None:
        """Refresh the groups list for the combo box delegate and header filter"""
        try:
            groups = ListGroupsQuery(user_id=self.widget.user_object.user_id, status="open").execute()
            self.groups_list = [(group.group_id, group.group_name) for group in groups]
            # Update the delegate with the new groups list
            self.group_delegate.groups_list = self.groups_list
            # Update the header filter groups dictionary
            groups_dict = {group_id: group_name for group_id, group_name in self.groups_list}
            self.groups_dict = groups_dict
            # Update the header filter mixin with the new groups dictionary
            self.update_groups_dict(groups_dict)
        except Exception:
            self.groups_list = []
            self.group_delegate.groups_list = []
            self.groups_dict = {}
            self.update_groups_dict({})

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
