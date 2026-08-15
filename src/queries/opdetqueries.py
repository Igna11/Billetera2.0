"""
billeterapp 2.0 - Junio 2024
Updated - Mayo 2026
"""

from typing import List

from pydantic import BaseModel

from src.models.opdetmodel import OperationDetails
from src.dbhandlers.opdetailsdb import OperationDetailsDB
from src.errorhandler.opdetailserrors import OperationDetailsNotFoundError


class GetOperationDetailByID(BaseModel):

    user_id: str
    operation_id: str

    def execute(self) -> OperationDetails:
        det_db = OperationDetailsDB(user_id=self.user_id)
        det_data = det_db.get_detail_by_operation_id(self.operation_id)
        if not det_data:
            raise OperationDetailsNotFoundError
        return OperationDetails.from_row(det_data)


class GetOperationDetailsByAccID(BaseModel):

    user_id: str
    account_id: str

    def execute(self) -> List[OperationDetails]:
        det_db = OperationDetailsDB(user_id=self.user_id)
        det_data = det_db.get_details_by_account_id(self.account_id)
        if not det_data:
            raise OperationDetailsNotFoundError
        return [OperationDetails.from_row(det) for det in det_data]
