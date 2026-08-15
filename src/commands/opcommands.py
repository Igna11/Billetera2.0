"""
billeterapp 2.0 - Junio 2024
updated - Mayo 2026
"""

from typing import List
from datetime import datetime, UTC
from typing import Optional, Literal

from src.models.opmodel import Operations
from src.dbhandlers.operationsdb import OperationsDB


class CreateOperationCommand(Operations):

    account_id: str
    amount: float  # type: ignore[assignment]
    cumulative_amount: float  # type: ignore[assignment]

    def execute(self) -> Operations:
        self.created_at = self.updated_at = datetime.now(UTC)
        oper_db = OperationsDB(self.user_id)  # type: ignore[arg-type]
        oper_row = oper_db.create_operation(self)
        return Operations.from_row(oper_row)


class CreateAndEditOperationsCommand(Operations):
    """Edits an account entry for a given user in a given account in the accounts_database for a given operation id"""

    account_id: str
    operation_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    cumulative_amount: Optional[float] = None  # type: ignore[assignment]
    operation_datetime: Optional[datetime] = None  # type: ignore[assignment]
    operation_type: Optional[Literal["income", "expense", "transfer_in", "transfer_out"]] = None  # type: ignore[assignment]

    def execute(self, existing_operations: list, edit_flag: bool = False) -> Operations:
        self.created_at = self.updated_at = datetime.now(UTC)
        for oper in existing_operations:
            oper.updated_at = self.updated_at

        oper_db = OperationsDB(self.user_id)  # type: ignore[arg-type]
        oper_row = oper_db.update_several_operations(self, existing_operations, edit_flag)
        return Operations.from_row(oper_row)


class DeleteOperationsCommand(Operations):
    """
    Deletes the self operation and edits all other affected operations for a given user in a given acount in a given
    account in the accounts_database for a given operation id
    """

    account_id: str
    operation_id: str
    amount: Optional[float] = None  # type: ignore[assignment]
    cumulative_amount: Optional[float] = None  # type: ignore[assignment]
    operation_datetime: Optional[datetime] = None  # type: ignore[assignment]
    operation_type: Optional[Literal["income", "expense", "transfer_in", "transfer_out"]] = None  # type: ignore[assignment]

    def execute(self, existing_operations: list) -> List[Operations]:
        self.updated_at = datetime.now(UTC)
        for oper in existing_operations:
            oper.updated_at = self.updated_at

        oper_db = OperationsDB(self.user_id)  # type: ignore[arg-type]
        oper_db.delete_operation(self, existing_operations)
        return existing_operations
