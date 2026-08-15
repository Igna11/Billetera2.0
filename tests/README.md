# UI Testing Guide for BilleterApp

This directory contains UI tests for the PyQt5 components of BilleterApp using pytest-qt.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements-ui-testing.txt
```

2. The required packages are:
- `pytest>=7.0.0` - Testing framework
- `pytest-qt>=4.0.0` - PyQt5 testing support
- `PyQt5>=5.15.0` - GUI framework

## Running Tests

### Run all UI tests:
```bash
pytest tests/ui/
```

### Run specific test file:
```bash
pytest tests/ui/test_welcomescreen.py
```

### Run specific test class:
```bash
pytest tests/ui/test_welcomescreen.py::TestWelcomeScreen
```

### Run specific test method:
```bash
pytest tests/ui/test_welcomescreen.py::TestWelcomeScreen::test_welcome_screen_initialization
```

### Run tests with verbose output:
```bash
pytest tests/ui/ -v
```

### Run tests without displaying windows (headless mode):
```bash
QT_QPA_PLATFORM=offscreen pytest tests/ui/
```

## Test Structure

### Fixtures (`conftest.py`)
- `qapp`: QApplication instance for the test session
- `stacked_widget`: QStackedWidget for screen navigation testing
- `temp_data_dir`: Temporary directory for test databases
- `mock_user`: Mock user for authentication testing
- `mock_account`: Mock account for account-related testing
- `mock_operations`: Mock operations for operation testing

### Test Files
- `test_welcomescreen.py`: Tests for WelcomeScreen component
- `test_loginscreen.py`: Tests for LoginScreen component
- `test_operationscreen.py`: Tests for OperationScreen component

## Writing New Tests

### Basic Test Structure:
```python
import pytest
from PyQt5.QtCore import Qt
from billeUI.yourscreen import YourScreen

class TestYourScreen:
    def test_screen_initialization(self, stacked_widget, temp_data_dir):
        screen = YourScreen(widget=stacked_widget)
        assert screen is not None
        screen.close()
    
    def test_button_click(self, stacked_widget, temp_data_dir, qtbot):
        screen = YourScreen(widget=stacked_widget)
        qtbot.addWidget(screen)
        qtbot.mouseClick(screen.your_button, Qt.LeftButton)
        # Add assertions
        screen.close()
```

### Key pytest-qt Features:
- `qtbot.addWidget(widget)`: Register widget for cleanup
- `qtbot.mouseClick(widget, button)`: Simulate mouse clicks
- `qtbot.keyClick(widget, key)`: Simulate keyboard input
- `qtbot.wait(ms)`: Wait for specified milliseconds
- `qtbot.waitSignal(signal, timeout=ms)`: Wait for signal emission

## Test Categories

Use pytest markers to categorize tests:
```python
@pytest.mark.ui
def test_ui_component():
    pass

@pytest.mark.authentication  
def test_login():
    pass

@pytest.mark.navigation
def test_screen_navigation():
    pass
```

Run tests by category:
```bash
pytest -m ui
pytest -m authentication
pytest -m "navigation and ui"
```

## Best Practices

1. **Always close widgets**: Call `screen.close()` in test cleanup
2. **Use temporary data**: Tests use temporary databases to avoid affecting real data
3. **Test user interactions**: Test actual button clicks, keyboard input, etc.
4. **Test navigation**: Verify screen transitions work correctly
5. **Test validation**: Check that form validation works as expected
6. **Mock external dependencies**: Use fixtures to mock database operations

## CI/CD Integration

For automated testing in CI/CD environments:
```bash
# Run tests in headless mode
QT_QPA_PLATFORM=offscreen pytest tests/ui/ --tb=short
```

## Troubleshooting

### "QApplication instance already exists"
This is normal - the fixture handles this by checking for existing instances.

### Tests fail with display errors
Use headless mode: `QT_QPA_PLATFORM=offscreen pytest tests/ui/`

### Database-related errors
Ensure the `temp_data_dir` fixture is working correctly and tests are isolated.

## Future Test Coverage

Consider adding tests for:
- Income/Expense screens
- Transfer screen
- Account browser
- Chart functionality (pie charts, bar charts)
- Calendar dialog
- All other screens in `billeUI/`