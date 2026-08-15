"""
billeterapp 2.0 - Junio 2024

This module handles the model of operation details.

This module is intended to be used by the module commands and not directly.
"""

from datetime import datetime
from typing import Optional, Any

from ulid import ULID
from pydantic import BaseModel, Field


class OperationDetails(BaseModel, validate_assignment=True):

    user_id: Optional[str] = None
    operation_id: Optional[str] = None
    account_id: Optional[str] = None
    detail_id: str = Field(default_factory=lambda: "detail_" + str(ULID()))
    account_name: Optional[str] = None
    details: Optional[bytes] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: Any) -> "OperationDetails":
        return cls(**row)
