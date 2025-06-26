#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 02/03/2023
"""
import os

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow

from src.models.accmodel import UserAccounts
from src.commands.acccommands import CreateUsersAccountCommand, AccountAlreadyExistsError

from billeUI import UISPATH
from billeUI import users_gui
from billeUI import accounts_gui
from billeUI import operationscreen


class CreateAccount(QMainWindow):
    """
    Operation screen
    """

    def __init__(self, parent=None, widget=None):
        super(CreateAccount, self).__init__(parent)
        operation_screen = os.path.join(UISPATH, "create_account_screen.ui")
        loadUi(operation_screen, self)
        self.widget = widget
        self.save_button.clicked.connect(self.create_account)
        self.cancel_button.clicked.connect(self.cancel)
        self.currency_comboBox.addItems(["ARS", "USD"])
        self.acc_name = self.acc_name_line.text()
        self.acc_currency = self.currency_comboBox.currentText()

    def create_account(self):
        """Creates the .txt file tha thold data' account."""
        acc_name = self.acc_name_line.text()
        acc_currency = self.currency_comboBox.currentText()
        print(f"{acc_name}: {acc_currency}")
        try:
            UserAccounts.create_acc_list_table(user_id=self.widget.user_object.user_id)
            account = CreateUsersAccountCommand(
                email=self.widget.user_object.email, account_name=acc_name, account_currency=acc_currency
            ).execute()
            self.create_account_label.setText(
                f"<font color='green'>Account <b>'{acc_name}'</b> successfully created.</font>"
            )
        except ValueError as e:
            self.create_account_label.setText(f"<font color='red'>Invalid currency'</b>.</font>")
            print(e)

        except AccountAlreadyExistsError:
            self.create_account_label.setText(
                f"<font color='red'>Account with name <b>'{acc_name}' already exists.</b>.</font>"
            )

    def cancel(self):
        """Cancel creation of account and returns to OperationScreen"""
        login_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(login_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to OperationScreen when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            login_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(login_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
