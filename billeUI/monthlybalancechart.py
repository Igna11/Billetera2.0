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
    Custom chart view that handles hover events for individual bars.
    Shows tooltips with date and balance information when hovering over specific bars.
    """

    def __init__(self, chart, parent=None):
        super().__init__(chart, parent)
        self.setMouseTracking(True)  # Enable mouse tracking for hover events
        self.day_labels = []  # Will be set by the chart
        self.total_values = []  # Will be set by the chart
        self.chart_instance = chart  # Store reference to the chart

    def set_tooltip_data(self, day_labels, total_values):
        """Set the data needed for tooltips"""
        self.day_labels = day_labels
        self.total_values = total_values

    def mouseMoveEvent(self, event):
        """Handle mouse move events to show tooltips on individual bar hover"""
        super().mouseMoveEvent(event)

        chart = self.chart()
        if not chart or not self.day_labels:
            return

        # Map mouse position to chart coordinates
        pos = event.pos()
        try:
            chart_pos = chart.mapToValue(pos)

            # Find the closest data point (X-axis represents the day index)
            if chart_pos.x() >= 0 and chart_pos.x() < len(self.day_labels):
                index = int(round(chart_pos.x()))
                if 0 <= index < len(self.day_labels):
                    day_label = self.day_labels[index]
                    balance = self.total_values[index]

                    # Show tooltip for the specific bar being hovered
                    tooltip_text = f"{day_label}\n{currency_format(balance)}"
                    QToolTip.showText(event.globalPos(), tooltip_text, self)
            else:
                QToolTip.hideText()
        except:
            QToolTip.hideText()


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

    def hover_labels(self):
        self.total_series.setLabelsVisible(True)

    def update_chart(self, daily_data: List[Dict[str, any]], month: int, year: int) -> None:
        """
        Update the chart with daily data.

        Args:
            daily_data: List of dictionaries with keys 'day', 'income', 'expense'
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

        # Calculate cumulative balance from income/expense
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

        # Update Y axis with asymmetric limits based on actual data ranges
        max_income = max(income_values) if income_values else 0
        max_expense = max(abs(x) for x in expense_values) if expense_values else 0

        # Calculate max positive and negative from cumulative values
        positive_totals = [x for x in total_values if x > 0]
        negative_totals = [x for x in total_values if x < 0]

        max_total_positive = max(positive_totals) if positive_totals else 0
        max_total_negative = min(negative_totals) if negative_totals else 0

        # Calculate asymmetric Y-axis limits based on actual data
        y_limit_positive = max(max_income, max_total_positive) * 1.1
        y_limit_negative = min(max_total_negative, -max_expense) * 1.1

        # Ensure we have some minimum range if all values are zero
        if y_limit_positive == 0 and y_limit_negative == 0:
            y_limit_positive = 100
            y_limit_negative = -100

        self.axis_y.setRange(y_limit_negative, y_limit_positive)

        # Format Y axis labels - use simpler format for better readability
        # Note: QtChart doesn't support custom suffixes like K/M directly in setLabelFormat
        # For proper K/M formatting, would need custom axis implementation
        if y_limit_positive >= 1_000_000 or abs(y_limit_negative) >= 1_000_000:
            self.axis_y.setLabelFormat("%.0f")  # Use simpler format for large numbers
        else:
            self.axis_y.setLabelFormat("%.0f")  # Regular format

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
