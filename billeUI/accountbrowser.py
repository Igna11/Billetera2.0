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

from src.models.accmodel import UserAccounts, InvalidAccountNameError
from src.queries.accqueries import ListAccountsQuery, GetAccountByIDQuery
from src.commands.acccommands import EditUsersAccountCommand, DeleteUsersAccountCommand

from billeUI import operationscreen, currency_format, animatedlabel
from billeUI import UISPATH, ICONSPATH


class AccountRow(QWidget):

    account_modified = pyqtSignal(str, str, bool)

    def __init__(self, account: UserAccounts, parent=None):
        super().__init__(parent)
        # Needed for the hover effect
        self.account = account
        self.account_id = account.account_id
        self.account_name = account.account_name
        self.new_acc_name = ""
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
        self.name_line_edit.editingFinished.connect(self.show_qlabel)
        self.balance_label = QLabel(f"{currency_format(account.account_total)} {account.account_currency}")
        self.balance_label.setFont(font)

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
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.name_line_edit)
        text_layout.addWidget(self.balance_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.enable_disable_btn)

        inner_layout = QHBoxLayout()
        inner_layout.addLayout(text_layout)
        inner_layout.addStretch()
        inner_layout.addLayout(btn_layout)
        inner_layout.setContentsMargins(5, 3, 5, 3)

        self.frame.setLayout(inner_layout)

        # outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)

    def enable_edit_mode(self) -> None:
        """Enables the edition of the account name"""
        self.name_label.hide()
        self.name_line_edit.show()
        self.name_line_edit.setFocus()
        self.name_line_edit.selectAll()

    def show_qlabel(self) -> None:
        """Resets the label with the new values"""
        self.new_acc_name = self.name_line_edit.text().strip()
        self.name_label.setText(self.new_acc_name)
        if self.new_acc_name != self.account_name:
            self.name_label.setStyleSheet("color: orange; font-weight: bold; font-style: italic;")
            self.account_modified.emit(self.account_id, self.new_acc_name, True)
        else:
            self.name_label.setStyleSheet("color: black; font-weight: bold;")
            self.account_modified.emit(self.account_id, self.account_name, False)
        self.name_line_edit.hide()
        self.name_label.show()

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
            DeleteUsersAccountCommand(user_id=self.account.user_id, account_id=self.account.account_id).execute()
            # refresh view without the deleted widget
            animatedlabel.AnimatedLabel("Account deleted ✅").display()
            parent_layout = self.parentWidget().layout()
            parent_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

    def enable_n_disable_account(self) -> None:
        if self.account.is_active:
            EditUsersAccountCommand(
                user_id=self.account.user_id, account_id=self.account.account_id, is_active=False
            ).execute()
            animatedlabel.AnimatedLabel("Account disabled! ✅", message_type="warning").display()
        else:
            EditUsersAccountCommand(
                user_id=self.account.user_id, account_id=self.account.account_id, is_active=True
            ).execute()
            animatedlabel.AnimatedLabel("Account enabled! ✅").display()
        self.refresh_account_data()

    def refresh_account_data(self) -> None:
        self.account = GetAccountByIDQuery(user_id=self.account.user_id, account_id=self.account.account_id).execute()


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

        self.save_changes_button.setEnabled(False)
        self.save_changes_button.clicked.connect(self.save_account_changes)

        self.accounts_object = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()

        self.back_button.clicked.connect(self.back)

        self.scroll_content = self.findChild(QWidget, "scrollAreaWidgetContents")
        self.scroll_layout = self.scroll_content.layout()

        for account in self.accounts_object:
            row = self.add_account(account)
            self.acc_row_list.append(row)

    def save_account_changes(self) -> None:
        """loops through all acc_ids in the account_changed set and saves the changes into the db"""
        row_to_be_saved = [row for row in self.acc_row_list if row.account_id in self.account_changed]
        for row in row_to_be_saved:
            try:
                EditUsersAccountCommand(
                    user_id=self.user_id, account_id=row.account_id, account_name=row.new_acc_name
                ).execute()
                row.name_label.setStyleSheet("color: black; font-weight: bold;")
                animatedlabel.AnimatedLabel("Changes saved! ✅", message_type="success").display()
                self.save_changes_button.setEnabled(False)
            except sqlite3.OperationalError:
                animatedlabel.AnimatedLabel("Duplicated name!", message_type="error").display()
            except InvalidAccountNameError:
                animatedlabel.AnimatedLabel("Invalid name!", message_type="error").display()

    def add_account(self, account: UserAccounts) -> AccountRow:
        row = AccountRow(account)
        row.account_modified.connect(self.handle_account_modified)
        self.scroll_layout.addWidget(row)
        return row

    def handle_account_modified(self, account_id: str, new_acc_name: str, is_modified: bool) -> None:
        if is_modified:
            self.account_changed.add(account_id)
        else:
            self.account_changed.discard(account_id)
        self.save_changes_button.setEnabled(len(self.account_changed) > 0)

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
