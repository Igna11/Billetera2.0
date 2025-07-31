#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 12/02/2023
updated on 21/06/2026
"""
import os
from typing import List
from datetime import datetime

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
    piechartfunctions,
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

        # Accounts information dashlet
        self.set_account_dashlet_widget()

        # Modifiers
        self.chart = categorypiechart.CategoricalPieChart()
        self.chart.setBackgroundVisible(False)
        self.chart_view = QChartView(self.chart)
        self.current_month_chart() # generates the chart when opening this window
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        self.currency_combobox.currentIndexChanged.connect(self.change_currency_chart)
        self.currency_combobox.currentIndexChanged.connect(self.set_account_dashlet_widget)
        # Add the chart_view to the central_VR_layout
        self.central_VR_Layout.addWidget(self.chart_view)

    def setup_ui(self) -> None:
        """Loads the ui file"""
        operation_screen = os.path.join(UISPATH, "operation_screen.ui")
        loadUi(operation_screen, self)

    def initialize_variables(self) -> None:
        """Set up the initial variables"""
        self.operation = None
        # variables for the pie chart
        self.chart_mode = "month"
        self.chart_type = "expense"
        # self.chart_period = "month"
        self.curr_datetime = datetime.now()
        self.selected_datetime = self.curr_datetime
        self.custom_initial_date = None
        self.custom_final_date = None
        self.period_dict = {}

        self.currency_combobox.addItems(self.get_currency_list())
        self.currency = self.currency_combobox.currentText()
        self.username_label.setText(f"<b>Hello {self.widget.user_object.first_name}!</b>")
        acc_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        self.widget.__setattr__("account_objects", acc_list)

    def setup_buttons(self) -> None:
        """Sets the signals for the buttons of the window."""
        buttons_function_pairs = [
            # operations buttons
            (self.income_button, self.income),
            (self.expense_button, self.expense),
            (self.transfer_button, self.transfer),
            (self.readjustment_button, self.readjustment),
            # account creation
            (self.create_new_account_button, self.create_account),
            (self.back_button, self.back),
            # pie chart buttons
            (self.custom_period_button, self.custom_date_range_chart),
            (self.switch_type_button, self.switch_chart_type),
            (self.previous_month_button, self.previous_month_chart),
            (self.next_month_button, self.next_month_chart),
            (self.reset_month_button, self.current_month_chart),
            # browsing accounts and operations buttons
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

    def get_currency_list(self) -> List[str]:
        """
        Generate the list of used currencies. This method does not filter by active because the currency
        is a parameter needed to generate the charts to be desplayed even though all accounts are inactive
        """
        acc_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute()
        currencies_list = list({account.account_currency for account in acc_list})
        currencies_list.sort()
        return currencies_list

    def income(self) -> None:
        """Takes the user to the income screen"""
        income_window = incomeexpensescreen.IncomeExpenseScreen("income", widget=self.widget)
        self.widget.addWidget(income_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def expense(self) -> None:
        """Takes the user to the expense screen"""
        expense_window = incomeexpensescreen.IncomeExpenseScreen("expense", widget=self.widget)
        self.widget.addWidget(expense_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def transfer(self) -> None:
        """Takes the user to the transfer screen"""
        transfer_window = transferscreen.TransferScreen(widget=self.widget)
        self.widget.addWidget(transfer_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def readjustment(self) -> None:
        """Takes the user to the readjustment screen"""
        readjustment_window = readjustmentscreen.ReadjustmentScreen(widget=self.widget)
        self.widget.addWidget(readjustment_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def create_account(self) -> None:
        """Takes the user to the CreateAccount screen"""
        create_account_window = createaccountscreen.CreateAccount(widget=self.widget)
        self.widget.addWidget(create_account_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def browse_operations(self) -> None:
        """Takes the user to the browse operation screen"""
        browse_operation_window = operationbrowser.OperationBrowser(widget=self.widget)
        self.widget.addWidget(browse_operation_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def browse_accounts(self) -> None:
        """Takes the user to the browse account screen"""
        browse_account_window = accountbrowser.AccountBrowser(widget=self.widget)
        self.widget.addWidget(browse_account_window)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def current_month_chart(self):
        """generates a pie chart of the current month and resets all chart data variables"""
        # set the month in the selected datetime to one more mont
        self.selected_datetime = self.curr_datetime
        self.chart_type = "expense"
        data_inner, data_outer = piechartfunctions.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode="month",
            chart_type=self.chart_type,
            time_period=self.curr_datetime,
            currency=self.currency,
        )
        chart_title = piechartfunctions.update_n_format_chart_title(
            user_id=self.widget.user_object.user_id,
            currency=self.currency,
            time_period=self.selected_datetime,
            chart_mode="month",
            chart_type=self.chart_type,
        )
        self.chart.setTitle(chart_title)
        self.chart.generate_chart(data_inner, data_outer, self.chart_type)

    def next_month_chart(self):
        """Changes to a pie chart for the next month"""
        self.selected_datetime = piechartfunctions.get_next_month(self.selected_datetime)
        data_inner, data_outer = piechartfunctions.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode="month",
            chart_type=self.chart_type,
            time_period=self.selected_datetime,
            currency=self.currency,
        )
        chart_title = piechartfunctions.update_n_format_chart_title(
            user_id=self.widget.user_object.user_id,
            currency=self.currency,
            time_period=self.selected_datetime,
            chart_mode="month",
            chart_type=self.chart_type,
        )
        self.chart.setTitle(chart_title)
        self.chart.generate_chart(data_inner, data_outer, self.chart_type)

    def previous_month_chart(self):
        """Changes to a pie chart for the previus month"""
        self.selected_datetime = piechartfunctions.get_prev_month(self.selected_datetime)
        data_inner, data_outer = piechartfunctions.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode="month",
            chart_type=self.chart_type,
            time_period=self.selected_datetime,
            currency=self.currency,
        )
        chart_title = piechartfunctions.update_n_format_chart_title(
            user_id=self.widget.user_object.user_id,
            currency=self.currency,
            time_period=self.selected_datetime,
            chart_mode="month",
            chart_type=self.chart_type,
        )
        self.chart.setTitle(chart_title)
        self.chart.generate_chart(data_inner, data_outer, self.chart_type)

    def switch_chart_type(self):
        """Changes the pie chart from income to expenses and viceversa"""
        # if custom period is being used, switch with custom period
        if self.period_dict:
            stime = self.period_dict
        else:
            stime = self.selected_datetime
        # switch income<->expense and viceversa
        if self.chart_type == "income":
            self.chart_type = "expense"
        elif self.chart_type == "expense":
            self.chart_type = "income"
        data_inner, data_outer = piechartfunctions.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode=self.chart_mode,
            chart_type=self.chart_type,
            time_period=stime,
            currency=self.currency,
        )
        chart_title = piechartfunctions.update_n_format_chart_title(
            user_id=self.widget.user_object.user_id,
            currency=self.currency,
            time_period=stime,
            chart_mode=self.chart_mode,
            chart_type=self.chart_type,
        )
        self.chart.setTitle(chart_title)
        self.chart.generate_chart(data_inner, data_outer, self.chart_type)

    def custom_date_range_chart(self):
        """
        Generates a new piechart with selected time period in the calendar widget. First it opens up
        a calendar widget to select the 2 dates that conform the desired period of time. Then uses
        it to gather the information needed for the pie chart.
        """
        calendar_dialog = calendardialog.CalendarDialog()
        calendar_dialog.select_button.clicked.connect(calendar_dialog.get_date_range)
        calendar_dialog.exec_()

        self.chart_mode = "period"
        self.custom_initial_date = calendar_dialog.initial_d
        self.custom_final_date = calendar_dialog.final_d

        if self.custom_initial_date and self.custom_final_date:
            self.period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            data_inner, data_outer = piechartfunctions.load_data(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=self.period_dict,
                currency=self.currency,
            )
            chart_title = piechartfunctions.update_n_format_chart_title(
                user_id=self.widget.user_object.user_id,
                currency=self.currency,
                time_period=self.period_dict,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
            )
            self.chart.setTitle(chart_title)
            self.chart.generate_chart(data_inner, data_outer, self.chart_type)

    def change_currency_chart(self):
        """Change the currency of the pie chart"""
        if self.chart_mode == "period" and self.period_dict:
            stime = self.period_dict
        else:
            stime = self.selected_datetime
        self.currency = self.currency_combobox.currentText()

        data_inner, data_outer = piechartfunctions.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode=self.chart_mode,
            chart_type=self.chart_type,
            time_period=stime,
            currency=self.currency,
        )
        chart_title = piechartfunctions.update_n_format_chart_title(
            user_id=self.widget.user_object.user_id,
            currency=self.currency,
            time_period=stime,
            chart_mode=self.chart_mode,
            chart_type=self.chart_type,
        )
        self.chart.setTitle(chart_title)
        self.chart.generate_chart(data_inner, data_outer, self.chart_type)

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
