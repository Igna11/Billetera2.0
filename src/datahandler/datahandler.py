"""
billeterapp 2.0 - Junio 2025                                                                                        120

This module handles the data stored in the operation tables.
"""

from decimal import Decimal
from datetime import datetime
from calendar import monthrange
from collections import defaultdict
from typing import List, Dict, Literal, ClassVar, Optional

from src.models.opmodel import Operations

from src.queries.accqueries import ListAccountsQuery
from src.queries.opqueries import ListOperationsQuery, GetOperationsForNetAnalysisQuery

from pydantic import BaseModel


class AccountDataAnalyzer(BaseModel):

    user_id: str
    coeff: ClassVar[dict] = {"income": 1, "expense": -1, "transfer_in": 0, "transfer_out": 0}

    def get_all_operations(self, **kwargs) -> List[Operations]:
        return ListOperationsQuery(user_id=self.user_id).execute(order="DESC", **kwargs)

    @classmethod
    def get_user_totals(cls, user_id: str, **kwargs) -> Dict[str, Decimal]:
        """Calculates the total balance across all accounts for each currency"""
        accounts_list = ListAccountsQuery(user_id=user_id).execute(**kwargs)
        if not accounts_list:
            return {"_": Decimal("0")}
        totals: Dict[str, Decimal] = {}
        for account in accounts_list:
            currency = account.account_currency if account.account_currency else "_"
            total = account.account_total if account.account_total is not None else Decimal("0")

            if currency not in totals:
                totals[currency] = Decimal("0")

            totals[currency] += total

        return totals

    @classmethod
    def get_user_totals_by_period(
        cls,
        user_id: str,
        from_dt: datetime,
        to_dt: datetime,
        operation_type: str,
        currency: str,
        is_active: bool = True,
    ) -> Decimal:
        filtered_operations = ListOperationsQuery(user_id=user_id).execute(
            from_dt=from_dt,
            to_dt=to_dt,
            operation_type=operation_type,
            currency=currency,
            is_active=is_active,
        )
        return Decimal(sum([oper.amount for oper in filtered_operations]))

    @classmethod
    def get_user_flow_totals_by_category(
        cls,
        user_id: str,
        from_dt: datetime,
        to_dt: datetime,
        data_type: str,
        currency: str,
        operation_type: Optional[Literal["income", "expense"]],
        is_active: bool,
    ) -> List[Dict]:
        """
        Gathers all operations for accounts with the same currency in a given period of time
        and groups them by category or by category and subcategory adding their amounts.
        This method does not discriminate for group of operations.
        Args:
            user_id (str): The unique identifier for the user
            from_dt (datetime): initial datetime
            to_dt (datetime): final datetime
            data_type (str): 'category'/'subcategory'
            currency (str): currency filter to avoid mixing currencies
            operation_type (Optional[Literal["income", "expense"]]): 'income'/'expense' or None for both
            is_active (bool): filter for active accounts
        Returns:
             category_data (List[Dict]): e.g.: [{'category': <category_name>, 'total': total}, ...]
             subcategory_data (List[Dict]):
                e.g.: [{'category': <category_name>, 'subcategory': <subcat_name>, 'total': total}, ...]
        """
        operations = ListOperationsQuery(user_id=user_id).execute(
            from_dt=from_dt,
            to_dt=to_dt,
            currency=currency,
            operation_type=operation_type,
            is_active=is_active,
        )
        # Grouping
        if data_type == "category":
            return AccountDataAnalyzer._group_categories(operations, operation_type)
        elif data_type == "subcategory":
            return AccountDataAnalyzer._group_subcategories(operations, operation_type)
        return []

    @classmethod
    def get_user_net_totals_by_category(
        cls,
        user_id: str,
        from_dt: datetime,
        to_dt: datetime,
        currency: str,
        data_type: str,
        operation_type: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> List[Dict]:
        """
        Gathers all operations for accounts with the same currency in a given period of time
        and groups them by category or by category and subcategory adding their amounts.
        This method does discriminate for group of operations: operations belonging to any group will be grouped and
        all their values will be summed in order to determine if its total is a net income or a net expense.
        Args:
            user_id (str): The unique identifier for the user
            from_dt (datetime): initial datetime
            to_dt (datetime): final datetime
            currency (str): currency filter to avoid mixing currencies
            data_type (str): 'category'/'subcategory'
            operation_type (str): 'income'/'expense' or None for both
        Returns:
             category_data (List[Dict]): e.g.: [{'category': <category_name>, 'total': total}, ...]
             subcategory_data (List[Dict]):
                e.g.: [{'category': <category_name>, 'subcategory': <subcat_name>, 'total': total}, ...]
        """
        operations = GetOperationsForNetAnalysisQuery(user_id=user_id).execute(
            from_dt=from_dt,
            to_dt=to_dt,
            currency=currency,
            is_active=is_active,
        )
        # Grouping
        if data_type == "category":
            return AccountDataAnalyzer._group_categories(operations, operation_type)
        elif data_type == "subcategory":
            return AccountDataAnalyzer._group_subcategories(operations, operation_type)
        return []

    @staticmethod
    def _sanitize_negative_values(results: List[Dict]) -> List[Dict]:
        """
        Sanitizes the results by:
        1. Setting operation_type based on total sign (positive=income, negative=expense)
        2. Converting total to absolute value
        3. Removing entries with total of 0

        Args:
            results: List of dictionaries with 'total' key

        Returns:
            Sanitized list of dictionaries
        """
        sanitized = []
        for item in results:
            total = item["total"]
            if total == 0:
                continue  # Skip items with total of 0

            # Determine operation_type based on sign
            operation_type = "income" if total > 0 else "expense"

            # Create new item with sanitized values
            sanitized_item = item.copy()
            sanitized_item["operation_type"] = operation_type
            sanitized_item["total"] = abs(total)
            sanitized.append(sanitized_item)

        return sanitized

    @staticmethod
    def _group_categories(operations: list[Operations], operation_type: Optional[str]) -> List[Dict]:
        coeff = {"income": 1, "expense": -1, "transfer_in": 0, "transfer_out": 0}
        totals_by_category: defaultdict[str, Decimal] = defaultdict(Decimal)
        for oper in operations:
            category = oper.category or ""
            if not operation_type:  # incomes and expenses
                totals_by_category[category] += oper.amount * coeff[oper.operation_type]
            elif oper.operation_type == operation_type == "income":
                totals_by_category[category] += oper.amount
            elif oper.operation_type == operation_type == "expense":
                totals_by_category[category] += oper.amount

        result = [
            {
                "category": cat,
                "total": Decimal(total),
            }
            for cat, total in sorted(totals_by_category.items())
        ]

        return result

    @staticmethod
    def _group_subcategories(operations: list[Operations], operation_type: Optional[str]) -> List[Dict]:
        coeff = {"income": 1, "expense": -1, "transfer_in": 0, "transfer_out": 0}
        totals_by_subcategory: defaultdict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for oper in operations:
            category = oper.category or ""
            subcategory = oper.subcategory or ""
            key = (category, subcategory)
            if not operation_type:  # incomes and expenses
                totals_by_subcategory[key] += oper.amount * coeff[oper.operation_type]
            elif oper.operation_type == operation_type == "income":
                totals_by_subcategory[key] += oper.amount
            elif oper.operation_type == operation_type == "expense":
                totals_by_subcategory[key] += oper.amount

        result = [
            {
                "category": category,
                "subcategory": subcategory,
                "total": Decimal(total),
            }
            for (category, subcategory), total in sorted(
                totals_by_subcategory.items(),
            )
        ]
        return result

    @classmethod
    def get_daily_totals(
        cls,
        user_id: str,
        from_dt: datetime,
        to_dt: datetime,
        currency: str,
        is_active: bool = True,
        account_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Gets daily income and expense totals for a specific time period.

        This method handles both:
        - Monthly periods (day numbers 1-31)
        - Custom time ranges spanning multiple months (using date strings for day labels)

        Args:
            user_id: User identifier
            from_dt: Start datetime for the period
            to_dt: End datetime for the period
            currency: Currency filter to avoid mixing currencies
            is_active: Filter for active accounts
            account_ids: Optional list of account IDs to filter by (if None, includes all accounts)

        Returns:
            List of dictionaries with keys 'day', 'income', 'expense'
            For monthly periods: day is an integer (1-31)
            For custom ranges: day is a date string (YYYY-MM-DD)
            e.g., [{'day': 1, 'income': 100.0, 'expense': 50.0}, ...]
                 or [{'day': '2026-08-01', 'income': 100.0, 'expense': 50.0}, ...]
        """
        # Get all operations for the time period
        operations = ListOperationsQuery(user_id=user_id).execute(
            from_dt=from_dt, to_dt=to_dt, currency=currency, is_active=is_active, accounts=account_ids, order="ASC"
        )

        # Check if this is a single month period
        is_single_month = (
            from_dt.year == to_dt.year
            and from_dt.month == to_dt.month
            and from_dt.day == 1
            and to_dt.day == monthrange(to_dt.year, to_dt.month)[1]
        )

        # Group by day and sum income/expenses
        if is_single_month:
            # Use integer day numbers for single month
            daily_totals = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

            for oper in operations:
                day = oper.operation_datetime.day
                if oper.operation_type == "income":
                    daily_totals[day]["income"] += oper.amount
                elif oper.operation_type == "expense":
                    daily_totals[day]["expense"] += oper.amount

            # Convert to list of dictionaries sorted by day
            result = [
                {
                    "day": day,
                    "income": totals["income"],
                    "expense": totals["expense"],
                }
                for day, totals in sorted(daily_totals.items())
            ]
        else:
            # Use date strings for custom ranges spanning multiple months
            daily_totals = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})

            for oper in operations:
                date_str = oper.operation_datetime.strftime("%Y-%m-%d")
                if oper.operation_type == "income":
                    daily_totals[date_str]["income"] += oper.amount
                elif oper.operation_type == "expense":
                    daily_totals[date_str]["expense"] += oper.amount

            # Convert to list of dictionaries sorted by date
            result = [
                {
                    "day": date_str,
                    "income": totals["income"],
                    "expense": totals["expense"],
                }
                for date_str, totals in sorted(daily_totals.items())
            ]
        return result

    @classmethod
    def get_cumulative_points(
        cls,
        user_id: str,
        from_dt: datetime,
        to_dt: datetime,
        currency: str,
        is_active: bool = True,
        account_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Gets individual cumulative points from operations for specific accounts.

        This method returns individual operation data with cumulative amounts and timestamps,
        which can be plotted as points on a line chart to show balance progression.

        Args:
            user_id: User identifier
            from_dt: Start datetime for the period
            to_dt: End datetime for the period
            currency: Currency filter to avoid mixing currencies
            is_active: Filter for active accounts
            account_ids: List of account IDs to filter by (if None, includes all accounts)

        Returns:
            List of dictionaries with keys 'datetime', 'cumulative', 'account_name'
            e.g., [{'datetime': datetime(2026, 8, 1, 10, 30), 'cumulative': 500.0, 'account_name': 'Savings'}, ...]
        """
        # Get all operations for the time period
        operations = ListOperationsQuery(user_id=user_id).execute(
            from_dt=from_dt, to_dt=to_dt, currency=currency, is_active=is_active, accounts=account_ids, order="ASC"
        )

        # Extract cumulative points from operations
        result = []
        for oper in operations:
            if oper.cumulative_amount is not None:
                result.append(
                    {
                        "datetime": oper.operation_datetime,
                        "cumulative": oper.cumulative_amount,
                        "account_name": oper.account_name,
                    }
                )

        return result
