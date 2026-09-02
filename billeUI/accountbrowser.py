#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 15/07/2025 21:17

@author: igna
"""

import os
import sqlite3

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QFrame,
    QWidget,
    QLineEdit,
    QPushButton,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QRadioButton,
)

from src.models.accmodel import Accounts, InvalidAccountNameError
from src.queries.accqueries import ListAccountsQuery, GetAccountByIDQuery
from src.commands.acccommands import EditAccountCommand, DeleteAccountCommand

from billeUI import operationscreen, currency_format, animatedlabel
from billeUI import UISPATH, ICONSPATH
from billeUI.accountdetailsdialog import AccountDetailsDialog
from billeUI.taglabel import TagContainer


def clean_tags(tags: str) -> tuple | None:
    """
    Clean up tag string by removing empty segments and extra spaces.

    Args:
        tags: Raw tag string (e.g., "hi,,yes, , no")

    Returns:
        Cleaned tag tuple (e.g., ("hi", "yes", "no")) or None if empty

    Examples:
        "hi,,yes, , no" -> ("hi", "yes", "no")
        "  tag1  ,  tag2  " -> ("tag1", "tag2")
        "" -> None
        "single" -> ("single",)
    """
    if not tags:
        return None

    # Split by comma and strip whitespace from each segment
    segments = [tag.strip() for tag in tags.split(",")]

    # Filter out empty segments
    clean_segments = tuple([tag for tag in segments if tag])

    return clean_segments if clean_segments else None


class AccountRow(QWidget):

    account_modified = pyqtSignal(str, str, tuple, bool)
    account_deleted = pyqtSignal(str)  # Signal when account is deleted

    def __init__(self, account: Accounts, parent=None):
        super().__init__(parent)
        # Needed for the hover effect
        self.account = account
        self.account_id = account.account_id
        self.account_name = account.account_name
        self.account_tags = account.tags
        self.new_acc_name = ""
        self.new_acc_tags = None
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.frame = QFrame(self)
        self.frame.setObjectName("AccountRowFrame")
        self.frame.setStyleSheet(
            """
            QFrame#AccountRowFrame {
                background-color: transparent;
                border-radius: 6px;
            }
            QFrame#AccountRowFrame:hover {
                background-color: #e6f2ff;
                border: 1px solid #cccccc;
            }
        """
        )

        # Labels
        font = QFont()
        font.setPointSize(11)

        # name_line
        self.name_label = QLabel(f"<b>{self.account_name}</b>")
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setText(self.account_name)
        self.name_line_edit.hide()
        self.name_line_edit.returnPressed.connect(self.move_to_tags_edit)
        self.balance_label = QLabel(f"{currency_format(account.account_total)} {account.account_currency}")
        self.balance_label.setFont(font)

        # tags_line
        self.tags_container = TagContainer(self.account_tags, show_close_buttons=False)
        self.tags_line_edit = QLineEdit(self)
        self.tags_line_edit.setText(",".join(self.account_tags) if self.account_tags else "")
        self.tags_line_edit.setPlaceholderText("Enter tags (comma-separated)")
        self.tags_line_edit.hide()
        self.tags_line_edit.returnPressed.connect(self.show_qlabel)

        # Buttons and Icons
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon(os.path.join(ICONSPATH, "edit.svg")))
        self.edit_btn.clicked.connect(self.enable_edit_mode)
        self.edit_btn.setToolTip("Edit account")

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(os.path.join(ICONSPATH, "delete.svg")))
        self.delete_btn.setToolTip("Delete account")
        self.delete_btn.clicked.connect(self.delete_account)

        # self.disable_btn = QPushButton()
        # self.disable_btn.setIcon(QIcon(os.path.join(ICONSPATH, "disable.svg")))
        # self.disable_btn.setToolTip("Disable account")

        self.enable_disable_btn = QRadioButton()
        self.enable_disable_btn.setToolTip("Disable account")
        if account.is_active:
            self.enable_disable_btn.setChecked(True)
        self.enable_disable_btn.clicked.connect(self.enable_n_disable_account)

        # Layouts
        self.text_layout = QVBoxLayout()
        self.text_layout.addWidget(self.name_label)
        self.text_layout.addWidget(self.name_line_edit)
        self.text_layout.addWidget(self.tags_container)
        self.text_layout.addWidget(self.tags_line_edit)
        self.text_layout.addWidget(self.balance_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.enable_disable_btn)

        inner_layout = QHBoxLayout()
        inner_layout.addLayout(self.text_layout)
        inner_layout.addStretch()
        inner_layout.addLayout(btn_layout)
        inner_layout.setContentsMargins(5, 3, 5, 3)

        self.frame.setLayout(inner_layout)

        # outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)

    def enable_edit_mode(self) -> None:
        """Enables the edition of the account name and tags"""
        self.name_label.hide()
        self.name_line_edit.show()
        self.tags_container.hide()
        self.tags_line_edit.show()
        self.name_line_edit.setFocus()
        self.name_line_edit.selectAll()

    def move_to_tags_edit(self) -> None:
        """Moves focus from name line edit to tags line edit"""
        self.tags_line_edit.setFocus()
        self.tags_line_edit.selectAll()

    def cancel_edit_mode(self) -> None:
        """Cancels edit mode and reverts to original values"""
        self.name_line_edit.setText(self.account_name)
        self.tags_line_edit.setText(",".join(self.account_tags) if self.account_tags else "")
        self.name_line_edit.hide()
        self.tags_line_edit.hide()
        self.name_label.show()
        self.tags_container.show()

    def show_qlabel(self) -> None:
        """Resets the label with the new values"""
        self.new_acc_name = self.name_line_edit.text().replace(" ", "")
        tags_input = self.tags_line_edit.text()

        # Clean up tags (remove empty segments and extra spaces)
        cleaned_tags = clean_tags(tags_input)

        # Convert empty tags to None to satisfy validation
        self.new_acc_tags = cleaned_tags if cleaned_tags else None

        # Update name label
        self.name_label.setText(self.new_acc_name)

        # Update tags container by replacing it with a new one
        old_tags_index = self.text_layout.indexOf(self.tags_container)
        self.tags_container.deleteLater()
        self.tags_container = TagContainer(self.new_acc_tags, show_close_buttons=False)
        self.text_layout.insertWidget(old_tags_index, self.tags_container)

        # Check if anything changed
        name_changed = self.new_acc_name != self.account_name
        tags_changed = self.new_acc_tags != self.account_tags

        if name_changed or tags_changed:
            self.name_label.setStyleSheet("color: orange; font-weight: bold; font-style: italic;")
            # Convert None to empty tuple for signal emission
            tags_to_emit = self.new_acc_tags if self.new_acc_tags is not None else ()
            self.account_modified.emit(self.account_id, self.new_acc_name, tags_to_emit, True)
        else:
            self.name_label.setStyleSheet("color: black; font-weight: bold;")
            # Convert None to empty tuple for signal emission
            tags_to_emit = self.account_tags if self.account_tags is not None else ()
            self.account_modified.emit(self.account_id, self.account_name, tags_to_emit, False)

        self.name_line_edit.hide()
        self.tags_line_edit.hide()
        self.name_label.show()
        self.tags_container.show()

    def delete_account(self) -> None:
        confirmation_message = """
        Are you really sure you want to delete the selected account?
        All the information will be lost and will not be recoverable.
        """
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            confirmation_message,
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            DeleteAccountCommand(user_id=self.account.user_id, account_id=self.account.account_id).execute()
            # refresh view without the deleted widget
            animatedlabel.AnimatedLabel("Account deleted ✅").display()
            parent_layout = self.parentWidget().layout()
            parent_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()
            # Emit signal to notify parent
            self.account_deleted.emit(self.account_id)

    def enable_n_disable_account(self) -> None:
        if self.account.is_active:
            EditAccountCommand(
                user_id=self.account.user_id, account_id=self.account.account_id, is_active=False
            ).execute()
            animatedlabel.AnimatedLabel("Account disabled! ✅", message_type="warning").display()
        else:
            EditAccountCommand(
                user_id=self.account.user_id, account_id=self.account.account_id, is_active=True
            ).execute()
            animatedlabel.AnimatedLabel("Account enabled! ✅").display()
        self.refresh_account_data()

    def refresh_account_data(self) -> None:
        self.account = GetAccountByIDQuery(user_id=self.account.user_id, account_id=self.account.account_id).execute()
        self.account_name = self.account.account_name
        self.account_tags = self.account.tags
        self.name_label.setText(f"<b>{self.account_name}</b>")

        # Update tags container
        old_tags_index = self.text_layout.indexOf(self.tags_container)
        self.tags_container.deleteLater()
        self.tags_container = TagContainer(self.account_tags, show_close_buttons=False)
        self.text_layout.insertWidget(old_tags_index, self.tags_container)

    def mouseDoubleClickEvent(self, event) -> None:
        """Open account details dialog on double click."""
        dialog = AccountDetailsDialog(self.account, self)
        dialog.exec()

    def keyPressEvent(self, event) -> None:
        """Handle key press events, specifically Escape to cancel edit mode."""
        if event.key() == Qt.Key_Escape:
            # Only cancel if we're in edit mode (line edits are visible)
            if self.name_line_edit.isVisible() or self.tags_line_edit.isVisible():
                self.cancel_edit_mode()
        else:
            super().keyPressEvent(event)


class AccountBrowser(QMainWindow):
    """
    Screen where accounts can be inspectioned, deleted and deactivated
    """

    def __init__(self, parent=None, widget=None):
        super(AccountBrowser, self).__init__(parent)
        account_browser_screen = os.path.join(UISPATH, "account_browser_screen.ui")
        loadUi(account_browser_screen, self)
        self.widget = widget

        self.user_id = self.widget.account_objects[0].user_id

        self.account_changed = set()
        self.acc_row_list = []
        self.all_accounts = []  # Store all accounts for search functionality

        self.save_changes_button.setEnabled(False)
        self.save_changes_button.clicked.connect(self.save_account_changes)

        self.accounts_object = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        self.accounts_object.sort(
            key=lambda acc: (acc.is_active, acc.account_total), reverse=True
        )  # Sort first the active accounts
        self.all_accounts = self.accounts_object  # Store all accounts

        self.back_button.clicked.connect(self.back)

        # Search functionality
        self.search_line_edit = self.findChild(QLineEdit, "search_line_edit")
        self.search_line_edit.textChanged.connect(self.filter_accounts)

        self.scroll_content = self.findChild(QWidget, "scrollAreaWidgetContents")
        self.scroll_layout = self.scroll_content.layout()

        self.refresh_accounts_display()

    def save_account_changes(self) -> None:
        """loops through all acc_ids in the account_changed set and saves the changes into the db"""
        row_to_be_saved = [row for row in self.acc_row_list if row.account_id in self.account_changed]
        for row in row_to_be_saved:
            try:
                # Convert empty string to ("",) tuple to satisfy validation
                tags_to_save = row.new_acc_tags if row.new_acc_tags else ("",)

                EditAccountCommand(
                    user_id=self.user_id, account_id=row.account_id, account_name=row.new_acc_name, tags=tags_to_save
                ).execute()
                row.name_label.setStyleSheet("color: black; font-weight: bold;")
                row.account_name = row.new_acc_name
                row.account_tags = tags_to_save

                # Refresh tags container after saving
                old_tags_index = row.text_layout.indexOf(row.tags_container)
                row.tags_container.deleteLater()
                row.tags_container = TagContainer(row.account_tags, show_close_buttons=False)
                row.text_layout.insertWidget(old_tags_index, row.tags_container)

                animatedlabel.AnimatedLabel("Changes saved! ✅", message_type="success").display()
                self.save_changes_button.setEnabled(False)
                # reset self.account_changed => bug fix
                self.account_changed = set()
            except sqlite3.IntegrityError:
                animatedlabel.AnimatedLabel("Duplicated name + currency!", message_type="error").display()
            except sqlite3.OperationalError:
                animatedlabel.AnimatedLabel("Duplicated name!", message_type="error").display()
            except InvalidAccountNameError:
                animatedlabel.AnimatedLabel("Invalid name!", message_type="error").display()

        # Update all_accounts to reflect changes including tag changes
        self.all_accounts = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        self.all_accounts.sort(key=lambda acc: (acc.is_active, acc.account_total), reverse=True)
        # Re-apply current search filter to reflect name and tag changes
        self.filter_accounts(self.search_line_edit.text())

    def add_account(self, account: Accounts) -> AccountRow:
        row = AccountRow(account)
        row.account_modified.connect(self.handle_account_modified)
        row.account_deleted.connect(self.handle_account_deleted)
        self.scroll_layout.addWidget(row)
        return row

    def refresh_accounts_display(self) -> None:
        """Clear and refresh the accounts display"""
        # Clear existing rows
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.acc_row_list.clear()

        # Add accounts
        for account in self.accounts_object:
            row = self.add_account(account)
            self.acc_row_list.append(row)

    def filter_accounts(self, search_text: str) -> None:
        """Filter accounts based on search text (case insensitive) - searches both name and tags"""
        search_text = search_text.lower().strip()

        if not search_text:
            # Show all accounts
            self.accounts_object = self.all_accounts
        else:
            # Filter accounts by name or tags (case insensitive)
            self.accounts_object = [
                account
                for account in self.all_accounts
                if search_text in account.account_name.lower()
                or (account.tags and any(search_text in tag.lower() for tag in account.tags))
            ]

        self.refresh_accounts_display()

    def handle_account_modified(self, account_id: str, new_acc_name: str, new_acc_tags: str, is_modified: bool) -> None:
        if is_modified:
            self.account_changed.add(account_id)
        else:
            self.account_changed.discard(account_id)
        self.save_changes_button.setEnabled(len(self.account_changed) > 0)

    def handle_account_deleted(self, account_id: str) -> None:
        """Handle account deletion by updating the all_accounts list"""
        # Remove the deleted account from all_accounts
        self.all_accounts = [acc for acc in self.all_accounts if acc.account_id != account_id]
        # Remove from acc_row_list
        self.acc_row_list = [row for row in self.acc_row_list if row.account_id != account_id]
        # Re-apply current search filter
        self.filter_accounts(self.search_line_edit.text())

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
