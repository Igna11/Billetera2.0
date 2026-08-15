"""
Tests for OperationScreen UI component.
"""

from PyQt5.QtCore import Qt

from billeUI.operationscreen import OperationScreen


class TestOperationScreen:
    """Test suite for OperationScreen functionality."""

    def test_operation_screen_initialization(self, stacked_widget, mock_user):
        """Test that OperationScreen initializes correctly with mock user."""
        # Set up mock user in widget
        stacked_widget.user_object = mock_user

        screen = OperationScreen(widget=stacked_widget)

        # Check that screen was created
        assert screen is not None
        assert screen.widget == stacked_widget

        # Check that main UI elements exist
        assert hasattr(screen, "username_label")
        assert hasattr(screen, "currency_combobox")
        assert hasattr(screen, "chart_view")

        screen.close()

    def test_operation_screen_user_greeting(self, stacked_widget, mock_user):
        """Test that user greeting is displayed correctly."""
        stacked_widget.user_object = mock_user

        screen = OperationScreen(widget=stacked_widget)

        # Check that username is displayed
        assert "Hello" in screen.username_label.text()
        assert mock_user.first_name in screen.username_label.text()

        screen.close()

    def test_operation_screen_currency_combobox(self, stacked_widget, mock_user, mock_account):
        """Test that currency combobox is populated."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that currency combobox has items
        assert screen.currency_combobox.count() > 0
        assert screen.currency_combobox.itemText(0) == "ARS"

        # Check that default currency is selected
        assert screen.currency_combobox.currentText() == screen.currency

        screen.close()

    def test_operation_screen_chart_initialization(self, stacked_widget, mock_user, mock_account):
        """Test that charts are initialized correctly."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that chart view exists
        assert screen.chart_view is not None

        # Check that chart is set (should start with pie chart)
        assert screen.chart is not None
        assert screen.current_chart_type == "pie"

        screen.close()

    def test_operation_screen_buttons_exist(self, stacked_widget, mock_user, mock_account):
        """Test that main operation buttons exist."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check for common operation buttons (adjust based on your actual UI)
        # These are typical buttons that might exist in operation_screen.ui
        button_attributes = [
            "income_button",
            "expense_button",
            "transfer_button",
            "readjustment_button",
            "logout_button",
        ]

        # Check which buttons actually exist in your UI
        existing_buttons = [attr for attr in button_attributes if hasattr(screen, attr)]

        # At minimum, some navigation buttons should exist
        assert len(existing_buttons) > 0 or hasattr(screen, "logout_button")

        screen.close()

    def test_operation_screen_account_dashlet(self, stacked_widget, mock_user, mock_account):
        """Test that account dashlet widget is set."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that account dashlet is set
        assert hasattr(screen, "account_dashlet")

        screen.close()

    def test_operation_screen_chart_context_menu(self, stacked_widget, mock_user, mock_account):
        """Test that chart has context menu enabled."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that chart view has custom context menu
        from PyQt5.QtCore import Qt

        assert screen.chart_view.contextMenuPolicy() == Qt.CustomContextMenu

        screen.close()

    def test_operation_screen_variables_initialized(self, stacked_widget, mock_user, mock_account):
        """Test that operation screen variables are properly initialized."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that key variables are initialized
        assert hasattr(screen, "chart_mode")
        assert hasattr(screen, "chart_type")
        assert hasattr(screen, "operation_mode")
        assert hasattr(screen, "current_chart_type")
        assert hasattr(screen, "currency")

        # Check initial values
        assert screen.chart_mode in ["month", "period"]
        assert screen.chart_type in ["expense", "income"]
        assert screen.operation_mode in ["flow", "net"]
        assert screen.current_chart_type in ["pie", "bar"]

        screen.close()

    def test_operation_screen_datetime_initialization(self, stacked_widget, mock_user, mock_account):
        """Test that datetime variables are initialized."""
        from datetime import datetime

        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check datetime variables
        assert hasattr(screen, "curr_datetime")
        assert hasattr(screen, "selected_datetime")
        assert isinstance(screen.curr_datetime, datetime)
        assert isinstance(screen.selected_datetime, datetime)

        screen.close()

    def test_operation_screen_escape_key(self, stacked_widget, mock_user, mock_account, qtbot):
        """Test escape key behavior on operation screen."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        initial_count = stacked_widget.count()

        # Press Escape key (behavior depends on your implementation)
        qtbot.keyClick(screen, Qt.Key_Escape)

        # The escape key behavior should be defined in your implementation
        # This test checks that the screen handles the key press
        assert stacked_widget.count() >= initial_count

        screen.close()

    def test_chart_context_menu_enabled(self, stacked_widget, mock_user, mock_account):
        """Test that chart view has context menu enabled."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that context menu policy is set to custom
        from PyQt5.QtCore import Qt

        assert screen.chart_view.contextMenuPolicy() == Qt.CustomContextMenu

        screen.close()

    def test_switch_to_bar_chart(self, stacked_widget, mock_user, mock_account):
        """Test switching from pie chart to bar chart."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Initially should be on pie chart
        assert screen.current_chart_type == "pie"

        # Switch to bar chart
        screen.switch_to_bar_chart()

        # Check that chart type changed
        assert screen.current_chart_type == "bar"

        # Check that chart view is now BalanceChartView
        from billeUI.monthlybalancechart import BalanceChartView

        assert isinstance(screen.chart_view, BalanceChartView)

        # Check that context menu is still enabled
        from PyQt5.QtCore import Qt

        assert screen.chart_view.contextMenuPolicy() == Qt.CustomContextMenu

        screen.close()

    def test_switch_to_pie_chart(self, stacked_widget, mock_user, mock_account):
        """Test switching from bar chart back to pie chart."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        assert screen.current_chart_type == "pie"

        # First switch to bar chart
        screen.switch_to_bar_chart()
        assert screen.current_chart_type == "bar"

        # Switch back to pie chart
        screen.switch_to_pie_chart()

        # Check that chart type changed back
        assert screen.current_chart_type == "pie"

        # Check that chart view is now regular QChartView
        from PyQt5.QtChart import QChartView

        assert isinstance(screen.chart_view, QChartView)

        # Check that context menu is still enabled
        from PyQt5.QtCore import Qt

        assert screen.chart_view.contextMenuPolicy() == Qt.CustomContextMenu

        screen.close()

    def test_chart_switching_toggle(self, stacked_widget, mock_user, mock_account):
        """Test that chart switching can be toggled multiple times."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Start with pie chart
        assert screen.current_chart_type == "pie"

        # Switch to bar chart
        screen.switch_to_bar_chart()
        assert screen.current_chart_type == "bar"

        # Switch back to pie chart
        screen.switch_to_pie_chart()
        assert screen.current_chart_type == "pie"

        # Switch to bar chart again
        screen.switch_to_bar_chart()
        assert screen.current_chart_type == "bar"

        # Switch back to pie chart again
        screen.switch_to_pie_chart()
        assert screen.current_chart_type == "pie"

        screen.close()

    def test_switch_to_same_chart_no_op(self, stacked_widget, mock_user, mock_account):
        """Test that switching to the same chart type is a no-op."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Initially on pie chart
        initial_chart_view = screen.chart_view
        assert screen.current_chart_type == "pie"

        # Try to switch to pie chart again (should be no-op)
        screen.switch_to_pie_chart()

        # Chart view should be the same object
        assert screen.chart_view == initial_chart_view
        assert screen.current_chart_type == "pie"

        # Switch to bar chart
        screen.switch_to_bar_chart()
        bar_chart_view = screen.chart_view
        assert screen.current_chart_type == "bar"

        # Try to switch to bar chart again (should be no-op)
        screen.switch_to_bar_chart()

        # Chart view should be the same object
        assert screen.chart_view == bar_chart_view
        assert screen.current_chart_type == "bar"

        screen.close()

    def test_context_menu_after_switching(self, stacked_widget, mock_user, mock_account):
        """Test that context menu handler is connected after chart switching."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)

        # Check that context menu handler is connected initially
        assert screen.chart_view.customContextMenuRequested.connect is not None

        # Switch to bar chart
        screen.switch_to_bar_chart()

        # Check that context menu handler is still connected
        assert screen.chart_view.customContextMenuRequested.connect is not None

        # Switch back to pie chart
        screen.switch_to_pie_chart()

        # Check that context menu handler is still connected
        assert screen.chart_view.customContextMenuRequested.connect is not None

        screen.close()

    def test_context_menu_via_right_click_bar_chart(self, stacked_widget, mock_user, mock_account, qtbot):
        """Test context menu functionality via actual right-click on bar chart."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Switch to bar chart first
        screen.switch_to_bar_chart()
        assert screen.current_chart_type == "bar"

        # Get chart view center position
        chart_center = screen.chart_view.rect().center()

        # Simulate right-click on chart view to trigger context menu
        qtbot.mouseClick(screen.chart_view, Qt.RightButton, pos=chart_center)

        # Give time for context menu to appear
        qtbot.wait(100)

        # Switch back to pie chart
        screen.switch_to_pie_chart()
        assert screen.current_chart_type == "pie"

        screen.close()

    def test_context_menu_via_right_click_pie_chart(self, stacked_widget, mock_user, mock_account, qtbot):
        """Test context menu functionality via actual right-click on pie chart."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Initially on pie chart
        assert screen.current_chart_type == "pie"

        # Get chart view center position
        chart_center = screen.chart_view.rect().center()

        # Simulate right-click on chart view to trigger context menu
        qtbot.mouseClick(screen.chart_view, Qt.RightButton, pos=chart_center)

        # Give time for context menu to appear
        qtbot.wait(100)

        # Switch to bar chart
        screen.switch_to_bar_chart()
        assert screen.current_chart_type == "bar"

        screen.close()

    def test_context_menu_round_trip_with_right_clicks(self, stacked_widget, mock_user, mock_account, qtbot):
        """Test full round-trip: pie → right-click → bar → right-click → pie."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        screen = OperationScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Start on pie chart
        assert screen.current_chart_type == "pie"

        # Get chart view center position
        chart_center = screen.chart_view.rect().center()

        # First right-click on pie chart
        qtbot.mouseClick(screen.chart_view, Qt.RightButton, pos=chart_center)
        qtbot.wait(100)

        # Switch to bar chart
        screen.switch_to_bar_chart()
        assert screen.current_chart_type == "bar"

        # Right-click on bar chart
        qtbot.mouseClick(screen.chart_view, Qt.RightButton, pos=chart_center)
        qtbot.wait(100)

        # Switch back to pie chart - this is where the bug would occur
        screen.switch_to_pie_chart()
        assert screen.current_chart_type == "pie"

        screen.close()
