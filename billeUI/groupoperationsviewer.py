#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 25/04/2026 13:06

@author: igna
"""
from typing import List, Optional
from decimal import Decimal

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTableView

from src.queries.opqueries import ListOperationsQuery
from src.models.opmodel import Operations
from billeUI import currency_format


class OperationsTableModel(QAbstractTableModel):
    """
    Model for displaying operations in a QTableView.
    Provides efficient data handling for large datasets using Qt's model/view architecture.
    """

    def __init__(self, operations: List[Operations] = None, parent=None):
        super().__init__(parent)
        self._operations = operations or []
        self._headers = ["Date", "Account", "Amount", "Type", "Category", "Subcategory", "Description"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of operations"""
        return len(self._operations)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns"""
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
        """
        Return data for the given index and role.
        Handles display text, background colors, and text alignment.
        """
        if not index.isValid():
            return None

        if index.row() >= len(self._operations) or index.column() >= len(self._headers):
            return None

        operation = self._operations[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            # Return display text for each column
            if column == 0:  # Date
                return operation.operation_datetime.strftime("%d/%m/%Y %H:%M")
            elif column == 1:  # Account
                return operation.account_name or "N/A"
            elif column == 2:  # Amount
                return currency_format(operation.amount)
            elif column == 3:  # Type
                return operation.operation_type
            elif column == 4:  # Category
                return operation.category or "N/A"
            elif column == 5:  # Subcategory
                return operation.subcategory or "N/A"
            elif column == 6:  # Description
                return operation.description or "N/A"

        elif role == Qt.BackgroundRole:
            # Set background color based on operation type
            if operation.operation_type == "income":
                return QColor(200, 255, 200)  # Light green
            elif operation.operation_type == "expense":
                return QColor(255, 200, 200)  # Light red
            elif operation.operation_type in ["transfer_in", "transfer_out"]:
                return QColor(200, 200, 255)  # Light blue

        elif role == Qt.ForegroundRole:
            # Set text color for amount column
            if column == 2:  # Amount column
                if operation.operation_type == "income":
                    return QColor("green")
                elif operation.operation_type == "expense":
                    return QColor("red")

        elif role == Qt.TextAlignmentRole:
            # Right-align numeric columns
            if column == 2:  # Amount column
                return Qt.AlignRight | Qt.AlignVCenter

        elif role == Qt.UserRole:
            # Store the full operation object for easy access
            return operation

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Optional[str]:
        """Return header data for the given section"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def set_operations(self, operations: List[Operations]) -> None:
        """
        Update the operations data in the model.
        Call beginResetModel() before and endResetModel() after updating data.
        """
        self.beginResetModel()
        self._operations = operations
        self.endResetModel()

    def get_operation_at_row(self, row: int) -> Optional[Operations]:
        """Get the operation object at the specified row"""
        if 0 <= row < len(self._operations):
            return self._operations[row]
        return None


class GroupOperationsViewer(QMainWindow):
    """
    Window to display all operations belonging to a specific group
    """

    def __init__(self, group_id: str, group_name: str, user_id: str, parent=None, widget=None) -> None:
        super(GroupOperationsViewer, self).__init__(parent)
        self.group_id = group_id
        self.group_name = group_name
        self.user_id = user_id
        self.widget = widget

        # Connect to parent group browser's groups_updated signal if parent is a GroupBrowserWidget
        if parent and hasattr(parent, "groups_updated"):
            parent.groups_updated.connect(self.update_group_name)

        # Create a simple UI programmatically since we don't have a UI file for this
        self.setWindowTitle(f"Operations for Group: {group_name}")
        self.setGeometry(200, 200, 800, 600)
        self.setMinimumSize(600, 400)  # Set minimum size for better UX

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Title label
        self.title_label = QLabel(f"<h2>Operations for Group: {group_name}</h2>")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)  # Make title wrap if window is too narrow
        layout.addWidget(self.title_label)

        # Balance label
        self.balance_label = QLabel("Calculating balance...")
        self.balance_label.setAlignment(Qt.AlignCenter)
        self.balance_label.setStyleSheet(
            """
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
        """
        )
        layout.addWidget(self.balance_label)

        # Create table view for operations
        self.operations_table = QTableView()
        self.operations_table.setAlternatingRowColors(True)  # Enable alternating row colors
        self.operations_table.setSelectionBehavior(QTableView.SelectRows)  # Select entire rows
        self.operations_table.setSelectionMode(QTableView.SingleSelection)  # Allow single row selection
        self.operations_table.setSortingEnabled(False)  # Disable sorting for now
        self.operations_table.horizontalHeader().setStretchLastSection(True)  # Stretch last column
        self.operations_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.operations_table.setWordWrap(True)  # Enable text wrapping in cells

        # Apply table styling
        self.operations_table.setStyleSheet(
            """
            QTableView {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableView::item {
                padding: 5px;
                border: none;
            }
            QTableView::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
            """
        )

        # Create and set the model
        self.operations_model = OperationsTableModel(parent=self)
        self.operations_table.setModel(self.operations_model)

        # Adjust column widths
        self.operations_table.setColumnWidth(0, 150)  # Date
        self.operations_table.setColumnWidth(1, 120)  # Account
        self.operations_table.setColumnWidth(2, 100)  # Amount
        self.operations_table.setColumnWidth(3, 80)  # Type
        self.operations_table.setColumnWidth(4, 100)  # Category
        self.operations_table.setColumnWidth(5, 100)  # Subcategory

        # Set row height for better readability
        self.operations_table.verticalHeader().setDefaultSectionSize(40)

        layout.addWidget(self.operations_table)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        close_button.setMaximumWidth(100)  # Limit button width
        layout.addWidget(close_button)

        # Load operations
        self.load_operations()

    def calculate_balance(self, operations: List[Operations]) -> Decimal:
        """Calculate the balance for the group (income - expense)"""
        balance = Decimal("0")
        for operation in operations:
            if operation.operation_type == "income":
                balance += operation.amount
            elif operation.operation_type == "expense":
                balance -= operation.amount
        return balance

    def update_balance_display(self, operations: List[Operations]) -> None:
        """Update the balance label with calculated balance"""
        if not operations:
            self.balance_label.setText("Balance: No operations")
            self.balance_label.setStyleSheet(
                """
                QLabel {
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 10px;
                    margin: 5px;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    color: #666666;
                }
            """
            )
            return

        balance = self.calculate_balance(operations)
        balance_str = currency_format(balance)

        if balance > 0:
            balance_text = f"Balance: {balance_str} (Positive)"
            color = "#28a745"  # Green
            bg_color = "#d4edda"
        elif balance < 0:
            balance_text = f"Balance: {balance_str} (Negative)"
            color = "#dc3545"  # Red
            bg_color = "#f8d7da"
        else:
            balance_text = f"Balance: {balance_str} (Balanced)"
            color = "#6c757d"  # Gray
            bg_color = "#e2e3e5"

        self.balance_label.setText(balance_text)
        self.balance_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 14pt;
                font-weight: bold;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
                background-color: {bg_color};
                color: {color};
                border: 2px solid {color};
            }}
        """
        )

    def load_operations(self) -> None:
        """Load and display all operations for this group"""
        try:
            operations = ListOperationsQuery(user_id=self.user_id).execute(group_id=self.group_id)

            # Update the model with the new operations
            self.operations_model.set_operations(operations)

            # Update balance display
            self.update_balance_display(operations)

        except Exception:
            # Show error in balance
            self.balance_label.setText("Balance: Error")
            self.balance_label.setStyleSheet(
                """
                QLabel {
                    font-size: 14pt;
                    font-weight: bold;
                    padding: 10px;
                    margin: 5px;
                    border-radius: 5px;
                    background-color: #f8d7da;
                    color: #dc3545;
                    border: 2px solid #dc3545;
                }
            """
            )
            # Clear the model to show no data
            self.operations_model.set_operations([])

    def update_group_name(self) -> None:
        """Update the group name and window title when group is modified"""
        try:
            # Fetch the updated group information from database
            from src.models.opgroupsmodel import OperationGroups

            updated_group = OperationGroups.get_group_by_id(self.user_id, self.group_id)
            self.group_name = updated_group.group_name

            # Update the window title
            self.setWindowTitle(f"Operations for Group: {self.group_name}")

            # Update the title label if it exists
            if hasattr(self, "title_label"):
                self.title_label.setText(f"<h2>Operations for Group: {self.group_name}</h2>")

        except Exception:
            # If we can't fetch the updated group, keep the current name
            pass

    def close(self) -> None:
        """Close the window"""
        super().close()

    def keyPressEvent(self, e) -> None:
        """Returns to the OperationScreen Menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
