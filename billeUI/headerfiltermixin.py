#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
created on 23/07/2023 16:00 by chatgpt
"""

from PyQt5 import QtWidgets, QtGui


class HeaderFilterMixin:
    def init_header_filter(self, table_widget, filterable_columns, operations_list):
        """
        Initialize the filter system for headers:
        :param table_widget: QTableWidget where filters are being applied.
        :param filterable_columns: List of column indices to be filtered.
        """
        self.operation_table_widget = table_widget
        self.operations_list = operations_list
        self.filterable_columns = filterable_columns
        self.active_filters = {}

        header = self.operation_table_widget.horizontalHeader()
        header.sectionClicked.connect(self._handle_header_click)

    def _handle_header_click(self, column_index):
        if column_index not in self.filterable_columns:
            return

        unique_values = set()
        filtered_ops = self._filtered_operations_for_column(exclude_col=column_index)

        for operation in filtered_ops:
            if column_index == 3:
                unique_values.add(operation.operation_type)
            elif column_index == 4:
                unique_values.add(operation.category)
            elif column_index == 5:
                unique_values.add(operation.subcategory)

        # for row in range(self.operation_table_widget.rowCount()):
        #     item = self.operation_table_widget.item(row, column_index)
        #     if item:
        #         unique_values.add(item.text())

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

    def _filtered_operations_for_column(self, exclude_col=None):
        """
        Devuelve la lista de operaciones filtradas por los filtros activos,
        exceptuando el filtro de la columna exclude_col (si existe).
        """
        filtered = []
        for op in self.operations_list:
            ok = True
            for col, allowed_vals in self.active_filters.items():
                if exclude_col is not None and col == exclude_col:
                    continue
                val = None
                if col == 3:
                    val = op.operation_type
                elif col == 4:
                    val = op.category
                elif col == 5:
                    val = op.subcategory
                if val not in allowed_vals:
                    ok = False
                    break
            if ok:
                filtered.append(op)
        return filtered

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

    def set_filter_callback(self, callback):
        self._filter_callback = callback

    def _apply_active_filters(self):
        if hasattr(self, "_filter_callback") and self._filter_callback:
            self._filter_callback()  # Llama al padre para regenerar la tabla

    def clear_all_filters(self):
        self.active_filters.clear()
        self._apply_active_filters()
