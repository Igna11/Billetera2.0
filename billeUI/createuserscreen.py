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
from billeUI import welcomescreen, operationscreen

from src import BASEPATH
from src.dbtables.accountstable import initialize_accounts_table
from src.dbtables.operationstable import initialize_operations_table
from src.dbtables.detailstable import initialize_details_table
from src.dbtables.groupstable import initialize_groups_table
from src.commands.userscommands import CreateUserCommand, UserAlreadyExistsError
from src.queries.usersqueries import GetUserByEmailQuery
from src.dbhandlers.accountsdb import AccountsDB
from src.dbhandlers.usersdb import UsersDB
from src.pwhandler.pwhandler import verify_password

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
                user = CreateUserCommand(first_name=username, email=useremail).execute(plain_text_passwd=password)
                db_directory_path = os.path.join(DATAPATH, user.user_id)
                os.mkdir(db_directory_path)
                # Initialize accounts database for the user
                initialize_accounts_table(user_id=user.user_id)
                initialize_operations_table(user_id=user.user_id)
                initialize_groups_table(user_id=user.user_id)
                initialize_details_table(user_id=user.user_id)
                AccountsDB(user_id=user.user_id)
                # The accounts table is created automatically by DatabaseConnection
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
            except ValueError as e:
                print(e)
                self.create_user_label.setText(f"<font color='red'>Email format '{useremail}' not valid.</font>")

    def login(self, useremail, password):
        """Logs in and takes the user to the OperationScreen menu."""
        user = GetUserByEmailQuery(email=useremail).execute()
        user_db = UsersDB()
        user_with_password = user_db.get_user_with_password(useremail)
        if not user_with_password:
            raise Exception("User not found")
        if not verify_password(user_with_password["password"], password):
            raise Exception("Invalid password")
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
