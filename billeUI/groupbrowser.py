#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 21/12/2025 11:56
Edited with devin 24/04/2026
@author: igna
"""
import os
import sqlite3
from decimal import Decimal

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QMessageBox,
    QWidget,
    QLabel,
    QFrame,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QRadioButton,
    QTextEdit,
    QGridLayout,
    QDialog,
    QComboBox,
)
from src.models.opmodel import InvalidAccountNameError
from src.models.opgroupsmodel import OperationGroups
from src.commands.groupcommands import (
    CreateOperationGroupCommand,
    DeleteOperationGroupCommand,
    EditOperationGroupCommand,
)
from src.queries.opqueries import GetOperationsByGroupQuery
from src.queries.accqueries import ListAccountsQuery

from billeUI import UISPATH, ICONSPATH, animatedlabel, groupoperationsviewer, currency_format


class GroupDataRow(QWidget):

    group_modified = pyqtSignal(str, dict, bool)  # group_id, changed_fields_dict, is_modified
    group_double_clicked = pyqtSignal(str, str)  # group_id, group_name

    def __init__(self, group: OperationGroups, user_id: str, parent=None):
        super().__init__(parent)
        # Needed for the hover effect
        self.group = group
        self.user_id = user_id
        self.group_id = group.group_id
        self.group_name = group.group_name
        self.group_currency = group.group_currency or ""
        self.category = group.category or ""
        self.subcategory = group.subcategory or ""
        self.description = group.description or ""

        # Store original values for comparison
        self.original_values = {
            "group_name": self.group_name,
            "group_currency": self.group_currency,
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
        }

        self.new_values = {}
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)

        # Minimal card frame with clean styling
        self.frame = QFrame(self)
        self.frame.setObjectName("GroupRowFrame")
        self.frame.setStyleSheet(
            """
            QFrame#GroupRowFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin: 2px;
            }
            QFrame#GroupRowFrame:hover {
                background-color: #f8f9fa;
                border: 1px solid #d0d0d0;
            }
        """
        )

        # Clean, readable fonts
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)

        body_font = QFont()
        body_font.setPointSize(9)

        balance_font = QFont()
        balance_font.setPointSize(9)
        balance_font.setBold(True)

        # Group name (clean and prominent)
        self.name_label = QLabel(f"{self.group_name}")
        self.name_label.setFont(title_font)
        self.name_label.setStyleSheet("color: #333;")
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setText(self.group_name)
        self.name_line_edit.setPlaceholderText("Group name")
        self.name_line_edit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
        """
        )
        self.name_line_edit.hide()
        self.name_line_edit.returnPressed.connect(self.show_qlabel)
        self.name_line_edit.installEventFilter(self)

        # Category and Subcategory (compact, side by side)
        self.category_label = QLabel(f"Cat: {self.category or 'N/A'}")
        self.category_label.setFont(body_font)
        self.category_label.setStyleSheet("color: #666;")
        self.category_line_edit = QLineEdit(self)
        self.category_line_edit.setText(self.category)
        self.category_line_edit.setPlaceholderText("Category")
        self.category_line_edit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
        """
        )
        self.category_line_edit.hide()
        self.category_line_edit.returnPressed.connect(self.show_qlabel)
        self.category_line_edit.installEventFilter(self)

        self.subcategory_label = QLabel(f"Sub: {self.subcategory or 'N/A'}")
        self.subcategory_label.setFont(body_font)
        self.subcategory_label.setStyleSheet("color: #666;")
        self.subcategory_line_edit = QLineEdit(self)
        self.subcategory_line_edit.setText(self.subcategory)
        self.subcategory_line_edit.setPlaceholderText("Subcategory")
        self.subcategory_line_edit.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
        """
        )
        self.subcategory_line_edit.hide()
        self.subcategory_line_edit.returnPressed.connect(self.show_qlabel)
        self.subcategory_line_edit.installEventFilter(self)

        description_text = self.description or "No description"
        self.description_label = QLabel(
            f"Desc: {description_text[:30]}..." if len(description_text) > 30 else f"Desc: {description_text}"
        )
        self.description_label.setFont(body_font)
        self.description_label.setStyleSheet("color: #888; font-style: italic;")
        self.description_label.hide()  # Hidden by default
        self.description_label.setToolTip(self.description or "No description")
        self.description_line_edit = QTextEdit(self)
        self.description_line_edit.setText(self.description)
        self.description_line_edit.setPlaceholderText("Description")
        self.description_line_edit.setMaximumHeight(50)
        self.description_line_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
        """
        )
        self.description_line_edit.hide()
        self.description_line_edit.installEventFilter(self)

        # Balance (minimal with simple color coding)
        balance = self.calculate_group_balance()
        balance_str = currency_format(balance)
        balance_color = "#28a745" if balance > 0 else "#dc3545" if balance < 0 else "#6c757d"
        self.balance_label = QLabel(f"{balance_str}")
        self.balance_label.setFont(balance_font)
        self.balance_label.setStyleSheet(f"color: {balance_color};")
        self.balance_label.setAlignment(Qt.AlignCenter)

        # Currency label
        self.currency_label = QLabel(f"{self.group_currency}")
        self.currency_label.setFont(body_font)
        self.currency_label.setStyleSheet("color: #007bff; font-weight: bold;")
        self.currency_label.setAlignment(Qt.AlignCenter)

        # Buttons with minimal styling
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon(os.path.join(ICONSPATH, "edit.svg")))
        self.edit_btn.clicked.connect(self.enable_edit_mode)
        self.edit_btn.setToolTip("Edit group")
        self.edit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(os.path.join(ICONSPATH, "delete.svg")))
        self.delete_btn.setToolTip("Delete group")
        self.delete_btn.clicked.connect(self.delete_group)
        self.delete_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )

        # self.disable_btn = QPushButton()
        # self.disable_btn.setIcon(QIcon(os.path.join(ICONSPATH, "disable.svg")))
        # self.disable_btn.setToolTip("Disable account")

        self.enable_disable_btn = QRadioButton()
        self.enable_disable_btn.setToolTip("Disable group")
        self.enable_disable_btn.setStyleSheet(
            """
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
        """
        )

        # Minimal grid layout for compact arrangement
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(8, 6, 8, 6)
        grid_layout.setSpacing(6)

        # Row 0: Group name (spans all columns)
        grid_layout.addWidget(self.name_label, 0, 0, 1, 5)
        grid_layout.addWidget(self.name_line_edit, 0, 0, 1, 5)

        # Row 1: Category | Subcategory | Balance | Currency (4 columns)
        grid_layout.addWidget(self.category_label, 1, 0)
        grid_layout.addWidget(self.category_line_edit, 1, 0)
        grid_layout.addWidget(self.subcategory_label, 1, 1)
        grid_layout.addWidget(self.subcategory_line_edit, 1, 1)
        grid_layout.addWidget(self.balance_label, 1, 2)
        grid_layout.addWidget(self.currency_label, 1, 3)

        # Row 2: Description (hidden by default, spans all columns)
        grid_layout.addWidget(self.description_label, 2, 0, 1, 5)
        grid_layout.addWidget(self.description_line_edit, 2, 0, 1, 5)

        # Buttons in horizontal layout at the bottom right with extra margins
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.enable_disable_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.setContentsMargins(8, 8, 8, 8)  # Add extra space around buttons

        # Main vertical layout
        main_layout = QVBoxLayout(self.frame)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(btn_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)

    def calculate_group_balance(self) -> Decimal:
        """Calculate the balance for the group (income - expense)"""
        try:
            operations = GetOperationsByGroupQuery(
                user_id=self.user_id, group_id=self.group_id, order_by_datetime="DESC"
            ).execute()

            balance = Decimal("0")
            for operation in operations:
                if operation.operation_type == "income":
                    balance += operation.amount
                elif operation.operation_type == "expense":
                    balance -= operation.amount
            return balance
        except Exception:
            return Decimal("0")

    def refresh_balance(self) -> None:
        """Refresh the balance display with minimal styling"""
        balance = self.calculate_group_balance()
        balance_str = currency_format(balance)
        balance_color = "#28a745" if balance > 0 else "#dc3545" if balance < 0 else "#6c757d"
        self.balance_label.setText(f"{balance_str}")
        self.balance_label.setStyleSheet(f"color: {balance_color}; font-weight: bold;")

    def refresh_group_info(self) -> None:
        """Refresh all group information from the database"""
        try:
            updated_group = OperationGroups.get_group_by_id(self.user_id, self.group_id)
            self.group = updated_group

            # Update stored values
            self.group_name = updated_group.group_name
            self.group_currency = updated_group.group_currency or ""
            self.category = updated_group.category or ""
            self.subcategory = updated_group.subcategory or ""
            self.description = updated_group.description or ""

            # Update original values to match database
            self.original_values = {
                "group_name": self.group_name,
                "group_currency": self.group_currency,
                "category": self.category,
                "subcategory": self.subcategory,
                "description": self.description,
            }

            # Update labels with minimal styling
            self.name_label.setText(f"{self.group_name}")
            self.name_label.setStyleSheet("color: #333; font-weight: bold;")
            self.currency_label.setText(f"{self.group_currency}")
            self.currency_label.setStyleSheet("color: #007bff; font-weight: bold;")
            self.category_label.setText(f"Cat: {self.category or 'N/A'}")
            self.category_label.setStyleSheet("color: #666;")
            self.subcategory_label.setText(f"Sub: {self.subcategory or 'N/A'}")
            self.subcategory_label.setStyleSheet("color: #666;")

            description_text = self.description or "No description"
            self.description_label.setText(
                f"Desc: {description_text[:30]}..." if len(description_text) > 30 else f"Desc: {description_text}"
            )
            self.description_label.setToolTip(self.description or "No description")
            self.description_label.setStyleSheet("color: #888; font-style: italic;")
            self.description_label.hide()  # Keep description hidden by default

            # Update line edit values too
            self.name_line_edit.setText(self.group_name)
            self.category_line_edit.setText(self.category)
            self.subcategory_line_edit.setText(self.subcategory)
            self.description_line_edit.setText(self.description)

            # Update balance with minimal styling
            self.refresh_balance()

        except Exception:
            pass

    def enable_edit_mode(self) -> None:
        """Enables the edition of all group fields"""
        self.name_label.hide()
        self.name_line_edit.show()
        self.name_line_edit.setFocus()
        self.name_line_edit.selectAll()

        self.category_label.hide()
        self.category_line_edit.show()

        self.subcategory_label.hide()
        self.subcategory_line_edit.show()

        self.description_label.hide()
        self.description_line_edit.show()

    def cancel_edit_mode(self) -> None:
        """Cancels edit mode and reverts to labels without saving changes"""
        # Reset line edit values to original values
        self.name_line_edit.setText(self.group_name)
        self.category_line_edit.setText(self.category)
        self.subcategory_line_edit.setText(self.subcategory)
        self.description_line_edit.setText(self.description)

        # Hide line edits and show labels
        self.name_line_edit.hide()
        self.name_label.show()
        self.category_line_edit.hide()
        self.category_label.show()
        self.subcategory_line_edit.hide()
        self.subcategory_label.show()
        self.description_line_edit.hide()
        self.description_label.hide()  # Hide description label after canceling

        # Clear focus from line edits to ensure proper event propagation
        self.name_line_edit.clearFocus()
        self.category_line_edit.clearFocus()
        self.subcategory_line_edit.clearFocus()
        self.description_line_edit.clearFocus()
        self.setFocus()  # Set focus to the parent widget

    def show_qlabel(self) -> None:
        """Resets the labels with the new values"""
        # Get new values from line edits
        new_name = self.name_line_edit.text().strip()
        new_category = self.category_line_edit.text().strip()
        new_subcategory = self.subcategory_line_edit.text().strip()
        new_description = self.description_line_edit.toPlainText().strip()

        # Update labels with minimal styling
        self.name_label.setText(f"{new_name}")
        self.category_label.setText(f"Cat: {new_category or 'N/A'}")
        self.subcategory_label.setText(f"Sub: {new_subcategory or 'N/A'}")

        description_text = new_description or "No description"
        self.description_label.setText(
            f"Desc: {description_text[:30]}..." if len(description_text) > 30 else f"Desc: {description_text}"
        )
        self.description_label.setToolTip(new_description or "No description")

        # Check if each field changed and apply individual styling
        changed_fields = {}

        # Name field styling
        if new_name != self.original_values["group_name"]:
            changed_fields["group_name"] = new_name
            self.name_label.setStyleSheet("color: #e67e22; font-weight: bold; font-style: italic;")
        else:
            self.name_label.setStyleSheet("color: #333; font-weight: bold;")

        # Category field styling
        if new_category != self.original_values["category"]:
            changed_fields["category"] = new_category
            self.category_label.setStyleSheet("color: #e67e22; font-weight: bold; font-style: italic;")
        else:
            self.category_label.setStyleSheet("color: #666;")

        # Subcategory field styling
        if new_subcategory != self.original_values["subcategory"]:
            changed_fields["subcategory"] = new_subcategory
            self.subcategory_label.setStyleSheet("color: #e67e22; font-weight: bold; font-style: italic;")
        else:
            self.subcategory_label.setStyleSheet("color: #666;")

        # Description field styling
        if new_description != self.original_values["description"]:
            changed_fields["description"] = new_description
            self.description_label.setStyleSheet("color: #e67e22; font-weight: bold; font-style: italic;")
        else:
            self.description_label.setStyleSheet("color: #888; font-style: italic;")

        is_modified = len(changed_fields) > 0
        self.new_values = changed_fields

        # Hide line edits and show labels
        self.name_line_edit.hide()
        self.name_label.show()
        self.category_line_edit.hide()
        self.category_label.show()
        self.subcategory_line_edit.hide()
        self.subcategory_label.show()
        self.description_line_edit.hide()
        self.description_label.hide()  # Hide description label after editing

        # Emit signal with changed fields
        self.group_modified.emit(self.group_id, changed_fields, is_modified)

    def delete_group(self) -> None:
        confirmation_message = """
        Are you really sure you want to delete the selected group?
        All the information will be lost and will not be recoverable.
        """
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            confirmation_message,
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            DeleteOperationGroupCommand(user_id=self.group.user_id, group_id=self.group.group_id).execute()
            # refresh view without the deleted widget
            animatedlabel.AnimatedLabel("Group deleted ✅").display()
            parent_layout = self.parentWidget().layout()
            parent_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

            # Notify parent widget that groups have changed
            if hasattr(self.parentWidget(), "groups_updated"):
                self.parentWidget().groups_updated.emit()
            # Also notify the main widget to refresh all open windows
            parent = self.parentWidget()
            if parent and hasattr(parent, "widget") and hasattr(parent.widget, "refresh_all_groups"):
                parent.widget.refresh_all_groups()

    def enable_n_disable_group(self) -> None:
        """not implemented"""
        pass

    def refresh_account_data(self) -> None:
        self.group = OperationGroups.get_groups_list(user_id=self.group.user_id).execute()

    def mouseDoubleClickEvent(self, event):
        """Handle double-click event to show group operations"""
        if event.button() == Qt.LeftButton:
            self.group_double_clicked.emit(self.group_id, self.group_name)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:
        """Handle key press events"""
        # Check if we're in edit mode (any line edit is visible)
        in_edit_mode = (
            self.name_line_edit.isVisible()
            or self.category_line_edit.isVisible()
            or self.subcategory_line_edit.isVisible()
            or self.description_line_edit.isVisible()
        )

        if in_edit_mode and event.key() == QtCore.Qt.Key_Escape:
            # Cancel edit mode without saving
            self.cancel_edit_mode()
        else:
            # Let the parent handle other keys (including ESC when not in edit mode)
            super().keyPressEvent(event)

    def eventFilter(self, obj, event) -> bool:
        """Event filter to handle ESC key in line edits"""
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                # Check if we're actually in edit mode
                in_edit_mode = (
                    self.name_line_edit.isVisible()
                    or self.category_line_edit.isVisible()
                    or self.subcategory_line_edit.isVisible()
                    or self.description_line_edit.isVisible()
                )

                if in_edit_mode:
                    # Cancel edit mode when ESC is pressed in any line edit
                    self.cancel_edit_mode()
                    return True  # Event handled
                # If not in edit mode, let the event propagate to parent
        return super().eventFilter(obj, event)

    def enterEvent(self, event) -> None:
        """Show description on hover"""
        if self.description and not self.description_line_edit.isVisible():
            self.description_label.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Hide description when not hovering"""
        if not self.description_line_edit.isVisible():
            self.description_label.hide()
        super().leaveEvent(event)


class CreateGroupDialog(QDialog):
    """Dialog for creating a new operation group"""

    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Create New Group")
        self.setModal(True)
        self.setFixedSize(400, 400)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Create New Group")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Form layout
        form_layout = QGridLayout()
        form_layout.setSpacing(8)

        # Group name (required)
        name_label = QLabel("Group Name *:")
        name_label.setStyleSheet("color: #333; font-weight: bold;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter group name")
        form_layout.addWidget(name_label, 0, 0)
        form_layout.addWidget(self.name_edit, 0, 1)

        # Currency (required)
        currency_label = QLabel("Currency *:")
        currency_label.setStyleSheet("color: #333; font-weight: bold;")
        self.currency_combo = QComboBox()
        self.currency_combo.setStyleSheet(
            """
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
                background: white;
            }
        """
        )
        # Get available currencies from accounts
        currencies = self.get_currency_list()
        self.currency_combo.addItems(currencies)
        form_layout.addWidget(currency_label, 1, 0)
        form_layout.addWidget(self.currency_combo, 1, 1)

        # Category (optional)
        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #666;")
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Enter category (optional)")
        form_layout.addWidget(category_label, 2, 0)
        form_layout.addWidget(self.category_edit, 2, 1)

        # Subcategory (optional)
        subcategory_label = QLabel("Subcategory:")
        subcategory_label.setStyleSheet("color: #666;")
        self.subcategory_edit = QLineEdit()
        self.subcategory_edit.setPlaceholderText("Enter subcategory (optional)")
        form_layout.addWidget(subcategory_label, 3, 0)
        form_layout.addWidget(self.subcategory_edit, 3, 1)

        # Description (optional)
        description_label = QLabel("Description:")
        description_label.setStyleSheet("color: #666;")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter description (optional)")
        self.description_edit.setMaximumHeight(60)
        form_layout.addWidget(description_label, 4, 0)
        form_layout.addWidget(self.description_edit, 4, 1)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        )

        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create_group)
        create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 1px solid #218838;
                border-radius: 3px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """
        )

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        layout.addLayout(button_layout)

    def get_currency_list(self) -> list[str]:
        """Get list of available currencies from user accounts"""
        try:
            acc_list = ListAccountsQuery(user_id=self.user_id).execute()
            currencies_list = list({account.account_currency for account in acc_list})
            currencies_list.sort()
            return currencies_list if currencies_list else ["USD", "EUR", "ARS"]  # Default currencies if no accounts
        except Exception:
            return ["USD", "EUR", "ARS"]  # Default currencies

    def create_group(self) -> None:
        """Create the new group with the entered data"""
        group_name = self.name_edit.text().strip()
        currency = self.currency_combo.currentText().strip()

        if not group_name:
            QMessageBox.warning(self, "Validation Error", "Group name is required!")
            self.name_edit.setFocus()
            return

        if not currency:
            QMessageBox.warning(self, "Validation Error", "Currency is required!")
            self.currency_combo.setFocus()
            return

        try:
            # Create the group using the command
            command = CreateOperationGroupCommand(
                user_id=self.user_id,
                group_name=group_name,
                group_currency=currency,
                category=self.category_edit.text().strip() or None,
                subcategory=self.subcategory_edit.text().strip() or None,
                description=self.description_edit.toPlainText().strip() or None,
            )
            command.execute()
            animatedlabel.AnimatedLabel("Group created successfully! ✅", message_type="success").display()
            self.accept()
        except sqlite3.OperationalError:
            animatedlabel.AnimatedLabel("Group name already exists!", message_type="error").display()
        except InvalidAccountNameError:
            animatedlabel.AnimatedLabel("Invalid group name!", message_type="error").display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create group: {str(e)}")


class GroupBrowserWidget(QWidget):
    """
    group browser and editor
    """

    # Signal emitted when groups are updated (name changed, deleted, etc.)
    groups_updated = pyqtSignal()

    def __init__(self, parent=None, widget=None) -> None:
        super(GroupBrowserWidget, self).__init__(parent)
        group_browser = os.path.join(UISPATH, "opgroups_browser_widget.ui")
        loadUi(group_browser, self)
        self.widget = widget

        self.user_id = self.widget.user_object.user_id

        self.group_changed = set()
        self.group_row_list = []
        self.all_groups = []  # Store all groups for search functionality

        self.save_changes_button.setEnabled(False)
        self.save_changes_button.clicked.connect(self.save_group_changes)

        self.add_group_button.clicked.connect(self.show_create_group_dialog)

        self.close_button.clicked.connect(self.close_group_widget)

        # Search functionality
        self.search_line_edit = self.findChild(QLineEdit, "search_line_edit")
        self.search_line_edit.textChanged.connect(self.filter_groups)

        self.group_object = OperationGroups.get_groups_list(user_id=self.widget.user_object.user_id)
        self.all_groups = list(self.group_object)  # Store all groups

        self.scroll_content = self.findChild(QWidget, "scrollAreaWidgetContents")
        self.scroll_layout = self.scroll_content.layout()

        self.refresh_groups_display()

        # Connect to our own groups_updated signal to refresh balances
        self.groups_updated.connect(self.refresh_all_balances)

    def save_group_changes(self) -> None:
        """loops through all group_ids in the group_changed set and saves the changes into the db"""
        row_to_be_saved = [row for row in self.group_row_list if row.group_id in self.group_changed]
        changes_saved = False
        for row in row_to_be_saved:
            try:
                # Build command with all changed fields
                command_params = {"user_id": self.user_id, "group_id": row.group_id}

                # Add only the fields that were changed
                if "group_name" in row.new_values:
                    command_params["group_name"] = row.new_values["group_name"]
                if "category" in row.new_values:
                    command_params["category"] = row.new_values["category"]
                if "subcategory" in row.new_values:
                    command_params["subcategory"] = row.new_values["subcategory"]
                if "description" in row.new_values:
                    command_params["description"] = row.new_values["description"]

                EditOperationGroupCommand(**command_params).execute()

                # Reset all label styling to minimal design after saving
                row.name_label.setStyleSheet("color: #333; font-weight: bold;")
                row.category_label.setStyleSheet("color: #666;")
                row.subcategory_label.setStyleSheet("color: #666;")
                row.description_label.setStyleSheet("color: #888; font-style: italic;")

                # Update the row's stored values
                if "group_name" in row.new_values:
                    row.group_name = row.new_values["group_name"]
                    row.original_values["group_name"] = row.new_values["group_name"]
                if "category" in row.new_values:
                    row.category = row.new_values["category"]
                    row.original_values["category"] = row.new_values["category"]
                if "subcategory" in row.new_values:
                    row.subcategory = row.new_values["subcategory"]
                    row.original_values["subcategory"] = row.new_values["subcategory"]
                if "description" in row.new_values:
                    row.description = row.new_values["description"]
                    row.original_values["description"] = row.new_values["description"]

                row.new_values = {}  # Clear new values after saving
                row.refresh_group_info()  # Refresh all group information including balance
                animatedlabel.AnimatedLabel("Changes saved! ✅", message_type="success").display()
                changes_saved = True
            except sqlite3.OperationalError:
                animatedlabel.AnimatedLabel("Duplicated name!", message_type="error").display()
            except InvalidAccountNameError:
                animatedlabel.AnimatedLabel("Invalid name!", message_type="error").display()

        if changes_saved:
            self.group_changed.clear()  # Clear the set after successfully saving changes
            self.save_changes_button.setEnabled(False)
            self.groups_updated.emit()  # Notify other components that groups have changed
            # Also notify the main widget to refresh all open windows
            if hasattr(self.widget, "refresh_all_groups"):
                self.widget.refresh_all_groups()
            # Update any open GroupOperationsViewer windows with the new names
            if hasattr(self, "open_viewers"):
                for viewer in self.open_viewers:
                    if viewer.isVisible():
                        viewer.update_group_name()
            # Refresh all group rows to update balances
            for row in self.group_row_list:
                row.refresh_balance()

    def add_group(self, group: OperationGroups) -> GroupDataRow:
        row = GroupDataRow(group, self.user_id)
        row.group_modified.connect(self.handle_group_modified)
        row.group_double_clicked.connect(self.handle_group_double_clicked)
        self.scroll_layout.addWidget(row)
        return row

    def refresh_groups_display(self) -> None:
        """Clear and refresh the groups display"""
        # Clear existing rows
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.group_row_list.clear()

        # Add groups
        for group in self.group_object:
            row = self.add_group(group)
            self.group_row_list.append(row)

    def refresh_all_balances(self) -> None:
        """Refresh the balance display for all group rows"""
        for row in self.group_row_list:
            row.refresh_balance()

    def filter_groups(self, search_text: str) -> None:
        """Filter groups based on search text"""
        search_text = search_text.lower().strip()

        if not search_text:
            # Show all groups
            self.group_object = self.all_groups
        else:
            # Filter groups by name
            self.group_object = [group for group in self.all_groups if search_text in group.group_name.lower()]

        self.refresh_groups_display()

    def handle_group_double_clicked(self, group_id: str, group_name: str) -> None:
        """Handle double-click on a group to show its operations"""
        try:
            operations_viewer = groupoperationsviewer.GroupOperationsViewer(
                group_id=group_id, group_name=group_name, user_id=self.user_id, parent=self, widget=self.widget
            )
            # Store reference to the viewer so we can update it when group name changes
            if not hasattr(self, "open_viewers"):
                self.open_viewers = []
            # Clean up closed viewers
            self.open_viewers = [v for v in self.open_viewers if v.isVisible()]
            self.open_viewers.append(operations_viewer)
            operations_viewer.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open operations viewer: {str(e)}")

    def handle_group_modified(self, group_id: str, changed_fields: dict, is_modified: bool) -> None:
        if is_modified:
            self.group_changed.add(group_id)
        else:
            self.group_changed.discard(group_id)
        self.save_changes_button.setEnabled(len(self.group_changed) > 0)

    def show_create_group_dialog(self) -> None:
        """Show the dialog to create a new group"""
        dialog = CreateGroupDialog(self.user_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # Refresh the groups list to show the new group
            self.group_object = OperationGroups.get_groups_list(user_id=self.widget.user_object.user_id)
            self.all_groups = list(self.group_object)
            self.refresh_groups_display()
            # Notify other components that groups have changed
            self.groups_updated.emit()
            if hasattr(self.widget, "refresh_all_groups"):
                self.widget.refresh_all_groups()

    def close_group_widget(self) -> None:
        """Returns to the OperationScreen Menu"""
        self.close()

    def keyPressEvent(self, e):
        """Returns to the OperationScreen Menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            self.close_group_widget()
