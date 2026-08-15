"""
billeterapp 2.0 - Junio 2024
billeterapp 2.0 - v2.0 Marzo 2026

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

from datetime import datetime, UTC
from typing import Optional

from pydantic import EmailStr

from src.errorhandler.userserrors import UserAlreadyExistsError, UserNotFoundError
from src.pwhandler.pwhandler import hash_password
from src.models.usersmodel import Users
from src.dbhandlers.usersdb import UsersDB


class CreateUserCommand(Users):

    def execute(self, plain_text_passwd: str, test: bool = False) -> Users:
        self.created_at = self.updated_at = datetime.now(UTC)
        user_db = UsersDB()
        if user_db.get_user_by_email(self.email):
            raise UserAlreadyExistsError

        if not test:
            hashed_passwd = hash_password(plain_text_passwd)
        else:
            hashed_passwd = plain_text_passwd
        user = Users.from_row(user_db.create_user(self, hashed_passwd))
        return user


class EditUserCommand(Users):

    def execute(self) -> Users:
        user_db = UsersDB()
        user_db_data = user_db.get_user_by_id(self.user_id)

        if not user_db_data:
            raise UserNotFoundError

        self.updated_at = datetime.now(UTC)
        user_db.update_user(self)

        return self


class DeleteUserCommand(Users):

    first_name: Optional[str] = None  # type: ignore[assignment]
    email: Optional[EmailStr] = None  # type: ignore[assignment]

    def execute(self):
        user_db = UsersDB()
        if not user_db.get_user_by_id(self.user_id):
            raise UserNotFoundError
        user_db.delete_user(user_id=self.user_id)
