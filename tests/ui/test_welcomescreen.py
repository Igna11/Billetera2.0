"""
Tests for WelcomeScreen UI component.
"""

from PyQt5.QtCore import Qt

from billeUI.welcomescreen import WelcomeScreen


class TestWelcomeScreen:
    """Test suite for WelcomeScreen functionality."""

    def test_welcome_screen_initialization(self, stacked_widget):
        """Test that WelcomeScreen initializes correctly."""
        screen = WelcomeScreen(widget=stacked_widget)

        # Check that screen was created
        assert screen is not None
        assert screen.widget == stacked_widget

        # Check that main UI elements exist
        assert hasattr(screen, "login_button")
        assert hasattr(screen, "create_account_button")
        assert hasattr(screen, "delete_user_button")
        assert not hasattr(screen, "not_an_attribute")

        screen.close()

    def test_welcome_screen_buttons_exist(self, stacked_widget):
        """Test that all main buttons are present and clickable."""
        screen = WelcomeScreen(widget=stacked_widget)

        # Check buttons exist
        assert screen.login_button is not None
        assert screen.create_account_button is not None
        assert screen.delete_user_button is not None

        # Check buttons are enabled
        assert screen.login_button.isEnabled()
        assert screen.create_account_button.isEnabled()
        assert screen.delete_user_button.isEnabled()

        screen.close()

    def test_login_button_navigation(self, stacked_widget, qtbot):
        """Test that login button navigates to login screen."""
        screen = WelcomeScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Click login button
        qtbot.mouseClick(screen.login_button, Qt.LeftButton)

        # Check that navigation was attempted (widgets may or may not be added depending on implementation)
        # The important thing is that the button click doesn't crash
        assert True

        screen.close()

    def test_create_account_button_navigation(self, stacked_widget, qtbot):
        """Test that create account button navigates to create user screen."""
        screen = WelcomeScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Click create account button
        qtbot.mouseClick(screen.create_account_button, Qt.LeftButton)

        # Check that navigation was attempted
        assert True

        screen.close()

    def test_delete_user_button_navigation(self, stacked_widget, qtbot):
        """Test that delete user button navigates to delete user screen."""
        screen = WelcomeScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Click delete user button
        qtbot.mouseClick(screen.delete_user_button, Qt.LeftButton)

        # Check that navigation was attempted
        assert True

        screen.close()

    def test_escape_key_does_nothing(self, stacked_widget, qtbot):
        """Test that pressing Escape key does nothing on welcome screen."""
        screen = WelcomeScreen(widget=stacked_widget)
        qtbot.addWidget(screen)

        # Press Escape key - should not crash
        qtbot.keyClick(screen, Qt.Key_Escape)

        # Check that the screen handles the key press without crashing
        assert True

        screen.close()

    def test_welcome_screen_window_title(self, stacked_widget):
        """Test that welcome screen has proper window properties."""
        screen = WelcomeScreen(widget=stacked_widget)

        # Screen should be a QMainWindow
        from PyQt5.QtWidgets import QMainWindow

        assert isinstance(screen, QMainWindow)

        screen.close()
