#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 08/02/2023
"""
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow

from pydantic import ValidationError

from src.pwhandler.pwhandler import UnauthorizedError, verify_password
from src.queries.usersqueries import GetUserByEmailQuery
from src.dbhandlers.usersdb import UsersDB
from src.errorhandler.userserrors import UserNotFoundError

from billeUI import UISPATH
from billeUI import welcomescreen
from billeUI import operationscreen


class LoginScreen(QMainWindow):
    """
    UI where the users can log in with their accounts using their credentials.
    """

    def __init__(self, parent=None, widget=None):
        super(LoginScreen, self).__init__(parent)
        login_screen = os.path.join(UISPATH, "login_screen.ui")
        loadUi(login_screen, self)
        self.widget = widget
        self.password_line.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_line.returnPressed.connect(self.login)
        self.user_email_line.returnPressed.connect(self.login)
        self.login_button.clicked.connect(self.login)
        self.back_button.clicked.connect(self.back)

    def login(self):
        """Logs in the user and takes them to the OperationScreen menu."""
        user_email = self.user_email_line.text().lower()
        password = self.password_line.text()
        try:
            user = GetUserByEmailQuery(email=user_email).execute()
            user_db = UsersDB()
            user_with_password = user_db.get_user_with_password(user_email)
            if not user_with_password:
                raise UserNotFoundError
            if not verify_password(user_with_password["password"], password):
                raise UnauthorizedError
            self.login_label.setText("<font color='green'>Log in successfull</font>")
            self.widget.user_object = user
            operation_screen = operationscreen.OperationScreen(widget=self.widget)
            self.widget.addWidget(operation_screen)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        except UnauthorizedError:
            self.login_label.setText("<font color='red'>User or password invalid.</font>")
        except ValidationError:
            self.login_label.setText("<font color='red'>Invalid email.</font>")
        except UserNotFoundError:
            self.login_label.setText("<font color='red'>User or password invalid.</font>")

    def back(self):
        """Returns to the WelcomeScreen menu"""
        welcome = welcomescreen.WelcomeScreen(widget=self.widget)
        self.widget.addWidget(welcome)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the WelcomeScreen menu when Esc Key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            welcome = welcomescreen.WelcomeScreen(widget=self.widget)
            self.widget.addWidget(welcome)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
