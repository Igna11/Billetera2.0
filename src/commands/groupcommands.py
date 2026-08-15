"""
billeterapp 2.0 - Agosto 2025
Updated - Mayo 2026

High level module to handle groups of operations
"""

from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional, Literal

from src.models.opgroupsmodel import OperationGroups
from src.dbhandlers.opgroupsdb import OperationGroupsDB
from src.errorhandler.opgroupserrors import GroupNotFoundError, NoEditedGroupFieldsError


class CreateOperationGroupCommand(OperationGroups):

    status: Literal["open", "closed"] = "open"

    def execute(self) -> OperationGroups:
        self.created_at = self.updated_at = datetime.now(UTC)
        group_db = OperationGroupsDB(self.user_id)  # type: ignore[arg-type]
        group_db.create_group(self)
        return self


class EditOperationGroupCommand(OperationGroups):

    user_id: str
    group_id: str
    group_name: Optional[str] = None
    group_currency: Optional[str] = None
    original_amount: Optional[Decimal] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["open", "closed"]] = None

    def execute(self) -> OperationGroups:
        field_check_list = [
            self.group_name,
            self.group_currency,
            self.original_amount,
            self.category,
            self.subcategory,
            self.description,
            self.status,
        ]

        if all(field is None for field in field_check_list):
            raise NoEditedGroupFieldsError

        group_db = OperationGroupsDB(self.user_id)  # type: ignore[arg-type]
        group_data = group_db.get_group_by_id(self.group_id)

        if not group_data:
            raise GroupNotFoundError

        # Get existing group and update only provided fields
        existing_group = OperationGroups.from_row(group_data)

        if self.group_name:
            existing_group.group_name = self.group_name
        if self.group_currency:
            existing_group.group_currency = self.group_currency
        if self.original_amount:
            existing_group.original_amount = self.original_amount
        if self.category:
            existing_group.category = self.category
        if self.subcategory:
            existing_group.subcategory = self.subcategory
        if self.description:
            existing_group.description = self.description
        if self.status:
            existing_group.status = self.status

        existing_group.updated_at = datetime.now(UTC)
        group_db.update_group(existing_group)

        return existing_group


class DeleteOperationGroupCommand(OperationGroups):

    user_id: str
    group_id: str

    def execute(self) -> None:
        group_db = OperationGroupsDB(self.user_id)  # type: ignore[arg-type]
        group_data = group_db.get_group_by_id(self.group_id)

        if not group_data:
            raise GroupNotFoundError

        group_db.delete_group(self.group_id)
