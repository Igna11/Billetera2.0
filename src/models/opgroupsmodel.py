"""
billeterapp 2.0 - Agosto 2025

This module handles the way operations group are stored into de database.

The main idea is that a table called 'operation_groups' is created to store linked operations with their amounts
so it is easy to fetch information about 'currency flow' and 'real expenses/incomes'. The easiest example are 
loans: If user A lends money to user B, it is not necesarily a real expense, because user B will reimburst to 
user A in another time. But it is a flow o money. The real expense, if user B repays the total to user A, would be 0.
"""

from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional, Literal, Any

from ulid import ULID
from pydantic import BaseModel, Field
from pydantic_extra_types.currency_code import ISO4217


class OperationGroups(BaseModel, validate_assignment=True):

    user_id: Optional[str] = None
    group_id: str = Field(default_factory=lambda: "group_" + str(ULID()))
    group_datetime: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))
    group_name: Optional[str] = None
    group_currency: Optional[ISO4217] = None
    original_amount: Optional[Decimal] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["open", "closed"]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: Any) -> "OperationGroups":
        return cls(**row)
