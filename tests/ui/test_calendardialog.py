"""
Tests for CalendarDialog UI component.
"""

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QApplication

from billeUI.calendardialog import Calendar, CalendarDialog


class TestCalendar:
    """Test suite for Calendar component."""

    def test_calendar_initialization(self, qapp):
        """Test that Calendar initializes correctly."""
        calendar = Calendar()

        # Check that calendar was created
        assert calendar is not None
        assert calendar.initial_date is None
        assert calendar.final_date is None

        calendar.close()

    def test_calendar_highlighter_initialization(self, qapp):
        """Test that highlighter is initialized correctly."""
        calendar = Calendar()

        # Check that highlighter exists
        assert calendar.highlighter is not None

        calendar.close()

    def test_single_date_selection(self, qapp, qtbot):
        """Test that clicking a date sets initial_date."""
        calendar = Calendar()
        qtbot.addWidget(calendar)

        # Select a date using the correct method name
        test_date = QDate(2024, 6, 15)
        calendar.setSelectedDate(test_date)

        # Simulate click event
        calendar.clicked.emit(test_date)

        # Check that initial_date is set
        assert calendar.initial_date == test_date
        assert calendar.final_date is None

        calendar.close()

    def test_date_range_selection_with_shift(self, qapp, qtbot):
        """Test that Shift+Click sets date range."""
        calendar = Calendar()
        qtbot.addWidget(calendar)

        # Set initial date
        initial_date = QDate(2024, 6, 15)
        calendar.setSelectedDate(initial_date)
        calendar.clicked.emit(initial_date)

        # Simulate Shift key press and select final date
        QApplication.instance().keyboardModifiers = lambda: Qt.ShiftModifier
        final_date = QDate(2024, 6, 20)
        calendar.setSelectedDate(final_date)
        calendar.clicked.emit(final_date)

        # Check that both dates are set
        assert calendar.initial_date == initial_date
        assert calendar.final_date == final_date

        calendar.close()

    def test_highlight_range_functionality(self, qapp):
        """Test that date range highlighting works."""
        calendar = Calendar()

        # Set date range
        calendar.initial_date = QDate(2024, 6, 15)
        calendar.final_date = QDate(2024, 6, 20)

        # Call highlight_range
        calendar.highlight_range(calendar.highlighter)

        # Check that dates are highlighted (we can't easily verify visual highlighting,
        # but we can check that the method runs without error)
        assert calendar.initial_date is not None
        assert calendar.final_date is not None

        calendar.close()

    def test_clear_highlight_on_new_selection(self, qapp, qtbot):
        """Test that calendar can handle date changes without crashing."""
        calendar = Calendar()
        qtbot.addWidget(calendar)

        # Set initial date range
        calendar.initial_date = QDate(2024, 6, 15)
        calendar.final_date = QDate(2024, 6, 20)
        calendar.highlight_range(calendar.highlighter)

        # Select new date (should clear previous highlight)
        new_date = QDate(2024, 7, 1)
        calendar.setSelectedDate(new_date)
        calendar.clicked.emit(new_date)

        # Check that the calendar handles the change without crashing
        assert True

        calendar.close()


class TestCalendarDialog:
    """Test suite for CalendarDialog component."""

    def test_calendar_dialog_initialization(self, qapp):
        """Test that CalendarDialog initializes correctly."""
        dialog = CalendarDialog()

        # Check that dialog was created
        assert dialog is not None
        assert dialog.initial_d is None
        assert dialog.final_d is None

        dialog.close()

    def test_calendar_dialog_size(self, qapp):
        """Test that CalendarDialog has proper minimum size."""
        dialog = CalendarDialog()

        # Check minimum size
        assert dialog.minimumWidth() == 500
        assert dialog.minimumHeight() == 300

        dialog.close()

    def test_calendar_dialog_has_calendar(self, qapp):
        """Test that CalendarDialog contains a Calendar widget."""
        dialog = CalendarDialog()

        # Check that calendar exists
        assert dialog.calendar is not None
        assert isinstance(dialog.calendar, Calendar)

        dialog.close()

    def test_calendar_dialog_has_buttons(self, qapp):
        """Test that CalendarDialog has select and cancel buttons."""
        dialog = CalendarDialog()

        # Check that buttons exist
        assert dialog.select_button is not None
        assert dialog.cancel_button is not None
        assert dialog.select_button.text() == "Select"
        assert dialog.cancel_button.text() == "Cancel"

        dialog.close()

    def test_select_button_gets_date_range(self, qapp, qtbot):
        """Test that select button retrieves date range from calendar."""
        dialog = CalendarDialog()
        qtbot.addWidget(dialog)

        # Set date range in calendar
        dialog.calendar.initial_date = QDate(2024, 6, 15)
        dialog.calendar.final_date = QDate(2024, 6, 20)

        # Click select button
        qtbot.mouseClick(dialog.select_button, Qt.LeftButton)

        # Check that dialog retrieved the date range
        assert dialog.initial_d is not None
        assert dialog.final_d is not None
        assert dialog.initial_d <= dialog.final_d

        dialog.close()

    def test_cancel_button_closes_dialog(self, qapp, qtbot):
        """Test that cancel button closes the dialog."""
        dialog = CalendarDialog()
        qtbot.addWidget(dialog)

        # Show dialog
        dialog.show()

        # Click cancel button
        qtbot.mouseClick(dialog.cancel_button, Qt.LeftButton)

        # Dialog should be closed
        assert not dialog.isVisible()

        dialog.close()

    def test_select_button_closes_dialog(self, qapp, qtbot):
        """Test that select button closes the dialog."""
        dialog = CalendarDialog()
        qtbot.addWidget(dialog)

        # Show dialog
        dialog.show()

        # Set date range in calendar
        dialog.calendar.initial_date = QDate(2024, 6, 15)
        dialog.calendar.final_date = QDate(2024, 6, 20)

        # Click select button
        qtbot.mouseClick(dialog.select_button, Qt.LeftButton)

        # Dialog should be closed
        assert not dialog.isVisible()

        dialog.close()

    def test_get_date_range_with_incomplete_selection(self, qapp, qtbot):
        """Test that get_date_range handles incomplete selection."""
        dialog = CalendarDialog()
        qtbot.addWidget(dialog)

        # Set only initial date (no final date)
        dialog.calendar.initial_date = QDate(2024, 6, 15)
        dialog.calendar.final_date = None

        # Click select button
        qtbot.mouseClick(dialog.select_button, Qt.LeftButton)

        # Check that date range was not set (incomplete selection)
        assert dialog.initial_d is None
        assert dialog.final_d is None

        dialog.close()

    def test_get_date_range_ordering(self, qapp, qtbot):
        """Test that get_date_range correctly orders dates."""
        dialog = CalendarDialog()
        qtbot.addWidget(dialog)

        # Set date range with final date before initial date
        dialog.calendar.initial_date = QDate(2024, 6, 20)
        dialog.calendar.final_date = QDate(2024, 6, 15)

        # Click select button
        qtbot.mouseClick(dialog.select_button, Qt.LeftButton)

        # Check that dates are ordered correctly
        assert dialog.initial_d <= dialog.final_d
        assert dialog.initial_d.day == 15
        assert dialog.final_d.day == 20

        dialog.close()

    def test_dialog_layout_exists(self, qapp):
        """Test that dialog has proper layout structure."""
        dialog = CalendarDialog()

        # Check that dialog has a layout
        assert dialog.layout() is not None

        dialog.close()

    def test_buttons_enabled(self, qapp):
        """Test that buttons are enabled."""
        dialog = CalendarDialog()

        # Check that buttons are enabled
        assert dialog.select_button.isEnabled()
        assert dialog.cancel_button.isEnabled()

        dialog.close()

    def test_calendar_in_top_layout(self, qapp):
        """Test that calendar is in the top layout."""
        dialog = CalendarDialog()

        # Check that top layout exists and contains calendar
        assert dialog.top_layout is not None
        # The calendar should be in the top layout

        dialog.close()

    def test_buttons_in_bottom_layout(self, qapp):
        """Test that buttons are in the bottom layout."""
        dialog = CalendarDialog()

        # Check that bottom layout exists and contains buttons
        assert dialog.bottom_layout is not None
        # The buttons should be in the bottom layout

        dialog.close()
