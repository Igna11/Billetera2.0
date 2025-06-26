"""
billeterapp 2.0 - Junio 2024

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

import datetime
from typing import Optional, Literal

from src.models.opmodel import OperationsModel, UserOperations


class NoEditedFieldsError(Exception):
    pass


class CreateAccountOperationCommand(OperationsModel):
    """Creates an operation entry for a given user in a given account in the accounts_database"""

    user_id: str
    account_id: str
    cumulative_amount: float
    amount: float

    def execute(self) -> None:
        oper = UserOperations(**self.model_dump())
        return oper.create()


class CreateNEditAccountOperationsCommand(OperationsModel):
    """Edits an account entry for a given user in a given account in the accounts_database for a given operation id"""

    user_id: str
    account_id: str
    operation_id: str
    amount: Optional[float] = None
    cumulative_amount: Optional[float] = None
    operation_datetime: Optional[datetime.datetime] = None
    operation_type: Optional[Literal["income", "expense", "transfer_in", "transfer_out"]] = None

    def execute(self, existing_operations: list, edit_flag: bool = False) -> "OperationsModel":
        oper = UserOperations(**self.model_dump())
        return oper.massive_save(existing_operations, edit_flag)


class DeleteNEditAccountOperationsCommand(OperationsModel):
    """
    Deletes the self operation and edits all other affected operations for a given user in a given acount in a given
    account in the accounts_database for a given operation id
    """

    user_id: str
    account_id: str
    operation_id: str
    amount: Optional[float] = None
    cumulative_amount: Optional[float] = None
    operation_datetime: Optional[datetime.datetime] = None
    operation_type: Optional[Literal["income", "expense", "transfer"]] = None

    def execute(self, existing_operations: list) -> "OperationsModel":
        oper = UserOperations(**self.model_dump())
        return oper.delete_n_massive_save(existing_operations)


class EditAccountOperationCommand(OperationsModel):
    """Edits an account entry for a given user in a given account in the accounts_database for a given operation id"""

    user_id: str
    account_id: str
    operation_id: str
    amount: Optional[float] = None
    cumulative_amount: Optional[float] = None
    operation_datetime: Optional[datetime.datetime] = None
    operation_type: Optional[Literal["income", "expense", "transfer"]] = None

    def execute(self) -> None:

        field_check_list = [
            self.account_name,
            self.cumulative_amount,
            self.operation_datetime,
            self.amount,
            self.operation_type,
            self.category,
            self.subcategory,
            self.description,
            self.tags,
            self.details,
            self.created_at,
            self.updated_at,
        ]

        if all(field is None for field in field_check_list):
            raise NoEditedFieldsError

        oper = UserOperations.get_operation_by_id(self.user_id, self.account_id, self.operation_id)

        if self.amount:
            oper.amount = self.amount
        if self.cumulative_amount:
            oper.cumulative_amount = self.cumulative_amount
        if self.operation_type:
            oper.operation_type = self.operation_type
        if self.operation_datetime:
            oper.operation_datetime = self.operation_datetime
        if self.category:
            oper.category = self.category
        if self.subcategory:
            oper.subcategory = self.subcategory
        if self.description:
            oper.description = self.description
        if self.tags:
            oper.tags = self.tags
        if self.details:
            oper.details = self.details
        return oper.save()


class DeleteAccountOperationCommand(OperationsModel):
    """
    Deletes an operation entry for a given user in a given account in the accounts_database for a given operation id
    """

    user_id: str
    account_id: str
    operation_id: str
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self) -> None:
        oper = UserOperations.get_operation_by_id(self.user_id, self.account_id, self.operation_id)
        oper.delete()
