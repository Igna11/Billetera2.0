#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 12/02/2023 18:10

@author: igna
"""
import os
import decimal
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QCompleter

from src.queries.accqueries import ListAccountsQuery
from src.ophandlers.operationhandler import OperationHandler
from src.queries.opqueries import GetUniqueCategoriesByAccount, GetUniqueSubcategoriesByAccount

from billeUI import UISPATH, operationscreen, animatedlabel


class ReadjustmentScreen(QMainWindow):
    """
    Screen where the user can make readjustment in accounts
    """

    def __init__(self, parent=None, widget=None):
        super(ReadjustmentScreen, self).__init__(parent)
        operation_readjustment_screen = os.path.join(UISPATH, "operation_readjustment_screen.ui")
        loadUi(operation_readjustment_screen, self)
        # self.readjustment_stacked_widget -> main widget
        self.widget = widget
        self.acc_name = None
        self.acc_currency = None
        self.set_account_info()
        self.accounts_comboBox.addItems(self.acc_names_list)
        self.set_account_data(self.accounts_comboBox.currentIndex())
        self.accounts_comboBox.currentIndexChanged.connect(self.set_account_data)
        self.accounts_comboBox.currentIndexChanged.connect(self.set_categories_completer)
        self.accounts_comboBox.currentIndexChanged.connect(self.set_subcategories_completer)
        self.category_line.textChanged.connect(self.set_subcategories_completer)
        self.set_categories_completer()
        self.set_subcategories_completer()
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.cancel)
        self.more_radio_button.clicked.connect(self.more_button)
        self._reset_more_data()

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

    def set_account_info(self) -> None:
        """Sets the account objects, names y currencies to be used in the acounts_comboBox widget"""
        acc_object_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        self.acc_object_list = [acc for acc in acc_object_list]
        self.acc_currency = [acc.account_currency for acc in self.acc_object_list]
        self.acc_names_list = [f"{acc.account_name} ({acc.account_currency})" for acc in self.acc_object_list]

    def set_account_data(self, i: int):
        """Sets the values of acc_name, acc_currency and the value of total label and the
        account_id to be used when saving the data."""
        self.acc_object_list = [acc for acc in ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()]
        self.acc_name = self.acc_names_list[i]
        self.account_id = self.acc_object_list[i].account_id
        account_total = self.acc_object_list[i].account_total
        self.total_label.setText(f"Total: {account_total}")

    def get_list_of_categories_from_db(self) -> list:
        """
        Gets all existing categories from a given account to be used as recomendation
        """
        categories = GetUniqueCategoriesByAccount(user_id=self.widget.user_object.user_id).execute()
        # transform list of tuples [(val1, ), (val2, ), ..., (valN, )] to list [val1, val2, ..., valN]
        categories = [cat[0] for cat in categories]

        return categories

    def get_list_of_subcategories_from_db(self, category: str = None) -> list:
        """
        Gets all existing categories from a given account to be used as recomendation
        """
        subcategories = GetUniqueSubcategoriesByAccount(
            user_id=self.widget.user_object.user_id,
            category=category,
        ).execute()
        # transform list of tuples [(val1, ), (val2, ), ..., (valN, )] to list [val1, val2, ..., valN]
        subcategories = [subcat[0] for subcat in subcategories]

        return subcategories

    def set_categories_completer(self) -> None:
        """
        Sets the list of categories for a given account to be recommendated in the
        Line text for category
        """
        data = self.get_list_of_categories_from_db()
        category_completer = QCompleter(data, self)
        category_completer.setCaseSensitivity(Qt.CaseInsensitive)
        category_completer.setFilterMode(Qt.MatchContains)
        self.category_line.setCompleter(category_completer)

    def set_subcategories_completer(self) -> None:
        """
        Sets the list of categories for a given account to be recommendated in the
        Line text for category
        """
        if self.category_line.text():
            category = self.category_line.text()
        else:
            category = None
        data = self.get_list_of_subcategories_from_db(category)
        subcategory_completer = QCompleter(data, self)
        subcategory_completer.setCaseSensitivity(Qt.CaseInsensitive)
        subcategory_completer.setFilterMode(Qt.MatchContains)
        self.subcategory_line.setCompleter(subcategory_completer)

    def save(self):
        """Saves the new total value of the account."""
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
            animatedlabel.AnimatedLabel("Operation successfull ✅").display()
            self.status_label.setText("<font color='green'>Operation successfull</font>")
        except ValueError:
            animatedlabel.AnimatedLabel("Invalid value!", message_type="error").display()
            self.status_label.setText("<font color='red'>Invalid value.</font>")
        except decimal.InvalidOperation:
            animatedlabel.AnimatedLabel("Invalid value!", message_type="error").display()
            self.status_label.setText("<font color='red'>Invalid value.</font>")
        except UnboundLocalError:
            animatedlabel.AnimatedLabel("No value given!", message_type="warning").display()
            self.status_label.setText("<font color='red'>No value given to readjust!</font>")

        # Updates the total value of the account in the label "total_label"
        self.set_account_data(self.accounts_comboBox.currentIndex())

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
