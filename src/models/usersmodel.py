"""
billeterapp 2.0 - Junio 2024
billeterapp 2.0 - v2.0 Marzo 2026

This module handles the models of users and accounts.
Creation of the users database and the table "users" in the main directory.

This module is intended to be used by the module commands and not directly.
"""

from datetime import date, datetime
from typing import Optional, Any

from ulid import ULID
from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.country import CountryAlpha3


class Users(BaseModel, validate_assignment=True):
    user_id: str = Field(default_factory=lambda: "user_" + str(ULID()))
    first_name: str
    last_name: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[str] = None
    region: Optional[CountryAlpha3] = Field(default=None, description="The ISO 3166-1-alfa3 country code.")  # type: ignore
    email: EmailStr
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: Any) -> "Users":
        return cls(**row)
