"""
billeterapp 2.0 - Agosto 2024
Updated - Mayo 2026

Higher order module for creation of databases, users and accounts.
It uses the models.py module.
"""

from datetime import datetime, UTC

from src.models.opdetmodel import OperationDetails
from src.dbhandlers.opdetailsdb import OperationDetailsDB
from src.errorhandler.opdetailserrors import OperationDetailsNotFoundError


class CreateOperationDetailCommand(OperationDetails):

    def execute(self) -> OperationDetails:
        self.created_at = self.updated_at = datetime.now(UTC)
        det_db = OperationDetailsDB(user_id=self.user_id)  # type: ignore[arg-type]
        det_db.create_detail(self)
        return self


class EditOperationDetailsCommand(OperationDetails):

    def execute(self) -> OperationDetails:
        self.updated_at = datetime.now(UTC)
        det_db = OperationDetailsDB(user_id=self.user_id)  # type: ignore[arg-type]
        det_db_data = det_db.get_detail_by_id(self.detail_id)

        if not det_db_data:
            raise OperationDetailsNotFoundError

        det_db.update_detail(self)
        return self


class DeleteOperationDetailsCommand(OperationDetails):

    def execute(self) -> None:
        det_db = OperationDetailsDB(user_id=self.user_id)  # type: ignore[arg-type]
        det_db_data = det_db.get_detail_by_id(self.detail_id)

        if not det_db_data:
            raise OperationDetailsNotFoundError

        det_db.delete_detail(detail_id=self.detail_id)
