"""
billeterapp 2.0 - Junio 2024
"""

from typing import List, Optional

from pydantic import EmailStr

from src.dbhandlers.usersdb import UsersDB
from src.models.usersmodel import Users
from src.errorhandler.userserrors import UserNotFoundError, NoUsersError


class GetUserByIDQuery(Users):
    first_name: Optional[str] = None  # type: ignore[assignment]
    email: Optional[EmailStr] = None  # type: ignore[assignment]

    def execute(self) -> Users:
        user_db = UsersDB()
        user_data = user_db.get_user_by_id(self.user_id)
        if not user_data:
            raise UserNotFoundError

        return Users.from_row(user_data)


class GetUserByEmailQuery(Users):
    first_name: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> Users:
        user_db = UsersDB()
        user_data = user_db.get_user_by_email(self.email)
        if not user_data:
            raise UserNotFoundError
        return Users.from_row(user_data)


class ListUsersQuery:
    def __init__(self):
        pass

    def execute(self) -> List[Users]:
        user_db = UsersDB()
        users_data = user_db.get_all_users()
        if not users_data:
            raise NoUsersError
        users = [Users.from_row(user) for user in users_data]
        return users
