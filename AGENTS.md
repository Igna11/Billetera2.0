# BilleterApp Project Summary

## Project Overview
BilleterApp is a Python-based expense tracker desktop application designed for personal finance management. Built with PyQt5 for the GUI and SQLite for data storage, it allows multiple users to create multiple accounts and track expenses, incomes, and transfers across different currencies.

## Architecture

### Backend Structure
- **Database**: SQLite with per-user databases stored in `data/` directory
- **Models**: Pydantic models for data validation (`src/models/`)
  - `Operations`: Financial transactions (income, expense, transfer)
  - `Accounts`: User accounts with currency support
  - `Users`: User management
  - `OperationGroups`: Grouped operations for complex transactions
- **Database Handlers**: Repository pattern (`src/dbhandlers/`)
  - `OperationsDB`: CRUD operations for financial transactions
  - `AccountsDB`: Account management
  - `UsersDB`: User management
  - `OpGroupsDB`: Operation groups handling
- **Queries**: Data retrieval layer (`src/queries/`)
  - `ListOperationsQuery`: Get operations with filtering
  - `GetOperationsForNetAnalysisQuery`: Net analysis by category
  - Various specialized queries for accounts, users, etc.
- **Commands**: Data manipulation layer (`src/commands/`)
  - `CreateOperationCommand`: Create new transactions
  - `CreateAndEditOperationsCommand`: Edit operations with cascade updates
  - `DeleteOperationsCommand`: Delete operations with cascade updates
- **Data Handler**: Business logic layer (`src/datahandler/`)
  - `AccountDataAnalyzer`: Analysis methods for totals, category grouping, time-based analysis
  - `get_daily_totals()`: Daily income/expense totals for monthly balance charts (supports both monthly and custom date ranges)

### Frontend Structure
- **GUI Framework**: PyQt5 with Qt Designer `.ui` files for layouts
- **Screens**: Multiple UI screens in `billeUI/`
  - `WelcomeScreen`: Entry point with login/create user options
  - `LoginScreen`: User authentication
  - `CreateUserScreen`: User registration
  - `OperationScreen`: Transaction entry with chart switching
  - `AccountBrowser`: Account management
  - Various operation-specific screens (income/expense, transfer, readjustment)
- **Visualization**: QtChart integration
  - `CategoricalPieChart`: Pie charts for category/subcategory breakdown
  - `MonthlyBalanceChart`: Bar charts for daily income/expense/balance visualization
  - `BalanceChartView`: Custom chart view with hover tooltips for custom ranges
  - HSV color generation for chart aesthetics
- **Utilities**: Currency formatting, icon management

## Key Features
- Multi-user support with individual databases
- Multi-account support per user
- Multi-currency support (ISO4217)
- Transaction types: income, expense, transfer_in, transfer_out
- Category/subcategory organization
- Operation grouping for complex transactions
- Time-based transaction tracking with datetime fields
- Pie chart visualization for spending analysis
- Monthly balance bar charts with daily income/expense/balance tracking
- Cumulative balance trend line with hover tooltips
- Context menu for switching between pie and bar charts
- Custom date range support for visualizations
- ULID-based unique identifiers
- Foreign key relationships with cascade handling
- **Account selection panel** for filtering balance charts by specific accounts
- **Multi-account cumulative plotting** with colored lines and dots for individual account balance tracking

## Database Schema
- **operations**: transaction records with datetime indexing
- **accounts**: user accounts with currency and totals
- **users**: user management
- **operation_groups**: grouped operations for net analysis
- **operation_details**: detailed operation information

## Key Dependencies
- PyQt5: GUI framework
- pydantic: Data validation
- pydantic-extra-types: Currency code support
- ulid: Unique identifier generation
- sqlite3: Database (built-in)
- pytest: Testing framework
- pytest-qt: PyQt5 testing support

## Current Capabilities
- CRUD operations for users, accounts, and transactions
- Time-based filtering and analysis
- Category-based spending analysis
- Net flow analysis (grouped operations)
- Currency-specific analysis
- Basic visualization (pie charts)

## Testing
- **UI Testing Framework**: pytest-qt based testing for PyQt5 components
- **Test Structure**: Located in `tests/ui/` directory
- **Test Fixtures**: Shared fixtures in `tests/conftest.py` for database mocking, user/account setup
- **Test Coverage**:
  - WelcomeScreen: Button navigation, UI loading, keyboard shortcuts
  - LoginScreen: Authentication flows, validation, error handling
  - OperationScreen: Chart initialization, user greeting, currency selection
- **Test Execution**: Run with `pytest tests/ui/` or `./run_ui_tests.sh`
- **Headless Mode**: Tests run without display using `QT_QPA_PLATFORM=offscreen`
- **Data Isolation**: Tests use temporary databases to avoid affecting real user data
- **Dependencies**: Install via `requirements-ui-testing.txt`

## Development Notes
- Uses a clean separation of concerns with models, handlers, queries, and commands
- Database indexes on operation_datetime, account_id, and operation_type for performance
- Comprehensive error handling in `src/errorhandler/`
- Data stored in `data/` directory with per-user subdirectories
- Qt Designer .ui files in `billeUI/uis/` for GUI layouts
- Chart switching via context menu (right-click on chart)
- Custom BalanceChartView for hover tooltips on trend lines
- Automatic X-axis label hiding for multi-month custom ranges

## Bar Chart Implementation Details
- **Data Source**: 
  - `AccountDataAnalyzer.get_daily_totals()` provides daily income/expense data for all accounts
  - `AccountDataAnalyzer.get_cumulative_points()` provides individual operation cumulative data for specific accounts
- **Chart Components**: 
  - `MonthlyBalanceChart`: QtChart with three bar series (income, expense, balance) and trend line
  - `BalanceChartView`: Custom QChartView with mouse tracking for hover tooltips
  - `AccountSelectionPanel`: Collapsible vertical panel for selecting which accounts to display
- **Visual Features**:
  - **Default mode (all accounts)**: 
    - Green bars: Daily income (positive, above zero)
    - Red bars: Daily expenses (negative, below zero)
    - Light blue bars: Cumulative balance (running total)
    - Dark blue dashed line: Trend line connecting balance peaks
    - Black line: Zero reference line
  - **Account-specific mode (selected accounts)**:
    - Colored lines: Individual account cumulative balance progression
    - Colored dots: Individual operation points with datetime-based x-axis positioning
    - Consistent color assignment per account name
    - Overlapping plot for multiple accounts at same timestamps
- **Interactive Features**:
  - Right-click context menu to switch between pie and bar charts
  - Hover tooltips show date and balance for custom ranges
  - Monthly navigation with << >> buttons
  - Custom date range support via calendar dialog
  - Currency filtering
  - Account selection panel with expand/collapse toggle
  - "All" and "None" buttons for quick account selection
  - Currency-sensitive account loading (only shows active accounts for selected currency)

## Future Enhancement Opportunities
- Deferred expense tracking (credit cards)
- Real vs. flow money analysis
- Operation deletion
- Account deletion
