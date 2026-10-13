#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Selection Dialog
Dialog for selecting multiple accounts to calculate total sum
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QLabel,
    QScrollArea,
    QWidget,
)


class AccountSelectionDialog(QDialog):
    """
    Dialog for selecting multiple accounts to include in total calculation.
    If no accounts are selected, it behaves as default (show current account only).
    """

    def __init__(self, accounts, parent=None, selected_account_ids=None):
        super().__init__(parent)
        self.accounts = accounts
        self.selected_accounts = set()
        self.previously_selected_ids = selected_account_ids if selected_account_ids else set()
        self.setMinimumSize(400, 300)
        self.setWindowTitle("Select Accounts for Total")

        self.setup_ui()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Title label
        title_label = QLabel("Select accounts to include in total sum:")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        main_layout.addWidget(title_label)

        # Instructions label
        info_label = QLabel("Uncheck accounts to exclude them from total")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        main_layout.addWidget(info_label)

        # Scroll area for checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.checkboxes_layout = QVBoxLayout()
        scroll_widget.setLayout(self.checkboxes_layout)

        # Create checkboxes for each account
        for account in self.accounts:
            checkbox = QCheckBox(f"{account.account_name} ({account.account_currency})")
            checkbox.account_id = account.account_id

            # Set checkbox state based on previous selection
            if self.previously_selected_ids:
                # If there's a previous selection, only check those accounts
                if account.account_id in self.previously_selected_ids:
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
            else:
                # First time opening: check all accounts (default behavior)
                checkbox.setChecked(True)

            self.checkboxes_layout.addWidget(checkbox)

        self.checkboxes_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Button layout
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()

        # Connect buttons
        self.select_button.clicked.connect(self.get_selected_accounts)
        self.select_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def get_selected_accounts(self):
        """Get the set of selected account IDs"""
        self.selected_accounts = set()
        all_checked = True
        checkbox_count = 0

        for i in range(self.checkboxes_layout.count()):
            widget = self.checkboxes_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                checkbox_count += 1
                if widget.isChecked():
                    self.selected_accounts.add(widget.account_id)
                else:
                    all_checked = False

        # If all checkboxes are checked, return empty set (means "all accounts")
        # If none are checked, also return empty set (means "all accounts" - default behavior)
        if all_checked or not self.selected_accounts:
            self.selected_accounts = set()
