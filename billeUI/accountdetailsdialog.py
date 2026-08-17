#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Details Dialog
Displays detailed information about an account in a read-only dialog.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.models.accmodel import Accounts
from billeUI import currency_format
from billeUI.taglabel import TagContainer


class AccountDetailsDialog(QDialog):
    """
    Dialog to display detailed account information.
    """

    def __init__(self, account: Accounts, parent=None):
        super().__init__(parent)
        self.account = account
        self.setWindowTitle("Account Details")
        self.setMinimumSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI with account information."""
        layout = QVBoxLayout()

        # Title
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label = QLabel(f"{self.account.account_name} ({self.account.account_currency})")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # information label
        info_font = QFont()
        info_font.setPointSize(6)
        information_label = QLabel("Account information")
        information_label.setFont(info_font)
        information_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(information_label)

        # Total
        total_text = (
            f"{currency_format(self.account.account_total)} {self.account.account_currency}"
            if self.account.account_total is not None
            else "N/A"
        )
        total_label = QLabel(f"<b>Total:</b> {total_text}")
        layout.addWidget(total_label)
        # Account Name
        name_label = QLabel(f"<b>Account Name:</b> {self.account.account_name or 'N/A'}")
        layout.addWidget(name_label)
        # Currency
        currency_label = QLabel(f"<b>Currency:</b> {self.account.account_currency or 'N/A'}")
        layout.addWidget(currency_label)
        # Tags
        tags_label = QLabel("<b>Tags:</b>")
        layout.addWidget(tags_label)
        tags_container = TagContainer(self.account.tags, show_close_buttons=False)
        layout.addWidget(tags_container)
        # Created At
        created_text = self.account.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.account.created_at else "N/A"
        created_label = QLabel(f"<b>Created At:</b> {created_text}")
        layout.addWidget(created_label)
        # Updated At
        updated_text = self.account.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.account.updated_at else "N/A"
        updated_label = QLabel(f"<b>Last Updated:</b> {updated_text}")
        layout.addWidget(updated_label)
        # Active Status
        status_text = "Active" if self.account.is_active else "Inactive"
        status_label = QLabel(f"<b>Status:</b> {status_text}")
        layout.addWidget(status_label)
        # Account ID
        id_label = QLabel(f"<b>Account ID:</b> {self.account.account_id}")
        layout.addWidget(id_label)

        layout.addStretch()

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)
