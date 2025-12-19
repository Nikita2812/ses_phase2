"""
CSA AIaaS Platform - Database Configuration
Sprint 1: The Neuro-Skeleton

Supabase connection configuration and helper functions.
"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
from app.core.constants import AUDIT_LOG_DISABLED_WARNING, AUDIT_LOG_SKIPPED_PREFIX


class DatabaseConfig:
    """
    Database configuration and connection management for Supabase.

    This class handles the connection to Supabase (PostgreSQL + pgvector)
    and provides helper methods for database operations.
    """

    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.supabase_url: str = settings.SUPABASE_URL
        self.supabase_key: str = settings.SUPABASE_ANON_KEY
        self._client: Optional[Client] = None
        self._connection_available: bool = True

        # Check if credentials are provided
        if not self.supabase_url or not self.supabase_key:
            print(AUDIT_LOG_DISABLED_WARNING)
            self._connection_available = False

    @property
    def client(self) -> Client:
        """
        Get or create Supabase client instance.

        Returns:
            Supabase client instance

        Raises:
            ValueError: If credentials are missing
        """
        if self._client is None:
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple query to test connection
            response = self.client.table("projects").select("id").limit(1).execute()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def log_audit(
        self,
        user_id: str,
        action: str,
        details: dict
    ) -> None:
        """
        Log an action to the audit_log table.

        This is critical for "Zero Trust" security as specified in requirements.

        Args:
            user_id: ID of the user performing the action
            action: Description of the action
            details: Additional details as JSON
        """
        # Skip if database is not available
        if not self._connection_available:
            print(f"{AUDIT_LOG_SKIPPED_PREFIX} {user_id} | {action}")
            return

        try:
            self.client.table("audit_log").insert({
                "user_id": user_id,
                "action": action,
                "details": details
            }).execute()
        except Exception as e:
            print(f"Failed to log audit entry: {e}")
            # Don't raise in development - just log the error
            # In production, this should raise an alert


# Global database instance
db_config = DatabaseConfig()


def get_db() -> Client:
    """
    Get the global Supabase client instance.

    Returns:
        Supabase client instance
    """
    return db_config.client


def log_audit_entry(user_id: str, action: str, details: dict) -> None:
    """
    Helper function to log audit entries.

    Args:
        user_id: ID of the user performing the action
        action: Description of the action
        details: Additional details as JSON
    """
    db_config.log_audit(user_id, action, details)
