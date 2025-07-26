"""
billeterapp 2.0 - Junio 2024
"""

import datetime
from typing import List, Optional, Sequence

from src.models.opmodel import OperationsModel, UserOperations


class GetOperationByIDQuery(OperationsModel):

    user_id: str
    account_id: str
    operation_id: str
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self) -> "UserOperations":
        operations = UserOperations.get_operation_by_id(self.user_id, self.account_id, self.operation_id)
        return operations


class GetUniqueCategoriesByAccount(OperationsModel):

    user_id: str
    account_id: str
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self) -> List:
        categories = UserOperations.get_unique_categories(self.user_id, self.account_id)
        return categories


class GetUniqueSubcategoriesByAccount(OperationsModel):

    user_id: str
    account_id: str
    category: Optional[str] = None
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self) -> List:
        subcategories = UserOperations.get_unique_subcategories(self.user_id, self.account_id, self.category)
        return subcategories


class GetLastChronologicalOperationQuery(OperationsModel):

    user_id: str
    account_id: str
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self) -> "UserOperations":
        operation = UserOperations.get_last_chronological_operation(self.user_id, self.account_id)
        return operation


class GetOperationByTagsQuery(OperationsModel):

    user_id: str
    account_id: str
    amount: Optional[float] = None
    operation_type: Optional[str] = None
    tags: Sequence

    def execute(self) -> List["UserOperations"]:
        operations = UserOperations.get_operations_list_by_tags(self.user_id, self.account_id, self.tags)
        return operations


class ListOperationsQuery(OperationsModel):

    user_id: str
    account_id: str
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self, order_by_datetime: bool = False) -> List["UserOperations"]:
        operations = UserOperations.get_operations_list(self.user_id, self.account_id, order_by_datetime)
        return operations


class ListOperationsByDatetime(OperationsModel):

    user_id: str
    account_id: str
    operation_datetime: datetime.datetime
    amount: Optional[float] = None
    operation_type: Optional[str] = None

    def execute(self) -> List["UserOperations"]:
        operations = UserOperations.get_operations_list_from_datetime(
            self.user_id, self.account_id, self.operation_datetime
        )
        return operations


class ListOperationsByIdFromDatetime(OperationsModel):

    user_id: str
    account_id: str
    operation_id: str
    amount: float = None
    operation_type: str = None

    def execute(self) -> List["UserOperations"]:
        operations = UserOperations.get_operations_list_from_id(self.user_id, self.account_id, self.operation_id)
        return operations
