"""
Tests for AccountDetailsDialog and AccountRow tag editing functionality.
"""

from datetime import datetime
from decimal import Decimal
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QKeyEvent
import unittest.mock as mock

from billeUI.accountdetailsdialog import AccountDetailsDialog
from billeUI.accountbrowser import AccountRow, clean_tags
from src.models.accmodel import Accounts


class TestTagsValidation:
    """Test suite for tags validation functionality."""

    def test_clean_tags_removes_empty_segments(self):
        """Test that clean_tags removes empty segments."""
        assert clean_tags("hi,,yes, , no") == ("hi", "yes", "no")
        assert clean_tags("tag1,,tag2,,tag3") == ("tag1", "tag2", "tag3")

    def test_clean_tags_removes_extra_spaces(self):
        """Test that clean_tags removes extra spaces."""
        assert clean_tags("  tag1  ,  tag2  ") == ("tag1", "tag2")
        assert clean_tags(" tag1 , tag2 , tag3 ") == ("tag1", "tag2", "tag3")

    def test_clean_tags_handles_combined_issues(self):
        """Test that clean_tags handles both empty segments and spaces."""
        assert clean_tags("hi,,yes, , no") == ("hi", "yes", "no")
        assert clean_tags("  tag1  ,,  tag2  ,  , tag3  ") == ("tag1", "tag2", "tag3")

    def test_clean_tags_handles_empty_input(self):
        """Test that clean_tags handles empty input."""
        assert clean_tags("") is None
        assert clean_tags("   ") is None
        assert clean_tags(", , ,") is None

    def test_clean_tags_handles_single_tag(self):
        """Test that clean_tags handles single tag."""
        assert clean_tags("single") == ("single",)
        assert clean_tags("  single  ") == ("single",)

    def test_clean_tags_handles_already_clean_tags(self):
        """Test that clean_tags doesn't modify already clean tags."""
        assert clean_tags("tag1,tag2,tag3") == ("tag1", "tag2", "tag3")
        assert clean_tags("personal,savings") == ("personal", "savings")

    def test_account_model_accepts_none_tags(self, qapp):
        """Test that Accounts model accepts None as tags."""
        account = Accounts(
            user_id="test",
            account_name="TestAccount",
            account_currency="USD",
            tags=None,
        )
        assert account.tags is None

    def test_account_model_accepts_non_empty_tags(self, qapp):
        """Test that Accounts model accepts non-empty tags."""
        account = Accounts(
            user_id="test", account_name="TestAccount", account_currency="USD", tags=("personal", "savings")
        )
        assert account.tags == ("personal", "savings")

    def test_account_model_accepts_empty_tuple_tags(self, qapp):
        """Test that Accounts model accepts empty tuple tags."""
        account = Accounts(user_id="test", account_name="TestAccount", account_currency="USD", tags=())
        assert account.tags == ()

    def test_ui_converts_empty_tags_to_none(self, qapp, mock_account):
        """Test that UI converts empty tags to None."""
        row = AccountRow(mock_account)
        row.show()
        row.enable_edit_mode()
        row.tags_line_edit.setText("")  # Empty input
        row.show_qlabel()

        # Should convert empty string to None
        assert row.new_acc_tags is None
        assert "No tags" in row.tags_container.findChild(QLabel).text()
        row.close()

    def test_ui_cleans_malformed_tags(self, qapp, mock_account):
        """Test that UI cleans malformed tag input."""
        row = AccountRow(mock_account)
        row.show()
        row.enable_edit_mode()
        row.tags_line_edit.setText("hi,,yes, , no")  # Malformed input
        row.show_qlabel()

        # Should clean the tags
        assert row.new_acc_tags == ("hi", "yes", "no")
        # Check that tags are displayed in the container
        tag_labels = row.tags_container.findChildren(QLabel)
        tag_texts = [label.text() for label in tag_labels]
        assert "hi" in tag_texts
        assert "yes" in tag_texts
        assert "no" in tag_texts
        row.close()


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
            tags=("personal", "savings"),
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


class TestAccountRowTagEditing:
    """Test suite for AccountRow tag editing functionality."""

    def test_account_row_has_tags_label(self, qapp, mock_account):
        """Test that AccountRow displays tags label."""
        row = AccountRow(mock_account)
        row.show()
        assert hasattr(row, "tags_container")
        assert hasattr(row, "tags_line_edit")
        row.close()

    def test_account_row_tags_display_with_tags(self, qapp, mock_user):
        """Test that tags are displayed when account has tags."""
        test_account = Accounts(
            user_id=mock_user.user_id,
            account_name="TestAccount",
            account_currency="USD",
            account_total=Decimal("1000.00"),
            tags=("personal", "savings"),
        )
        row = AccountRow(test_account)
        row.show()
        # Check that tags are displayed in the container
        tag_labels = row.tags_container.findChildren(QLabel)
        tag_texts = [label.text() for label in tag_labels]
        assert "personal" in tag_texts
        assert "savings" in tag_texts
        row.close()

    def test_account_row_tags_display_without_tags(self, qapp, mock_account):
        """Test that 'No tags' is displayed when account has no tags."""
        row = AccountRow(mock_account)
        row.show()
        assert "No tags" in row.tags_container.findChild(QLabel).text()
        row.close()

    def test_edit_mode_shows_tags_field(self, qapp, mock_account):
        """Test that edit mode shows the tags edit field."""
        row = AccountRow(mock_account)
        row.show()
        row.enable_edit_mode()
        # Check that the field is shown (not hidden)
        assert not row.tags_line_edit.isHidden()
        assert row.tags_container.isHidden()
        row.close()

    def test_edit_mode_hides_tags_field_on_save(self, qapp, mock_account):
        """Test that tags field is hidden when editing is finished."""
        row = AccountRow(mock_account)
        row.show()
        row.enable_edit_mode()
        row.tags_line_edit.setText("test,new,tags")
        row.show_qlabel()
        # Check that the field is hidden
        assert row.tags_line_edit.isHidden()
        assert not row.tags_container.isHidden()
        row.close()

    def test_tag_changes_emit_modified_signal(self, qapp, mock_account):
        """Test that changing tags emits the modified signal."""
        row = AccountRow(mock_account)
        row.show()

        # Track signal emissions
        signal_emissions = []

        def slot(acc_id, name, tags, modified):
            signal_emissions.append((acc_id, name, tags, modified))

        row.account_modified.connect(slot)
        row.enable_edit_mode()
        row.tags_line_edit.setText("new,tags")
        row.show_qlabel()

        # Check that signal was emitted with modified=True
        assert len(signal_emissions) > 0
        assert signal_emissions[-1][3] == True  # modified should be True
        assert signal_emissions[-1][2] == ("new", "tags")  # tags should be updated

        row.close()

    def test_tag_changes_update_label(self, qapp, mock_account):
        """Test that tag changes update the display label."""
        row = AccountRow(mock_account)
        row.show()
        row.enable_edit_mode()
        row.tags_line_edit.setText("personal,business")
        row.show_qlabel()
        # Check that tags are displayed in the container
        tag_labels = row.tags_container.findChildren(QLabel)
        tag_texts = [label.text() for label in tag_labels]
        assert "personal" in tag_texts
        assert "business" in tag_texts
        row.close()

    def test_both_name_and_tags_changes_emit_modified(self, qapp, mock_account):
        """Test that changing both name and tags emits modified signal."""
        row = AccountRow(mock_account)
        row.show()

        # Track signal emissions
        signal_emissions = []

        def slot(acc_id, name, tags, modified):
            signal_emissions.append((acc_id, name, tags, modified))

        row.account_modified.connect(slot)
        row.enable_edit_mode()
        row.name_line_edit.setText("NewName")
        row.tags_line_edit.setText("new,tags")
        row.show_qlabel()

        # Check that signal was emitted with modified=True
        assert len(signal_emissions) > 0
        assert signal_emissions[-1][3] == True  # modified should be True
        assert signal_emissions[-1][1] == "NewName"
        assert signal_emissions[-1][2] == ("new", "tags")

        row.close()

    def test_no_changes_emits_not_modified(self, qapp, mock_account):
        """Test that no changes emits modified=False signal."""
        row = AccountRow(mock_account)
        row.show()

        # Track signal emissions
        signal_emissions = []

        def slot(acc_id, name, tags, modified):
            signal_emissions.append((acc_id, name, tags, modified))

        row.account_modified.connect(slot)
        row.enable_edit_mode()
        # Don't change anything (keep same values)
        row.name_line_edit.setText(row.account_name)
        row.tags_line_edit.setText(",".join(row.account_tags) if row.account_tags else "")
        row.show_qlabel()

        # Check that signal was emitted with modified=False
        assert len(signal_emissions) > 0
        assert signal_emissions[-1][3] == False  # modified should be False

        row.close()

    def test_edit_mode_does_not_close_on_focus_change(self, qapp, mock_account):
        """Test that edit mode doesn't close when clicking away from line edit (the bug fix)."""
        row = AccountRow(mock_account)
        row.show()

        # Enter edit mode
        row.enable_edit_mode()

        # Verify we're in edit mode
        assert not row.name_line_edit.isHidden()
        assert not row.tags_line_edit.isHidden()
        assert row.name_label.isHidden()
        assert row.tags_container.isHidden()

        # Simulate focus change by clearing focus from name line edit
        # This should NOT trigger show_qlabel() anymore (the bug fix)
        row.name_line_edit.clearFocus()

        # Verify we're still in edit mode (this is the key test for the bug fix)
        assert not row.name_line_edit.isHidden()
        assert not row.tags_line_edit.isHidden()
        assert row.name_label.isHidden()
        assert row.tags_container.isHidden()

        # Now properly complete editing by pressing Enter
        row.tags_line_edit.setText("new,tags")
        row.show_qlabel()

        # Verify edit mode is now properly closed
        assert row.name_line_edit.isHidden()
        assert row.tags_line_edit.isHidden()
        assert not row.name_label.isHidden()
        assert not row.tags_container.isHidden()

        row.close()

    def test_return_key_moves_focus_from_name_to_tags(self, qapp, mock_account):
        """Test that pressing Enter in name field moves focus to tags field."""
        row = AccountRow(mock_account)
        row.show()

        # Enter edit mode
        row.enable_edit_mode()

        # Simulate pressing Enter in name field
        row.name_line_edit.returnPressed.emit()

        # Verify the method was called (in headless mode we can't reliably test focus)
        # but we can verify the widgets are still in edit mode
        assert not row.name_line_edit.isHidden()
        assert not row.tags_line_edit.isHidden()

        row.close()

    def test_return_key_in_tags_completes_editing(self, qapp, mock_account):
        """Test that pressing Enter in tags field completes editing."""
        row = AccountRow(mock_account)
        row.show()

        # Track signal emissions
        signal_emissions = []

        def slot(acc_id, name, tags, modified):
            signal_emissions.append((acc_id, name, tags, modified))

        row.account_modified.connect(slot)

        # Enter edit mode
        row.enable_edit_mode()
        row.tags_line_edit.setText("new,tags")

        # Simulate pressing Enter in tags field
        row.tags_line_edit.returnPressed.emit()

        # Verify editing completed
        assert row.name_line_edit.isHidden()
        assert row.tags_line_edit.isHidden()
        assert not row.name_label.isHidden()
        assert not row.tags_container.isHidden()

        # Verify signal was emitted
        assert len(signal_emissions) > 0

        row.close()

    def test_escape_key_cancels_edit_mode(self, qapp, mock_account):
        """Test that pressing Escape cancels edit mode and reverts changes."""
        row = AccountRow(mock_account)
        row.show()

        # Enter edit mode
        row.enable_edit_mode()
        row.name_line_edit.setText("ChangedName")
        row.tags_line_edit.setText("changed,tags")

        # Simulate pressing Escape
        escape_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        row.keyPressEvent(escape_event)

        # Verify edit mode was cancelled
        assert row.name_line_edit.isHidden()
        assert row.tags_line_edit.isHidden()
        assert not row.name_label.isHidden()
        assert not row.tags_container.isHidden()

        # Verify name was reverted (check the label, not the line edit)
        assert row.account_name in row.name_label.text()

        row.close()
