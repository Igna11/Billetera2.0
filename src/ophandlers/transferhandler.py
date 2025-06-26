"""
billeterapp 2.0 - Enero 2025

Class to handle transfers between accounts
"""

import sqlite3
from src.models.opmodel import OperationsModel, UserOperations
from src.ophandlers.operationhandler import OperationHandler


class NegativeAccountTotalError(Exception):
    """Raised when an operation would result in negative account total"""


class SameAccountError(Exception):
    """Raised when attempting to make a transfer where the in acc is the same as the out acc."""


class EmptyAccountError(Exception):
    """Raised when attempting to withdraw from an empty account"""


class DifferentCurrencyTransferError(Exception):
    """Raised when a transfer is intended to be made with two accounts of different currencies"""


class TransferHandler(OperationsModel):

    user_id: str
    operation_type: str = "transfer"  # dummy value

    def set_transfer_objects(
        self,
        in_acc: str,
        out_acc: str,
        in_original_op: OperationHandler = None,
        out_original_op: OperationHandler = None,
        edit_flag: bool = False,
    ):
        if in_acc == out_acc:
            raise SameAccountError

        if edit_flag and in_original_op and out_original_op:
            self.operation_id = in_original_op.operation_id

        transfer_in = OperationHandler(
            user_id=self.user_id,
            account_id=in_acc,
            operation_id=self.operation_id,
            amount=self.amount,
            operation_datetime=self.operation_datetime,
            operation_type="transfer_in",
            category="Transfer",
            subcategory="Incoming",
            description=f"Transfer from {in_acc}",
        )
        transfer_out = OperationHandler(
            user_id=self.user_id,
            account_id=out_acc,
            operation_id=self.operation_id,
            amount=self.amount,
            operation_datetime=self.operation_datetime,
            operation_type="transfer_out",
            category="Transfer",
            subcategory="Outcoming",
            description=f"Transfer to {out_acc}",
        )

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
        Saves the new transfer into the account table, edits the account_total column in 'accounts' table and makes the
        editions in cumulative_amount column for every operation in a given account table.
        Args:
            self: TransferOperations object
            existing_operations: List[OperationsModel] List of every operation to be updated
        Returns:
            oper: OperationsModel object
        """
        in_cml = transfer_object_in.set_cumulatives()
        out_cml = transfer_object_out.set_cumulatives()

        try:
            if not in_cml:
                UserOperations(**transfer_object_in.model_dump()).create()
            else:
                UserOperations(**transfer_object_in.model_dump()).massive_save(in_cml)
            if not out_cml:
                UserOperations(**transfer_object_out.model_dump()).create()
            else:
                UserOperations(**transfer_object_out.model_dump()).massive_save(out_cml)
        except sqlite3.Error:
            raise sqlite3.Error

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
            existing_operations: List[OperationsModel], list of every operation to be updated including the self
        Returns:
            operation: OperationsModel object
        """
        in_cml = transfer_object_in.set_cumulatives(edit_flag=True, original_operation=in_original_op)
        out_cml = transfer_object_out.set_cumulatives(edit_flag=True, original_operation=out_original_op)

        try:
            UserOperations(**transfer_object_in.model_dump()).massive_save(in_cml, edit_flag=True)
            UserOperations(**transfer_object_out.model_dump()).massive_save(out_cml, edit_flag=True)
        except sqlite3.Error:
            raise sqlite3.Error
