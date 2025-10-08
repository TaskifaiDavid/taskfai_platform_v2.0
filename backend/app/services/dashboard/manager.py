"""
Dashboard configuration management service
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
import asyncpg

from app.models.dashboard import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardInDB
)
from app.core.security import encrypt_data, decrypt_data
from .validator import DashboardURLValidator


class DashboardManager:
    """
    Manage dashboard configurations with encryption

    Features:
    - CRUD operations for dashboard configs
    - URL validation
    - Credential encryption/decryption
    - Primary dashboard management
    """

    def __init__(self, db_pool: asyncpg.Pool, encryption_key: str):
        """
        Initialize dashboard manager

        Args:
            db_pool: Database connection pool
            encryption_key: Encryption key for sensitive data
        """
        self.pool = db_pool
        self.encryption_key = encryption_key
        self.url_validator = DashboardURLValidator()

    async def create_dashboard(
        self,
        dashboard: DashboardCreate
    ) -> DashboardResponse:
        """
        Create new dashboard configuration

        Args:
            dashboard: Dashboard creation data

        Returns:
            Created dashboard

        Raises:
            ValueError: If URL validation fails
        """
        # Validate URL
        self.url_validator.validate_url(dashboard.dashboard_url)

        # Encrypt authentication config if present
        encrypted_auth = None
        if dashboard.authentication_config:
            encrypted_auth = encrypt_data(
                dashboard.authentication_config,
                self.encryption_key
            )

        config_id = str(uuid4())

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO dashboard_configs (
                    config_id,
                    user_id,
                    dashboard_name,
                    dashboard_type,
                    dashboard_url,
                    authentication_method,
                    authentication_config,
                    permissions,
                    is_active,
                    created_at,
                    updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
                """,
                UUID(config_id),
                UUID(dashboard.user_id),
                dashboard.dashboard_name,
                dashboard.dashboard_type,
                dashboard.dashboard_url,
                dashboard.authentication_method,
                encrypted_auth,
                dashboard.permissions or [],
                dashboard.is_active,
                datetime.utcnow(),
                datetime.utcnow()
            )

        return self._row_to_response(dict(row))

    async def get_dashboard(
        self,
        config_id: str,
        user_id: str
    ) -> Optional[DashboardResponse]:
        """
        Get dashboard by ID

        Args:
            config_id: Dashboard config ID
            user_id: User ID (for authorization)

        Returns:
            Dashboard or None
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM dashboard_configs
                WHERE config_id = $1 AND user_id = $2
                """,
                UUID(config_id),
                UUID(user_id)
            )

        if not row:
            return None

        return self._row_to_response(dict(row))

    async def list_dashboards(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[DashboardResponse]:
        """
        List user's dashboards

        Args:
            user_id: User ID
            skip: Pagination offset
            limit: Max results

        Returns:
            List of dashboards
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM dashboard_configs
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                UUID(user_id),
                limit,
                skip
            )

        return [self._row_to_response(dict(row)) for row in rows]

    async def update_dashboard(
        self,
        config_id: str,
        user_id: str,
        update_data: DashboardUpdate
    ) -> Optional[DashboardResponse]:
        """
        Update dashboard configuration

        Args:
            config_id: Dashboard config ID
            user_id: User ID (for authorization)
            update_data: Update data

        Returns:
            Updated dashboard or None

        Raises:
            ValueError: If URL validation fails
        """
        # Validate URL if provided
        if update_data.dashboard_url:
            self.url_validator.validate_url(update_data.dashboard_url)

        # Build update query dynamically
        update_fields = []
        params = [UUID(config_id), UUID(user_id)]
        param_idx = 3

        if update_data.dashboard_name is not None:
            update_fields.append(f"dashboard_name = ${param_idx}")
            params.append(update_data.dashboard_name)
            param_idx += 1

        if update_data.dashboard_type is not None:
            update_fields.append(f"dashboard_type = ${param_idx}")
            params.append(update_data.dashboard_type)
            param_idx += 1

        if update_data.dashboard_url is not None:
            update_fields.append(f"dashboard_url = ${param_idx}")
            params.append(update_data.dashboard_url)
            param_idx += 1

        if update_data.authentication_method is not None:
            update_fields.append(f"authentication_method = ${param_idx}")
            params.append(update_data.authentication_method)
            param_idx += 1

        if update_data.authentication_config is not None:
            encrypted_auth = encrypt_data(
                update_data.authentication_config,
                self.encryption_key
            )
            update_fields.append(f"authentication_config = ${param_idx}")
            params.append(encrypted_auth)
            param_idx += 1

        if update_data.permissions is not None:
            update_fields.append(f"permissions = ${param_idx}")
            params.append(update_data.permissions)
            param_idx += 1

        if update_data.is_active is not None:
            update_fields.append(f"is_active = ${param_idx}")
            params.append(update_data.is_active)
            param_idx += 1

        if not update_fields:
            # No updates provided
            return await self.get_dashboard(config_id, user_id)

        update_fields.append(f"updated_at = ${param_idx}")
        params.append(datetime.utcnow())

        query = f"""
            UPDATE dashboard_configs
            SET {', '.join(update_fields)}
            WHERE config_id = $1 AND user_id = $2
            RETURNING *
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if not row:
            return None

        return self._row_to_response(dict(row))

    async def delete_dashboard(
        self,
        config_id: str,
        user_id: str
    ) -> bool:
        """
        Delete dashboard configuration

        Args:
            config_id: Dashboard config ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM dashboard_configs
                WHERE config_id = $1 AND user_id = $2
                """,
                UUID(config_id),
                UUID(user_id)
            )

        return "DELETE 1" in result

    async def set_primary_dashboard(
        self,
        config_id: str,
        user_id: str
    ) -> Optional[DashboardResponse]:
        """
        Set dashboard as primary (is_active=true)

        Only one dashboard can be primary per user

        Args:
            config_id: Dashboard config ID
            user_id: User ID

        Returns:
            Updated dashboard or None
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Unset all other primary dashboards for this user
                await conn.execute(
                    """
                    UPDATE dashboard_configs
                    SET is_active = false, updated_at = $1
                    WHERE user_id = $2 AND is_active = true
                    """,
                    datetime.utcnow(),
                    UUID(user_id)
                )

                # Set this dashboard as primary
                row = await conn.fetchrow(
                    """
                    UPDATE dashboard_configs
                    SET is_active = true, updated_at = $1
                    WHERE config_id = $2 AND user_id = $3
                    RETURNING *
                    """,
                    datetime.utcnow(),
                    UUID(config_id),
                    UUID(user_id)
                )

        if not row:
            return None

        return self._row_to_response(dict(row))

    async def get_primary_dashboard(
        self,
        user_id: str
    ) -> Optional[DashboardResponse]:
        """
        Get user's primary dashboard

        Args:
            user_id: User ID

        Returns:
            Primary dashboard or None
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM dashboard_configs
                WHERE user_id = $1 AND is_active = true
                LIMIT 1
                """,
                UUID(user_id)
            )

        if not row:
            return None

        return self._row_to_response(dict(row))

    def _row_to_response(self, row: Dict[str, Any]) -> DashboardResponse:
        """Convert database row to response model"""
        # Decrypt authentication config if present
        if row.get("authentication_config"):
            try:
                row["authentication_config"] = decrypt_data(
                    row["authentication_config"],
                    self.encryption_key
                )
            except Exception:
                # If decryption fails, return None
                row["authentication_config"] = None

        return DashboardResponse(
            config_id=str(row["config_id"]),
            dashboard_name=row["dashboard_name"],
            dashboard_type=row["dashboard_type"],
            dashboard_url=row["dashboard_url"],
            authentication_method=row["authentication_method"],
            authentication_config=row["authentication_config"],
            permissions=row.get("permissions", []),
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_primary=row["is_active"]  # is_active serves as is_primary
        )
