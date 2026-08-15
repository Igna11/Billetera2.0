"""
Tests for AccountDetailsDialog functionality.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from PyQt5.QtCore import Qt
import unittest.mock as mock

from billeUI.accountdetailsdialog import AccountDetailsDialog
from billeUI.accountbrowser import AccountRow
from src.models.accmodel import Accounts


class TestAccountDetailsDialog:
    """Test suite for AccountDetailsDialog."""

    def test_dialog_creation(self, qapp, mock_account):
        """Test that the dialog can be created with an account."""
        dialog = AccountDetailsDialog(mock_account)
        assert dialog is not None
        assert dialog.windowTitle() == "Account Details"
        dialog.close()

    def test_dialog_setup_ui_called(self, qapp, mock_account):
        """Test that setup_ui is called during initialization."""
        with mock.patch.object(AccountDetailsDialog, "setup_ui") as mock_setup:
            dialog = AccountDetailsDialog(mock_account)
            mock_setup.assert_called_once()
            dialog.close()

    def test_dialog_with_optional_fields(self, qapp, mock_user):
        """Test dialog with optional fields like tags and timestamps."""
        # Create account with optional fields
        test_account = Accounts(
            user_id=mock_user.user_id,
            account_name="TestAccount",
            account_currency="USD",
            account_total=Decimal("2500.50"),
            tags="personal,savings",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
        )

        dialog = AccountDetailsDialog(test_account)
        assert dialog is not None
        dialog.close()

    def test_dialog_with_none_values(self, qapp, mock_user):
        """Test dialog handles None values gracefully."""
        # Create account with None values
        test_account = Accounts(
            user_id=mock_user.user_id,
            account_name="TestAccount",
            account_currency="EUR",
            account_total=None,
            tags=None,
            created_at=None,
            updated_at=None,
        )

        dialog = AccountDetailsDialog(test_account)
        dialog.show()

        # Dialog should not crash with None values
        assert dialog is not None
        dialog.close()

    def test_dialog_minimum_size(self, qapp, mock_account):
        """Test that dialog has minimum size set."""
        dialog = AccountDetailsDialog(mock_account)
        assert dialog.minimumWidth() >= 400
        assert dialog.minimumHeight() >= 300
        dialog.close()


class TestAccountRowDoubleClick:
    """Test suite for AccountRow double-click functionality."""

    def test_account_row_has_double_click_method(self, qapp, mock_account):
        """Test that AccountRow has mouseDoubleClickEvent method."""
        row = AccountRow(mock_account)
        assert hasattr(row, "mouseDoubleClickEvent")
        row.close()

    def test_account_row_double_click_opens_dialog(self, qapp, mock_account):
        """Test that double-clicking an AccountRow opens the details dialog."""
        row = AccountRow(mock_account)

        # Mock the dialog creation to verify it's called
        with mock.patch("billeUI.accountbrowser.AccountDetailsDialog") as mock_dialog:
            row.mouseDoubleClickEvent(None)
            mock_dialog.assert_called_once_with(mock_account, row)

        row.close()

    def test_account_row_double_click_with_event(self, qapp, mock_account):
        """Test double-click event handling with proper event object."""
        from PyQt5.QtGui import QMouseEvent
        from PyQt5.QtCore import QPoint

        row = AccountRow(mock_account)

        # Mock the dialog to avoid hanging
        with mock.patch("billeUI.accountbrowser.AccountDetailsDialog") as mock_dialog:
            # Create a mock double-click event
            event = QMouseEvent(
                QMouseEvent.MouseButtonDblClick, QPoint(10, 10), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier
            )

            # This should not raise an exception
            row.mouseDoubleClickEvent(event)
            mock_dialog.assert_called_once()

        row.close()
