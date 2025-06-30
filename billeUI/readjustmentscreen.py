#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 12/02/2023 18:10

@author: igna
"""
import os
import decimal
from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QStackedWidget

from src.queries.accqueries import ListAccountsQuery
from src.ophandlers.operationhandler import OperationHandler

from billeUI import UISPATH
from billeUI import operationscreen


class ReadjustmentScreen(QMainWindow):
    """
    Screen where the user can make readjustment in accounts
    """

    def __init__(self, operation_flag: str, parent=None, widget=None):
        super(ReadjustmentScreen, self).__init__(parent)
        operation_readjustment_screen = os.path.join(UISPATH, "operation_readjustment_screen.ui")
        loadUi(operation_readjustment_screen, self)
        self.readjustment_stacked_widget
        self.widget = widget
        self.acc_name = None
        self.acc_currency = None
        self.operation_flag = operation_flag
        self.set_account_info()
        self.accounts_comboBox.addItems(self.acc_names_list)
        self.set_acc_data(self.accounts_comboBox.currentIndex())
        self.accounts_comboBox.currentIndexChanged.connect(self.set_acc_data)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.cancel)
        self.more_radio_button.clicked.connect(self.more_button)
        self._reset_more_data()

    def set_account_info(self) -> None:
        """Sets the account objects, names y currencies"""
        acc_object_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        self.acc_object_list = [acc for acc in acc_object_list if acc.account_total]
        self.acc_currency = [acc.account_currency for acc in self.acc_object_list]
        self.acc_names_list = [f"{acc.account_name} ({acc.account_currency})" for acc in self.acc_object_list]

    def _reset_more_data(self) -> None:
        """Reset the data from the toggle more"""
        self.more_data = {}
        self.quantity_line_2.setText("")
        self.category_line.setText("")
        self.subcategory_line.setText("")
        self.description_line.setText("")
        self.status_label.setText("")

    def more_button(self, i: int):
        """Changes between the simple set option or the more option when performing a readjustment"""
        if self.readjustment_stacked_widget.currentIndex() == 1:
            self.readjustment_stacked_widget.setCurrentIndex(0)
            self._reset_more_data()
        else:
            self.readjustment_stacked_widget.setCurrentIndex(1)
            self.quantity_line.setText("")
            self.status_label.setText("")

    def set_acc_data(self, i: int):
        """Sets the values of acc_name, acc_currency and the value of total label."""
        self.acc_object_list = [
            acc for acc in ListAccountsQuery(user_id=self.widget.user_object.user_id).execute() if acc.account_total
        ]
        self.acc_name = self.acc_names_list[i]
        self.account_id = self.acc_object_list[i].account_id
        account_total = self.acc_object_list[i].account_total
        self.total_label.setText(f"Total: {account_total}")

    def save(self):
        """Saves the new total value of the account."""
        if self.operation_flag == "readjustment":
            if self.quantity_line_2.text() != "":
                value = decimal.Decimal(self.quantity_line_2.text())
                self.more_data = {
                    "category": self.category_line.text(),
                    "subcategory": self.subcategory_line.text(),
                    "description": self.description_line.text(),
                }
            elif self.quantity_line.text() != "":
                self.more_data = {
                    "category": "Readjustment",
                    "subcategory": "Readjustment",
                    "Description": "Readjustment",
                }
                value = decimal.Decimal(self.quantity_line.text())
            try:
                readjustment = OperationHandler(
                    user_id=self.widget.user_object.user_id,
                    account_id=self.account_id,
                    operation_type="income",  # dummy operation type, it gets overwritten
                    amount=0.1,  # dummy value, it gets overwritten
                    **self.more_data,
                )
                cml = readjustment.readjustment(account_total=value)
                readjustment.create_operations(cml)
                self.status_label.setText(f"<font color='green'>Operation successfull</font>")
            except ValueError as e:
                self.status_label.setText(f"<font color='red'>Invalid value.</font>")
                print(f"{e}=")
            except decimal.InvalidOperation as e:
                self.status_label.setText(f"<font color='red'>Invalid value.</font>")
                print(f"{e}=")
            except UnboundLocalError:
                self.status_label.setText(f"<font color='red'>No value given to readjust!</font>")

        # Updates the total value of the account in the label "total_label"
        self.set_acc_data(self.accounts_comboBox.currentIndex())

    def cancel(self):
        """Returns to the OperationScreen menu"""
        operation_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(operation_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the OperationScreen menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            operation_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(operation_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
