"""
billeterapp 2.0 - Junio 2024

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

from datetime import datetime, UTC

from src.dbhandlers.accountsdb import AccountsDB
from src.models.accmodel import Accounts
from src.errorhandler.accountserrors import AccountNotFoundError, AccountAlreadyExistsError


class CreateAccountCommand(Accounts):

    def execute(self) -> Accounts:
        self.created_at = self.updated_at = datetime.now(UTC)
        acc_db = AccountsDB(self.user_id)

        if acc_db.get_account_by_name_and_currency(self.account_name, self.account_currency):  # type: ignore[arg-type]
            raise AccountAlreadyExistsError

        return Accounts.from_row(acc_db.create_account(self))


class EditAccountCommand(Accounts):

    def execute(self) -> Accounts:
        self.updated_at = datetime.now(UTC)
        acc_db = AccountsDB(self.user_id)
        acc_db_data = acc_db.get_account_by_id(self.account_id)

        if not acc_db_data:
            raise AccountNotFoundError

        if self.account_name is None:
            self.account_name = acc_db_data["account_name"]
        if self.account_currency is None:
            self.account_currency = acc_db_data["account_currency"]
        if self.account_total is None:
            self.account_total = acc_db_data["account_total"]
        if self.tags is None:
            self.tags = acc_db_data["tags"]
        if self.is_active is None:
            self.is_active = acc_db_data["is_active"]

        self.updated_at = datetime.now(UTC)
        acc_db.update_account(self)

        return self


class DeleteAccountCommand(Accounts):

    def execute(self) -> None:
        acc_db = AccountsDB(self.user_id)
        acc_db_data = acc_db.get_account_by_id(self.account_id)

        if not acc_db_data:
            raise AccountNotFoundError

        acc_db.delete_account(account_id=self.account_id)
