#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 12/02/2023 18:10

@author: igna
"""
import os
from decimal import Decimal, InvalidOperation

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QToolButton

from src.queries.accqueries import ListAccountsQuery
from src.ophandlers.operationhandler import NegativeAccountTotalError
from src.ophandlers.transferhandler import (
    TransferHandler,
    EmptyAccountError,
    DifferentCurrencyTransferError,
    SameAccountError,
)

from billeUI import UISPATH, operationscreen, animatedlabel


class TransferScreen(QMainWindow):
    """
    Screen where the user can make transfers between accounts
    """

    def __init__(self, operation_flag: str, parent=None, widget=None):
        super(TransferScreen, self).__init__(parent)
        operation_transfer_screen = os.path.join(UISPATH, "operation_transfer_screen.ui")
        loadUi(operation_transfer_screen, self)
        self.widget = widget
        self.operation_flag = operation_flag
        self.acc_object_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        self.acc_item_list = [f"{acc.account_name} ({acc.account_currency})" for acc in self.acc_object_list]

        # origin account info
        self.origin_acc_name = None
        self.origin_acc_currency = None
        self.origin_acc_total = None
        # destination account info
        self.dest_acc_name = None
        self.dest_acc_currency = None
        self.dest_acc_total = None

        # origin accounts comboBox
        self.accounts_origin_comboBox.addItems(self.acc_item_list)
        self.set_origin_acc_data(self.accounts_origin_comboBox.currentIndex())
        self.accounts_origin_comboBox.currentIndexChanged.connect(self.set_origin_acc_data)

        # dest accounts comboBox
        self.accounts_dest_comboBox.addItems(self.acc_item_list)
        self.set_dest_acc_data(self.accounts_dest_comboBox.currentIndex())
        self.accounts_dest_comboBox.currentIndexChanged.connect(self.set_dest_acc_data)

        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.cancel)
        self.setup_all_button_in_lineedit()

    def setup_all_button_in_lineedit(self):
        """Embeds a clickable 'All' button into the quantity_line QLineEdit."""
        self.all_button = QToolButton(self.quantity_line)
        self.all_button.setText("All")
        self.all_button.setCursor(Qt.PointingHandCursor)
        self.all_button.setStyleSheet(
            """
            QToolButton {
                padding: 0px;
                border: none;
                color: #007bff;
                font-weight: bold;
                background: transparent;
            }
            QToolButton:hover {
                color: #0056b3;
                text-decoration: underline;
            }
        """
        )

        # Adjust size and position
        height = self.quantity_line.sizeHint().height() - 2
        self.all_button.setFixedSize(QtCore.QSize(30, height))
        self.quantity_line.setTextMargins(0, 0, self.all_button.width() + 6, 0)
        # Click event
        self.all_button.clicked.connect(self.insert_full_amount)
        # position
        original_resize_event = self.quantity_line.resizeEvent

        def resizeEvent(event):
            x = self.quantity_line.rect().right() - self.all_button.width() - 4
            y = (self.quantity_line.height() - self.all_button.height()) // 2
            self.all_button.move(x, y)
            if original_resize_event:
                original_resize_event(event)

        self.quantity_line.resizeEvent = resizeEvent

    def insert_full_amount(self):
        """Sets the total amount in the quantity field for transfers"""
        if self.origin_acc_total is not None:
            self.quantity_line.setText(str(self.origin_acc_total))

    def set_origin_acc_data(self, i: int):
        """
        Called when user switchs items in the comboBox in order to update the
        total value of the origin account
        """
        self.acc_object_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        self.acc_item_list = [f"{acc.account_name} ({acc.account_currency})" for acc in self.acc_object_list]
        self.origin_account_object = self.acc_object_list[i]
        self.origin_acc_currency = self.origin_account_object.account_currency
        self.origin_acc_total = self.origin_account_object.account_total
        self.total_origin_label.setText(f"<b>Total</b>: {self.origin_acc_total}")

    def set_dest_acc_data(self, i: int):
        """
        Called when user switchs items in the comboBox in order to update the
        total value of the destination account
        """
        self.acc_object_list = ListAccountsQuery(user_id=self.widget.user_object.user_id).execute(active=1)
        self.acc_item_list = [f"{acc.account_name} ({acc.account_currency})" for acc in self.acc_object_list]
        self.destination_account_object = self.acc_object_list[i]
        self.destination_acc_currency = self.destination_account_object.account_currency
        self.destination_acc_total = self.destination_account_object.account_total
        self.total_dest_label.setText(f"<b>Total</b>: {self.destination_acc_total}")

    def save(self):
        """Function called by the save_button to perform the transfer."""
        try:
            value = Decimal(self.quantity_line.text())
            transfer = TransferHandler(user_id=self.widget.user_object.user_id, amount=value)
            trin, trout = transfer.set_transfer_objects(
                in_acc=self.destination_account_object.account_id, out_acc=self.origin_account_object.account_id
            )
            transfer.create_transfer(transfer_object_in=trin, transfer_object_out=trout)

            self.status_label.setText("<font color='green'>Transfer successfull!</font>")
            # Display the new totals
            self.set_origin_acc_data(self.accounts_origin_comboBox.currentIndex())
            self.set_dest_acc_data(self.accounts_dest_comboBox.currentIndex())
            animatedlabel.AnimatedLabel("Transfer successfull ✅", message_type="success").display()
        except InvalidOperation:  # Decimal error
            animatedlabel.AnimatedLabel("Incorrect amount!", message_type="warning").display()
            self.status_label.setText("<font color='red'>Amount to transfer can not be null.</font>")
        except ValueError as e:
            animatedlabel.AnimatedLabel("Invalid value!", message_type="error").display()
            self.status_label.setText("<font color='red'>Invalid value entered.</font>")
        except SameAccountError:
            animatedlabel.AnimatedLabel("Origin and destination are the same!", message_type="warning").display()
            self.status_label.setText("<font color='red'>Origin and destination accounts can't be the same.</font>")
        except DifferentCurrencyTransferError:
            animatedlabel.AnimatedLabel("Currencies must be the same!", message_type="warning").display()
            self.status_label.setText(
                "<font color='red'>Can not transfer between accounts with different currencies.</font>"
            )
        except EmptyAccountError:
            animatedlabel.AnimatedLabel("Empty account!", message_type="error").display()
            self.status_label.setText("<font color='red'>Origin account is empty.")
        except NegativeAccountTotalError:
            animatedlabel.AnimatedLabel("Invalid amount!", message_type="error").display()
            self.status_label.setText(
                f"<font color='red'>Can not transfer more than the current balance of the account: {value}."
            )

    def cancel(self):
        """Returns to previous screen OperationScreen menu."""
        operation_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(operation_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to OperationScreen menu when the Esc key is pressed"""
        if e.key() == QtCore.Qt.Key_Escape:
            operation_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(operation_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
