"""                                                                                                                 120
billeterapp 2.0 - Agosto 2024
Mayo 2026

Class to handle the incomes into a given account
"""

from typing import List, Optional
from decimal import Decimal
from src.models.accmodel import Accounts
from src.models.opmodel import Operations
from src.commands.opcommands import CreateOperationCommand, CreateAndEditOperationsCommand
from src.queries.accqueries import GetAccountByIDQuery
from src.queries.opqueries import ListOperationsByDatetimeQuery, ListOperationsQuery
from src.errorhandler.operationserrors import EmptyAccountError, NegativeAccountTotalError


class OperationHandler(Operations):

    user_id: str
    account_id: str
    account: Optional[Accounts] = None
    coeff: dict = {"income": 1, "expense": -1, "transfer_in": 1, "transfer_out": -1}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account = GetAccountByIDQuery(user_id=self.user_id, account_id=self.account_id).execute()
        self.operation_currency = self.account.account_currency

    def readjustment(self, account_total: Decimal) -> List:
        """
        Calculates the values for the amount y cumulative amount when a readjustment is required.
        Args:
            account_total (Decimal): The required account_total
        Returns:
            [] (List): An empty list to be passed to create_operations method.
        """
        amount = account_total - self.account.account_total  # type: ignore[operator, union-attr]
        self.account.account_total = self.account_total = account_total  # type: ignore[union-attr]
        self.cumulative_amount = account_total
        if amount < 0:
            self.amount = abs(amount)
            self.operation_type = "expense"
            self.tags = "Readjustment,Negative"
        elif amount == 0:
            pass
        elif amount > 0:
            self.amount = amount
            self.operation_type = "income"
            self.tags = "Readjustment,Positive"
        return []

    def _calculate_cumulatives(
        self,
        operations_list: List[Operations],
        previous_amount: Decimal,
        edit_flag=False,
    ) -> List[Operations]:
        """
        Iterates over the list of operations chronologically to calculate the cumulative amount
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
        if edit_flag:
            operations_list.append(self)
        return operations_list

    def _handle_new_operation(self) -> List[Operations]:
        """
        Handles all possible cases for creation of operations and manages the impact on the rest of the operations.
        """
        existing_operations = ListOperationsByDatetimeQuery(
            user_id=self.user_id, account_id=self.account_id, operation_datetime=self.operation_datetime  # type: ignore[arg-type]
        ).execute()
        if not existing_operations:
            self.cumulative_amount = self.amount
            return []

        first_operation = existing_operations[0]
        # new operation datetime is OLDER than the oldest operation saved in database (first operation)
        if self.operation_datetime < first_operation.operation_datetime:  # type: ignore[operator]
            if self.operation_type == "expense":
                raise NegativeAccountTotalError

            self.cumulative_amount = self.amount

            return self._calculate_cumulatives(existing_operations, self.amount)

        # New operation with exact same datetime than an existing operation
        if self.operation_datetime == first_operation.operation_datetime:  # type: ignore[operator]
            self.cumulative_amount = first_operation.cumulative_amount + self.coeff[self.operation_type] * self.amount
            existing_operations = existing_operations[1:]

            return self._calculate_cumulatives(existing_operations, self.cumulative_amount)

        # New operation in the middle of other operations:
        if first_operation.operation_datetime < self.operation_datetime and len(existing_operations) > 1:  # type: ignore[operator]
            self.cumulative_amount = first_operation.cumulative_amount + self.coeff[self.operation_type] * self.amount
            # Removes the operation before the interest operation
            existing_operations = existing_operations[1:]

            return self._calculate_cumulatives(existing_operations, self.cumulative_amount)

        # New operation datetime is NEWER than the last operation
        if first_operation.operation_datetime < self.operation_datetime and len(existing_operations) == 1:  # type: ignore[operator]
            self.cumulative_amount = first_operation.cumulative_amount + self.coeff[self.operation_type] * self.amount
            return existing_operations

        return []

    def _handle_edited_operation(self, original_operation: Operations) -> List[Operations]:
        """
        Handles all possible cases of editions in an operation and manages the impact on the rest of the operations.
        """
        # In case of editing the datetime on top of everything else of a given operation
        older_datetime = min(self.operation_datetime, original_operation.operation_datetime)  # type: ignore[type-var]
        existing_operations = ListOperationsByDatetimeQuery(
            user_id=self.user_id, account_id=self.account_id, operation_datetime=older_datetime  # type: ignore[arg-type]
        ).execute()
        # Remove the original operation from the list
        existing_operations = [oper for oper in existing_operations if oper.operation_id != self.operation_id]

        if not existing_operations:
            self.cumulative_amount = (
                original_operation.cumulative_amount
                - self.coeff[original_operation.operation_type] * original_operation.amount
                + self.coeff[self.operation_type] * self.amount
            )
            return [self]

        first_operation = existing_operations[0]

        # when the edited datetime is older than the original
        if self.operation_datetime < original_operation.operation_datetime:  # type: ignore[operator]
            if self.operation_datetime < first_operation.operation_datetime:  # type: ignore[operator]
                self.cumulative_amount = self.coeff[self.operation_type] * self.amount
                return self._calculate_cumulatives(existing_operations, self.cumulative_amount, edit_flag=True)

            self.cumulative_amount = first_operation.cumulative_amount + self.coeff[self.operation_type] * self.amount
            existing_operations = existing_operations[1:]
            return self._calculate_cumulatives(existing_operations, self.cumulative_amount, edit_flag=True)

        # when the edited datetime is newer than the original
        if self.operation_datetime >= original_operation.operation_datetime:  # type: ignore[operator]
            # Insert the edited operation in the correct place
            insert_index = 0
            for i, oper in enumerate(existing_operations):
                if self.operation_datetime < oper.operation_datetime:  # type: ignore[operator]
                    insert_index = i
                    break
            else:
                insert_index = len(existing_operations)

            # Insert the edited operation into the list
            existing_operations.insert(insert_index, self)

            # Original operation was the first operation or the order of the operations didn't change
            if original_operation.operation_datetime < first_operation.operation_datetime:  # type: ignore[operator]
                # the new date is newer than the original but not newer than the the first operation
                if self.operation_datetime < first_operation.operation_datetime:  # type: ignore[operator]
                    all_operations_len = len(
                        ListOperationsQuery(user_id=self.user_id).execute(account_id=self.account_id)
                    )
                    # Original operation was the first operation of all
                    if all_operations_len == len(existing_operations):
                        return self._calculate_cumulatives(existing_operations, Decimal("0"), edit_flag=True)
                    # Original operation is in the middle and the new date is newer but does'n produce order changes
                    self.cumulative_amount += (
                        self.coeff[self.operation_type] * self.amount
                        - self.coeff[original_operation.operation_type] * original_operation.amount
                    )
                    existing_operations = existing_operations[1:]
                    return self._calculate_cumulatives(existing_operations, self.cumulative_amount, edit_flag=True)
                # the new date is newer than the original and newer than the first operation
                if self.operation_datetime > first_operation.operation_datetime:  # type: ignore[operator]
                    previous_amount = (
                        original_operation.cumulative_amount
                        - self.coeff[original_operation.operation_type] * original_operation.amount
                    )
                    return self._calculate_cumulatives(existing_operations, previous_amount, edit_flag=True)

            elif original_operation.operation_datetime > first_operation.operation_datetime:  # type: ignore[operator]
                # SCENARIO NOT COVERED BY TESTS => Is this a plausible scenario?
                second_operation = existing_operations[1]
                second_operation.cumulative_amount = (
                    first_operation.cumulative_amount
                    + self.coeff[second_operation.operation_type] * second_operation.amount
                )
                return self._calculate_cumulatives(
                    existing_operations, second_operation.cumulative_amount, edit_flag=True
                )

        return []

    def set_account_total(self, edit_flag: bool = False, original_operation: Optional[Operations] = None) -> None:
        """
        Sets the account_total value for the 'accounts' table.
        Args:
            self: Operations object
            edit_flag (bool, optional): Flag to indicate if the operation is an edit. Defaults to False.
            original_operation (Operations, optional): Original operation prior to edition. Used to calculate the
            new account_total. Defaults to None.
        """
        account_total = self.account.account_total or Decimal("0")  # type: ignore[union-attr]

        if account_total == 0 and self.operation_type == "expense" and not edit_flag:
            raise EmptyAccountError

        if edit_flag and original_operation:
            self.account_total = (
                account_total
                - self.coeff[original_operation.operation_type] * original_operation.amount
                + self.coeff[self.operation_type] * self.amount
            )
        else:
            self.account_total = account_total + self.coeff[self.operation_type] * self.amount

    def set_cumulatives(self, edit_flag=False, original_operation: Optional[Operations] = None) -> List[Operations]:
        """
        Calculates and, if necessary, corrects the cumulative_amount of every operation with a posterior date to the
        self operation date. It can handle the creation of new operations the edition of existing operations with any
        given datetime.
        Args:
            self: Operations object
            edit_flag (bool, optional): Flag to indicate if the operation is an edit. Defaults to False.
            original_operation (Operations, optional): Original operation prior to edition. Defaults to None.
        Returns:
            List[Operations]: List with all involved operations to be modified and/or created.
        """
        if not edit_flag:
            return self._handle_new_operation()

        if edit_flag and original_operation:
            return self._handle_edited_operation(original_operation)
        return []

    def create_operations(self, existing_operations: Optional[List[Operations]] = None) -> Operations:
        """
        Saves the new income into the database, edits the account_total column in 'accounts' table and makes the
        editions in cumulative_amount column for every operation in the operations table.
        Args:
            self: Operations object
            existing_operations: List[Operations] List of every operation to be updated
        Returns:
            oper: Operations object
        """
        if not existing_operations:
            operation = CreateOperationCommand(**self.to_dict()).execute()
            return operation

        return CreateAndEditOperationsCommand(**self.to_dict()).execute(existing_operations)

    def save(self, existing_operations: List[Operations]) -> Operations:
        """
        Saves the edited operation and all other operations affected by the original edition
        Args:
            self: Operations object
            existing_operations: List[Operations], list of every operation to be updated including the self
        Returns:
            operation: Operations object
        """
        return CreateAndEditOperationsCommand(**self.to_dict()).execute(
            existing_operations=existing_operations, edit_flag=True
        )
