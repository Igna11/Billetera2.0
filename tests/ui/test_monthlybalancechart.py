"""
Tests for MonthlyBalanceChart UI component.
"""

from decimal import Decimal

from billeUI.monthlybalancechart import MonthlyBalanceChart, BalanceChartView


class TestBalanceChartView:
    """Test suite for BalanceChartView functionality."""

    def test_balance_chart_view_initialization(self, qapp):
        """Test that BalanceChartView initializes correctly."""
        from PyQt5.QtChart import QChart

        chart = QChart()
        view = BalanceChartView(chart)

        # Check that view was created
        assert view is not None
        assert view.chart() == chart

        # Check that mouse tracking is enabled
        assert view.hasMouseTracking()

        view.close()

    def test_balance_chart_view_tooltip_data(self, qapp):
        """Test that tooltip data can be set."""
        from PyQt5.QtChart import QChart

        chart = QChart()
        view = BalanceChartView(chart)

        # Set tooltip data
        day_labels = ["2024-01-01", "2024-01-02", "2024-01-03"]
        total_values = [Decimal("100.00"), Decimal("150.00"), Decimal("200.00")]

        view.set_tooltip_data(day_labels, total_values)

        # Check that data was set
        assert view.day_labels == day_labels
        assert view.total_values == total_values

        view.close()

    def test_balance_chart_view_empty_tooltip_data(self, qapp):
        """Test that empty tooltip data is handled."""
        from PyQt5.QtChart import QChart

        chart = QChart()
        view = BalanceChartView(chart)

        # Set empty tooltip data
        view.set_tooltip_data([], [])

        # Check that empty data is handled
        assert view.day_labels == []
        assert view.total_values == []

        view.close()


class TestMonthlyBalanceChart:
    """Test suite for MonthlyBalanceChart functionality."""

    def test_monthly_balance_chart_initialization(self, qapp):
        """Test that MonthlyBalanceChart initializes correctly."""
        chart = MonthlyBalanceChart()

        # Check that chart was created
        assert chart is not None
        # MonthlyBalanceChart inherits from QChart directly
        assert chart.income_series is not None
        assert chart.expense_series is not None
        assert chart.total_series is not None

        chart.close()

    def test_monthly_balance_chart_with_empty_data(self, qapp):
        """Test that chart handles empty data gracefully."""
        chart = MonthlyBalanceChart()

        # Update chart with empty data
        daily_data = []
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that chart was updated without errors
        assert chart is not None

        chart.close()

    def test_monthly_balance_chart_with_single_day(self, qapp):
        """Test that chart handles single day data."""
        chart = MonthlyBalanceChart()

        # Update chart with single day data
        daily_data = [{"day": 1, "income": 100.00, "expense": 50.00}]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that chart was updated
        assert chart is not None
        assert chart.income_bar_set.count() == 1

        chart.close()

    def test_monthly_balance_chart_with_multiple_days(self, qapp):
        """Test that chart handles multiple days data."""
        chart = MonthlyBalanceChart()

        # Update chart with multiple days data
        daily_data = [
            {"day": 1, "income": 100.00, "expense": 50.00},
            {"day": 2, "income": 200.00, "expense": 75.00},
            {"day": 3, "income": 150.00, "expense": 100.00},
        ]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that chart was updated
        assert chart is not None
        assert chart.income_bar_set.count() == 3

        chart.close()

    def test_monthly_balance_chart_title_update(self, qapp):
        """Test that chart title is updated correctly."""
        chart = MonthlyBalanceChart()

        # Update chart with data for January 2024
        daily_data = [{"day": 1, "income": 100.00, "expense": 50.00}]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that title includes month and year
        assert "January" in chart.title()
        assert "2024" in chart.title()

        chart.close()

    def test_monthly_balance_chart_series_creation(self, qapp):
        """Test that chart series are created correctly."""
        chart = MonthlyBalanceChart()

        # Update chart with data
        daily_data = [{"day": 1, "income": 100.00, "expense": 50.00}]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that series are created
        assert chart.income_series is not None
        assert chart.expense_series is not None
        assert chart.total_series is not None

        chart.close()

    def test_monthly_balance_chart_with_negative_balance(self, qapp):
        """Test that chart handles negative balance."""
        chart = MonthlyBalanceChart()

        # Update chart with data that creates negative balance
        daily_data = [{"day": 1, "income": 50.00, "expense": 100.00}]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that chart was updated
        assert chart is not None

        chart.close()

    def test_monthly_balance_chart_with_zero_values(self, qapp):
        """Test that chart handles zero values."""
        chart = MonthlyBalanceChart()

        # Update chart with zero values
        daily_data = [{"day": 1, "income": 0.00, "expense": 0.00}]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that chart was updated
        assert chart is not None

        chart.close()

    def test_monthly_balance_chart_custom_range_format(self, qapp):
        """Test that chart handles custom date range format."""
        chart = MonthlyBalanceChart()

        # Update chart with custom range (date string format)
        daily_data = [
            {"day": "2024-01-01", "income": 100.00, "expense": 50.00},
            {"day": "2024-01-15", "income": 200.00, "expense": 75.00},
        ]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that chart was updated and title reflects custom range
        assert chart is not None
        assert "Custom Range" in chart.title()

        chart.close()

    def test_monthly_balance_chart_clear_data(self, qapp):
        """Test that clear_data method works correctly."""
        chart = MonthlyBalanceChart()

        # Update chart with data
        daily_data = [{"day": 1, "income": 100.00, "expense": 50.00}]
        chart.update_chart(daily_data, month=1, year=2024)

        # Check that data was added
        assert chart.income_bar_set.count() == 1

        # Clear data
        chart.clear_data()

        # Check that data was cleared
        assert chart.income_bar_set.count() == 0

        chart.close()

    def test_monthly_balance_chart_axes_creation(self, qapp):
        """Test that chart axes are created correctly."""
        chart = MonthlyBalanceChart()

        # Check that axes exist
        assert chart.axis_x is not None
        assert chart.axis_y is not None

        chart.close()

    def test_monthly_balance_chart_trend_line(self, qapp):
        """Test that trend line is created correctly."""
        chart = MonthlyBalanceChart()

        # Check that trend line exists
        assert chart.trend_line is not None
        assert chart.zero_line is not None

        chart.close()
