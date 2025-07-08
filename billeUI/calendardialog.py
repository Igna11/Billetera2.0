#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 08/02/2023
"""

from PyQt5.QtWidgets import (
    QDialog,
    QCalendarWidget,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QPushButton,
)
from PyQt5.QtGui import QPalette, QTextCharFormat
from PyQt5.QtCore import Qt


class Calendar(QCalendarWidget):
    """
    Calendar that lets the user to select a range of dates.
    The ideas were taken from here:
    https://learndataanalysis.org/source-code-how-to-use-calendar-widget-to-select-a-date-range-pyqt5-tutorial/
    """

    def __init__(self):
        super().__init__()
        self.highlighter = QTextCharFormat()
        self.highlighter.setBackground(self.palette().brush(QPalette.Highlight))
        self.highlighter.setForeground(self.palette().color(QPalette.HighlightedText))

        self.initial_date = None
        self.final_date = None

        self.clicked.connect(self.select_date_range)

    def select_date_range(self, date_value):
        self.highlight_range(QTextCharFormat())
        if QApplication.instance().keyboardModifiers() & Qt.ShiftModifier and self.initial_date:
            self.final_date = date_value
            self.highlight_range(self.highlighter)
        else:
            self.initial_date = date_value
            self.final_date = None

    def highlight_range(self, format):
        if self.initial_date and self.final_date:
            day_1 = min(self.initial_date, self.final_date)
            day_2 = max(self.initial_date, self.final_date)
            while day_2 >= day_1:
                self.setDateTextFormat(day_1, format)
                day_1 = day_1.addDays(1)


class CalendarDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.calendar_width = 500
        self.calendar_height = 300
        self.setMinimumSize(self.calendar_width, self.calendar_height)

        self.calendar = Calendar()

        self.top_layout = QVBoxLayout()
        self.top_layout.addWidget(self.calendar)

        self.bottom_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.cancel_button = QPushButton("Cancel")
        self.bottom_layout.addWidget(self.select_button)
        self.bottom_layout.addWidget(self.cancel_button)
        self.select_button.clicked.connect(self.get_date_range)
        self.select_button.clicked.connect(self.close_on_click)
        self.cancel_button.clicked.connect(self.close_on_click)

        main_layout = QVBoxLayout()
        main_layout.addLayout(self.top_layout)
        main_layout.addLayout(self.bottom_layout)

        self.initial_d = None
        self.final_d = None
        self.setLayout(main_layout)

    def get_date_range(self):
        if self.calendar.initial_date and self.calendar.final_date:
            self.initial_d = min(self.calendar.initial_date.toPyDate(), self.calendar.final_date.toPyDate())
            self.final_d = max(self.calendar.initial_date.toPyDate(), self.calendar.final_date.toPyDate())

    def close_on_click(self):
        self.close()
