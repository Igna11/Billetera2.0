"""
billeterapp 2.0 - Junio 2024
Updated - Mayo 2026
"""

from datetime import datetime
from typing import List, Optional

from src.models.opmodel import Operations
from src.dbhandlers.operationsdb import OperationsDB
from src.errorhandler.operationserrors import (
    OperationNotFoundError,
    OperationsNotFoundError,
    NoCategoriesFoundError,
    NoSubcategoriesFoundError,
)


class GetOperationByIDQuery(Operations):

    user_id: str
    operation_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> Operations:
        op_db = OperationsDB(user_id=self.user_id)
        op_data = op_db.get_operation_by_id(self.operation_id)
        if not op_data:
            raise OperationNotFoundError
        print(dict(op_data))
        operation = Operations.from_row(op_data)
        operation.user_id = self.user_id

        return operation


class GetTransferOperationsByIDQuery(Operations):

    user_id: str
    transfer_id: str
    operation_id: Optional[str] = None  # type: ignore[assignment]
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> List[Operations]:
        tr_db = OperationsDB(user_id=self.user_id)
        tr_data = tr_db.get_transfer_operations_by_id(self.transfer_id)
        if not tr_data:
            raise OperationsNotFoundError
        operation_list = [Operations.from_row(oper) for oper in tr_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list


class GetUniqueCategoriesQuery(Operations):

    user_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> List:
        op_db = OperationsDB(user_id=self.user_id)
        cat_data = op_db.get_unique_categories()
        if not cat_data:
            raise NoCategoriesFoundError
        return [row[0] for row in cat_data]


class GetUniqueSubcategoriesQuery(Operations):

    user_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    category: Optional[str] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> List:
        op_db = OperationsDB(user_id=self.user_id)
        subcat_data = op_db.get_unique_subcategories(self.category)
        if not subcat_data:
            raise NoSubcategoriesFoundError
        return [row[0] for row in subcat_data]


class GetOperationByTagsQuery(Operations):

    user_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self, tags: tuple[str, ...]) -> List[Operations]:
        op_db = OperationsDB(user_id=self.user_id)
        ops_data = op_db.get_all_operations(tags=tags)
        if not ops_data:
            raise OperationsNotFoundError
        operation_list = [Operations.from_row(oper) for oper in ops_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list


class GetOperationByCategoryQuery(Operations):

    user_id: str
    account_id: Optional[str] = None  # type: ignore[assignment]
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self, category: str, subcategory: Optional[str] = None) -> List[Operations]:
        op_db = OperationsDB(user_id=self.user_id)
        ops_data = op_db.get_all_operations(account_id=self.account_id, category=category, subcategory=subcategory)  # type: ignore[arg-type]
        if not ops_data:
            raise OperationsNotFoundError
        operation_list = [Operations.from_row(oper) for oper in ops_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list


class ListOperationsQuery(Operations):

    user_id: str
    account_id: Optional[str] = None  # type: ignore[assignment]
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self, account_id: Optional[str] = None, **kwargs) -> List[Operations]:
        """
        kwargs:
            - category: Matches exact string,
            - subcategory: Matches exact string,
            - description: Matches a for likeness,
            - tags: Matches exact strings of tags,
            - order: set out order by datetime - allowd vals: 'ASC' or 'DESC',
        """
        op_db = OperationsDB(user_id=self.user_id)
        ops_data = op_db.get_all_operations(account_id, **kwargs)
        operation_list = [Operations.from_row(oper) for oper in ops_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list


class ListOperationsByDatetimeQuery(Operations):

    user_id: str
    account_id: str
    operation_datetime: datetime
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> List[Operations]:
        op_db = OperationsDB(user_id=self.user_id)
        ops_data = op_db.get_operations_list_from_datetime(self.account_id, self.operation_datetime)
        operation_list = [Operations.from_row(oper) for oper in ops_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list


class ListOperationsByIdFromDatetimeQuery(Operations):

    user_id: str
    account_id: str
    operation_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    operation_type: Optional[str] = None  # type: ignore[assignment]

    def execute(self) -> List[Operations]:
        op_db = OperationsDB(user_id=self.user_id)
        ops_data = op_db.get_operations_list_from_id(self.account_id, self.operation_id)
        if not ops_data:
            raise OperationsNotFoundError
        operation_list = [Operations.from_row(oper) for oper in ops_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list


class GetOperationsForNetAnalysisQuery(Operations):

    user_id: str
    operation_type: Optional[str] = None  # type: ignore[assignment]
    amount: Optional[float] = None  # type: ignore[assignment]

    def execute(self, from_dt: datetime, to_dt: datetime, currency: str, is_active: Optional[bool] = True) -> List:
        op_db = OperationsDB(user_id=self.user_id)
        ops_data = op_db.get_operations_for_net_analysis(
            from_dt=from_dt,
            to_dt=to_dt,
            currency=currency,
            is_active=is_active,
        )
        operation_list = [Operations.from_row(row) for row in ops_data]
        for operation in operation_list:
            operation.user_id = self.user_id
        return operation_list
