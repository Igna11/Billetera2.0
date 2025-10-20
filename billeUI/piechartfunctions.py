#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 28/07/2025
Auxiliary functions to generate the PieCharts
"""
from typing import Tuple, Dict
from datetime import datetime, timedelta, UTC

from src.datahandler.datahandler import AccountDataAnalyzer


def get_next_month(current_date: datetime) -> datetime:
    """
    Given a datetime object, returns a datetime object with an arbitrary date and the original month + 1
    Example: datetime(2020,1,1) -> datetime(2020,2,1)
    """
    next_month_date = current_date + timedelta(days=(32 - current_date.day))
    return next_month_date


def get_prev_month(current_date: datetime) -> datetime:
    """
    Given a datetime object, returns a datetime object with an arbitrary date and the original month - 1
    Example: datetime(2020,1,1) -> datetime(2020,2,1)
    """
    prev_month_date = current_date - timedelta(days=(current_date.day + 1))
    return prev_month_date


def _get_month_interval(year: int, month: int) -> Tuple[datetime, datetime]:
    """
    Given a year and a month, it returns two complete datetime objects with the first day of two consecutives months.
    Example:
        year = 2000
        month = 12
        => from_datetime = datetime.datetime(2000, 12, 1, tzinfo=UTC)
        => to_datetime = datetime.datetime(2001, 1, 1, tzinfo=UTC)
    Example:
        year = 2000
        month = 6
        => from_datetime = datetime.datetime(2000, 6, 1, tzinfo=UTC)
        => to_datetime = datetime.datetime(2001, 7, 1, tzinfo=UTC)
    Args:
    """
    from_datetime = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        to_datetime = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        to_datetime = datetime(year, month + 1, 1, tzinfo=UTC)
    return from_datetime, to_datetime


def load_data(
    user_id: str, currency: str, time_period: datetime | Dict[str, str], chart_mode: str, chart_type: str = "expense"
) -> tuple:
    """
    Loads the raw data in the given currency and for the given filters in order to be passed to the chart.
    Args:
        user_id (str): The user id, required to make the query to the db.
        currency (str): The currency of the data to be retrieve.
        time_period (datetime.datetime): Used to generate the month interval for the chart
        chart_mode (str): Can be 'month' or 'period', where period is a custom period selected by the user.
        chart_type (str): Can be "income" or "expense"
    Returns:
        data_outer: category data
        data_inner: subcategory data
    """
    if chart_mode == "month":
        # set the time frame
        from_datetime, to_datetime = _get_month_interval(time_period.year, time_period.month)

        data_outer = AccountDataAnalyzer.categorize_flow_operations(
            user_id=user_id,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            operation_type=chart_type,
            data_type="category",
            currency=currency,
        )
        data_inner = AccountDataAnalyzer.categorize_flow_operations(
            user_id=user_id,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            operation_type=chart_type,
            data_type="subcategory",
            currency=currency,
        )

    elif chart_mode == "period":
        ci_date, cf_date = time_period.values()
        data_outer = AccountDataAnalyzer.categorize_flow_operations(
            user_id=user_id,
            from_datetime=ci_date,
            to_datetime=cf_date,
            operation_type=chart_type,
            data_type="category",
            currency=currency,
        )
        data_inner = AccountDataAnalyzer.categorize_flow_operations(
            user_id=user_id,
            from_datetime=ci_date,
            to_datetime=cf_date,
            operation_type=chart_type,
            data_type="subcategory",
            currency=currency,
        )
    else:
        raise ValueError("Valid types: 'expense', 'income'. Valid modes: 'month', 'period'")
    return data_inner, data_outer


def update_n_format_chart_title(
    user_id: str,
    currency: str,
    time_period: datetime,
    chart_mode: str,
    chart_type: str,
    ci_date=None,
    cf_date=None,
) -> str:
    """
    Creates the format for the title of the chart and updates it every time a chart is instantiated.
    Args:
        user_id (str): The user id, required to make the query to the db.
        currency (str): The currency of the data to be retrieve.
        chart_mode (str): Can be 'month' or 'period', where period is a custom period selected by the user.
        time_period (datetime.datetime): Used to generate the month interval for the chart
        chart_type (str): Can be "income" or "expense"
        ci_date (custom initial date - str): initial date to be used for create a custom pie chart.
        cf_date (custom final date - str): final date to be used for create a custom pie chart.
    Returns:
        data_outer: category data
        data_inner: subcategory data
    """
    if chart_mode == "month":
        from_datetime, to_datetime = _get_month_interval(time_period.year, time_period.month)
        selected_period = time_period.strftime(format="%B %Y").capitalize()
        total = AccountDataAnalyzer.get_user_totals_by_period(
            user_id=user_id,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            operation_type=chart_type,
            currency=currency,
        )
    elif chart_mode == "period":
        ci_date, cf_date = time_period.values()
        selected_period = f"Period: {ci_date} -- {cf_date}"
        total = AccountDataAnalyzer.get_user_totals_by_period(
            user_id=user_id,
            from_datetime=ci_date,
            to_datetime=cf_date,
            operation_type=chart_type,
            currency=currency,
        )
    title_type = chart_type.capitalize()
    total_int = f"{total:,.0f}".replace(",", ".")
    total_decimal = f"{total:.2f}".split(".")[1]
    title = f"<h3><p align='center' style='color:black'><b>{title_type}: ${total_int}<sup>{total_decimal}</sup><br>{selected_period}</b></p>"
    return title
