#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 12/02/2023
updated on 21/06/2026
"""
import os
from typing import List
from datetime import datetime, timedelta

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPainter
from PyQt5.QtChart import QChartView
from PyQt5.QtWidgets import QMainWindow, QStackedWidget

from billeUI import UISPATH
from billeUI import (
    loginscreen,
    incomeexpensescreen,
    readjustmentscreen,
    createaccountscreen,
    categorypiechart,
    calendardialog,
    transferscreen,
    accounts_dashlet_widget,
    operationbrowser,
    accountbrowser,
)

from src.queries.accqueries import ListAccountsQuery


class OperationScreen(QMainWindow):
    """
    Operation screen
    """

    def __init__(self, widget=None) -> None:
        super().__init__()
        self.widget = widget
        self.setup_ui()
        self.initialize_variables()
        self.setup_buttons()
        self.disable_operation_buttons()

        # transition for accounts
        self.set_account_dashlet_widget()

        # Modifiers
        # self.text_item = QGraphicsTextItem("0")
        self.chart = categorypiechart.CategoricalPieChart()
        self.chart_view = QChartView(self.chart)
        self.current_month_chart()
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        self.currency_combobox.currentIndexChanged.connect(self.change_currency_chart)
        self.currency_combobox.currentIndexChanged.connect(self.set_account_dashlet_widget)
        # Add the chart_view to the central_VR_layout
        self.central_VR_Layout.addWidget(self.chart_view)

    def _get_currency_list(self) -> List[str]:
        """
        Generate the list of used currencies. This method does not filter by active because the currency
        is a parameter needed to generate the charts to be desplayed even though all accounts are inactive
        """
        acc_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        currencies_list = list({account.account_currency for account in acc_list})
        currencies_list.sort()
        return currencies_list

    def set_account_dashlet_widget(self) -> None:
        """Sets the data to the dashlet of the accounts totals"""
        new_data = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(currency=self.currency, active=1)
        if hasattr(self, "account_dashlet") and self.account_dashlet is not None:
            self.account_dashlet.update_data(new_data)
        else:
            self.account_dashlet = accounts_dashlet_widget.AccountDashletWidget(new_data)
            self.acc_totals_widget = QStackedWidget()
            self.acc_totals_widget.addWidget(self.account_dashlet)
            self.central_VL_Layout.insertWidget(0, self.acc_totals_widget)

    def setup_ui(self) -> None:
        """Loads the ui file"""
        operation_screen = os.path.join(UISPATH, "operation_screen.ui")
        loadUi(operation_screen, self)

    def initialize_variables(self) -> None:
        """Set up the initial variables"""
        self.operation = None
        self.chart_mode = "month"
        self.chart_type = "expense"
        self.currency_combobox.addItems(self._get_currency_list())
        self.currency = self.currency_combobox.currentText()
        self.curr_datetime = datetime.now()
        self.selected_datetime = self.curr_datetime
        self.custom_initial_date = None
        self.custom_final_date = None
        self.username_label.setText(f"<b>Hello {self.widget.user_object.first_name}!</b>")

    def setup_buttons(self) -> None:
        """Sets the signals for the buttons of the window."""
        buttons_function_pairs = [
            (self.income_button, self.pre_income),
            (self.expense_button, self.pre_expense),
            (self.transfer_button, self.pre_transfer),
            (self.readjustment_button, self.pre_readjustment),
            (self.create_new_account_button, self.create_account),
            (self.back_button, self.back),
            (self.custom_period_button, self.custom_date_range),
            (self.switch_type_button, self.switch_chart_type),
            (self.previous_month_button, self.previous_month_chart),
            (self.next_month_button, self.next_month_chart),
            (self.reset_month_button, self.current_month_chart),
            (self.browse_account_button, self.browse_operations),
            (self.account_button, self.browse_accounts),
        ]
        for button, function in buttons_function_pairs:
            button.clicked.connect(function)

    def disable_operation_buttons(self):
        """checks if any account exists"""
        acc_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        if not acc_list:
            self.income_button.setEnabled(False)
            self.expense_button.setEnabled(False)
            self.transfer_button.setEnabled(False)
            self.readjustment_button.setEnabled(False)

    def pre_operation(self, operation) -> None:
        """Sets the UIs according to the operation value"""
        self.operation = operation
        acc_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        self.widget.__setattr__("account_objects", acc_list)
        if operation == "income":
            operation_inputs = incomeexpensescreen.IncomeExpenseScreen(self.operation, widget=self.widget)
        elif operation == "expense":
            operation_inputs = incomeexpensescreen.IncomeExpenseScreen(self.operation, widget=self.widget)
        elif operation == "transfer":
            operation_inputs = transferscreen.TransferScreen(self.operation, widget=self.widget)
        elif operation == "readjustment":
            operation_inputs = readjustmentscreen.ReadjustmentScreen(self.operation, widget=self.widget)
        self.widget.addWidget(operation_inputs)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def pre_income(self) -> None:
        """Takes the user to the income/expense screen and sets the flag operation to income"""
        self.pre_operation("income")

    def pre_expense(self) -> None:
        """Takes the user to the income/expense screen and sets the flag operation to expense"""
        self.pre_operation("expense")

    def pre_transfer(self) -> None:
        """Takes the user to the transfer screen and sets the flag operation to transfer"""
        self.pre_operation("transfer")

    def pre_readjustment(self) -> None:
        """Takes the user to the readjustment screen and sets the flag operation to readjustment"""
        self.pre_operation("readjustment")

    def create_account(self) -> None:
        """Takes the user to the CreateAccount screen"""
        create_account_window = createaccountscreen.CreateAccount(widget=self.widget)
        self.widget.addWidget(create_account_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def browse_operations(self) -> None:
        browse_operation_window = operationbrowser.OperationBrowser(widget=self.widget)
        self.widget.addWidget(browse_operation_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def browse_accounts(self) -> None:
        browse_account_window = accountbrowser.AccountDialog(widget=self.widget)
        self.widget.addWidget(browse_account_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def generate_chart(self, mode: str, time_period: datetime | None, currency: str) -> None:
        """
        docstring
        """
        self.chart.clear_slices()

        if mode == "current":
            self.selected_datetime = self.curr_datetime
            chart_period = "month"
            stime = self.selected_datetime
        elif mode == "previous":
            chart_period = "month"
            cur_date = self.selected_datetime.day
            # last day of the previous month
            self.selected_datetime = self.selected_datetime - timedelta(days=cur_date)
            stime = self.selected_datetime
        elif mode == "next":
            chart_period = "month"
            cur_date = self.selected_datetime.day
            # first days of the next month
            self.selected_datetime = self.selected_datetime - timedelta(days=cur_date - 1) + timedelta(days=32)
            stime = self.selected_datetime
        elif mode == "period" and time_period:
            stime = time_period
            chart_period = "period"
        else:
            chart_period = mode
            stime = time_period

        data_inner, data_outer = self.chart.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode=chart_period,
            chart_type=self.chart_type,
            time_period=stime,
            currency=self.currency,
        )
        self.chart.update_title(
            user_id=self.widget.user_object.user_id,
            chart_mode=chart_period,
            chart_type=self.chart_type,
            time_period=stime,
            currency=self.currency,
        )
        self.chart.add_slices(data_inner, data_outer)
        self.chart.update_labels()
        # Add the chart_view to the central_VR_layout
        self.central_VR_Layout.addWidget(self.chart_view)
        # reset the chart mode in case the period mode was activated
        self.chart_mode = "month"
        return 0

    def current_month_chart(self) -> None:
        """
        Generates a new piechart of the current month and updates the variable
        self.selected_datetime
        """
        self.chart_mode = "month"
        self.generate_chart(mode="current", time_period=1, currency=self.currency)

    def previous_month_chart(self) -> None:
        """
        Generates a new piechart of the previous month and updates the
        variable self.selected_datetime
        """
        self.chart_mode = "month"
        self.generate_chart(mode="previous", time_period=1, currency=self.currency)

    def next_month_chart(self) -> None:
        """
        Generates a new piechart of the next month and updates the
        variable self.selected_datetime
        """
        self.chart_mode = "month"
        self.generate_chart(mode="next", time_period=1, currency=self.currency)

    def custom_date_range(self) -> None:
        """
        Generates a new piechart of the period of time selected in the calendar.
        First it opens up a calendar widget to select the 2 dates that conform the
        desired period of time. Then uses it to gather the information needed for
        the pie chart.
        """
        calendar_dialog = calendardialog.CalendarDialog()
        calendar_dialog.select_button.clicked.connect(calendar_dialog.get_date_range)
        calendar_dialog.exec_()
        self.custom_initial_date = calendar_dialog.initial_d
        self.custom_final_date = calendar_dialog.final_d
        if self.custom_initial_date and self.custom_final_date:
            period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            self.generate_chart(mode="period", time_period=period_dict, currency=self.currency)
            self.chart_mode = "period"

    def switch_chart_type(self) -> None:
        """
        Changes the chart type to switch between incomes and expenses
        """
        self.chart.clear_slices()
        if self.chart_type == "expense":
            self.chart_type = "income"
        elif self.chart_type == "income":
            self.chart_type = "expense"
        stime = self.selected_datetime
        if self.chart_mode == "month":
            data_inner, data_outer = self.chart.load_data(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=stime,
                currency=self.currency,
            )
            self.chart.update_title(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=stime,
                currency=self.currency,
            )
        elif self.chart_mode == "period":
            period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            data_inner, data_outer = self.chart.load_data(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=period_dict,
                currency=self.currency,
            )
            self.chart.update_title(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=period_dict,
                currency=self.currency,
            )

        self.chart.add_slices(data_inner, data_outer)
        self.chart.update_labels()
        # Add the chart_view to the central_VR_layout
        self.central_VR_Layout.addWidget(self.chart_view)

    def change_currency_chart(self) -> None:
        """
        Generates a new piechart changing the currency used to filter the operations
        """
        if self.chart_mode == "period":
            period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            stime = period_dict
        else:
            stime = self.selected_datetime
        self.currency = self.currency_combobox.currentText()
        self.generate_chart(mode=self.chart_mode, time_period=stime, currency=self.currency)

    def back(self) -> None:
        """Returns to the LoginScreen Menu"""
        login_screen = loginscreen.LoginScreen(widget=self.widget)
        self.widget.addWidget(login_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the LoginScreen Menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            login_screen = loginscreen.LoginScreen(widget=self.widget)
            self.widget.addWidget(login_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
