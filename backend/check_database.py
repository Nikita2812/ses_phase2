#!/usr/bin/env python3
"""
Check Database Schema Status
Verifies if Phase 2 Sprint 2 schema is installed.
"""

import os
import sys
import psycopg2
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

def check_database():
    """Check if database schema is properly initialized."""

    print("="*70)
    print("Database Schema Check")
    print("="*70)

    if not settings.DATABASE_URL:
        print("❌ DATABASE_URL not configured in .env file")
        print("\nPlease add:")
        print("  DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres")
        return False

    print(f"\n📍 Connecting to database...")
    print(f"   Host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'unknown'}")

    try:
        # Import database config
        from app.core.database import DatabaseConfig

        db = DatabaseConfig()
        conn = db.get_pg_connection()
        cursor = conn.cursor()

        print("✅ Connection successful!\n")

        # Check CSA schema
        print("Checking schema status:")
        print("-" * 70)

        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'csa'")
        csa_exists = cursor.fetchone()

        if csa_exists:
            print("✅ CSA schema exists")

            # Check tables
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'csa'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()

            print(f"\n📊 Tables in csa schema ({len(tables)}):")
            for table in tables:
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM csa.{table[0]}")
                count = cursor.fetchone()[0]
                print(f"   ✓ csa.{table[0]:<30} ({count} rows)")

            # Check for deliverable_schemas specifically
            cursor.execute("""
                SELECT COUNT(*) FROM csa.deliverable_schemas
            """)
            schema_count = cursor.fetchone()[0]

            print(f"\n📋 Workflow schemas defined: {schema_count}")

            if schema_count > 0:
                cursor.execute("""
                    SELECT deliverable_type, display_name, discipline, version
                    FROM csa.deliverable_schemas
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                schemas = cursor.fetchall()
                print("\nAvailable workflows:")
                for s in schemas:
                    print(f"   - {s[0]:<30} v{s[3]}  ({s[1]}) - {s[2]}")

                print("\n✅ Everything looks good! Your database is ready.")
                print("\n💡 The frontend should work now. Try refreshing the page.")

            else:
                print("\n⚠️  No workflows defined yet.")
                print("\n📝 Next step: The foundation_design workflow should have been")
                print("   inserted by init_phase2_sprint2.sql")
                print("\n   Check if the INSERT statement at the end of the SQL file ran successfully.")

        else:
            print("❌ CSA schema does NOT exist")
            print("\n📝 Action required:")
            print("   1. Open Supabase SQL Editor")
            print("   2. Run: backend/init_phase2_sprint2.sql")
            print("   3. Verify the script completes without errors")
            print("\n   The script creates:")
            print("      - csa schema")
            print("      - csa.deliverable_schemas table")
            print("      - csa.workflow_executions table")
            print("      - csa.schema_version_history table")
            return False

        cursor.close()
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\n   Type: {type(e).__name__}")

        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("\n💡 Network connectivity issue detected.")
            print("\n   Solutions:")
            print("   1. Use Supabase Connection Pooler:")
            print("      DATABASE_URL=postgresql://postgres.[PROJECT]:[PASSWORD]@")
            print("                   aws-0-us-east-1.pooler.supabase.com:6543/postgres")
            print("\n   2. Check your network/firewall settings")
            print("\n   See: TROUBLESHOOTING_DATABASE_CONNECTION.md for details")

        return False

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)
