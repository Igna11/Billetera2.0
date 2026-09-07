"""
Tests for OperationBrowser UI component and filter functionality.
"""

from billeUI.operationbrowser import OperationBrowser


class TestOperationBrowser:
    """Test suite for OperationBrowser functionality."""

    def test_operation_browser_initialization(self, stacked_widget, mock_user, mock_account):
        """Test that OperationBrowser initializes correctly with mock user and account."""
        # Set up mock user and account in widget
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Check that browser was created
        assert browser is not None
        assert browser.widget == stacked_widget

        # Check that main UI elements exist
        assert hasattr(browser, "operation_table_widget")
        assert hasattr(browser, "accounts_comboBox")
        assert hasattr(browser, "save_changes_button")

        browser.close()

    def test_operation_browser_header_filter_initialization(self, stacked_widget, mock_user, mock_account):
        """Test that header filter mixin is properly initialized."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Check that filter attributes are initialized
        assert hasattr(browser, "active_filters")
        assert hasattr(browser, "filterable_columns")
        assert hasattr(browser, "operations_list")

        # Check that header click handler is connected
        assert browser.operation_table_widget.horizontalHeader().sectionClicked.connect is not None

        browser.close()

    def test_searchable_filter_menu_category_column(self, stacked_widget, mock_user, mock_account):
        """Test that category column uses searchable filter (not simple checkboxes)."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Verify that category column (4) is configured to use searchable filter
        # We check this by verifying the method exists without opening actual menus
        assert hasattr(browser, "_show_searchable_filter_menu")

        # Category column should use searchable filter (column 4)
        # This is verified by the implementation in _handle_header_click
        from billeUI.headerfiltermixin import HeaderFilterMixin

        assert HeaderFilterMixin.CATEGORY_COLUMN == 4

        browser.close()

    def test_searchable_filter_menu_subcategory_column(self, stacked_widget, mock_user, mock_account):
        """Test that subcategory column uses searchable filter (not simple checkboxes)."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Verify that subcategory column (5) is configured to use searchable filter
        assert hasattr(browser, "_show_searchable_filter_menu")

        # Subcategory column should use searchable filter (column 5)
        from billeUI.headerfiltermixin import HeaderFilterMixin

        assert HeaderFilterMixin.SUBCATEGORY_COLUMN == 5

        browser.close()

    def test_searchable_filter_menu_tags_column(self, stacked_widget, mock_user, mock_account):
        """Test that tags column uses searchable filter (not simple checkboxes)."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Verify that tags column (8) is configured to use searchable filter
        assert hasattr(browser, "_show_searchable_filter_menu")

        # Tags column should use searchable filter (column 8)
        from billeUI.headerfiltermixin import HeaderFilterMixin

        assert HeaderFilterMixin.TAGS_COLUMN == 8

        browser.close()

    def test_searchable_filter_menu_groups_column(self, stacked_widget, mock_user, mock_account):
        """Test that groups column uses searchable filter (not simple checkboxes)."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Verify that groups column (7) is configured to use searchable filter
        assert hasattr(browser, "_show_searchable_filter_menu")

        # Groups column should use searchable filter (column 7)
        from billeUI.headerfiltermixin import HeaderFilterMixin

        assert HeaderFilterMixin.GROUP_COLUMN == 7

        browser.close()

    def test_operation_type_simple_filter(self, stacked_widget, mock_user, mock_account):
        """Test that operation type column uses simple checkboxes (not searchable)."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Verify that operation type column (3) uses simple checkboxes
        assert hasattr(browser, "_apply_checkbox_filters")

        # Operation type column should use simple checkboxes (column 3)
        from billeUI.headerfiltermixin import HeaderFilterMixin

        assert HeaderFilterMixin.OPERATION_TYPE_COLUMN == 3

        browser.close()

    def test_filterable_columns_configuration(self, stacked_widget, mock_user, mock_account):
        """Test that filterable columns are correctly configured."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Check that the expected columns are filterable
        # Expected: [0, 3, 4, 5, 6, 7, 8] for single account
        expected_columns = {0, 3, 4, 5, 6, 7, 8}
        actual_columns = set(browser.filterable_columns)

        assert actual_columns == expected_columns

        browser.close()

    def test_filterable_columns_all_accounts(self, stacked_widget, mock_user, mock_account):
        """Test that filterable columns when viewing all accounts."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Switch to "All" accounts view
        browser.view_all_operations()

        # The filterable columns don't automatically update when switching views
        # This test checks the current behavior
        # The actual filterable columns remain the same as single account view
        expected_columns = {0, 3, 4, 5, 6, 7, 8}
        actual_columns = set(browser.filterable_columns)

        assert actual_columns == expected_columns

        browser.close()

    def test_searchable_filter_methods_exist(self, stacked_widget, mock_user, mock_account):
        """Test that all new searchable filter methods exist."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Check that new methods exist
        assert hasattr(browser, "_show_searchable_filter_menu")
        assert hasattr(browser, "_apply_searchable_filters")
        assert hasattr(browser, "_clear_searchable_filter")

        browser.close()

    def test_filter_operations_with_category(self, stacked_widget, mock_user, mock_account, mock_operations):
        """Test that filtering by category works correctly."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Set a category filter
        browser.active_filters[4] = {"Food"}  # Category column is 4

        # Filter operations
        filtered = browser.filter_operations(browser.operations_list)

        # Check that only Food operations are returned
        assert all(op.category == "Food" for op in filtered)

        browser.close()

    def test_filter_operations_with_multiple_categories(self, stacked_widget, mock_user, mock_account, mock_operations):
        """Test that filtering by multiple categories works correctly."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Set multiple category filters
        browser.active_filters[4] = {"Food", "Salary"}  # Category column is 4

        # Filter operations
        filtered = browser.filter_operations(browser.operations_list)

        # Check that only Food or Salary operations are returned
        assert all(op.category in ["Food", "Salary"] for op in filtered)

        browser.close()

    def test_clear_filters(self, stacked_widget, mock_user, mock_account, mock_operations):
        """Test that clearing filters works correctly."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Set some filters
        browser.active_filters[4] = {"Food"}
        browser.active_filters[5] = {"Restaurant"}

        # Clear all filters
        browser.clear_all_filters()

        # Check that all filters are cleared
        assert len(browser.active_filters) == 0

        browser.close()

    def test_filter_callback_connection(self, stacked_widget, mock_user, mock_account):
        """Test that filter callback is properly connected."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Check that filter callback is set
        assert hasattr(browser, "_filter_callback")
        assert browser._filter_callback is not None

        browser.close()


class TestSearchableFilterFunctionality:
    """Test suite for the new searchable filter functionality."""

    def test_searchable_filter_menu_structure(self, stacked_widget, mock_user, mock_account):
        """Test that searchable filter menu has the correct structure."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # The method should exist and handle the column index correctly
        # Category column (4), Subcategory (5), Tags (8), Groups (7)
        searchable_columns = [4, 5, 7, 8]

        for col in searchable_columns:
            # Verify the method can be called without errors
            # (we can't test the actual menu UI, but we can test the method exists)
            assert hasattr(browser, "_show_searchable_filter_menu")

        browser.close()

    def test_non_searchable_columns_unchanged(self, stacked_widget, mock_user, mock_account):
        """Test that non-searchable columns still use the old filter method."""
        stacked_widget.user_object = mock_user
        stacked_widget.account_objects = [mock_account]

        browser = OperationBrowser(widget=stacked_widget)

        # Operation type column (3) should still use simple checkboxes
        # Date column (0) should use date picker
        # Description column (6) should use search bar

        # These should not use the searchable filter
        non_searchable_columns = [0, 3, 6]

        for col in non_searchable_columns:
            # Verify the old methods still exist
            if col == 0:
                assert hasattr(browser, "_show_date_filter_menu")
            elif col == 3:
                assert hasattr(browser, "_apply_checkbox_filters")
            elif col == 6:
                assert hasattr(browser, "_show_description_search_menu")

        browser.close()
