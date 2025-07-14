#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
created on 09/02/2023
"""
import os

from PyQt5 import QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QMainWindow

from src.models.usrmodel import UserNotFoundError
from src.queries.usrqueries import GetUserByEmailQuery
from src.commands.usrcommands import DeleteUserCommand
from src.pwhandler.pwhandler import UnauthorizedError

from billeUI import welcomescreen
from billeUI import UISPATH


class DeleteUserScreen(QMainWindow):
    """
    UI where the users can delete an existing userwith e-mail, user name, and password
    """

    def __init__(self, parent=None, widget=None):
        super(DeleteUserScreen, self).__init__(parent)
        delete_user_screen = os.path.join(UISPATH, "delete_user_screen.ui")
        loadUi(delete_user_screen, self)
        self.widget = widget
        self.password_line.setEchoMode(QLineEdit.Password)
        self.delete_user_button.clicked.connect(self.delete_user)
        self.back_button.clicked.connect(self.back)
        self.usr_deleted_msg = QMessageBox()

    def delete_user(self):
        """Deletes the user: Remove data from database and remove all directories with accounts on it."""
        confirmation = self.confirmation_box.isChecked()
        if not confirmation:
            self.delete_label.setText("<font color='red'>Please confirm by checking the box.</font>")
            return
        username = self.user_name_line.text()
        useremail = self.email_line.text()
        password = self.password_line.text().encode("utf-8")
        try:
            user = GetUserByEmailQuery(user_email=useremail).execute()
            DeleteUserCommand(user_id=user.user_id, password=password).execute()
            popup_message = self.usr_deleted_msg.question(
                self,
                "User deleted.",
                f"User {username} deleted.\nDo you want to go back?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if popup_message == QMessageBox.Yes:
                self.back()
            if popup_message == QMessageBox.No:
                pass
            self.delete_label.setText(f"<font color='green'>User {username} deleted.</font>")
        except UserNotFoundError:
            self.delete_label.setText(f"<font color='red'>User <b>{username}</b> does not exist</font>")
        except UnauthorizedError:
            self.delete_label.setText("<font color='red'>Wrong password</font>")
        except ValueError:
            self.delete_label.setText("<font color='red'>Invalid email format.</font>")

    def back(self):
        """Returns to the WelcomScren menu."""
        welcome = welcomescreen.WelcomeScreen(widget=self.widget)
        self.widget.addWidget(welcome)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def keyPressEvent(self, e):
        """Returns to the WelcomScren menu when Esc Key is pressed."""
        if e.key() == QtCore.Qt.Key_Escape:
            welcome = welcomescreen.WelcomeScreen(widget=self.widget)
            self.widget.addWidget(welcome)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
