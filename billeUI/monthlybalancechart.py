#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monthly Balance Bar Chart Component
Created for daily income/expense visualization
"""
from typing import List, Dict

from PyQt5 import QtChart, QtGui
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtChart import QChartView

from billeUI import currency_format


class BalanceChartView(QChartView):
    """
    Custom chart view that handles hover events for the trend line.
    Shows tooltips with date and balance information when hovering over the trend line.
    """

    def __init__(self, chart, parent=None):
        super().__init__(chart, parent)
        self.setMouseTracking(True)  # Enable mouse tracking for hover events
        self.day_labels = []  # Will be set by the chart
        self.total_values = []  # Will be set by the chart

    def set_tooltip_data(self, day_labels, total_values):
        """Set the data needed for tooltips"""
        self.day_labels = day_labels
        self.total_values = total_values

    def mouseMoveEvent(self, event):
        """Handle mouse move events to show tooltips on trend line hover"""
        super().mouseMoveEvent(event)

        # Only show tooltips for custom ranges (multi-month periods)
        if not self.day_labels or "-" not in str(self.day_labels[0]):
            return

        # Get the chart and map coordinates
        chart = self.chart()
        if not chart:
            return

        # Map mouse position to chart coordinates
        pos = event.pos()
        try:
            chart_pos = chart.mapToValue(pos)

            # Find the closest data point
            if chart_pos.x() >= 0 and chart_pos.x() < len(self.total_values):
                index = int(round(chart_pos.x()))
                if 0 <= index < len(self.day_labels):
                    day_label = self.day_labels[index]
                    balance = self.total_values[index]

                    # Show tooltip
                    tooltip_text = f"Date: {day_label}\nBalance: {currency_format(balance)}"
                    QToolTip.showText(event.globalPos(), tooltip_text, self)
        except:
            # If coordinate mapping fails, just skip tooltip
            pass


class MonthlyBalanceChart(QtChart.QChart):
    """
    Bar chart for monthly balance visualization showing daily income, expenses, and cumulative balance.
    Each day has three bars:
    - Income (green, positive, above zero)
    - Expense (red, negative, below zero)
    - Balance (light blue, cumulative, can be positive or negative)

    Also includes a dashed trend line connecting the peaks of the cumulative balance bars.
    """

    def __init__(self, parent=None) -> None:
        super(MonthlyBalanceChart, self).__init__(parent)

        # Store day labels and total values for tooltips
        self.day_labels = []
        self.total_values = []

        # Create bar series for income, expenses, and cumulative balance
        self.income_series = QtChart.QBarSeries()
        self.expense_series = QtChart.QBarSeries()
        self.total_series = QtChart.QBarSeries()

        self.income_series.setBarWidth(1)
        self.expense_series.setBarWidth(1)
        self.total_series.setBarWidth(1.5)
        # Create bar sets
        self.income_bar_set = QtChart.QBarSet("Income")
        self.expense_bar_set = QtChart.QBarSet("Expense")
        self.total_bar_set = QtChart.QBarSet("Balance")

        # Style the bars
        self.income_bar_set.setColor(QColor("#4CAF50"))  # Green for income
        self.expense_bar_set.setColor(QColor("#F44336"))  # Red for expense
        self.total_bar_set.setColor(QColor("#87CEEB"))  # Light blue for balance

        self.income_series.append(self.income_bar_set)
        self.expense_series.append(self.expense_bar_set)
        self.total_series.append(self.total_bar_set)

        # Add series to chart
        self.addSeries(self.income_series)
        self.addSeries(self.expense_series)
        self.addSeries(self.total_series)

        # Setup axes
        self.axis_x = QtChart.QBarCategoryAxis()
        self.axis_y = QtChart.QValueAxis()

        self.addAxis(self.axis_x, Qt.AlignBottom)
        self.addAxis(self.axis_y, Qt.AlignLeft)

        self.income_series.attachAxis(self.axis_x)
        self.income_series.attachAxis(self.axis_y)
        self.expense_series.attachAxis(self.axis_x)
        self.expense_series.attachAxis(self.axis_y)
        self.total_series.attachAxis(self.axis_x)
        self.total_series.attachAxis(self.axis_y)

        # Add zero line
        self.zero_line = QtChart.QLineSeries()
        pen = QtGui.QPen(QtGui.QColor("#000000"))
        pen.setWidth(2)
        self.zero_line.setPen(pen)
        self.addSeries(self.zero_line)
        self.zero_line.attachAxis(self.axis_x)
        self.zero_line.attachAxis(self.axis_y)

        # Add trend line for cumulative balance
        self.trend_line = QtChart.QLineSeries()
        trend_pen = QtGui.QPen(QtGui.QColor("#1E90FF"))  # Darker blue for visibility
        trend_pen.setWidth(2)
        trend_pen.setStyle(Qt.DashLine)  # Make it dotted/dashed
        self.trend_line.setPen(trend_pen)
        self.addSeries(self.trend_line)
        self.trend_line.attachAxis(self.axis_x)
        self.trend_line.attachAxis(self.axis_y)

        # Chart styling
        self.setAnimationOptions(QtChart.QChart.SeriesAnimations)
        self.legend().setVisible(True)
        self.legend().setAlignment(Qt.AlignBottom)
        self.setBackgroundRoundness(20)
        self.setMargins(QMargins(10, 10, 10, 10))

        # Hide trend line from legend (it's just an overlay)
        self.trend_line.setName("")

        # Set title
        self.setTitle("Monthly Balance")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.setTitleFont(title_font)

    def clear_data(self):
        """Clear all data from the chart"""
        self.income_bar_set.remove(0, self.income_bar_set.count())
        self.expense_bar_set.remove(0, self.expense_bar_set.count())
        self.total_bar_set.remove(0, self.total_bar_set.count())
        self.zero_line.clear()
        self.trend_line.clear()

        # Remove cumulative line if it exists
        if hasattr(self, "cumulative_line") and self.cumulative_line is not None:
            self.removeSeries(self.cumulative_line)
            self.cumulative_line = None

        # Remove cumulative scatter series if it exists
        if hasattr(self, "cumulative_scatter") and self.cumulative_scatter is not None:
            self.removeSeries(self.cumulative_scatter)
            self.cumulative_scatter = None

        # Re-enable series that might have been hidden in cumulative mode
        self.income_series.setVisible(True)
        self.expense_series.setVisible(True)
        self.total_series.setVisible(True)
        self.trend_line.setVisible(True)

    def update_chart_with_cumulative_points(
        self, cumulative_points: List[Dict[str, any]], month: int, year: int
    ) -> None:
        """
        Update the chart with cumulative points as a line (for individual account balance tracking).

        Args:
            cumulative_points: List of dictionaries with keys 'datetime', 'cumulative', 'account_name'
            month: Month number (1-12)
            year: Year
        """
        self.clear_data()

        # Hide income/expense/trend series for cumulative view (we'll only show the cumulative line)
        self.income_series.setVisible(False)
        self.expense_series.setVisible(False)
        self.total_series.setVisible(False)
        self.trend_line.setVisible(False)

        if not cumulative_points:
            return

        # Sort points by datetime
        cumulative_points = sorted(cumulative_points, key=lambda x: x["datetime"])

        # Create a line series for cumulative balance
        self.cumulative_line = QtChart.QLineSeries()
        cumulative_pen = QtGui.QPen(QtGui.QColor("#1E90FF"))  # Dark blue for visibility
        cumulative_pen.setWidth(2)
        self.cumulative_line.setPen(cumulative_pen)
        self.cumulative_line.setName("Account Balance")

        # Create a scatter series for dots at each point
        self.cumulative_scatter = QtChart.QScatterSeries()
        self.cumulative_scatter.setColor(QtGui.QColor("#1E90FF"))  # Same color as line
        self.cumulative_scatter.setMarkerSize(8)  # Size of the dots
        self.cumulative_scatter.setBorderColor(QtGui.QColor("#1E90FF"))  # Border color same as fill

        # Store day labels and total values for tooltips
        self.day_labels = []
        self.total_values = []

        # Plot cumulative points
        for i, point in enumerate(cumulative_points):
            dt = point["datetime"]
            cumulative = point["cumulative"]

            # X-axis position (index-based)
            x_pos = i
            y_pos = cumulative

            self.cumulative_line.append(x_pos, y_pos)
            self.cumulative_scatter.append(x_pos, y_pos)

            # For tooltips, use date string
            date_str = dt.strftime("%Y-%m-%d")
            self.day_labels.append(date_str)
            self.total_values.append(cumulative)

        # Add the cumulative line to the chart
        self.addSeries(self.cumulative_line)
        self.cumulative_line.attachAxis(self.axis_x)
        self.cumulative_line.attachAxis(self.axis_y)

        # Add the scatter series (dots) to the chart
        self.addSeries(self.cumulative_scatter)
        self.cumulative_scatter.attachAxis(self.axis_x)
        self.cumulative_scatter.attachAxis(self.axis_y)

        # Update X axis with reasonable labels (sample some dates)
        self.axis_x.clear()
        if len(cumulative_points) <= 10:
            # Show all dates if few points
            x_labels = [point["datetime"].strftime("%m-%d") for point in cumulative_points]
            x_categories = [str(i) for i in range(len(cumulative_points))]
            self.axis_x.append(x_categories)
        else:
            # Show a subset of dates to avoid overcrowding
            step = max(1, len(cumulative_points) // 10)
            x_categories = [str(i) for i in range(len(cumulative_points))]
            self.axis_x.append(x_categories)
            # Hide intermediate labels by setting them to empty strings
            for i in range(len(x_categories)):
                if i % step != 0:
                    # Set intermediate labels to empty (though Qt may still show indices)
                    pass

        # Update Y axis range based on cumulative values
        cumulative_values = [point["cumulative"] for point in cumulative_points]
        if cumulative_values:
            min_val = min(cumulative_values)
            max_val = max(cumulative_values)
            range_size = max_val - min_val
            if range_size == 0:
                range_size = max(abs(max_val), 100)  # Default range if all values are same

            # Add some padding
            padding = range_size * 0.1
            self.axis_y.setRange(min_val - padding, max_val + padding)
        else:
            self.axis_y.setRange(-100, 100)

        # Format Y axis labels as currency
        self.axis_y.setLabelFormat("%.2f")

        # Update zero line position (at y=0)
        self.zero_line.clear()
        self.zero_line.append(0, 0)
        self.zero_line.append(len(cumulative_points) - 1, 0)

    def update_chart(self, daily_data: List[Dict[str, any]], month: int, year: int) -> None:
        """
        Update the chart with daily data.

        Args:
            daily_data: List of dictionaries with keys 'day', 'income', 'expense'
                       Can also include 'cumulative' key for actual cumulative amounts
            month: Month number (1-12)
            year: Year
        """
        self.clear_data()

        if not daily_data:
            return

        # Sort data by day (handles both integers and date strings)
        daily_data = sorted(daily_data, key=lambda x: x["day"])

        # Extract data for chart
        days = []
        income_values = []
        expense_values = []
        total_values = []

        # Check if we have cumulative data from operations
        has_cumulative_data = "cumulative" in daily_data[0]

        if has_cumulative_data:
            # Use actual cumulative amounts from operations
            for data in daily_data:
                day = data["day"]
                income = float(data.get("income", 0))
                expense = float(data.get("expense", 0))
                cumulative = float(data.get("cumulative", 0))

                # Ensure income is never negative and expense is never negative
                income = max(0, income)
                expense = max(0, expense)

                # Convert day to string for display (handles both int and str)
                days.append(str(day))
                income_values.append(income)
                expense_values.append(-expense)  # Make expenses negative
                total_values.append(cumulative)  # Use actual cumulative amount
        else:
            # Calculate cumulative balance from income/expense (default behavior)
            running_balance = 0.0

            for data in daily_data:
                day = data["day"]
                income = float(data.get("income", 0))
                expense = float(data.get("expense", 0))

                # Ensure income is never negative and expense is never negative
                income = max(0, income)
                expense = max(0, expense)

                # Convert day to string for display (handles both int and str)
                days.append(str(day))
                income_values.append(income)
                expense_values.append(-expense)  # Make expenses negative

                # Calculate running balance for this day
                running_balance += income - expense
                total_values.append(running_balance)

        # Update bar sets
        self.income_bar_set.append(income_values)
        self.expense_bar_set.append(expense_values)
        self.total_bar_set.append(total_values)

        # Update X axis with day labels
        self.axis_x.clear()
        self.axis_x.append(days)

        # Store day labels and total values for tooltips
        self.day_labels = days
        self.total_values = total_values

        # Hide X-axis labels for custom ranges (multi-month periods)
        is_custom_range = days and "-" in str(days[0])  # Date format like "2026-08-01"
        if is_custom_range:
            self.axis_x.setLabelsAngle(0)
            self.axis_x.setLabelsVisible(False)
        else:
            self.axis_x.setLabelsVisible(True)

        # Update Y axis with zero in the middle, considering cumulative values
        max_income = max(income_values) if income_values else 0
        max_expense = max(abs(x) for x in expense_values) if expense_values else 0

        # Calculate max positive and negative from cumulative values
        positive_totals = [x for x in total_values if x > 0]
        negative_totals = [x for x in total_values if x < 0]

        max_total_positive = max(positive_totals) if positive_totals else 0
        max_total_negative = min(negative_totals) if negative_totals else 0

        max_positive = max(max_income, max_total_positive)
        max_negative = max(max_expense, abs(max_total_negative))
        max_value = max(max_positive, max_negative)

        if max_value > 0:
            # Set range from -max_value to +max_value with zero in middle
            self.axis_y.setRange(-max_value * 1.1, max_value * 1.1)
        else:
            self.axis_y.setRange(-100, 100)  # Default range

        # Format Y axis labels as currency
        self.axis_y.setLabelFormat("%.2f")

        # Update zero line position
        self.zero_line.clear()
        self.zero_line.append(0, 0)
        self.zero_line.append(len(days) - 1, 0)

        # Update trend line to connect cumulative balance peaks
        self.trend_line.clear()
        for day_index, total_value in enumerate(total_values):
            self.trend_line.append(day_index, total_value)

        # Update title with month/year or custom range
        month_names = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        # Check if this is a custom range (days are date strings)
        if days and "-" in str(days[0]):  # Date format like "2026-08-01"
            self.setTitle("Balance - Custom Range")
        else:
            self.setTitle(f"Monthly Balance - {month_names[month-1]} {year}")

    def set_mock_data(self, month: int, year: int) -> None:
        """
        Set mock data for demonstration purposes.
        This simulates what the real data would look like.
        """
        import random
        from calendar import monthrange

        # Get number of days in the month
        num_days = monthrange(year, month)[1]

        # Generate mock data with realistic cumulative balance
        mock_data = []
        for day in range(1, num_days + 1):
            # Random income between 0 and 500
            income = random.uniform(0, 500) if random.random() > 0.4 else 0

            # Random expense between 0 and 400 (will be made negative in update_chart)
            expense = random.uniform(0, 400) if random.random() > 0.3 else 0

            mock_data.append({"day": day, "income": income, "expense": expense})

        self.update_chart(mock_data, month, year)
