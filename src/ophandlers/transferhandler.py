"""
billeterapp 2.0 - Enero 2025
Updated - Mayo 2026

Class to handle transfers between accounts
"""

from typing import Optional

from ulid import ULID
from pydantic import Field

from src.models.opmodel import Operations
from src.commands.opcommands import CreateOperationCommand, CreateAndEditOperationsCommand
from src.ophandlers.operationhandler import OperationHandler
from src.errorhandler.operationserrors import (
    SameAccountError,
    DifferentCurrencyTransferError,
)
from src.queries.opqueries import GetTransferOperationsByIDQuery


class TransferHandler(Operations):

    user_id: str
    operation_type: str = "transfer"  # type: ignore # Dummy value, will be overwritten
    transfer_id: str = Field(default_factory=lambda: "tr_" + str(ULID()))

    def set_transfer_objects(
        self,
        in_acc: str,
        out_acc: str,
        in_original_op: Optional[OperationHandler] = None,
        out_original_op: Optional[OperationHandler] = None,
        transfer_id: Optional[str] = None,
        edit_flag: bool = False,
    ):

        if in_acc == out_acc:
            raise SameAccountError

        transfer_in_params = {
            "user_id": self.user_id,
            "account_id": in_acc,
            "amount": self.amount,
            "operation_datetime": self.operation_datetime,
            "operation_type": "transfer_in",
            "category": "Transfer",
            "subcategory": "Incoming",
            "description": f"Transfer from {in_acc}",
            "transfer_id": self.transfer_id,
        }
        transfer_out_params = {
            "user_id": self.user_id,
            "account_id": out_acc,
            "amount": self.amount,
            "operation_datetime": self.operation_datetime,
            "operation_type": "transfer_out",
            "category": "Transfer",
            "subcategory": "Outcoming",
            "description": f"Transfer to {out_acc}",
            "transfer_id": self.transfer_id,
        }

        # For editing, if only transfer id is given, retrieve both operations
        if edit_flag and transfer_id:
            self.transfer_id = transfer_id
            in_original_op, out_original_op = GetTransferOperationsByIDQuery(
                user_id=self.user_id, transfer_id=self.transfer_id
            ).execute()  # type: ignore[misc, assignment]
            transfer_in_params.update({"operation_id": in_original_op.operation_id, "transfer_id": self.transfer_id})  # type: ignore[union-attr]
            transfer_out_params.update({"operation_id": out_original_op.operation_id, "transfer_id": self.transfer_id})  # type: ignore[union-attr]
        # if not, preserve the existing transfer_id and operation_ids
        elif edit_flag and in_original_op and out_original_op:
            self.transfer_id = in_original_op.transfer_id or self.transfer_id
            transfer_in_params.update({"operation_id": in_original_op.operation_id, "transfer_id": self.transfer_id})
            transfer_out_params.update({"operation_id": out_original_op.operation_id, "transfer_id": self.transfer_id})

        transfer_in = OperationHandler(**transfer_in_params)
        transfer_out = OperationHandler(**transfer_out_params)

        if transfer_in.operation_currency != transfer_out.operation_currency:
            raise DifferentCurrencyTransferError

        transfer_in.set_account_total(edit_flag, in_original_op)
        transfer_out.set_account_total(edit_flag, out_original_op)

        return transfer_in, transfer_out

    def create_transfer(
        self,
        transfer_object_in: OperationHandler,
        transfer_object_out: OperationHandler,
        edit_flag: bool = False,
    ):
        """
        Saves the new transfer into the operations table, edits the account_total column in 'accounts' table and makes
        the editions in cumulative_amount column for every operation in the operations table.
        Args:
            self: TransferOperations object
            existing_operations: List[Operations] List of every operation to be updated
        Returns:
            oper: Operations object
        """
        in_cml = transfer_object_in.set_cumulatives()
        out_cml = transfer_object_out.set_cumulatives()

        if not in_cml:
            CreateOperationCommand(**transfer_object_in.to_dict()).execute()
        else:
            CreateAndEditOperationsCommand(**transfer_object_in.to_dict()).execute(in_cml)
        # if not out_cml:
        #    CreateOperationCommand(**transfer_object_out.to_dict()).execute()
        # else:
        CreateAndEditOperationsCommand(**transfer_object_out.to_dict()).execute(out_cml)

    def save_transfer(
        self,
        transfer_object_in: OperationHandler,
        transfer_object_out: OperationHandler,
        in_original_op: OperationHandler,
        out_original_op: OperationHandler,
    ):
        """
        Saves the edited transfer and all other operations affected by the original edition
        Args:
            cls: TransferOperations
            existing_operations: List[Operations], list of every operation to be updated including the self
        Returns:
            operation: Operations object
        """
        in_cml = transfer_object_in.set_cumulatives(edit_flag=True, original_operation=in_original_op)
        out_cml = transfer_object_out.set_cumulatives(edit_flag=True, original_operation=out_original_op)

        CreateAndEditOperationsCommand(**transfer_object_in.to_dict()).execute(in_cml, edit_flag=True)
        CreateAndEditOperationsCommand(**transfer_object_out.to_dict()).execute(out_cml, edit_flag=True)
