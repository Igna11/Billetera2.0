"""
billeterapp 2.0 - Junio 2024
Model migration - Abril 2026

This module handles the model of operations.

This module is intended to be used by the module commands and not directly.
"""

from decimal import Decimal
from datetime import datetime, UTC
from typing import Optional, Literal, Any

from ulid import ULID
from pydantic import BaseModel, Field
from pydantic_extra_types.currency_code import ISO4217


class Operations(BaseModel, validate_assignment=True):
    user_id: Optional[str] = None
    account_id: Optional[str] = None
    operation_id: str = Field(default_factory=lambda: "op_" + str(ULID()))
    operation_datetime: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))
    cumulative_amount: Optional[Decimal] = Field(ge=0, default=None)
    account_name: Optional[str] = None
    account_total: Optional[Decimal] = Field(ge=0, default=None)
    amount: Decimal = Field(gt=0)
    operation_type: Literal["income", "expense", "transfer_in", "transfer_out"]
    operation_currency: Optional[ISO4217] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    group_id: Optional[str] = None
    detail_id: Optional[str] = None
    transfer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: Any) -> "Operations":
        return cls(**row)
