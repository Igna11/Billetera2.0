"""
billeterapp 2.0 - Junio 2024
"""

from typing import List

from pydantic import BaseModel

from src.models.accmodel import UserAccounts


class GetAccountByIDQuery(BaseModel):

    user_id: str
    account_id: str

    def execute(self) -> UserAccounts:
        account = UserAccounts.get_account_by_id(self.user_id, self.account_id)
        return account


class GetAccountByTableNameQuery(BaseModel):

    user_id: str
    table_name: str

    def execute(self) -> UserAccounts:
        account = UserAccounts.get_account_by_table_name(self.user_id, self.table_name)
        return account


class ListAccountsQuery(BaseModel):

    user_id: str

    def execute(self, **kwargs: int | str) -> List[UserAccounts]:
        accounts = UserAccounts.get_all_accounts(self.user_id, **kwargs)
        return accounts
