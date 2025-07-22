#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 21/07/2025 16:23

@author: igna
"""

from PyQt5.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtWidgets import (
    QLabel,
    QApplication,
    QGraphicsOpacityEffect,
)


class AnimatedLabel(QLabel):
    def __init__(self, message: str, message_type: str = "success", duration_ms: int = 2000, parent=None):
        if parent is None:
            parent = QApplication.activeWindow() or QApplication.topLevelWidgets()[0]
        super().__init__(message, parent)
        self.duration_ms = duration_ms

        if message_type == "success":
            background_color = "#4CAF50"
        elif message_type == "warning":
            background_color = "#FFC107"
        elif message_type == "error":
            background_color = "#F44336"
        else:
            background_color = "#FFFFFF"

        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {background_color};
                color: white;
                padding: 6px 12px;
                border-radius: 10px;
                font-weight: bold;
            }}
        """
        )
        self.setFixedHeight(30)
        self.adjustSize()

        # botton right
        parent_rect = parent.rect()
        self.move(
            parent_rect.width() - self.width() - 20,
            parent_rect.height() - self.height() - 60,
        )

    def display(self) -> None:
        self.show()

        # slide animation
        start_pos = self.pos() + QPoint(0, 60)
        end_pos = self.pos()
        self.move(start_pos)

        slide_animation = QPropertyAnimation(self, b"pos")
        slide_animation.setDuration(1000)
        slide_animation.setStartValue(start_pos)
        slide_animation.setEndValue(end_pos)
        slide_animation.setEasingCurve(QEasingCurve.OutElastic)

        slide_animation.start()

        # fade out effect
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(1.0)
        self.setGraphicsEffect(effect)

        fade_animation = QPropertyAnimation(effect, b"opacity")
        fade_animation.setDuration(1000)
        fade_animation.setStartValue(1.0)
        fade_animation.setEndValue(0.0)
        fade_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.slide_animation = slide_animation
        self.fade_animation = fade_animation

        # delete after a little while
        QTimer.singleShot(self.duration_ms, fade_animation.start)
        QTimer.singleShot(self.duration_ms + 1000, self.deleteLater)
