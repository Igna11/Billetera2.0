#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 21/12/2025 11:56

@author: igna
"""
import os
import sqlite3

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QMessageBox,
    QWidget,
    QLabel,
    QFrame,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QRadioButton,
)
from src.models.opmodel import InvalidAccountNameError
from src.models.opgroupsmodel import OperationGroups
from src.commands.groupcommands import (
    DeleteOperationGroupCommand,
    EditOperationGroupCommand,
)

from billeUI import UISPATH, ICONSPATH, animatedlabel


class GroupDataRow(QWidget):

    group_modified = pyqtSignal(str, str, bool)

    def __init__(self, group: OperationGroups, parent=None):
        super().__init__(parent)
        # Needed for the hover effect
        self.group = group
        self.group_id = group.group_id
        self.group_name = group.group_name
        self.new_group_name = ""
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.frame = QFrame(self)
        self.frame.setObjectName("GroupRowFrame")
        self.frame.setStyleSheet(
            """
            QFrame#GroupRowFrame {
                background-color: transparent;
                border-radius: 6px;
            }
            QFrame#GroupRowFrame:hover {
                background-color: #e6f2ff;
                border: 1px solid #cccccc;
            }
        """
        )

        # Labels
        font = QFont()
        font.setPointSize(11)

        # name_line
        self.name_label = QLabel(f"<b>{self.group_name}</b>")
        self.name_line_edit = QLineEdit(self)
        self.name_line_edit.setText(self.group_name)
        self.name_line_edit.hide()
        self.name_line_edit.editingFinished.connect(self.show_qlabel)
        self.category_label = QLabel(group.category)
        self.category_label.setFont(font)

        # Buttons and Icons
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon(os.path.join(ICONSPATH, "edit.svg")))
        self.edit_btn.clicked.connect(self.enable_edit_mode)
        self.edit_btn.setToolTip("Edit group")

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(os.path.join(ICONSPATH, "delete.svg")))
        self.delete_btn.setToolTip("Delete group")
        self.delete_btn.clicked.connect(self.delete_group)

        # self.disable_btn = QPushButton()
        # self.disable_btn.setIcon(QIcon(os.path.join(ICONSPATH, "disable.svg")))
        # self.disable_btn.setToolTip("Disable account")

        self.enable_disable_btn = QRadioButton()
        self.enable_disable_btn.setToolTip("Disable group")
        # if group.is_active:
        #    self.enable_disable_btn.setChecked(True)
        # self.enable_disable_btn.clicked.connect(self.enable_n_disable_group)

        # Layouts
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.name_line_edit)
        text_layout.addWidget(self.category_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.enable_disable_btn)

        inner_layout = QHBoxLayout()
        inner_layout.addLayout(text_layout)
        inner_layout.addStretch()
        inner_layout.addLayout(btn_layout)
        inner_layout.setContentsMargins(5, 3, 5, 3)

        self.frame.setLayout(inner_layout)

        # outer layout
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.frame)
        outer_layout.setContentsMargins(0, 0, 0, 0)

    def enable_edit_mode(self) -> None:
        """Enables the edition of the account name"""
        self.name_label.hide()
        self.name_line_edit.show()
        self.name_line_edit.setFocus()
        self.name_line_edit.selectAll()

    def show_qlabel(self) -> None:
        """Resets the label with the new values"""
        self.new_group_name = self.name_line_edit.text().strip()
        self.name_label.setText(self.new_group_name)
        if self.new_group_name != self.group_name:
            self.name_label.setStyleSheet("color: orange; font-weight: bold; font-style: italic;")
            self.group_modified.emit(self.group_id, self.new_group_name, True)
        else:
            self.name_label.setStyleSheet("color: black; font-weight: bold;")
            self.group_modified.emit(self.group_id, self.group_name, False)
        self.name_line_edit.hide()
        self.name_label.show()

    def delete_group(self) -> None:
        confirmation_message = """
        Are you really sure you want to delete the selected group?
        All the information will be lost and will not be recoverable.
        """
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            confirmation_message,
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            DeleteOperationGroupCommand(user_id=self.group.user_id, group_id=self.group.group_id).execute()
            # refresh view without the deleted widget
            animatedlabel.AnimatedLabel("Group deleted ✅").display()
            parent_layout = self.parentWidget().layout()
            parent_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

    def enable_n_disable_group(self) -> None:
        """not implemented"""
        pass

    def refresh_account_data(self) -> None:
        self.group = OperationGroups.get_groups_list(user_id=self.group.user_id).execute()


class GroupBrowserWidget(QWidget):
    """
    group browser and editor
    """

    def __init__(self, parent=None, widget=None) -> None:
        super(GroupBrowserWidget, self).__init__(parent)
        group_browser = os.path.join(UISPATH, "opgroups_browser_widget.ui")
        loadUi(group_browser, self)
        self.widget = widget

        self.user_id = self.widget.user_object.user_id

        self.group_changed = set()
        self.group_row_list = []

        self.save_changes_button.setEnabled(False)
        self.save_changes_button.clicked.connect(self.save_group_changes)

        self.close_button.clicked.connect(self.close_group_widget)

        self.group_object = OperationGroups.get_groups_list(user_id=self.widget.user_object.user_id)

        self.scroll_content = self.findChild(QWidget, "scrollAreaWidgetContents")
        self.scroll_layout = self.scroll_content.layout()

        for group in self.group_object:
            row = self.add_group(group)
            self.group_row_list.append(row)

    def save_group_changes(self) -> None:
        """loops through all group_ids in the group_changed set and saves the changes into the db"""
        row_to_be_saved = [row for row in self.group_row_list if row.group_id in self.group_changed]
        for row in row_to_be_saved:
            try:
                EditOperationGroupCommand(
                    user_id=self.user_id, group_id=row.group_id, group_name=row.new_group_name
                ).execute()
                row.name_label.setStyleSheet("color: black; font-weight: bold;")
                animatedlabel.AnimatedLabel("Changes saved! ✅", message_type="success").display()
                self.save_changes_button.setEnabled(False)
            except sqlite3.OperationalError:
                animatedlabel.AnimatedLabel("Duplicated name!", message_type="error").display()
            except InvalidAccountNameError:
                animatedlabel.AnimatedLabel("Invalid name!", message_type="error").display()

    def add_group(self, group: OperationGroups) -> GroupDataRow:
        row = GroupDataRow(group)
        row.group_modified.connect(self.handle_group_modified)
        self.scroll_layout.addWidget(row)
        return row

    def handle_group_modified(self, group_id: str, new_group_name: str, is_modified: bool) -> None:
        if is_modified:
            self.group_changed.add(group_id)
        else:
            self.group_changed.discard(group_id)
        self.save_changes_button.setEnabled(len(self.group_changed) > 0)

    def close_group_widget(self) -> None:
        """Returns to the OperationScreen Menu"""
        self.close()

    def keyPressEvent(self, e):
        """Returns to the OperationScreen Menu when Esc key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            self.close_group_widget()
