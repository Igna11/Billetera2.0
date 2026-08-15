"""
billeterapp 2.0 - Diciembre 2024

Class to handle the deletion of individual operations that are not transfers and the subsequent corrections on other
operations.
"""

from typing import List
from decimal import Decimal
from src.models.opmodel import Operations
from src.queries.accqueries import GetAccountByIDQuery
from src.queries.opqueries import ListOperationsByIdFromDatetimeQuery
from src.commands.opcommands import DeleteOperationsCommand
from src.errorhandler.operationserrors import EmptyAccountError, NegativeAccountTotalError


class DeletionHandler(Operations):

    user_id: str
    account_id: str
    amount: Decimal = Decimal(0)
    coeff: dict = {"income": 1, "expense": -1, "transfer_in": 1, "transfer_out": -1}

    def _calculate_cumulatives(self, operations_list: List[Operations], previous_amount: Decimal) -> List[Operations]:
        """
        Iterates over the list of operations order chronologically to calculate the cumulative amount
        Args:
            self: Operations object
            operations_list (list): List of operations order chronologically.
        Returns:
            operations_list (list): List of operations order chronologically after corrections.
        """
        for operation in operations_list:
            operation.cumulative_amount = previous_amount = (
                previous_amount + self.coeff[operation.operation_type] * operation.amount
            )
        return operations_list

    def set_account_total(self) -> None:
        """
        Sets the account_total value for the 'accounts' table.
        Args:
            self: Operations object
            new account_total. Defaults to None.
        """

        account = GetAccountByIDQuery(user_id=self.user_id, account_id=self.account_id).execute()
        account_total = account.account_total or Decimal("0")

        self.account_total = account_total - self.coeff[self.operation_type] * self.amount

    def set_cumulatives(self) -> List[Operations]:
        """
        Calculates and, if necessary, corrects the cumulative_amount of every operation with a posterior date to the
        self operation date. It can handle the creation of new operations the edition of existing operations with any
        given datetime.
        Args:
            self: Operations object
        Returns:
            List[Operations]: List with all involved operations to be modified and/or created.
        """
        existing_operations = ListOperationsByIdFromDatetimeQuery(
            user_id=self.user_id, account_id=self.account_id, operation_id=self.operation_id
        ).execute()

        if not existing_operations:
            raise EmptyAccountError

        # Remove the original operation from the list
        existing_operations = [oper for oper in existing_operations if oper.operation_id != self.operation_id]
        if not existing_operations:
            return [self]

        first_operation = existing_operations[0]

        # When the account has N operations and the self operation is the first of all
        if self.operation_datetime < first_operation.operation_datetime:  # type: ignore[operator]
            if first_operation.operation_type == "expense":
                raise NegativeAccountTotalError

            substracted_amount = -self.amount
            return self._calculate_cumulatives(existing_operations, substracted_amount)

        # When the account has N operations and the self operation is not the first of all Calculate the previus amount
        previous_amount = first_operation.cumulative_amount or Decimal("0")
        # remove the first operation
        existing_operations = existing_operations[1:]
        return self._calculate_cumulatives(existing_operations, previous_amount)

    def save(self, existing_operations: List[Operations]) -> List[Operations]:
        """
        Saves all the affected operations by the deletion
        Args:
            self: Operations object
            existing_operations: List[Operations], list of every operation to be updated including the self
        Returns:
            operations: List[Operations] object
        """
        return DeleteOperationsCommand(**self.to_dict()).execute(existing_operations=existing_operations)
