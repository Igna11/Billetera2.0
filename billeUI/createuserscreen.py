#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 09/02/2023
"""
import os

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QMainWindow

# from src.errors import errors
from billeUI import UISPATH
from billeUI import welcomescreen
from billeUI import operationscreen

from src import BASEPATH
from src.models.usrmodel import User
from src.models.accmodel import UserAccounts
from src.commands.usrcommands import CreateUserCommand, UserAlreadyExistsError
from src.queries.usrqueries import GetUserByEmailQuery

DATAPATH = os.path.join(BASEPATH, "data")


class CreateUserScreen(QMainWindow):
    """
    UI where the users can create a new account with an e-mail, user name, and password
    """

    def __init__(self, parent=None, widget=None):
        super(CreateUserScreen, self).__init__(parent)
        create_user_screen = os.path.join(UISPATH, "create_user_screen.ui")
        loadUi(create_user_screen, self)
        self.widget = widget
        self.password_line.setEchoMode(QLineEdit.Password)
        self.confirm_password_line.setEchoMode(QLineEdit.Password)
        self.signup_button.clicked.connect(self.sign_up)
        self.back_button.clicked.connect(self.back)
        self.usr_created_msg = QMessageBox()

    def sign_up(self):
        """Creates the user: saves it into the database and creates the directories"""
        username = self.user_name_line.text()
        useremail = self.email_line.text()
        password = self.password_line.text()
        password_check = self.confirm_password_line.text()
        if password != password_check:
            self.create_user_label.setText("<font color='red'><b>Passwords don't match.</b></font>")
        else:
            try:
                user = CreateUserCommand(first_name=username, email=useremail, password=password).execute()
                db_directory_path = os.path.join(DATAPATH, user.user_id)
                os.mkdir(db_directory_path)
                UserAccounts.create_acc_list_table(user.user_id)
                self.create_user_label.setText(f"<font color='green'>User {username} successfully created.</font>")
                popup_message = self.usr_created_msg.question(
                    self,
                    "User created!.",
                    f"User {username} successfully created!\nDo you want to log in?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if popup_message == QMessageBox.Yes:
                    self.login(useremail, password)
                if popup_message == QMessageBox.No:
                    self.back()
            except UserAlreadyExistsError:
                self.create_user_label.setText(f"<font color='red'>User with email {useremail} already exists.</font>")
            except ValueError:
                self.create_user_label.setText(f"<font color='red'>Email format '{useremail}' not valid.</font>")

    def login(self, useremail, password):
        """Logs in and takes the user to the OperationScreen menu."""
        user = GetUserByEmailQuery(user_email=useremail).execute()
        User.authenticate(user_id=user.user_id, password=password)
        self.widget.user_object = user
        operation_screen = operationscreen.OperationScreen(widget=self.widget)
        self.widget.addWidget(operation_screen)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def back(self):
        """Returns to the WelcomeScreen."""
        welcome = welcomescreen.WelcomeScreen(widget=self.widget)
        self.widget.addWidget(welcome)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the WelcomeScreen when Esc Key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            welcome = welcomescreen.WelcomeScreen(widget=self.widget)
            self.widget.addWidget(welcome)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
