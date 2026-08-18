#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TagLabel Widget
Displays tags as oval-shaped labels with light purple background and dark grey text.
"""

from PyQt5.QtWidgets import QLabel, QHBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt


class TagLabel(QWidget):
    """
    A widget that displays a tag as an oval-shaped label with optional close button.
    """

    def __init__(self, tag_text: str, show_close_button: bool = False, parent=None):
        super().__init__(parent)
        self.tag_text = tag_text
        self.show_close_button = show_close_button
        self.setup_ui()

    def setup_ui(self):
        """Setup the tag label UI with oval styling."""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Tag label with oval styling
        self.label = QLabel(self.tag_text)
        self.label.setStyleSheet(
            """
            QLabel {
                background-color: #E0D4F0;
                color: #4A4A4A;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 8pt;
            }
        """
        )
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # Optional close button
        if self.show_close_button:
            self.close_button = QPushButton("×")
            self.close_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #E0D4F0;
                    color: #4A4A4A;
                    border: none;
                    border-radius: 8px;
                    font-size: 12pt;
                    font-weight: bold;
                    padding: 0px 4px;
                    min-width: 16px;
                    max-width: 16px;
                }
                QPushButton:hover {
                    background-color: #D0C4E0;
                }
                QPushButton:pressed {
                    background-color: #C0B4D0;
                }
            """
            )
            self.close_button.setCursor(Qt.PointingHandCursor)
            layout.addWidget(self.close_button)

        self.setLayout(layout)
        self.setStyleSheet("background-color: transparent;")


class TagContainer(QWidget):
    """
    A container widget that displays multiple tags as a horizontal layout of TagLabels.
    """

    def __init__(self, tags: tuple | None, show_close_buttons: bool = False, parent=None):
        super().__init__(parent)
        self.tags = tags
        self.show_close_buttons = show_close_buttons
        self.setup_ui()

    def setup_ui(self):
        """Setup the tag container with horizontal layout of tags."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if self.tags:
            for tag in self.tags:
                tag_label = TagLabel(tag, show_close_button=self.show_close_buttons)
                layout.addWidget(tag_label)
        else:
            no_tags_label = QLabel("No tags")
            no_tags_label.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
            layout.addWidget(no_tags_label)

        layout.addStretch()
        self.setLayout(layout)
