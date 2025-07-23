#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
created on 23/07/2023 16:00 by chatgpt
"""

from PyQt5 import QtWidgets, QtGui


class HeaderFilterMixin:
    def init_header_filter(self, table_widget, filterable_columns):
        """
        Initialize the filter system for headers:
        :param table_widget: QTableWidget where filters are being applied.
        :param filterable_columns: List of column indices to be filtered.
        """
        self.operation_table_widget = table_widget
        self.filterable_columns = filterable_columns
        self.active_filters = {}

        header = self.operation_table_widget.horizontalHeader()
        header.sectionClicked.connect(self._handle_header_click)

    def _handle_header_click(self, column_index):
        if column_index not in self.filterable_columns:
            return

        unique_values = set()
        for row in range(self.operation_table_widget.rowCount()):
            item = self.operation_table_widget.item(row, column_index)
            if item:
                unique_values.add(item.text())

        current_filters = self.active_filters.get(column_index, set())

        # Menu creation
        menu = QtWidgets.QMenu(self.operation_table_widget)
        actions = {}

        # checkboxes
        for val in sorted(unique_values):
            checkbox = QtWidgets.QCheckBox(val)
            checkbox.setChecked(val in current_filters)

            widget_action = QtWidgets.QWidgetAction(menu)
            widget_action.setDefaultWidget(checkbox)

            menu.addAction(widget_action)
            actions[checkbox] = val

        # Separator
        menu.addSeparator()

        btn_apply = QtWidgets.QPushButton("✅ Apply")
        btn_clear = QtWidgets.QPushButton("❌ Clear")

        action_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(btn_apply)
        layout.addWidget(btn_clear)
        action_widget.setLayout(layout)

        widget_action_buttons = QtWidgets.QWidgetAction(menu)
        widget_action_buttons.setDefaultWidget(action_widget)
        menu.addAction(widget_action_buttons)

        # Signalas
        btn_apply.clicked.connect(lambda: self._apply_checkbox_filters(menu, column_index, actions))
        btn_clear.clicked.connect(lambda: self._clear_column_filter(menu, column_index))

        # Show menu
        menu.exec_(QtGui.QCursor.pos())

    def _apply_checkbox_filters(self, menu, column_index, actions):
        selected = {val for cb, val in actions.items() if cb.isChecked()}
        if selected:
            self.active_filters[column_index] = selected
        else:
            self.active_filters.pop(column_index, None)
        menu.close()
        self._apply_active_filters()

    def _clear_column_filter(self, menu, column_index):
        self.active_filters.pop(column_index, None)
        menu.close()
        self._apply_active_filters()

    def _apply_active_filters(self):
        for row in range(self.operation_table_widget.rowCount()):
            show_row = True
            for col_idx, allowed_values in self.active_filters.items():
                item = self.operation_table_widget.item(row, col_idx)
                if not item or item.text() not in allowed_values:
                    show_row = False
                    break
            self.operation_table_widget.setRowHidden(row, not show_row)

    def clear_all_filters(self):
        self.active_filters.clear()
        self._apply_active_filters()
