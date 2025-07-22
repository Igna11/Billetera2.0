#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 06/04/2023
updated on 06/2025
"""
from datetime import datetime, UTC
from typing import List, Tuple, Dict

from PyQt5 import QtChart
from PyQt5.QtGui import QFont, QColor

from src.datahandler.datahandler import AccountDataAnalyzer
from billeUI import currency_format


class CategoricalPieChart(QtChart.QChart):
    """
    class to create pie charts with expenses and incomes with slices for categories
    and subcategories.
    data_inner: a pandas data frame with data to fill the inner pie chart
    data_outer: a pandas data frame with data to fill the outer pie chart
    period: a dictionary containing day, month ander to define the period (month) of the data to be displayed
    """

    def __init__(self, parent=None) -> None:
        super(CategoricalPieChart, self).__init__(parent)

        self.month = datetime.now().month
        self.year = datetime.now().year

        self.series_outer = QtChart.QPieSeries()
        self.series_inner = QtChart.QPieSeries()

        self.series_outer.setHoleSize(0.45)
        self.series_inner.setHoleSize(0.30)
        self.series_inner.setPieSize(0.45)

        self.addSeries(self.series_outer)
        self.addSeries(self.series_inner)

        self.legend().hide()
        self.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        self.setBackgroundRoundness(20)

    def get_month_interval(self, year: int, month: int) -> Tuple[datetime, datetime]:
        from_datetime = datetime(year, month, 1, tzinfo=UTC)
        if month == 12:
            to_datetime = datetime(year + 1, 1, 1, tzinfo=UTC)
        else:
            to_datetime = datetime(year, month + 1, 1, tzinfo=UTC)
        return from_datetime, to_datetime

    def load_data(
        self,
        user_id: str,
        currency: str,
        chart_mode: str,
        time_period: datetime,
        chart_type: str = "expense",
    ) -> tuple:
        """
        Loads the raw data in the given currency and for the given filters
        in order to create the desired piechart
        """
        if chart_mode == "month":
            # set the time frame
            from_datetime, to_datetime = self.get_month_interval(time_period.year, time_period.month)

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

    def clear_slices(self):
        """
        Clear all slices in the pie chart
        """
        for pie_slice in self.series_outer.slices():
            self.series_outer.take(pie_slice)

        for pie_slice in self.series_inner.slices():
            self.series_inner.take(pie_slice)

    def add_slices(self, data_inner: List[Dict], data_outer: List[Dict], chart_type: str = "expense") -> None:
        """
        Loops through the data to the create each slice of the inner and
        the outer series of the pie chart.
        """
        font = QFont()
        font.setPointSize(7)

        categories_list = [data_dict["category"] for data_dict in data_outer]
        categories_colors = dict(
            zip(categories_list, self.slices_colorsHSV(n=len(categories_list), chart_type=chart_type))
        )

        for group in data_outer:
            category = group["category"]
            cat_total = group["total"]
            # base_color = CATEGORY_COLOR_MAP.get(category, QColor("#999999"))
            base_color = categories_colors.get(category, QColor("gray"))

            slice_outer = QtChart.QPieSlice(category, cat_total)
            slice_outer.setBrush(base_color)
            self.series_outer.append(slice_outer)

            sub_index = 0
            sub_count = sum(1 for s in data_inner if s["category"] == category)

            for subgroup in data_inner:
                if subgroup["category"] == category:
                    subcategory = subgroup["subcategory"]
                    subcat_total = subgroup["total"]
                    slice_inner = QtChart.QPieSlice(subcategory, subcat_total)

                    factor = (sub_index + 1) / (sub_count + 1)
                    lighter = self.lighten_color(base_color, factor)
                    slice_inner.setBrush(lighter)
                    sub_index += 1

                    slice_inner.hovered.connect(
                        lambda is_hovered, slice_=slice_inner: slice_.setLabelVisible(is_hovered)
                    )
                    slice_inner.hovered.connect(lambda is_hovered, slice_=slice_inner: slice_.setExploded(is_hovered))
                    slice_inner.setExplodeDistanceFactor(0.05)
                    label = f"<p align='center' style='color:black'>{subgroup['subcategory']}<br><b>${currency_format(subgroup['total'])}</b></p>"
                    slice_inner.setLabel(label)
                    slice_inner.setLabelFont(font)
                    self.series_inner.append(slice_inner)

    def update_labels(self):
        """
        Updates the labels of the outer slices:
            If the percentage of a given slice is less or equal than 5%
            then the label is invisible unless the user hovers over the
            slcie.
            If the percentage of a given slice is greater than 5%, then
            the label is visible all the time.
        """
        for pie_slice in self.series_outer.slices():
            font = QFont()
            font.setPointSize(8)
            slice_lbl = pie_slice.label()
            slice_val = pie_slice.value()
            pie_slice.setLabelFont(font)
            label = f"<p align='center' style='color:black'>{slice_lbl}<br><b>${currency_format(slice_val)}</b></p>"
            if pie_slice.percentage() > 0.05:
                pie_slice.setLabelVisible()
            elif pie_slice.percentage() <= 0.05:
                pie_slice.hovered.connect(lambda is_hovered, slice_=pie_slice: slice_.setLabelVisible(is_hovered))
            pie_slice.setLabel(label)

    def update_title(
        self,
        user_id: str,
        chart_mode: str,
        time_period: datetime,
        currency: str = "ARS",
        chart_type: str = "expense",
        ci_date=None,
        cf_date=None,
    ) -> str:
        """
        Creates the format for the title of the chart and updates it every time a chart
        is instantiated.
        chart_mode: monthly or period
        chart_type: incomes or expenses
        title_type
        """
        if chart_mode == "month":
            from_datetime, to_datetime = self.get_month_interval(time_period.year, time_period.month)
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

    def lighten_color(self, color: QColor, factor: float) -> QColor:
        """
        Devuelve un QColor aclarado por un factor (0.0 - 1.0).
        factor cercano a 1 = muy claro, cercano a 0 = color original
        """
        r = int(color.red() + (255 - color.red()) * factor)
        g = int(color.green() + (255 - color.green()) * factor)
        b = int(color.blue() + (255 - color.blue()) * factor)
        return QColor(r, g, b)

    def slices_colorsHSV(
        self, n: int, saturation: int = 180, value: int = 230, chart_type: str = "expense"
    ) -> List[QColor]:
        if n == 0:
            n = 1
        if chart_type == "expense":
            start_hue, end_hue = 0, 80
        elif chart_type == "income":
            start_hue, end_hue = 110, 280
        else:
            start_hue, end_hue = 0, 360

        color_step = (end_hue - start_hue) / n
        colors = [QColor.fromHsv(int(start_hue + i * color_step), saturation, value) for i in range(n)]

        return colors
