"""
Tests for AnimatedLabel UI component.
"""

from PyQt5.QtWidgets import QMainWindow

from billeUI.animatedlabel import AnimatedLabel


class TestAnimatedLabel:
    """Test suite for AnimatedLabel functionality."""

    def test_animated_label_initialization_success(self, qapp):
        """Test that AnimatedLabel initializes correctly with success type."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test success message", message_type="success", parent=main_window)

        # Check that label was created
        assert label is not None
        assert label.text() == "Test success message"
        assert label.duration_ms == 2000

        # Check that success style is applied (green background)
        assert "#4CAF50" in label.styleSheet()

        label.close()
        main_window.close()

    def test_animated_label_initialization_warning(self, qapp):
        """Test that AnimatedLabel initializes correctly with warning type."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test warning message", message_type="warning", parent=main_window)

        # Check that label was created
        assert label is not None
        assert label.text() == "Test warning message"

        # Check that warning style is applied (yellow background)
        assert "#FFC107" in label.styleSheet()

        label.close()
        main_window.close()

    def test_animated_label_initialization_error(self, qapp):
        """Test that AnimatedLabel initializes correctly with error type."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test error message", message_type="error", parent=main_window)

        # Check that label was created
        assert label is not None
        assert label.text() == "Test error message"

        # Check that error style is applied (red background)
        assert "#F44336" in label.styleSheet()

        label.close()
        main_window.close()

    def test_animated_label_custom_duration(self, qapp):
        """Test that AnimatedLabel accepts custom duration."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test message", message_type="success", duration_ms=5000, parent=main_window)

        # Check that custom duration is set
        assert label.duration_ms == 5000

        label.close()
        main_window.close()

    def test_animated_label_default_message_type(self, qapp):
        """Test that AnimatedLabel defaults to success when no type specified."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test message", parent=main_window)

        # Check that default style is applied (success/green background when no type specified)
        assert "#4CAF50" in label.styleSheet()

        label.close()
        main_window.close()

    def test_animated_label_positioning(self, qapp):
        """Test that AnimatedLabel is positioned correctly."""
        main_window = QMainWindow()
        main_window.resize(800, 600)
        main_window.show()

        label = AnimatedLabel("Test message", parent=main_window)

        # Check that label has a position
        pos = label.pos()
        assert pos.x() >= 0
        assert pos.y() >= 0

        # Check that label is positioned in bottom-right area
        main_rect = main_window.rect()
        assert pos.x() > main_rect.width() / 2  # Right side
        assert pos.y() > main_rect.height() / 2  # Bottom side

        label.close()
        main_window.close()

    def test_animated_label_height(self, qapp):
        """Test that AnimatedLabel has fixed height."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test message", parent=main_window)

        # Check that label has fixed height
        assert label.height() == 30

        label.close()
        main_window.close()

    def test_animated_label_display_method(self, qapp):
        """Test that display method shows the label."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test message", parent=main_window)

        # Initially label might not be visible
        label.hide()

        # Call display method
        label.display()

        # Check that label is now visible
        assert label.isVisible()

        label.close()
        main_window.close()

    def test_animated_label_style_properties(self, qapp):
        """Test that AnimatedLabel has correct style properties."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("Test message", message_type="success", parent=main_window)

        # Check that style sheet contains expected properties
        style = label.styleSheet()
        assert "background-color" in style
        assert "color: white" in style
        assert "padding:" in style
        assert "border-radius:" in style
        assert "font-weight: bold" in style

        label.close()
        main_window.close()

    def test_animated_label_empty_message(self, qapp):
        """Test that AnimatedLabel handles empty message."""
        main_window = QMainWindow()
        main_window.show()

        label = AnimatedLabel("", message_type="success", parent=main_window)

        # Check that label was created even with empty message
        assert label is not None
        assert label.text() == ""

        label.close()
        main_window.close()

    def test_animated_label_long_message(self, qapp):
        """Test that AnimatedLabel handles long message."""
        main_window = QMainWindow()
        main_window.show()

        long_message = (
            "This is a very long message that should still be displayed correctly by the animated label component"
        )
        label = AnimatedLabel(long_message, message_type="success", parent=main_window)

        # Check that label was created with long message
        assert label is not None
        assert label.text() == long_message

        label.close()
        main_window.close()
