#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
created on 23/07/2023 16:00 by chatgpt
"""

from PyQt5 import QtWidgets, QtGui


class HeaderFilterMixin:
    OPERATION_TYPE_COLUMN = 3
    CATEGORY_COLUMN = 4
    SUBCATEGORY_COLUMN = 5
    DESCRIPTION_COLUMN = 6
    GROUP_COLUMN = 7
    TAGS_COLUMN = 8

    def init_header_filter(self, table_widget, filterable_columns, operations_list, groups_dict=None):
        """
        Initialize the filter system for headers:
        :param table_widget: QTableWidget where filters are being applied.
        :param filterable_columns: List of column indices to be filtered.
        :param groups_dict: Optional dictionary mapping group_id to group_name for column 7.
        """
        self.operation_table_widget = table_widget
        self.operations_list = operations_list
        self.filterable_columns = filterable_columns
        self.active_filters = {}
        self.groups_dict = groups_dict or {}

        header = self.operation_table_widget.horizontalHeader()
        header.sectionClicked.connect(self._handle_header_click)

    def _handle_header_click(self, column_index):
        if column_index not in self.filterable_columns:
            return

        # Special handling for description column (column 6) - show search bar instead of checkboxes
        if column_index == 6:
            self._show_description_search_menu(column_index)
            return

        unique_values = set()
        filtered_ops = self._filtered_operations_for_column(exclude_col=column_index)

        for operation in filtered_ops:
            if column_index == self.OPERATION_TYPE_COLUMN:
                unique_values.add(operation.operation_type)
            elif column_index == self.CATEGORY_COLUMN:
                unique_values.add(operation.category)
            elif column_index == self.SUBCATEGORY_COLUMN:
                unique_values.add(operation.subcategory)
            elif column_index == self.GROUP_COLUMN:
                if operation.group_id:
                    group_name = self.groups_dict.get(operation.group_id, operation.group_id)
                    unique_values.add(group_name)
                else:
                    unique_values.add("N/A")
            elif column_index == self.TAGS_COLUMN:
                if operation.tags:
                    unique_values.update(operation.tags)

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

    def _show_description_search_menu(self, column_index):
        """Show a search bar menu for the description column"""
        current_search = self.active_filters.get(column_index, "")

        # Menu creation
        menu = QtWidgets.QMenu(self.operation_table_widget)

        # Search input field
        search_widget = QtWidgets.QWidget()
        search_layout = QtWidgets.QVBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)

        # Label
        label = QtWidgets.QLabel("Filter by description:")
        search_layout.addWidget(label)

        # Search input
        search_input = QtWidgets.QLineEdit()
        search_input.setPlaceholderText("Enter search term...")
        search_input.setText(current_search)
        search_layout.addWidget(search_input)

        # Buttons
        btn_apply = QtWidgets.QPushButton("✅ Apply")
        btn_clear = QtWidgets.QPushButton("❌ Clear")

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(btn_apply)
        button_layout.addWidget(btn_clear)
        search_layout.addLayout(button_layout)

        search_widget.setLayout(search_layout)

        widget_action = QtWidgets.QWidgetAction(menu)
        widget_action.setDefaultWidget(search_widget)
        menu.addAction(widget_action)

        # Signals
        btn_apply.clicked.connect(lambda: self._apply_description_filter(menu, column_index, search_input))
        btn_clear.clicked.connect(lambda: self._clear_description_filter(menu, column_index, search_input))

        # Focus on search input when menu is shown
        menu.aboutToShow.connect(lambda: search_input.setFocus())

        # Show menu
        menu.exec_(QtGui.QCursor.pos())

    def _apply_description_filter(self, menu, column_index, search_input):
        """Apply the description search filter"""
        search_term = search_input.text().strip()
        if search_term:
            self.active_filters[column_index] = search_term
        else:
            self.active_filters.pop(column_index, None)
        menu.close()
        self._apply_active_filters()

    def _clear_description_filter(self, menu, column_index, search_input):
        """Clear the description search filter"""
        search_input.clear()
        self.active_filters.pop(column_index, None)
        menu.close()
        self._apply_active_filters()

    def _filtered_operations_for_column(self, exclude_col=None):
        """
        Returns the list of filtered operations by the active filters, except the exclude_col filter (if exists)
        """
        filtered = []
        for op in self.operations_list:
            ok = True
            for col, filter_value in self.active_filters.items():
                if exclude_col is not None and col == exclude_col:
                    continue
                if col == self.OPERATION_TYPE_COLUMN:
                    if op.operation_type not in filter_value:
                        ok = False
                        break
                elif col == self.CATEGORY_COLUMN:
                    if op.category not in filter_value:
                        ok = False
                        break
                elif col == self.SUBCATEGORY_COLUMN:
                    if op.subcategory not in filter_value:
                        ok = False
                        break
                elif col == self.DESCRIPTION_COLUMN:
                    if not (op.description and filter_value.lower() in op.description.lower()):
                        ok = False
                        break
                elif col == self.GROUP_COLUMN:
                    group_name = self.groups_dict.get(op.group_id, op.group_id) if op.group_id else "N/A"
                    if group_name not in filter_value:
                        ok = False
                        break
                elif col == self.TAGS_COLUMN:
                    if op.tags:
                        allowed_vals_lower = {val.lower() for val in filter_value}
                        if not any(tag.lower() in allowed_vals_lower for tag in op.tags):
                            ok = False
                            break
                    else:
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

    def update_groups_dict(self, groups_dict):
        """Update the groups dictionary for group column filtering"""
        self.groups_dict = groups_dict

    def update_operations_list(self, operations_list):
        """Update the operations list for filtering"""
        self.operations_list = operations_list
