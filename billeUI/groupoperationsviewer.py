#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 25/04/2026 13:06

@author: igna
"""
from typing import List
from decimal import Decimal

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea

from src.queries.opqueries import GetOperationsByGroupQuery
from src.models.opmodel import UserOperations
from billeUI import currency_format


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

        # Create scroll area for operations
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allow the widget inside to resize with the scroll area
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Show horizontal scrollbar when needed
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Show vertical scrollbar when needed

        # Operations widget inside scroll area
        self.operations_widget = QWidget()
        self.operations_layout = QVBoxLayout(self.operations_widget)
        self.operations_layout.addStretch()  # Add stretch at the bottom to push content to the top

        self.scroll_area.setWidget(self.operations_widget)
        layout.addWidget(self.scroll_area)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        close_button.setMaximumWidth(100)  # Limit button width
        layout.addWidget(close_button)

        # Load operations
        self.load_operations()

    def calculate_balance(self, operations: List[UserOperations]) -> Decimal:
        """Calculate the balance for the group (income - expense)"""
        balance = Decimal("0")
        for operation in operations:
            if operation.operation_type == "income":
                balance += operation.amount
            elif operation.operation_type == "expense":
                balance -= operation.amount
            # Note: transfer operations typically don't affect group balance
            # but you can add logic here if needed
        return balance

    def update_balance_display(self, operations: List[UserOperations]) -> None:
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
            operations = GetOperationsByGroupQuery(
                user_id=self.user_id, group_id=self.group_id, order_by_datetime="DESC"
            ).execute()

            # Clear existing operations (but keep the stretch at the end)
            for i in reversed(range(self.operations_layout.count() - 1)):  # -1 to keep the stretch
                child = self.operations_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            if not operations:
                no_ops_label = QLabel("No operations found for this group.")
                no_ops_label.setAlignment(Qt.AlignCenter)
                no_ops_label.setWordWrap(True)
                self.operations_layout.insertWidget(self.operations_layout.count() - 1, no_ops_label)
                # Update balance display for empty operations list
                self.update_balance_display(operations)
                return

            # Display operations
            for operation in operations:
                op_widget = self.create_operation_widget(operation)
                self.operations_layout.insertWidget(self.operations_layout.count() - 1, op_widget)

            # Update balance display
            self.update_balance_display(operations)

        except Exception as e:
            error_label = QLabel(f"Error loading operations: {str(e)}")
            error_label.setStyleSheet("color: red;")
            error_label.setWordWrap(True)
            self.operations_layout.insertWidget(self.operations_layout.count() - 1, error_label)
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

    def create_operation_widget(self, operation: UserOperations) -> QWidget:
        """Create a widget to display a single operation"""
        widget = QWidget()
        widget.setStyleSheet(
            """
            QWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                background-color: #f9f9f9;
            }
        """
        )

        layout = QVBoxLayout(widget)

        # Operation details
        date_str = operation.operation_datetime.strftime("%d/%m/%Y %H:%M")
        amount_str = currency_format(operation.amount)
        amount_color = "green" if operation.operation_type == "income" else "red"

        details_html = f"""
        <b>Date:</b> {date_str}<br>
        <b>Account:</b> {operation.account_name or 'N/A'}<br>
        <b>Amount:</b> <font color="{amount_color}">{amount_str}</font><br>
        <b>Type:</b> {operation.operation_type}<br>
        <b>Category:</b> {operation.category or 'N/A'}<br>
        <b>Subcategory:</b> {operation.subcategory or 'N/A'}<br>
        <b>Description:</b> {operation.description or 'N/A'}
        """

        details_label = QLabel(details_html)
        details_label.setWordWrap(True)  # Enable text wrapping
        details_label.setTextFormat(Qt.RichText)  # Ensure rich text formatting
        details_label.setOpenExternalLinks(False)  # Prevent opening external links
        layout.addWidget(details_label)

        return widget

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
