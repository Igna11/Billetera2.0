#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 28/07/2025
"""
def _get_month_interval(self, year: int, month: int) -> Tuple[datetime, datetime]:
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

def load_data(self, user_id: str, currency: str, time_period: datetime, chart_mode: str, chart_type: str = "expense") -> tuple:
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
        from_datetime, to_datetime = self._get_month_interval(time_period.year, time_period.month)

        data_outer = AccountDataAnalyzer.group_operations(
            user_id=user_id,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            operation_type=chart_type,
            data_type="category",
            currency=currency,
        )
        data_inner = AccountDataAnalyzer.group_operations(
            user_id=user_id,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            operation_type=chart_type,
            data_type="subcategory",
            currency=currency,
        )

    elif chart_mode == "period":
        ci_date, cf_date = time_period.values()
        data_outer = AccountDataAnalyzer.group_operations(
            user_id=user_id,
            from_datetime=ci_date,
            to_datetime=cf_date,
            operation_type=chart_type,
            data_type="category",
            currency=currency,
        )
        data_inner = AccountDataAnalyzer.group_operations(
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

    def update_title(
        self,
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
            ci_date (custom initial date - 
        Returns:
            data_outer: category data
            data_inner: subcategory data
        """
        if chart_mode == "month":
            from_datetime, to_datetime = self._get_month_interval(time_period.year, time_period.month)
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
        self.setTitle(title)

    def generate_chart(self, mode: str, time_period: datetime | None, currency: str) -> None:
        """
        docstring
        """
        self.chart.clear_slices()

        if mode == "current":
            self.selected_datetime = self.curr_datetime
            chart_period = "month"
            stime = self.selected_datetime
        elif mode == "previous":
            chart_period = "month"
            cur_date = self.selected_datetime.day
            # last day of the previous month
            self.selected_datetime = self.selected_datetime - timedelta(days=cur_date)
            stime = self.selected_datetime
        elif mode == "next":
            chart_period = "month"
            cur_date = self.selected_datetime.day
            # first days of the next month
            self.selected_datetime = self.selected_datetime - timedelta(days=cur_date - 1) + timedelta(days=32)
            stime = self.selected_datetime
        elif mode == "period" and time_period:
            stime = time_period
            chart_period = "period"
        else:
            chart_period = mode
            stime = time_period

        data_inner, data_outer = self.chart.load_data(
            user_id=self.widget.user_object.user_id,
            chart_mode=chart_period,
            chart_type=self.chart_type,
            time_period=stime,
            currency=self.currency,
        )
        self.chart.update_title(
            user_id=self.widget.user_object.user_id,
            chart_mode=chart_period,
            chart_type=self.chart_type,
            time_period=stime,
            currency=self.currency,
        )
        self.chart.add_slices(data_inner, data_outer, self.chart_type)
        self.chart.update_labels()
        # Add the chart_view to the central_VR_layout
        self.central_VR_Layout.addWidget(self.chart_view)
        # reset the chart mode in case the period mode was activated
        self.chart_mode = "month"

    def current_month_chart(self) -> None:
        """
        Generates a new piechart of the current month and updates the variable
        self.selected_datetime
        """
        self.chart_mode = "month"
        self.generate_chart(mode="current", time_period=1, currency=self.currency)

    def previous_month_chart(self) -> None:
        """
        Generates a new piechart of the previous month and updates the
        variable self.selected_datetime
        """
        self.chart_mode = "month"
        self.generate_chart(mode="previous", time_period=1, currency=self.currency)

    def next_month_chart(self) -> None:
        """
        Generates a new piechart of the next month and updates the
        variable self.selected_datetime
        """
        self.chart_mode = "month"
        self.generate_chart(mode="next", time_period=1, currency=self.currency)

    def custom_date_range(self) -> None:
        """
        Generates a new piechart of the period of time selected in the calendar.
        First it opens up a calendar widget to select the 2 dates that conform the
        desired period of time. Then uses it to gather the information needed for
        the pie chart.
        """
        calendar_dialog = calendardialog.CalendarDialog()
        calendar_dialog.select_button.clicked.connect(calendar_dialog.get_date_range)
        calendar_dialog.exec_()
        self.custom_initial_date = calendar_dialog.initial_d
        self.custom_final_date = calendar_dialog.final_d
        if self.custom_initial_date and self.custom_final_date:
            period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            self.generate_chart(mode="period", time_period=period_dict, currency=self.currency)
            self.chart_mode = "period"

    def switch_chart_type(self) -> None:
        """
        Changes the chart type to switch between incomes and expenses
        """
        self.chart.clear_slices()
        if self.chart_type == "expense":
            self.chart_type = "income"
        elif self.chart_type == "income":
            self.chart_type = "expense"
        stime = self.selected_datetime
        if self.chart_mode == "month":
            data_inner, data_outer = self.chart.load_data(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=stime,
                currency=self.currency,
            )
            self.chart.update_title(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=stime,
                currency=self.currency,
            )
        elif self.chart_mode == "period":
            period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            data_inner, data_outer = self.chart.load_data(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=period_dict,
                currency=self.currency,
            )
            self.chart.update_title(
                user_id=self.widget.user_object.user_id,
                chart_mode=self.chart_mode,
                chart_type=self.chart_type,
                time_period=period_dict,
                currency=self.currency,
            )

        self.chart.add_slices(data_inner, data_outer, self.chart_type)
        self.chart.update_labels()
        # Add the chart_view to the central_VR_layout
        self.central_VR_Layout.addWidget(self.chart_view)

    def change_currency_chart(self) -> None:
        """
        Generates a new piechart changing the currency used to filter the operations
        """
        if self.chart_mode == "period":
            period_dict = {
                "initial": str(self.custom_initial_date),
                "final": str(self.custom_final_date),
            }
            stime = period_dict
        else:
            stime = self.selected_datetime
        self.currency = self.currency_combobox.currentText()
        self.generate_chart(mode=self.chart_mode, time_period=stime, currency=self.currency)
