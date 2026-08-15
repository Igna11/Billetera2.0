# BilleterApp

Expense tracker project made entirely with python. Designed to be robust but easy to use as a desktop App with a basic UI made with PyQt5. On one machine, several users can be created which can have several accounts with all their expenses/incomes/transfers. All existing currencies can be used when creating accounts.

This app was created with the idea of tracking the expenses in the most similar way that they occur in real life. Any income/expense can be added with their specific date and time, no matter when it is being tracked. The only detail to bare in mind is that no negative values are allowed for totals.

## Current Features
- Multi-user support with individual databases
- Multi-account support per user  
- Multi-currency support (ISO4217)
- Transaction types: income, expense, transfer_in, transfer_out
- Category/subcategory organization
- Operation grouping for complex transactions
- Time-based transaction tracking with datetime fields
- Pie chart visualization for spending analysis by category
- Monthly balance bar charts with daily income/expense/balance tracking
- Cumulative balance trend line with hover tooltips
- Context menu for switching between pie and bar charts
- Custom date range support for visualizations
- Currency-specific analysis

## Usage
- **Chart Switching**: Right-click on any chart to switch between pie chart and bar chart
- **Monthly Balance**: Use the bar chart to see daily income, expenses, and cumulative balance evolution
- **Custom Ranges**: Use the "Custom" button to select custom date ranges for analysis
- **Hover Tooltips**: For custom date ranges, hover over the chart to see date and balance information
- **Currency Filtering**: Change currency dropdown to filter analysis by currency

## Testing
The project includes a comprehensive UI testing framework using pytest-qt for PyQt5 components.

### Setup
Install testing dependencies:
```bash
pip install -r requirements-ui-testing.txt
```

### Running Tests
Run all UI tests:
```bash
pytest tests/ui/
```

Or use the convenience script:
```bash
./run_ui_tests.sh
```

Run specific test files:
```bash
pytest tests/ui/test_welcomescreen.py
pytest tests/ui/test_loginscreen.py
pytest tests/ui/test_operationscreen.py
```

### Test Features
- **Headless Mode**: Tests run without displaying windows (suitable for CI/CD)
- **Data Isolation**: Uses temporary databases to avoid affecting real user data
- **Interactive Testing**: Simulates real user interactions (clicks, keyboard input)
- **Coverage**: Tests for WelcomeScreen, LoginScreen, and OperationScreen

For detailed testing documentation, see `tests/README.md`.

## Planned Features
- Deferred expenses (credit cards) - track future payment obligations
- Flow vs. real money analysis - distinguish between money flow and actual expenses
- Operation deletion
- Account deletion

