"""BilleterApp 2.0 - v2.0 Marzo 2026"""


class AccountNotFoundError(Exception):
    pass


class NoAccountsError(Exception):
    pass


class AccountAlreadyExistsError(Exception):
    pass


class InvalidAccountNameError(Exception):
    pass
