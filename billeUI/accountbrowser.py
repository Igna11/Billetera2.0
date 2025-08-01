#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 15/07/2025 21:17

@author: igna
"""
import os

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
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

from src.models.accmodel import UserAccounts
from src.queries.accqueries import ListAccountsQuery, GetAccountByIDQuery
from src.commands.acccommands import EditUsersAccountCommand, DeleteUsersAccountCommand

from billeUI import operationscreen, currency_format, animatedlabel
from billeUI import UISPATH, ICONSPATH


class AccountRow(QWidget):
    def __init__(self, account: UserAccounts, parent=None):
        super().__init__(parent)
        # Needed for the hover effect
        self.account = account
        self.account_name = account.account_name
        self.account_changed = set()
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
        self.name_label = QLabel(f"<b>{self.account_name}</b>")
        self.balance_label = QLabel(f"{currency_format(account.account_total)} {account.account_currency}")
        self.balance_label.setFont(font)

        # Line edits - hidden until edition
        self.name_line_edit = QLineEdit(self)
        #self.name_line_edit.setStyleSheet("margin: 6px")
        self.name_line_edit.setText(self.account_name)
        self.name_line_edit.hide()

        # Buttons and Icons
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

        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon(os.path.join(ICONSPATH, "edit.svg")))
        self.edit_btn.clicked.connect(self.enable_edit_mode)
        self.edit_btn.setToolTip("Edit account")

        # Layouts
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.name_label)
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

        self.name_line_edit.returnPressed.connect(self.show_qlabel)
        self.name_line_edit.editingFinished.connect(self.show_qlabel)

    def show_qlabel(self) -> None:
        """Resets the label with the new values"""
        new_acc_name = self.name_line_edit.text().strip()
        if new_acc_name != self.account_name:
            self.name_line_edit.hide()
            self.name_label.setText(new_acc_name)
            self.name_label.setStyleSheet("color: orange; font-weight: bold; font-style: italic;")
            self.name_label.show()
            self.account_changed.add(self.account_name)
            print("account edited")
        else:
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
            # self.show_temporary_message("Account deleted ✅")
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

        self.accounts_object = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()

        self.back_button.clicked.connect(self.back)

        self.scroll_content = self.findChild(QWidget, "scrollAreaWidgetContents")
        self.scroll_layout = self.scroll_content.layout()

        for account in self.accounts_object:
            self.add_account(account)

    def add_account(self, account: UserAccounts):
        row = AccountRow(account)
        self.scroll_layout.addWidget(row)

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
