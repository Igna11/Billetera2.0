#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 05/02/2023
"""
import os

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow

from src.models.usrmodel import User
from billeUI import UISPATH
from billeUI import loginscreen
from billeUI import createuserscreen
from billeUI import deleteuserscreen


class WelcomeScreen(QMainWindow):
    """
    UI where the user can choose between log in into an existing account or
    creating a new one.
    """

    def __init__(self, parent=None, widget=None):
        super(WelcomeScreen, self).__init__(parent)
        welcome_screen = os.path.join(UISPATH, "bille_screen.ui")
        loadUi(welcome_screen, self)
        User.create_table()
        self.widget = widget
        self.login_button.clicked.connect(self.login_window)
        self.create_account_button.clicked.connect(self.create_user_window)
        self.delete_user_button.clicked.connect(self.delete_user_window)

    def login_window(self):
        login_button = loginscreen.LoginScreen(widget=self.widget)
        self.widget.addWidget(login_button)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def create_user_window(self):
        signup_button = createuserscreen.CreateUserScreen(widget=self.widget)
        self.widget.addWidget(signup_button)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def delete_user_window(self):
        delete_button = deleteuserscreen.DeleteUserScreen(widget=self.widget)
        self.widget.addWidget(delete_button)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            pass
