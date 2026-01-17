#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 05/02/2023 18:10

@author: igna
"""
import os
import datetime
import decimal

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtWidgets import QMainWindow, QCompleter, QMessageBox

from src.models.opgroupsmodel import OperationGroups
from src.queries.accqueries import ListAccountsQuery
from src.queries.opqueries import GetUniqueCategoriesByAccount, GetUniqueSubcategoriesByAccount
from src.commands.groupcommands import CreateOperationGroupCommand
from src.ophandlers.operationhandler import OperationHandler, NegativeAccountTotalError

from billeUI import UISPATH, operationscreen, groupbrowser, animatedlabel, currency_format


class IncomeExpenseScreen(QMainWindow):
    """
    Screen where inputs for the operations are managed
    """

    def __init__(self, operation_flag: str, parent=None, widget=None) -> None:
        super(IncomeExpenseScreen, self).__init__(parent)
        operation_incomeexpense_screen = os.path.join(UISPATH, "operation_incomeexpense_screen.ui")
        loadUi(operation_incomeexpense_screen, self)
        self.widget = widget
        self.operation_flag = operation_flag

        self.index = None
        self.acc_name = None
        self.acc_currency = None
        self.acc_items_list = widget.account_objects
        self.acc_list = [f"{acc.account_name} ({acc.account_currency})" for acc in widget.account_objects]

        # groups
        self.group_browser = None
        self.groups_button.clicked.connect(self.open_group_browser)
        self.groups_list = self.get_list_of_groups_from_db()
        self.group_combo_box.addItems(self.set_group_combo_box())
        self.on_enter_pressed_group_combo_box()
        self.create_group_message = QMessageBox()

        self.group_operation_checkBox.clicked.connect(self.set_enable_groups_combo_box)
        self.set_operation_label(operation_flag)
        self.accounts_comboBox.addItems(self.acc_list)
        self.set_acc_data(self.accounts_comboBox.currentIndex())
        self.accounts_comboBox.currentIndexChanged.connect(self.set_acc_data)
        self.accounts_comboBox.currentIndexChanged.connect(self.set_categories_completer)
        self.accounts_comboBox.currentIndexChanged.connect(self.set_subcategories_completer)
        self.category_line.textChanged.connect(self.set_subcategories_completer)
        self.set_categories_completer()
        self.set_subcategories_completer()
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.cancel)
        self.date_edit.setDate(QDate.currentDate())
        self.time_edit.setTime(QTime.currentTime())

        # activate save button after a save if any line text suffer a change
        self.activate_save_button_on_changes()

    def get_date_time(self) -> datetime.datetime:
        """Generates a datetime object to be saved in the database"""
        _date = self.date_edit.date()
        _time = self.time_edit.time()
        dttime = datetime.datetime(
            _date.year(),
            _date.month(),
            _date.day(),
            _time.hour(),
            _time.minute(),
            QTime.currentTime().second(),
            QTime.currentTime().msec(),
            tzinfo=datetime.UTC,
        )
        return dttime

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
        list_acc_objects = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        if list_acc_objects:
            self.acc_list = [acc.account_name for acc in list_acc_objects]
            self.acc_list_currencies = [acc.account_currency for acc in list_acc_objects]
            self.index = i
            self.acc_name = self.acc_list[self.index]
            self.acc_currency = self.acc_list_currencies[self.index]
            account_total = currency_format(list_acc_objects[self.index].account_total)
            self.total_label.setText(f"Total: {account_total}")
        else:
            self.acc_list = []
            self.acc_list_currencies = []
            self.index = i
            self.acc_name = None
            self.acc_currency = None
            account_total = None
            self.total_label.setText("Total: None")

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

    ################# GROUPS #################
    def open_group_browser(self) -> None:
        """
        Opens the window widget for the group browser
        """
        if self.group_browser is None:
            self.group_browser = groupbrowser.GroupBrowserWidget(widget=self.widget)
        self.group_browser.show()

    def get_list_of_groups_from_db(self) -> list[OperationGroups]:
        """
        Returns the list of existing operation groups with their ids
        """
        operation_groups_list = OperationGroups().get_groups_list(
            user_id=self.widget.user_object.user_id, status="open"
        )

        return operation_groups_list

    def set_enable_groups_combo_box(self) -> None:
        """
        Enables the combo box for creating groups or choosing one.
        """
        if not self.group_combo_box.isEnabled():
            self.group_combo_box.setEnabled(True)
        else:
            self.group_combo_box.setEnabled(False)

    def set_group_combo_box(self) -> list[str]:
        groups = [f"{group.group_name} {group.group_currency}" for group in self.groups_list]
        return groups

    def create_group(self) -> None:
        group_name = self.group_combo_box.currentText()

        popup_message = self.create_group_message.question(
            self,
            "Group Creation",
            f"Do you want to create the group {group_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if popup_message == QMessageBox.Yes:
            group = CreateOperationGroupCommand(
                user_id=self.widget.user_object.user_id, group_name=group_name, group_currency="ARS"
            )
            group.execute()
        if popup_message == QMessageBox.No:
            pass

    def on_enter_pressed_group_combo_box(self) -> None:
        if self.group_combo_box.lineEdit():
            self.group_combo_box.lineEdit().returnPressed.connect(self.create_group)

    ################# Save operations #################

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
            self.status_label.setText("<font color='green'>Operation successfull</font>")
            self.save_button.setEnabled(False)
            animatedlabel.AnimatedLabel("Operation saved ✅").display()
        except decimal.InvalidOperation:
            self.status_label.setText("<font color='red'>Invalid value entered.</font>")
            animatedlabel.AnimatedLabel("Invalid value", message_type="error").display()
        except ValueError:
            self.status_label.setText("<font color='red'>Invalid value entered.</font>")
            animatedlabel.AnimatedLabel("Invalid value", message_type="error").display()
        except NegativeAccountTotalError:
            animatedlabel.AnimatedLabel("Invalid value", message_type="error").display()
            self.status_label.setText(
                "<font color='red'>This value could lead to a negative total amount. Please check the date or the value.</font>"
            )
        # Updates the total value of the account in the label "total_label"
        self.set_acc_data(self.accounts_comboBox.currentIndex())

    def activate_save_button(self) -> None:
        self.save_button.setEnabled(True)

    def activate_save_button_on_changes(self) -> None:
        self.accounts_comboBox.currentIndexChanged.connect(self.activate_save_button)
        self.date_edit.dateChanged.connect(self.activate_save_button)
        self.time_edit.timeChanged.connect(self.activate_save_button)
        self.quantity_line.textChanged.connect(self.activate_save_button)
        self.category_line.textChanged.connect(self.activate_save_button)
        self.subcategory_line.textChanged.connect(self.activate_save_button)
        self.description_line.textChanged.connect(self.activate_save_button)

    def cancel(self) -> None:
        """Returns to the OperationScreen Menu"""
        operation_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(operation_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e) -> None:
        """Returns to the OperationScreen Menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            operation_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(operation_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
