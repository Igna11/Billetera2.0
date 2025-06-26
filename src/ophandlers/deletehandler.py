"""
billeterapp 2.0 - Diciembre 2024

Class to handle the deletion of individual operations that are not transfers and the subsequent corrections on other
operations.
"""

from typing import List, Literal
from decimal import Decimal
from src.models.accmodel import UserAccounts
from src.models.opmodel import OperationsModel, UserOperations


class NegativeAccountTotalError(Exception):
    """Raised when an operation would result in negative account total"""


class EmptyAccountError(Exception):
    """Raised when attempting to withdraw from an empty account"""


class DeletionHandler(OperationsModel):

    user_id: str
    account_id: str
    amount: Decimal = Decimal(0)
    operation_type: Literal["income", "expense", "transfer"]
    coeff: dict = {"income": 1, "expense": -1}

    def _calculate_cumulatives(
        self, operations_list: List[OperationsModel], previus_amount: Decimal
    ) -> List[OperationsModel]:
        """
        Iterates over the list of operations order chronologically to calculate the cumulative amount
        Args:
            self: OperationsModel object
            operations_list (list): List of operations order chronologically.
        Returns:
            operations_list (list): List of operations order chronologically after corrections.
        """
        for operation in operations_list:
            operation.cumulative_amount = previus_amount = (
                previus_amount + self.coeff[operation.operation_type] * operation.amount
            )
        return operations_list

    def set_account_total(self) -> None:
        """
        Sets the account_total value for the 'accounts' table.
        Args:
            self: OperationsModel object
            new account_total. Defaults to None.
        """

        account = UserAccounts.get_account_by_id(user_id=self.user_id, account_id=self.account_id)
        account_total = account.account_total or 0

        if account_total == 0 and self.operation_type == "expense":
            raise EmptyAccountError

        self.account_total = account_total - self.coeff[self.operation_type] * self.amount

        if self.account_total < 0:
            raise NegativeAccountTotalError

    def set_cumulatives(self) -> List[OperationsModel]:
        """
        Calculates and, if necessary, corrects the cumulative_amount of every operation with a posterior date to the
        self operation date. It can handle the creation of new operations the edition of existing operations with any
        given datetime.
        Args:
            self: OperationsModel object
        Returns:
            List[OperationsModel]: List with all involved operations to be modified and/or created.
        """
        existing_operations = UserOperations.get_operations_list_from_id(
            user_id=self.user_id, account_id=self.account_id, operation_id=self.operation_id
        )

        if not existing_operations:
            raise EmptyAccountError

        # Remove the original operation from the list
        existing_operations = [oper for oper in existing_operations if oper.operation_id != self.operation_id]
        if not existing_operations:
            return [self]

        first_operation = existing_operations[0]

        # When the account has N operations and the self operation is the first of all
        if self.operation_datetime < first_operation.operation_datetime:
            if first_operation.operation_type == "expense":
                raise NegativeAccountTotalError

            substracted_amount = -self.amount
            return self._calculate_cumulatives(existing_operations, substracted_amount)

        # When the account has N operations and the self operation is not the first of all
        # Calculate the previus amount
        previus_amount = first_operation.cumulative_amount
        # remove the first operation
        existing_operations = existing_operations[1:]
        return self._calculate_cumulatives(existing_operations, previus_amount)

    def save(self, existing_operations: List[OperationsModel]) -> "OperationsModel":
        """
        Saves all the affected operations by the deletion
        Args:
            self: OperationsModel object
            existing_operations: List[OperationsModel], list of every operation to be updated including the self
        Returns:
            operation: OperationsModel object
        """
        operation = UserOperations(**self.model_dump()).delete_n_massive_save(existing_operations)
        return operation
