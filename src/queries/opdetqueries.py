"""
billeterapp 2.0 - Junio 2024
"""

from typing import List

from pydantic import BaseModel

from src.models.opdetmodel import OperationsDetails


class GetOperationDetailByID(BaseModel):

    user_id: str
    operation_id: str

    def execute(self) -> "OperationsDetails":
        details = OperationsDetails.get_details_by_operation_id(self.user_id, self.operation_id)
        return details


class GetOperationDetailsByAccID(BaseModel):

    user_id: str
    account_id: str

    def execute(self) -> List["OperationsDetails"]:
        details = OperationsDetails.get_all_operation_details_by_account_id(self.user_id, self.account_id)
        return details
