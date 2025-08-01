#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 06/04/2023
updated on 06/2025
"""
from typing import List, Dict

from PyQt5 import QtChart
from PyQt5.QtGui import QFont, QColor

from billeUI import currency_format


class CategoricalPieChart(QtChart.QChart):
    """
    class to create pie charts with expenses and incomes with slices for categories
    and subcategories.
    data_inner: a dictionary with data of categories and subcategories with the totals
    data_outer: a dictionary with data of categories and with the totals
    period: a dictionary containing day, month ander to define the period (month) of the data to be displayed
    """

    def __init__(self, parent=None) -> None:
        super(CategoricalPieChart, self).__init__(parent)

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

    def clear_slices(self):
        """
        Clear all slices in the pie chart
        """
        for pie_slice in self.series_outer.slices():
            self.series_outer.take(pie_slice)

        for pie_slice in self.series_inner.slices():
            self.series_inner.take(pie_slice)

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

    def generate_chart(self, data_inner: List[Dict], data_outer: List[Dict], chart_type: str) -> None:
        """
        Add the slices to the pie chart usign the data_outer and the data_inner dictionaries
        Args:
            data_inner (List[Dict]): List of dictionaries of the form
            [{"category": "House", "subcategory": "Maintenance", "total": 2032}, {...}, ..., {...}]
            data_outer (List[Dict]): idem data inner but without subcategories.
            chart_type (str): 'income' or 'expense', so warm colors can be used to expenses and cold ones for incomes.
        Returns:
            None
        """

        self.clear_slices()
        self.add_slices(data_inner, data_outer, chart_type)
        self.update_labels()
        # Add the chart_view to the central_VR_layout
        # self.central_VR_Layout.addWidget(self.chart_view)
        # reset the chart mode in case the period mode was activated
        # self.chart_mode = "month"

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
                    label = f"""
                        <p align='center' style='color:black'>{subgroup['subcategory']}<br>
                        <b>${currency_format(subgroup['total'])}</b></p>
                        """
                    slice_inner.setLabel(label)
                    slice_inner.setLabelFont(font)
                    self.series_inner.append(slice_inner)
