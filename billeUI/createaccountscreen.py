#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 02/03/2023
"""
import os

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow

from src.models.accmodel import UserAccounts, InvalidAccountNameError
from src.commands.acccommands import CreateUsersAccountCommand, AccountAlreadyExistsError

from billeUI import UISPATH, operationscreen, animatedlabel


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
        try:
            UserAccounts.create_acc_list_table(user_id=self.widget.user_object.user_id)
            CreateUsersAccountCommand(
                email=self.widget.user_object.email, account_name=acc_name, account_currency=acc_currency
            ).execute()
            animatedlabel.AnimatedLabel(f"Account '{acc_name}' successfully created! ✅").display()
            self.create_account_label.setText(
                f"<font color='green'>Account <b>'{acc_name}'</b> successfully created.</font>"
            )
        except InvalidAccountNameError:
            animatedlabel.AnimatedLabel(f"'{acc_name}' is not a valid name.", message_type="error").display()
            self.create_account_label.setText(
                "<font color='red'><b>Invalid account name. No special chars are allowed</b>.</font>"
            )
        except ValueError:
            animatedlabel.AnimatedLabel(f"'{acc_currency}' is not a valid currency.", message_type="error").display()
            self.create_account_label.setText("<font color='red'><b>Invalid currency</b>.</font>")
        except AccountAlreadyExistsError:
            animatedlabel.AnimatedLabel(f"'{acc_name}' already exists!", message_type="warning").display()
            self.create_account_label.setText(
                f"<font color='red'>Account with name <b>'{acc_name}' already exists</b>.</font>"
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
