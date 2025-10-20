"""
billeterapp 2.0 - Agosto 2025

High level module to handle groups of operations
"""

from decimal import Decimal
from typing import Optional, Literal

from src.models.opgroupsmodel import OperationGroups


class NoEditedFieldsError(Exception):
    pass


class CreateOperationGroupCommand(OperationGroups):

    status: str = "open"

    def execute(self):
        oper_group = OperationGroups(**self.model_dump())
        group = oper_group.create()
        return group


class EditOperationGroupCommand(OperationGroups):

    group_id: str
    group_name: Optional[str] = None
    group_currency: Optional[str] = None
    original_amount: Optional[Decimal] = None
    status: Optional[Literal["open", "closed", "cancelled"]] = None

    def execute(self):

        field_check_list = [
            self.group_name,
            self.group_currency,
            self.status,
        ]

        if all(field is None for field in field_check_list):
            raise NoEditedFieldsError

        oper_group = OperationGroups.get_group_by_id(self.user_id, self.group_id)

        if self.group_name:
            oper_group.group_name = self.group_name
        if self.group_currency:
            oper_group.group_currency = self.group_currency
        if self.original_amount:
            oper_group.original_amount = self.original_amount
        if self.status:
            oper_group.status = self.status

        return oper_group.save()


class DeleteOperationGroupCommand(OperationGroups):

    user_id: str
    group_id: str
    group_name: str = None
    status: str = "cancelled"

    def execute(self):
        group = OperationGroups.get_group_by_id(user_id=self.user_id, group_id=self.group_id)
        group.delete()
