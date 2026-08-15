class OperationsNotFoundError(Exception):
    pass


class OperationNotFoundError(Exception):
    pass


class NoEditedFieldsError(Exception):
    pass


class NoCategoriesFoundError(Exception):
    pass


class NoSubcategoriesFoundError(Exception):
    pass


class NegativeAccountTotalError(Exception):
    """Raised when an operation would result in negative account total"""

    pass


class EmptyAccountError(Exception):
    """Raised when attempting to withdraw from an empty account"""

    pass


class DifferentCurrencyTransferError(Exception):
    pass


class SameAccountError(Exception):
    pass
