#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 15/07/2025 21:17

@author: igna
"""
import os

from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QPushButton, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from src.models.accmodel import UserAccounts
from src.queries.accqueries import ListAccountsQuery

from billeUI import operationscreen, currency_format
from billeUI import UISPATH, ICONSPATH


class AccountRow(QWidget):
    def __init__(self, account_object: UserAccounts, parent=None):
        super().__init__(parent)
        # Needed for the hover effect
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
        self.name_label = QLabel(f"<b>{account_object.account_name}</b>")
        self.balance_label = QLabel(
            f"{currency_format(account_object.account_total)} {account_object.account_currency}"
        )
        self.balance_label.setFont(font)

        # Buttons and Icons
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(os.path.join(ICONSPATH, "delete.svg")))

        self.disable_btn = QPushButton()
        self.disable_btn.setIcon(QIcon(os.path.join(ICONSPATH, "disable.svg")))

        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon(os.path.join(ICONSPATH, "edit.svg")))

        # Layouts
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.balance_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.disable_btn)
        btn_layout.addWidget(self.edit_btn)

        inner_layout = QHBoxLayout()
        inner_layout.addLayout(text_layout)
        inner_layout.addStretch()
        inner_layout.addLayout(btn_layout)
        inner_layout.setContentsMargins(5, 3, 5, 3)

        self.frame.setLayout(inner_layout)

        # Layout externo (el de este widget)
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)


class AccountDialog(QMainWindow):
    """
    Screen where accounts can be inspectioned, deleted and deactivated
    """

    def __init__(self, parent=None, widget=None):
        super(AccountDialog, self).__init__(parent)
        account_browser_screen = os.path.join(UISPATH, "account_browser_screen.ui")
        loadUi(account_browser_screen, self)
        self.widget = widget

        self.accounts_object = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()

        self.back_button.clicked.connect(self.back)

        # Aquí asumimos que en tu UI tenés un QWidget dentro del scroll con layout vertical
        self.scroll_content = self.findChild(QWidget, "scrollAreaWidgetContents")
        self.scroll_layout = self.scroll_content.layout()

        # Agregar cuentas de ejemplo
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
