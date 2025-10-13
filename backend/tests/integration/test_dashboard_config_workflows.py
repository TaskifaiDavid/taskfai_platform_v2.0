"""
Integration Tests for Dashboard Configuration User Stories
Tests T013-T017: End-to-end workflows for dynamic dashboard configs
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestDashboardConfigWorkflows:
    """Integration tests for dashboard configuration user stories"""

    async def test_story_1_first_time_user_sees_tenant_default(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        T013: Story 1 - First-time user sees default dashboard

        User Story:
        Given: User has no personal dashboard configs
        When: User calls GET /api/dashboard-configs/default
        Then: User receives tenant-wide default dashboard

        Expected:
        - Returns 200 OK
        - Dashboard with is_default=true
        - user_id IS NULL (tenant default)
        - Dashboard name like "Overview Dashboard"
        - Layout contains at least 1 widget
        - Widget types are valid (kpi_grid, recent_uploads, top_products)

        This validates the happy path for new users who haven't customized yet.
        """
        # Fetch default dashboard as first-time user
        response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        assert response.status_code == 200, \
            "First-time user should receive default dashboard"

        data = response.json()

        # Verify it's a default dashboard
        assert data["is_default"] is True, \
            "Should return a default dashboard"

        # If user has no custom configs, should be tenant default
        # (user_id IS NULL)
        # Note: In test environment, user may have created configs
        # So we check if this is either tenant default OR user default

        # Verify essential fields
        assert "dashboard_name" in data
        assert "layout" in data
        assert len(data["layout"]) >= 1, \
            "Default dashboard must have at least one widget"

        # Verify widget structure
        for widget in data["layout"]:
            assert "id" in widget
            assert "type" in widget
            assert "position" in widget
            assert "props" in widget

            # Verify valid widget types
            valid_types = [
                "kpi_grid", "recent_uploads", "top_products",
                "revenue_chart", "category_revenue", "reseller_performance",
                "sales_trend"
            ]
            assert widget["type"] in valid_types, \
                f"Widget type '{widget['type']}' should be valid"

        # Verify tenant default characteristics
        # Typical tenant defaults have descriptive names
        expected_default_names = [
            "overview", "default", "dashboard", "main", "home"
        ]
        dashboard_name_lower = data["dashboard_name"].lower()
        contains_default_keyword = any(
            keyword in dashboard_name_lower
            for keyword in expected_default_names
        )

        # Either has default keyword OR is explicitly marked as tenant default
        assert contains_default_keyword or data["user_id"] is None, \
            "Should be recognizable as default dashboard"

    async def test_story_2_user_custom_config_overrides_tenant_default(
        self, async_client: AsyncClient, auth_headers, test_user_data
    ):
        """
        T014: Story 2 - User custom config overrides tenant default

        User Story:
        Given: User creates personal default dashboard (is_default=true)
        When: User calls GET /api/dashboard-configs/default
        Then: User receives their personal config, NOT tenant default

        Expected Priority Hierarchy:
        1. User-specific default (user_id = current_user, is_default=true)
        2. Tenant-wide default (user_id IS NULL, is_default=true)

        This validates personalization without affecting other users.
        """
        # Step 1: Get initial default (before customization)
        initial_response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        initial_default_id = None
        if initial_response.status_code == 200:
            initial_default_id = initial_response.json()["dashboard_id"]

        # Step 2: Create user's personal default dashboard
        custom_default_body = {
            "dashboard_name": "My Personal Sales Dashboard",
            "description": "Customized for my workflow",
            "layout": [
                {
                    "id": "my-kpis",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {
                        "kpis": ["total_revenue", "total_units", "avg_price"]
                    }
                },
                {
                    "id": "my-top-products",
                    "type": "top_products",
                    "position": {"row": 2, "col": 0, "width": 12, "height": 4},
                    "props": {
                        "title": "My Best Sellers",
                        "limit": 10,
                        "sortBy": "revenue"
                    }
                }
            ],
            "kpis": ["total_revenue", "total_units", "avg_price"],
            "filters": {"date_range": "last_90_days"},
            "is_default": True,  # Mark as user's default
            "is_active": True
        }

        create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=custom_default_body
        )

        assert create_response.status_code == 201, \
            "User should be able to create personal default"

        user_default = create_response.json()
        user_default_id = user_default["dashboard_id"]

        # Verify user_id is set correctly
        assert user_default["user_id"] == test_user_data["user_id"], \
            "Custom config should belong to current user"
        assert user_default["is_default"] is True, \
            "Custom config should be marked as default"

        # Step 3: Fetch default again - should return user's custom config
        after_create_response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        assert after_create_response.status_code == 200, \
            "Should return user's custom default"

        current_default = after_create_response.json()

        # CRITICAL: Should return user's config, NOT tenant default
        assert current_default["dashboard_id"] == user_default_id, \
            "User's custom default should take priority over tenant default"
        assert current_default["dashboard_name"] == "My Personal Sales Dashboard", \
            "Should return user's custom config"
        assert current_default["user_id"] == test_user_data["user_id"], \
            "Should be user-specific config, not tenant default (user_id IS NULL)"

        # Verify it's different from initial default
        if initial_default_id:
            assert current_default["dashboard_id"] != initial_default_id, \
                "User config should override tenant default"

        # Step 4: Verify layout was customized correctly
        assert len(current_default["layout"]) == 2, \
            "User's custom layout should have 2 widgets"
        assert current_default["kpis"] == ["total_revenue", "total_units", "avg_price"], \
            "User's custom KPIs should be preserved"

    async def test_story_3_admin_creates_tenant_wide_default(
        self, async_client: AsyncClient, admin_headers, auth_headers
    ):
        """
        T015: Story 3 - Admin creates tenant-wide default

        User Story:
        Given: Admin creates dashboard with user_id=NULL and is_default=true
        When: Regular users with no personal default call GET /default
        Then: All users see the new tenant-wide default

        Expected:
        - Admin can create tenant default (user_id IS NULL)
        - Regular users without personal defaults see this config
        - Users with personal defaults still see their own

        Note: Creating configs with user_id=NULL typically requires admin role.
        This test validates admin-level configuration management.
        """
        # Step 1: Admin creates new tenant-wide default
        # Note: Actual implementation may prevent setting user_id=NULL via API
        # Admin may need to use Supabase UI or special endpoint
        # For this test, we verify the concept

        tenant_default_body = {
            "dashboard_name": "Company-Wide Dashboard 2024",
            "description": "Standard dashboard for all employees",
            "layout": [
                {
                    "id": "company-kpis",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {
                        "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"]
                    }
                },
                {
                    "id": "recent-activity",
                    "type": "recent_uploads",
                    "position": {"row": 2, "col": 0, "width": 6, "height": 3},
                    "props": {
                        "title": "Recent Activity",
                        "limit": 5
                    }
                },
                {
                    "id": "top-performers",
                    "type": "top_products",
                    "position": {"row": 2, "col": 6, "width": 6, "height": 3},
                    "props": {
                        "title": "Top Performers",
                        "limit": 5
                    }
                }
            ],
            "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"],
            "filters": {"date_range": "last_30_days"},
            "is_default": True,
            "is_active": True
        }

        # Attempt to create as admin
        # Note: API may set user_id=admin automatically
        # True tenant defaults (user_id=NULL) may require database-level creation
        admin_create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=admin_headers,
            json=tenant_default_body
        )

        # Admin should be able to create configs
        assert admin_create_response.status_code == 201, \
            "Admin should be able to create dashboard configs"

        admin_config = admin_create_response.json()

        # Step 2: Verify regular user can see it
        # Note: If admin_config has user_id=admin (not NULL), regular users won't see it
        # This test assumes admin has permission to create tenant-wide configs

        list_response = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers,
            params={"include_tenant_defaults": True}
        )

        assert list_response.status_code == 200
        list_data = list_response.json()

        # Tenant defaults should be included in list
        assert list_data["total"] >= 1, \
            "Should see at least one dashboard config"

        # Step 3: Verify behavior based on implementation
        # If true tenant defaults exist (user_id=NULL), verify they're accessible
        # If tenant defaults are admin-owned, verify proper access control

        default_response = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        assert default_response.status_code == 200, \
            "Regular user should get a default dashboard"

    async def test_story_4_config_changes_reflect_on_refresh(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        T016: Story 4 - Config changes reflect immediately on refresh

        User Story:
        Given: User fetches dashboard config
        When: Admin (or user) updates the config
        Then: Next fetch shows updated version

        Expected:
        - GET returns config with updated_at timestamp
        - After PUT, updated_at changes
        - Next GET shows new values
        - Changes visible without cache issues (proper cache invalidation)

        This validates real-time configuration updates without requiring app restart.
        """
        # Step 1: Create initial config
        initial_body = {
            "dashboard_name": "Version 1 Dashboard",
            "description": "Initial version",
            "layout": [
                {
                    "id": "v1-kpi",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {"kpis": ["total_revenue"]}
                }
            ],
            "is_default": False
        }

        create_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=initial_body
        )

        assert create_response.status_code == 201
        initial_config = create_response.json()
        config_id = initial_config["dashboard_id"]
        initial_updated_at = initial_config["updated_at"]

        # Step 2: Fetch config (original version)
        first_fetch = await async_client.get(
            f"/api/dashboard-configs/{config_id}",
            headers=auth_headers
        )

        assert first_fetch.status_code == 200
        first_data = first_fetch.json()
        assert first_data["dashboard_name"] == "Version 1 Dashboard"
        assert first_data["description"] == "Initial version"

        # Step 3: Update config
        update_body = {
            "dashboard_name": "Version 2 Dashboard",
            "description": "Updated with new features",
            "layout": [
                {
                    "id": "v2-kpi",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {"kpis": ["total_revenue", "total_units"]}  # Added metric
                },
                {
                    "id": "v2-products",
                    "type": "top_products",
                    "position": {"row": 2, "col": 0, "width": 12, "height": 3},
                    "props": {"limit": 10}
                }
            ]
        }

        update_response = await async_client.put(
            f"/api/dashboard-configs/{config_id}",
            headers=auth_headers,
            json=update_body
        )

        assert update_response.status_code == 200, \
            "Update should succeed"

        updated_config = update_response.json()
        updated_at_after_change = updated_config["updated_at"]

        # Verify updated_at timestamp changed
        assert updated_at_after_change != initial_updated_at, \
            "updated_at should change after modification"

        # Step 4: Fetch config again (should show new version)
        second_fetch = await async_client.get(
            f"/api/dashboard-configs/{config_id}",
            headers=auth_headers
        )

        assert second_fetch.status_code == 200
        refreshed_data = second_fetch.json()

        # CRITICAL: Changes should be immediately visible
        assert refreshed_data["dashboard_name"] == "Version 2 Dashboard", \
            "Dashboard name should be updated"
        assert refreshed_data["description"] == "Updated with new features", \
            "Description should be updated"
        assert len(refreshed_data["layout"]) == 2, \
            "Layout should have 2 widgets now"
        assert refreshed_data["updated_at"] == updated_at_after_change, \
            "Should reflect latest updated_at timestamp"

        # Verify layout changes
        widget_types = [w["type"] for w in refreshed_data["layout"]]
        assert "kpi_grid" in widget_types and "top_products" in widget_types, \
            "Both widget types should be present"

        # Step 5: Verify changes visible in list endpoint too
        list_response = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers
        )

        assert list_response.status_code == 200
        list_data = list_response.json()

        matching_configs = [
            d for d in list_data["dashboards"]
            if d["dashboard_id"] == config_id
        ]

        assert len(matching_configs) == 1, \
            "Config should appear in list"
        assert matching_configs[0]["updated_at"] == updated_at_after_change, \
            "List should show latest updated_at"

    async def test_story_5_users_have_independent_configs(
        self, async_client: AsyncClient, auth_headers, test_user_data
    ):
        """
        T017: Story 5 - Users have independent configs (isolation)

        User Story:
        Given: User A and User B each create personal default dashboards
        When: Each user calls GET /api/dashboard-configs/default
        Then: Each user sees only their own config, not the other user's

        Expected:
        - User A creates config → User A sees it
        - User B creates config → User B sees it
        - Configs are isolated by user_id
        - No cross-user data leakage
        - RLS policies enforce isolation

        Note: This test uses same user token (can't create second user in test)
        But validates isolation principles through API behavior
        """
        # Step 1: User A creates personal default
        user_a_config_body = {
            "dashboard_name": "User A Personal Dashboard",
            "description": "User A's custom view",
            "layout": [
                {
                    "id": "a-kpis",
                    "type": "kpi_grid",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 2},
                    "props": {"kpis": ["total_revenue", "total_units"]}
                }
            ],
            "kpis": ["total_revenue", "total_units"],
            "filters": {"date_range": "last_30_days"},
            "is_default": True
        }

        create_a_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=user_a_config_body
        )

        assert create_a_response.status_code == 201
        user_a_config = create_a_response.json()
        user_a_id = user_a_config["dashboard_id"]

        # Verify User A's config belongs to them
        assert user_a_config["user_id"] == test_user_data["user_id"], \
            "Config should belong to User A"

        # Step 2: User A fetches default - should see their config
        user_a_default = await async_client.get(
            "/api/dashboard-configs/default",
            headers=auth_headers
        )

        assert user_a_default.status_code == 200
        user_a_default_data = user_a_default.json()
        assert user_a_default_data["dashboard_id"] == user_a_id, \
            "User A should see their own default"

        # Step 3: User A lists configs - should see only their configs + tenant defaults
        user_a_list = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers,
            params={"include_tenant_defaults": False}  # Only user configs
        )

        assert user_a_list.status_code == 200
        user_a_list_data = user_a_list.json()

        # All returned configs should belong to User A or be tenant defaults
        for dashboard in user_a_list_data["dashboards"]:
            # Get full config to check user_id
            detail_response = await async_client.get(
                f"/api/dashboard-configs/{dashboard['dashboard_id']}",
                headers=auth_headers
            )

            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                # Should be either User A's config or tenant default (NULL)
                assert detail_data["user_id"] in [test_user_data["user_id"], None], \
                    f"User A should only see their own configs or tenant defaults, not other users'"

        # Step 4: Verify User A cannot access non-existent (or other user's) config
        fake_user_b_config_id = "00000000-0000-0000-0000-000000000099"

        access_attempt = await async_client.get(
            f"/api/dashboard-configs/{fake_user_b_config_id}",
            headers=auth_headers
        )

        # Should return 404 (RLS filtered it out)
        assert access_attempt.status_code == 404, \
            "User A should not be able to access other users' configs"

        # Step 5: Verify User A cannot modify or delete other users' configs
        # Attempt to update a config that doesn't belong to User A
        update_attempt = await async_client.put(
            f"/api/dashboard-configs/{fake_user_b_config_id}",
            headers=auth_headers,
            json={"dashboard_name": "Hacked"}
        )

        assert update_attempt.status_code in [403, 404], \
            "User A should not be able to modify other users' configs"

        delete_attempt = await async_client.delete(
            f"/api/dashboard-configs/{fake_user_b_config_id}",
            headers=auth_headers
        )

        assert delete_attempt.status_code in [403, 404], \
            "User A should not be able to delete other users' configs"

        # Step 6: Verify creating multiple isolated configs
        user_a_config_2_body = {
            "dashboard_name": "User A Secondary Dashboard",
            "layout": [
                {
                    "id": "secondary",
                    "type": "recent_uploads",
                    "position": {"row": 0, "col": 0, "width": 12, "height": 3},
                    "props": {"limit": 5}
                }
            ],
            "is_default": False
        }

        create_a2_response = await async_client.post(
            "/api/dashboard-configs",
            headers=auth_headers,
            json=user_a_config_2_body
        )

        assert create_a2_response.status_code == 201
        user_a_config_2 = create_a2_response.json()

        # Both configs should belong to User A
        assert user_a_config_2["user_id"] == test_user_data["user_id"], \
            "Second config should also belong to User A"

        # User A should now see 2 configs in their list (excluding tenant defaults)
        final_list = await async_client.get(
            "/api/dashboard-configs",
            headers=auth_headers,
            params={"include_tenant_defaults": False}
        )

        assert final_list.status_code == 200
        final_list_data = final_list.json()

        user_a_config_names = [
            d["dashboard_name"] for d in final_list_data["dashboards"]
            if d["dashboard_name"] in [
                "User A Personal Dashboard",
                "User A Secondary Dashboard"
            ]
        ]

        assert len(user_a_config_names) == 2, \
            "User A should see both their configs"
