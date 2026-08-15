"""
billeterapp 2.0 - Junio 2024
"""

from typing import List

from src.models.accmodel import Accounts
from src.dbhandlers.accountsdb import AccountsDB
from src.errorhandler.accountserrors import AccountNotFoundError

from pydantic_extra_types.currency_code import ISO4217


class GetAccountByIDQuery(Accounts):

    user_id: str
    account_id: str

    def execute(self) -> Accounts:
        acc_db = AccountsDB(self.user_id)
        acc_data = acc_db.get_account_by_id(self.account_id)
        if not acc_data:
            raise AccountNotFoundError
        return Accounts.from_row(acc_data)


class GetAccountByUniqueNameQuery(Accounts):

    user_id: str
    account_name: str
    account_currency: ISO4217

    def execute(self) -> Accounts:
        acc_db = AccountsDB(self.user_id)
        acc_data = acc_db.get_account_by_name_and_currency(self.account_name, self.account_currency)
        if not acc_data:
            raise AccountNotFoundError
        return Accounts.from_row(acc_data)


class ListAccountsQuery(Accounts):

    def execute(self, **kwargs: int | str) -> List[Accounts]:
        accounts = AccountsDB(self.user_id).get_accounts_lists(**kwargs)
        return [Accounts.from_row(row) for row in accounts]
