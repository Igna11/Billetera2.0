#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created viernes 03/03/2023 
@author: igna
Modulo para condensar las funciones que tienen las cuentas GUI
create_account()
delete_account()
"""

# from src.portfolios import account_core as accounts
# from src.errors import errors


def create_account(name_acc: str = None, currency_acc: str = None) -> None:
    """
    Creates a .csv file which name will be the account name. Currencies must
    follow the ISO 4217 standard.
    """
    if name_acc.strip() == "":
        raise errors.InvalidNameError
    if currency_acc == "" or len(currency_acc) != 3:
        raise ValueError
    account = accounts.AccountsCreator(acc_name=name_acc, acc_currency=currency_acc)
    account.add_account()


def delete_account(name_acc: str = None, currency_acc: str = None, confirmation: bool = False) -> None:
    """Deletes the .csv file of the given account name"""
    if name_acc.strip() == "":
        raise errors.InvalidNameError
    if currency_acc == "":
        raise ValueError
    account = accounts.AccountsCreator(acc_name=name_acc, acc_currency=currency_acc)
    if not account.exists:
        raise errors.AccountDoesNotExistError
    if not confirmation:
        raise errors.NoConfirmationToDeleteAccountError
    account.remove_account()
