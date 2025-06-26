"""
billeterapp 2.0 - Junio 2024

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr

from src.models.usrmodel import User
from src.models.accmodel import UserAccounts, AccountNotFoundError


class AccountAlreadyExistsError(Exception):
    pass


class CreateUsersAccountCommand(BaseModel):
    """Creates an account table with name <table_name> for a given user in the accounts_database"""

    email: EmailStr
    account_name: str
    account_currency: str

    def execute(self) -> UserAccounts:
        user = User.get_user_by_email(self.email)
        try:
            UserAccounts.get_account_by_table_name(user.user_id, f"{self.account_name}_{self.account_currency}")
            raise AccountAlreadyExistsError
        except AccountNotFoundError:
            pass
        user_account = UserAccounts(
            user_id=user.user_id, account_name=self.account_name, account_currency=self.account_currency
        )
        user_account.create_acc_table()
        return user_account


class EditUsersAccountCommand(BaseModel):
    """Edits an account table with name <table_name> for a given user in the accounts_database"""

    user_id: str
    account_id: str
    account_name: Optional[str] = None
    account_currency: Optional[str] = None
    account_total: Optional[float] = None
    is_active: Optional[bool] = None

    def execute(self) -> UserAccounts:
        user = User.get_user_by_id(self.user_id)
        user_acc = UserAccounts.get_account_by_id(user.user_id, self.account_id)

        flag = False
        if self.account_name:
            user_acc.account_name = self.account_name
            flag = True
        if self.account_currency:
            user_acc.account_currency = self.account_currency
            flag = True
        if self.account_total:
            user_acc.account_total = self.account_total
        if self.is_active is not None:
            user_acc.is_active = self.is_active
        user_acc.save(change_table_name_flag=flag)
        return user_acc


class DeleteUsersAccountCommand(BaseModel):
    """Deletes a given account from table accounts and drops the <account_name> talbe"""

    user_id: str
    account_id: str

    def execute(self) -> None:
        user = User.get_user_by_id(self.user_id)
        UserAccounts.delete_account(user.user_id, self.account_id)
