"""
billeterapp 2.0 - Junio 2024

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.country import CountryAlpha3

from src.pwhandler.pwhandler import hash_password
from src.models.usrmodel import User, UserNotFoundError


class UserAlreadyExistsError(Exception):
    pass


class CreateUserCommand(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    birthdate: Optional[datetime.date] = None
    gender: Optional[str] = None
    region: Optional[CountryAlpha3] = Field(default=None, description="The ISO 3166-1-alfa3 country code.")
    email: EmailStr
    password: str

    def execute(self, test=False) -> User:
        try:
            User.get_user_by_email(self.email)
            raise UserAlreadyExistsError
        except UserNotFoundError:
            pass

        if not test:
            self.password = hash_password(self.password)

        user = User(
            first_name=self.first_name,
            last_name=self.last_name,
            birthdate=self.birthdate,
            gender=self.gender,
            region=self.region,
            email=self.email,
            password=self.password,
        ).create()

        return user


class EditUserCommand(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[datetime.date] = None
    gender: Optional[str] = None
    region: Optional[CountryAlpha3] = Field(default=None, description="The ISO 3166-1-alfa3 country code.")

    def execute(self) -> User:
        user = User.get_user_by_id(self.user_id)
        if self.first_name:
            user.first_name = self.first_name
        if self.last_name:
            user.last_name = self.last_name
        if self.birthdate:
            user.birthdate = self.birthdate
        if self.gender:
            user.gender = self.gender
        if self.region:
            user.region = self.region
        user.save()

        return user


class DeleteUserCommand(BaseModel):
    user_id: str
    password: str

    def execute(self):
        user = User.get_user_by_id(self.user_id)
        user.delete(user_id=self.user_id, password=self.password)
