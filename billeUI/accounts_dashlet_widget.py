#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 29/07/2023
"""
import os
from typing import List
from decimal import Decimal

from PyQt5.QtWidgets import QWidget, QDialog
from PyQt5.uic import loadUi

from src.models.accmodel import Accounts

from billeUI import UISPATH, currency_format
from billeUI.accountselectiondialog import AccountSelectionDialog


class AccountDashletWidget(QWidget):
    def __init__(self, acc_list):
        super().__init__()
        dashlet_widget = os.path.join(UISPATH, "account_dashlet_widget.ui")
        loadUi(dashlet_widget, self)
        # variables
        self.acc_index = 0
        self.acc_list = acc_list
        self.account_name = None
        self.account_currency = None
        # Initialize with all account IDs selected (default behavior)
        self.selected_account_ids = {acc.account_id for acc in self.acc_list}
        # buttons
        self.acc_next_button.clicked.connect(self.next_acc)
        self.acc_prev_button.clicked.connect(self.prev_acc)
        # Double-click event for acc_total_label to open account selection dialog
        self.acc_total_label.mouseDoubleClickEvent = self.on_acc_total_label_double_click
        self.set_labels()
        self.total = self._calculate_total()

    def _calculate_total(self) -> Decimal:
        total = Decimal(0)
        # Calculate total based on selected accounts or all accounts
        # If selected_account_ids is empty, it means "all accounts" (default behavior)
        # If it has specific IDs, only sum those accounts
        accounts_to_sum = self.acc_list
        if self.selected_account_ids:
            accounts_to_sum = [acc for acc in self.acc_list if acc.account_id in self.selected_account_ids]

        for account in accounts_to_sum:
            if account.account_total:
                total += Decimal(account.account_total)
        return total

    def on_acc_total_label_double_click(self, event):
        """Handle double-click on acc_total_label to open account selection dialog"""
        if not self.acc_list:
            return

        dialog = AccountSelectionDialog(self.acc_list, self, self.selected_account_ids)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            self.selected_account_ids = dialog.selected_accounts
            self.set_labels()

    def set_monthly_balance(self, balance: Decimal) -> None:
        if balance >= 0:
            text_color = "green"
            arrow = "\u2197"
        else:
            text_color = "red"
            arrow = "\u2198"
        text = f"Balance: <font color='{text_color}'><b>{currency_format(balance)} {self.account_currency} {arrow}</b></font>"
        self.balance_label.setText(text)

    def set_labels(self):
        """Sets the values of acc_name, acc_currency and the value of total label."""
        if not self.acc_list:
            self.acc_label.setText("None")
        else:
            self.account_name = self.acc_list[self.acc_index].model_dump()["account_name"]
            self.account_currency = self.acc_list[self.acc_index].model_dump()["account_currency"]
            account_total = (
                f"Total: <b>{currency_format(self.acc_list[self.acc_index].model_dump()['account_total'])}</b>"
            )

            # Calculate filtered total and add indication if filtered
            calculated_total = self._calculate_total()
            # Only show "selected" indicator if not all accounts are selected
            if self.selected_account_ids and len(self.selected_account_ids) != len(self.acc_list):
                user_total = f"Total: <b>{currency_format(calculated_total)} ({self.account_currency})</b> <i>({len(self.selected_account_ids)} selected)</i>"
            else:
                user_total = f"Total: <b>{currency_format(calculated_total)} ({self.account_currency})</b>"

            self.acc_label.setText(f"{self.account_name} ({self.account_currency})")
            self.total_label.setText(account_total)
            self.acc_total_label.setText(user_total)

    def next_acc(self):
        """Increments the index number that determines which account data will be displayed"""
        if self.acc_index < len(self.acc_list) - 1:
            self.acc_index += 1
        else:
            self.acc_index = 0
        self.set_labels()

    def prev_acc(self):
        """Decreases the index number that determines which account data will be displayed"""
        if self.acc_index > 0:
            self.acc_index -= 1
        else:
            self.acc_index = len(self.acc_list) - 1
        self.set_labels()

    def update_data(self, data: List[Accounts]) -> None:
        self.acc_list = data
        # Update selected_account_ids to include new accounts and remove deleted ones
        current_account_ids = {acc.account_id for acc in self.acc_list}
        if self.selected_account_ids:
            # Remove IDs of deleted accounts
            self.selected_account_ids = self.selected_account_ids.intersection(current_account_ids)
        else:
            # If no selection, set to all accounts (default behavior)
            self.selected_account_ids = current_account_ids
        self._calculate_total()
        self.set_labels()
