"""
billeterapp 2.0 - Junio 2024
"""

from typing import List

from pydantic import BaseModel, EmailStr

from src.models.usrmodel import User


class GetUserByIDQuery(BaseModel):

    user_id: str

    def execute(self) -> "User":
        user = User.get_user_by_id(self.user_id)
        return user


class GetUserByEmailQuery(BaseModel):

    user_email: EmailStr

    def execute(self) -> "User":
        user = User.get_user_by_email(self.user_email)
        return user


class ListUsersQuery(BaseModel):
    def execute(self) -> List["User"]:
        users = User.get_all_users()
        return users
