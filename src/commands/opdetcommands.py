"""
billeterapp 2.0 - Agosto 2024

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

from pydantic import BaseModel

from src.models.opdetmodel import OperationsDetails


class CreateOperationDetailCommand(BaseModel):

    user_id: str
    account_id: str
    operation_id: str
    details: bytes

    def execute(self):
        oper_details = OperationsDetails(
            user_id=self.user_id, account_id=self.account_id, operation_id=self.operation_id, details=self.details
        )
        det = oper_details.create()
        return det


class EditOperationDetailsCommand(BaseModel):

    user_id: str
    account_id: str
    operation_id: str
    details: bytes

    def execute(self):
        oper_details = OperationsDetails(
            user_id=self.user_id, account_id=self.account_id, operation_id=self.operation_id, details=self.details
        )
        det = oper_details.save()
        return det


class DeleteOperationDetailsCommand(BaseModel):

    user_id: str
    operation_id: str

    def execute(self):
        det = OperationsDetails.get_details_by_operation_id(user_id=self.user_id, operation_id=self.operation_id)
        det.delete()
