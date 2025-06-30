#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 05/02/2023 18:10

@author: igna
"""
import os
import time
import datetime
import decimal

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QDate, QTime, QDateTime

from src.queries.accqueries import ListAccountsQuery
from src.ophandlers.operationhandler import OperationHandler, NegativeAccountTotalError
from src.ophandlers.transferhandler import TransferHandler
from src.ophandlers.deletehandler import DeletionHandler

from billeUI import operationscreen
from billeUI import UISPATH, currency_format


class IncomeExpenseScreen(QMainWindow):
    """
    Screen where inputs for the operations are managed
    """

    def __init__(self, operation_flag: str, parent=None, widget=None):
        super(IncomeExpenseScreen, self).__init__(parent)
        operation_incomeexpense_screen = os.path.join(UISPATH, "operation_incomeexpense_screen.ui")
        loadUi(operation_incomeexpense_screen, self)
        self.widget = widget
        self.operation_flag = operation_flag

        self.index = None
        self.acc_name = None
        self.acc_currency = None
        self.acc_items_list = widget.accounts_object
        self.acc_list = [f"{acc.account_name} ({acc.account_currency})" for acc in widget.accounts_object]

        self.set_operation_label(operation_flag)
        self.accounts_comboBox.addItems(self.acc_list)
        self.set_acc_data(self.accounts_comboBox.currentIndex())
        self.accounts_comboBox.currentIndexChanged.connect(self.set_acc_data)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.cancel)
        self.date_edit.setDate(QDate.currentDate())
        self.time_edit.setTime(QTime.currentTime())

    def get_date_time(self) -> datetime.datetime:
        """Generates a datetime object to be saved in the database"""
        date = self.date_edit.date()
        time = self.time_edit.time()
        dttime = datetime.datetime(
            date.year(),
            date.month(),
            date.day(),
            time.hour(),
            time.minute(),
            QTime.currentTime().second(),
            QTime.currentTime().msec(),
            tzinfo=datetime.UTC,
        )
        return dttime

    def set_operation_label(self, operation_flag) -> None:
        """
        Sets the label of the operation to let know the user
        if it is an income or an expense
        """
        if operation_flag == "income":
            self.operation_label.setText("<font color='green'><b>INCOME</b></font>")
        elif operation_flag == "expense":
            self.operation_label.setText("<font color='orange'><b>EXPENSE</b></font>")

    def set_acc_data(self, i: int) -> None:
        """Sets the values of acc_name, acc_currency and the value of total label."""
        list_acc_objects = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        self.acc_list = [acc.account_name for acc in list_acc_objects]
        self.acc_list_currencies = [acc.account_currency for acc in list_acc_objects]
        self.index = i
        self.acc_name = self.acc_list[self.index]
        self.acc_currency = self.acc_list_currencies[self.index]
        account_total = currency_format(list_acc_objects[self.index].account_total)
        self.total_label.setText(f"Total: {account_total}")

    def save(self) -> None:
        """Saves the operation into the database"""
        dttime = self.get_date_time()
        category = self.category_line.text()
        subcategory = self.subcategory_line.text()
        description = self.description_line.text()
        try:
            value = decimal.Decimal(self.quantity_line.text())
            operation = OperationHandler(
                user_id=self.widget.user_object.user_id,
                account_id=self.acc_items_list[self.index].account_id,
                amount=value,
                operation_datetime=dttime,
                operation_type=self.operation_flag,
                category=category,
                subcategory=subcategory,
                description=description,
            )
            operation.set_account_total()
            cmls = operation.set_cumulatives()
            operation = operation.create_operations(cmls)
            self.status_label.setText(f"<font color='green'>Operation successfull</font>")
        except decimal.InvalidOperation as e:
            self.status_label.setText(f"<font color='red'>Invalid value entered.</font>")
        except ValueError as e:
            self.status_label.setText(f"<font color='red'>Invalid value entered.</font>")
        except NegativeAccountTotalError as e:
            self.status_label.setText(
                f"<font color='red'>This value could lead to a negative total amount. Please check the date or the value.</font>"
            )
        # Updates the total value of the account in the label "total_label"
        self.set_acc_data(self.accounts_comboBox.currentIndex())

    def cancel(self) -> None:
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
