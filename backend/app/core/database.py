"""
CSA AIaaS Platform - Database Configuration
Sprint 1: The Neuro-Skeleton
Phase 2 Sprint 2: Enhanced for SQL query execution

Supabase connection configuration and helper functions.
"""

from typing import Optional, List, Tuple, Any
from supabase import create_client, Client
from app.core.config import settings
from app.core.constants import AUDIT_LOG_DISABLED_WARNING, AUDIT_LOG_SKIPPED_PREFIX
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import register_adapter, AsIs
from uuid import UUID

# Register UUID adapter for psycopg2
def adapt_uuid(uuid_val):
    return AsIs(f"'{uuid_val}'")

register_adapter(UUID, adapt_uuid)


class DatabaseConfig:
    """
    Database configuration and connection management for Supabase.

    This class handles the connection to Supabase (PostgreSQL + pgvector)
    and provides helper methods for database operations.

    Supports both:
    - Supabase REST API (via supabase-py client)
    - Direct PostgreSQL connections (via psycopg2) for raw SQL queries
    """

    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.supabase_url: str = settings.SUPABASE_URL
        self.supabase_key: str = settings.SUPABASE_ANON_KEY
        self._client: Optional[Client] = None
        self._pg_connection: Optional[psycopg2.extensions.connection] = None
        self._connection_available: bool = True

        # Check if credentials are provided
        if not self.supabase_url or not self.supabase_key:
            print(AUDIT_LOG_DISABLED_WARNING)
            self._connection_available = False

        # Extract PostgreSQL connection string from Supabase URL
        # Format: https://your-project.supabase.co
        # PostgreSQL: postgresql://postgres:[password]@db.your-project.supabase.co:5432/postgres
        self._pg_connection_string: Optional[str] = None
        if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
            self._pg_connection_string = settings.DATABASE_URL

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

    def close_pg_connection(self):
        """Close the PostgreSQL connection if it exists."""
        if self._pg_connection is not None and not self._pg_connection.closed:
            try:
                self._pg_connection.close()
                print("PostgreSQL connection closed")
            except Exception as e:
                print(f"Error closing PostgreSQL connection: {e}")
            finally:
                self._pg_connection = None

    def get_pg_connection(self) -> psycopg2.extensions.connection:
        """
        Get or create PostgreSQL connection for raw SQL queries.
        Implements retry logic for transient connection failures.

        Returns:
            psycopg2 connection object

        Raises:
            ValueError: If DATABASE_URL is not configured
        """
        if not self._pg_connection_string:
            raise ValueError(
                "DATABASE_URL not configured. Add it to your .env file.\n"
                "Format: postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
            )

        if self._pg_connection is None or self._pg_connection.closed:
            # Connect using the connection string directly
            # Parse the connection string to extract components
            import socket
            import time
            from urllib.parse import urlparse, parse_qs, urlencode

            # Parse the URL
            parsed = urlparse(self._pg_connection_string)

            # Extract components
            dbname = parsed.path[1:] if parsed.path else 'postgres'
            user = parsed.username
            password = parsed.password
            host = parsed.hostname
            port = parsed.port or 5432

            # Try to resolve IPv4 address to avoid IPv6 issues
            try:
                # Get IPv4 address if available
                addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
                if addr_info:
                    ipv4_addr = addr_info[0][4][0]
                    print(f"Resolved {host} to IPv4: {ipv4_addr}")
                    host = ipv4_addr
            except (socket.gaierror, IndexError):
                # If IPv4 resolution fails, try with IPv6
                print(f"IPv4 resolution failed for {host}, will try original hostname")
                pass

            # Parse query parameters
            query_params = parse_qs(parsed.query)

            # Build connection parameters
            conn_params = {
                'dbname': dbname,
                'user': user,
                'password': password,
                'host': host,
                'port': port,
                'connect_timeout': 30,  # Increased from 10 to 30 seconds
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            }

            # Add SSL mode if present
            if 'sslmode' in query_params:
                conn_params['sslmode'] = query_params['sslmode'][0]

            # Add options if present
            if 'options' in query_params and query_params['options'][0]:
                conn_params['options'] = query_params['options'][0]

            # Connect with retry logic for transient failures
            max_retries = 3
            retry_delay = 2  # seconds
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    print(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...")
                    self._pg_connection = psycopg2.connect(**conn_params)
                    print(f"✓ Database connection established successfully")
                    break
                except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
                    last_error = e
                    error_msg = str(e)
                    
                    # Check if it's a timeout or connection issue
                    if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower():
                        if attempt < max_retries - 1:
                            print(f"⚠ Connection attempt {attempt + 1} failed: {error_msg}")
                            print(f"  Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 1.5  # Exponential backoff
                        else:
                            print(f"✗ All connection attempts failed")
                            raise ConnectionError(
                                f"Failed to connect to database after {max_retries} attempts. "
                                f"Last error: {error_msg}"
                            ) from e
                    else:
                        # Non-transient error, don't retry
                        raise

        return self._pg_connection

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch: bool = True
    ) -> List[Tuple[Any, ...]]:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters (tuple)
            fetch: Whether to fetch results

        Returns:
            List of result tuples (if fetch=True)

        Example:
            >>> db.execute_query("SELECT * FROM users WHERE id = %s", (user_id,))
            [(1, 'user@example.com', ...)]
        """
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                conn = self.get_pg_connection()
                cursor = conn.cursor()

                try:
                    cursor.execute(query, params)

                    if fetch:
                        results = cursor.fetchall()
                        conn.commit()
                        return results
                    else:
                        conn.commit()
                        return []

                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    cursor.close()
                    
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last_error = e
                error_msg = str(e)
                
                # Close stale connection
                self.close_pg_connection()
                
                # Retry on connection errors
                if attempt < max_retries - 1 and ('timeout' in error_msg.lower() or 'connection' in error_msg.lower()):
                    print(f"⚠ Query execution failed (attempt {attempt + 1}), retrying: {error_msg}")
                    import time
                    time.sleep(1)
                else:
                    raise ConnectionError(f"Database query failed: {error_msg}") from e

    def execute_query_dict(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[dict]:
        """
        Execute a raw SQL query and return results as dictionaries.

        Args:
            query: SQL query string
            params: Query parameters (tuple)

        Returns:
            List of result dictionaries

        Example:
            >>> db.execute_query_dict("SELECT * FROM users WHERE id = %s", (user_id,))
            [{'id': 1, 'email': 'user@example.com', ...}]
        """
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                conn = self.get_pg_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                try:
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    conn.commit()
                    return [dict(row) for row in results]

                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    cursor.close()
                    
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last_error = e
                error_msg = str(e)
                
                # Close stale connection
                self.close_pg_connection()
                
                # Retry on connection errors
                if attempt < max_retries - 1 and ('timeout' in error_msg.lower() or 'connection' in error_msg.lower()):
                    print(f"⚠ Query execution failed (attempt {attempt + 1}), retrying: {error_msg}")
                    import time
                    time.sleep(1)
                else:
                    raise ConnectionError(f"Database query failed: {error_msg}") from e

    def log_audit(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict
    ) -> None:
        """
        Log an action to the audit_log table.

        This is critical for "Zero Trust" security as specified in requirements.

        Args:
            user_id: ID of the user performing the action
            action: Description of the action
            entity_type: Type of entity (e.g., "schema", "workflow_execution")
            entity_id: ID of the entity
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
                "entity_type": entity_type,
                "entity_id": entity_id,
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
