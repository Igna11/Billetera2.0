"""
billeterapp 2.0 - Mayo 2026
"""

from typing import List, Optional, Literal

from src.models.opgroupsmodel import OperationGroups
from src.dbhandlers.opgroupsdb import OperationGroupsDB
from src.errorhandler.opgroupserrors import GroupNotFoundError


class GetGroupByIDQuery(OperationGroups):

    user_id: str
    group_id: str

    def execute(self) -> OperationGroups:
        group_db = OperationGroupsDB(self.user_id)
        group_data = group_db.get_group_by_id(self.group_id)
        if not group_data:
            raise GroupNotFoundError
        return OperationGroups.from_row(group_data)


class ListGroupsQuery(OperationGroups):

    user_id: str
    status: Optional[Literal["open", "closed"]] = None

    def execute(self) -> List[OperationGroups]:
        group_db = OperationGroupsDB(self.user_id)
        groups_data = group_db.get_groups_list(status=self.status)
        if not groups_data:
            raise GroupNotFoundError
        return [OperationGroups.from_row(row) for row in groups_data]
