"""
billeterapp 2.0 - Junio 2024
billeterapp 2.0 - v2.0 Marzo 2026

This module handles the model of accounts.
Creation of one dedicated directory and database for every user created and
their corresponding accounts table.

This module is intended to be used by the module commands and not directly.

"""

import re
from decimal import Decimal
from datetime import datetime
from typing import Optional, Any

from ulid import ULID
from pydantic import BaseModel, Field, field_validator
from pydantic_extra_types.currency_code import ISO4217

from src.errorhandler.accountserrors import InvalidAccountNameError


class Accounts(BaseModel, validate_assignment=True):
    user_id: str
    account_id: str = Field(default_factory=lambda: "acc_" + str(ULID()))
    account_name: Optional[str] = None
    account_currency: Optional[ISO4217] = None
    account_total: Optional[Decimal] = Field(ge=0, default=None)
    is_active: bool = True
    tags: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("account_name")
    @classmethod
    def __name_validator(cls, acc_name) -> str:
        """
        Validates names of the account or the table if they have only alphanumeric chars and underscores for
        security reasons.

        Args:
            acc_name (str): Name of the account.

        Returns:
            str: Name of the account.
        """
        if not re.match(r"^[a-zA-Z0-9_]*$", acc_name):
            raise InvalidAccountNameError
        return acc_name

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: Any) -> "Accounts":
        return cls(**row)
