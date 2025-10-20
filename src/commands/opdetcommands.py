"""
billeterapp 2.0 - Agosto 2024

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

from src.models.opdetmodel import OperationsDetails


class CreateOperationDetailCommand(OperationsDetails):

    def execute(self):
        oper_details = OperationsDetails(**self.model_dump())
        det = oper_details.create()
        return det


class EditOperationDetailsCommand(OperationsDetails):

    def execute(self):
        oper_details = OperationsDetails(**self.model_dump())
        det = oper_details.save()
        return det


class DeleteOperationDetailsCommand(OperationsDetails):

    def execute(self):
        det = OperationsDetails.get_details_by_operation_id(self.user_id, self.operation_id)
        det.delete()
