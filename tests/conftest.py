"""
Shared fixtures for UI testing using pytest-qt.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from decimal import Decimal

import pytest
from PyQt5.QtWidgets import QApplication, QStackedWidget

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def qapp():
    """
    Create QApplication instance for the entire test session.
    This is required for all PyQt5 widgets.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def stacked_widget(qapp):
    """
    Create a QStackedWidget instance for testing screens.
    """
    widget = QStackedWidget()
    yield widget
    widget.close()


@pytest.fixture
def temp_data_dir():
    """
    Create a temporary directory for test databases.
    This prevents test data from interfering with real user data.
    """
    temp_dir = tempfile.mkdtemp()

    # Create test data directory structure
    test_data_dir = os.path.join(temp_dir, "data")
    os.makedirs(test_data_dir, exist_ok=True)

    # Mock the DATAPATH before any imports that use it
    import src

    original_datapath = src.DATAPATH
    src.DATAPATH = test_data_dir

    # Patch DATAPATH comprehensively across all modules that actually use it
    # We need to patch it before any database operations occur
    modules_to_patch = [
        "src",
        "src.dbhandlers.accountsdb",
        "src.dbhandlers.operationsdb",
        "src.dbhandlers.usersdb",
        "src.dbhandlers.opgroupsdb",
        "src.dbhandlers.opdetailsdb",
        "src.dbtables.accountstable",
        "src.dbtables.operationstable",
        "src.dbtables.userstable",
        "src.dbtables.groupstable",
        "src.dbtables.detailstable",
    ]

    patches = []
    for module in modules_to_patch:
        try:
            # Import the module first to ensure it exists
            __import__(module)
            # Then try to patch it
            patches.append(patch(module + ".DATAPATH", test_data_dir))
        except (ImportError, AttributeError):
            pass  # Module might not exist or not have DATAPATH

    # Start all patches
    for p in patches:
        p.start()

    try:
        # Create main users database in the temp directory
        from src.dbtables.userstable import initialize_users_table

        initialize_users_table()

        yield temp_dir
    finally:
        # Stop all patches
        for p in patches:
            p.stop()

        # Restore original DATAPATH
        src.DATAPATH = original_datapath

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_user(temp_data_dir):
    """
    Create a mock user for testing authentication flows.
    """
    from src.models.usersmodel import Users
    from src.dbhandlers.usersdb import UsersDB
    from src.dbtables.accountstable import initialize_accounts_table
    from src.dbtables.operationstable import initialize_operations_table
    from src.dbtables.groupstable import initialize_groups_table
    from src.dbtables.detailstable import initialize_details_table

    user_db = UsersDB()

    # Create test user with correct field names
    test_user = Users(first_name="Test", last_name="User", email="test@example.com")

    try:
        hashed_password = "hashed_password"  # No need to actually hash the password
        user_db.create_user(test_user, hashed_password=hashed_password)

        # Create user directory and initialize databases
        user_dir = os.path.join(temp_data_dir, "data", test_user.user_id)
        os.makedirs(user_dir, exist_ok=True)

        # Initialize user-specific database tables
        initialize_accounts_table(user_id=test_user.user_id)
        initialize_operations_table(user_id=test_user.user_id)
        initialize_groups_table(user_id=test_user.user_id)
        initialize_details_table(user_id=test_user.user_id)

        yield test_user
    except Exception as e:
        # User might already exist, just yield the model
        print(f"Warning: User creation failed: {e}")
        yield test_user
    finally:
        # Cleanup test user
        try:
            user_db.delete_user(test_user.user_id)
        except Exception:
            pass


@pytest.fixture
def mock_account(temp_data_dir, mock_user):
    """
    Create a mock account for testing account-related screens.
    """
    from src.models.accmodel import Accounts
    from src.dbhandlers.accountsdb import AccountsDB

    # The AccountsDB will use the patched DATAPATH, so we need to ensure the directory exists
    user_dir = os.path.join(temp_data_dir, "data", mock_user.user_id)
    os.makedirs(user_dir, exist_ok=True)

    acc_db = AccountsDB(user_id=mock_user.user_id)

    # Create test account with correct field names
    test_account = Accounts(
        user_id=mock_user.user_id, account_name="TestAccount", account_currency="ARS", account_total=Decimal("1000.00")
    )

    try:
        acc_db.create_account(test_account)
        yield test_account
    except Exception as e:
        # Account might already exist, just yield the model
        print(f"Warning: Account creation failed: {e}")
        yield test_account
    finally:
        # Cleanup test account
        try:
            acc_db.delete_account(test_account.account_id)
        except Exception:
            pass


@pytest.fixture
def mock_operations(temp_data_dir, mock_user, mock_account):
    """
    Create mock operations for testing operation-related screens.
    """
    from src.models.opmodel import Operations
    from src.dbhandlers.operationsdb import OperationsDB
    from datetime import datetime

    # Ensure the user directory exists
    user_dir = os.path.join(temp_data_dir, "data", mock_user.user_id)
    os.makedirs(user_dir, exist_ok=True)

    op_db = OperationsDB(user_id=mock_user.user_id)

    # Create test operations with correct field names
    test_operations = [
        Operations(
            user_id=mock_user.user_id,
            account_id=mock_account.account_id,
            operation_type="expense",
            category="Food",
            subcategory="Restaurant",
            amount=Decimal("50.00"),
            operation_datetime=datetime.now(),
        ),
        Operations(
            user_id=mock_user.user_id,
            account_id=mock_account.account_id,
            operation_type="income",
            category="Salary",
            subcategory="Monthly",
            amount=Decimal("2000.00"),
            operation_datetime=datetime.now(),
        ),
    ]

    created_ops = []
    try:
        for op in test_operations:
            created_op = op_db.create_operation(op)
            created_ops.append(created_op)
        yield created_ops
    except Exception as e:
        print(f"Warning: Operations creation failed: {e}")
        yield []
    finally:
        # Cleanup test operations
        try:
            for op in created_ops:
                op_db.delete_operation(op.operation_id)
        except Exception:
            pass


@pytest.fixture
def mock_operations_with_tags_and_groups(temp_data_dir, mock_user, mock_account, mock_group):
    """
    Create mock operations with tags and groups for testing filter functionality.
    """
    from src.models.opmodel import Operations
    from src.dbhandlers.operationsdb import OperationsDB
    from datetime import datetime

    # Ensure the user directory exists
    user_dir = os.path.join(temp_data_dir, "data", mock_user.user_id)
    os.makedirs(user_dir, exist_ok=True)

    op_db = OperationsDB(user_id=mock_user.user_id)

    # Get group_id if mock_group exists, otherwise None
    group_id = mock_group.group_id if mock_group else None

    # Create test operations with tags and groups
    test_operations = [
        Operations(
            user_id=mock_user.user_id,
            account_id=mock_account.account_id,
            operation_type="expense",
            category="Food",
            subcategory="Restaurant",
            amount=Decimal("50.00"),
            operation_datetime=datetime.now(),
            tags=("dinner", "weekend"),
            group_id=group_id,
        ),
        Operations(
            user_id=mock_user.user_id,
            account_id=mock_account.account_id,
            operation_type="expense",
            category="Transport",
            subcategory="Uber",
            amount=Decimal("25.00"),
            operation_datetime=datetime.now(),
            tags=("work",),
            group_id=group_id,
        ),
        Operations(
            user_id=mock_user.user_id,
            account_id=mock_account.account_id,
            operation_type="income",
            category="Salary",
            subcategory="Monthly",
            amount=Decimal("2000.00"),
            operation_datetime=datetime.now(),
            tags=("monthly",),
        ),
    ]

    created_ops = []
    try:
        for op in test_operations:
            created_op = op_db.create_operation(op)
            created_ops.append(created_op)
        yield created_ops
    except Exception as e:
        print(f"Warning: Operations with tags and groups creation failed: {e}")
        yield []
    finally:
        # Cleanup test operations
        try:
            for op in created_ops:
                op_db.delete_operation(op.operation_id)
        except Exception:
            pass


@pytest.fixture
def mock_group(temp_data_dir, mock_user, mock_account):
    """
    Create a mock group for testing group-related functionality.
    """
    from src.models.groupmodel import OperationGroups
    from src.dbhandlers.opgroupsdb import OpGroupsDB

    # Ensure the user directory exists
    user_dir = os.path.join(temp_data_dir, "data", mock_user.user_id)
    os.makedirs(user_dir, exist_ok=True)

    group_db = OpGroupsDB(user_id=mock_user.user_id)

    # Create test group
    test_group = OperationGroups(
        user_id=mock_user.user_id,
        group_name="TestGroup",
        group_currency=mock_account.account_currency,
        status="open",
    )

    created_group = None
    try:
        created_group = group_db.create_group(test_group)
        yield created_group
    except Exception as e:
        print(f"Warning: Group creation failed: {e}")
        yield None
    finally:
        # Cleanup test group
        try:
            if created_group and created_group.group_id:
                group_db.delete_group(created_group.group_id)
        except Exception:
            pass
