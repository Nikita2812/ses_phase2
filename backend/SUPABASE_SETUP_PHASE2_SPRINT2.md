# Phase 2 Sprint 2: Supabase Setup Guide

This guide explains how to set up Phase 2 Sprint 2 (Configuration Layer) with Supabase as your database.

---

## Prerequisites

1. **Supabase Account**: Sign up at [https://supabase.com](https://supabase.com)
2. **Existing Project**: You should already have a Supabase project from Phase 1
3. **Python Environment**: Virtual environment activated with dependencies installed

---

## Step 1: Get Your Database Connection String

### 1.1 Navigate to Database Settings

1. Go to your Supabase Dashboard: `https://app.supabase.com/project/<your-project-id>`
2. Click on **Settings** (gear icon in the left sidebar)
3. Click on **Database**

### 1.2 Copy Connection String

In the **Connection string** section, you'll see different formats. Copy the **URI** format:

```
postgresql://postgres:[YOUR-PASSWORD]@db.your-project-id.supabase.co:5432/postgres
```

**Important**: Replace `[YOUR-PASSWORD]` with your actual database password.

### 1.3 Find Your Database Password

If you don't remember your database password:
1. Go to **Database Settings**
2. Scroll to **Database password**
3. Click **Reset database password** (⚠️ This will invalidate the old password!)
4. Copy the new password and save it securely

---

## Step 2: Update Your `.env` File

Add the `DATABASE_URL` to your `.env` file:

```bash
# Existing Supabase configuration (from Phase 1)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here

# NEW: PostgreSQL connection string (Phase 2 Sprint 2)
DATABASE_URL=postgresql://postgres:your-actual-password@db.your-project-id.supabase.co:5432/postgres

# LLM Configuration
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key-here
```

**Security Warning**: Never commit your `.env` file to version control! It should already be in `.gitignore`.

---

## Step 3: Install Required Dependencies

The `psycopg2-binary` package is required for direct PostgreSQL connections:

```bash
# Activate your virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install/update dependencies
pip install -r requirements.txt
```

This will install:
- `supabase>=2.3.0` - For REST API operations (existing)
- `psycopg2-binary>=2.9.9` - For raw SQL queries (new)

---

## Step 4: Run the Database Schema Migration

### 4.1 Option A: Using Supabase SQL Editor (Recommended)

1. Go to **SQL Editor** in your Supabase Dashboard
2. Click **New query**
3. Copy the contents of `backend/init_phase2_sprint2.sql`
4. Paste into the SQL editor
5. Click **Run** (or press Ctrl+Enter)

You should see:
```
Success: No rows returned
```

This is normal - the SQL script creates tables and functions but doesn't return data.

### 4.2 Option B: Using psql Command Line

If you have `psql` installed locally:

```bash
# From the backend/ directory
psql "postgresql://postgres:YOUR-PASSWORD@db.YOUR-PROJECT-ID.supabase.co:5432/postgres" \
  < init_phase2_sprint2.sql
```

Replace:
- `YOUR-PASSWORD` with your database password
- `YOUR-PROJECT-ID` with your Supabase project ID

---

## Step 5: Verify the Schema

### 5.1 Check Tables Were Created

In the Supabase Dashboard:
1. Go to **Table Editor**
2. You should see these new tables in the `csa` schema:
   - `deliverable_schemas`
   - `workflow_executions`
   - `schema_versions`

### 5.2 Run a Test Query

In the **SQL Editor**, run:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'csa'
AND table_name IN ('deliverable_schemas', 'workflow_executions', 'schema_versions');
```

You should see all three tables listed.

### 5.3 Check Helper Functions

Run this query to verify functions were created:

```sql
SELECT proname
FROM pg_proc
WHERE proname IN ('get_deliverable_schema', 'log_workflow_execution', 'update_workflow_execution');
```

You should see all three functions listed.

---

## Step 6: Test the Connection

### 6.1 Test from Python

Create a test script `test_db_connection.py`:

```python
from app.core.database import DatabaseConfig

# Test REST API connection (Phase 1)
db = DatabaseConfig()
print("Testing Supabase REST API connection...")
if db.test_connection():
    print("✅ REST API connection successful!")
else:
    print("❌ REST API connection failed!")

# Test PostgreSQL connection (Phase 2 Sprint 2)
print("\nTesting PostgreSQL connection...")
try:
    result = db.execute_query("SELECT current_database(), version();")
    print(f"✅ PostgreSQL connection successful!")
    print(f"   Database: {result[0][0]}")
    print(f"   Version: {result[0][1][:50]}...")
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
```

Run it:

```bash
python test_db_connection.py
```

Expected output:
```
Testing Supabase REST API connection...
✅ REST API connection successful!

Testing PostgreSQL connection...
✅ PostgreSQL connection successful!
   Database: postgres
   Version: PostgreSQL 15.1 on x86_64-pc-linux-gnu...
```

### 6.2 Test Schema Service

```python
from app.services.schema_service import SchemaService

service = SchemaService()

# List schemas
schemas = service.list_schemas()
print(f"Found {len(schemas)} workflow schemas")
```

---

## Step 7: Run the Demonstration

Now you're ready to run the Phase 2 Sprint 2 demo:

```bash
python demo_phase2_sprint2.py
```

This will:
1. Create a foundation design workflow schema
2. Execute the workflow dynamically
3. Show variable substitution
4. Display statistics

---

## Troubleshooting

### Error: "No module named 'psycopg2'"

**Solution**: Install psycopg2-binary:
```bash
pip install psycopg2-binary
```

### Error: "Database connection test failed"

**Causes**:
1. Incorrect `DATABASE_URL` in `.env`
2. Wrong password
3. Firewall blocking connection

**Solution**:
1. Verify your `DATABASE_URL` format
2. Reset your database password in Supabase
3. Check if you need to enable database access (Supabase → Settings → Database → Connection pooling)

### Error: "relation 'csa.deliverable_schemas' does not exist"

**Cause**: Database schema not initialized

**Solution**: Run the SQL migration script (Step 4)

### Error: "SSL connection has been closed unexpectedly"

**Cause**: Network issue or Supabase maintenance

**Solution**:
1. Check Supabase status: https://status.supabase.com
2. Try again in a few minutes
3. Ensure your internet connection is stable

### Error: "permission denied for schema csa"

**Cause**: The `csa` schema might not exist or you don't have permissions

**Solution**: Run this first in Supabase SQL Editor:
```sql
CREATE SCHEMA IF NOT EXISTS csa;
GRANT ALL ON SCHEMA csa TO postgres;
```

---

## Connection Architecture

Phase 2 Sprint 2 uses **two types of database connections**:

### 1. Supabase REST API (via `supabase-py`)
**Used for**: Simple CRUD operations in Phase 1
```python
db.client.table("projects").select("*").execute()
```

### 2. Direct PostgreSQL Connection (via `psycopg2`)
**Used for**: Complex SQL queries, JSONB operations, PostgreSQL functions
```python
db.execute_query("SELECT * FROM csa.deliverable_schemas WHERE id = %s", (schema_id,))
```

Both connections use the same Supabase database - they're just different access methods.

---

## Security Best Practices

### 1. Connection String Security
- ✅ Store `DATABASE_URL` in `.env` file
- ✅ Add `.env` to `.gitignore`
- ❌ Never commit passwords to version control
- ❌ Never share connection strings publicly

### 2. Password Management
- Use strong, unique passwords for your database
- Rotate passwords regularly
- Consider using Supabase's connection pooler for production

### 3. Network Security
- Enable Row Level Security (RLS) on sensitive tables
- Use Supabase's built-in auth for user-facing features
- Limit database access to trusted IPs in production

---

## Production Deployment

For production environments:

### 1. Use Connection Pooling

Supabase provides a connection pooler for high-traffic applications:

```bash
# In .env for production
DATABASE_URL=postgresql://postgres:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Benefits:
- Handles many concurrent connections efficiently
- Reduces connection overhead
- Automatically manages connection lifecycle

### 2. Enable SSL Mode

For extra security, append `?sslmode=require` to your connection string:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.project.supabase.co:5432/postgres?sslmode=require
```

### 3. Use Environment-Specific Credentials

Maintain separate `.env` files for different environments:
- `.env.development`
- `.env.staging`
- `.env.production`

---

## Next Steps

After completing this setup:

1. ✅ Run the demo: `python demo_phase2_sprint2.py`
2. ✅ Run tests: `pytest tests/unit/services/ -v`
3. ✅ Create your first workflow schema using `SchemaService`
4. ✅ Execute workflows dynamically with `WorkflowOrchestrator`

---

## Additional Resources

- **Supabase Database Docs**: https://supabase.com/docs/guides/database
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **psycopg2 Tutorial**: https://www.psycopg.org/docs/
- **Phase 2 Sprint 2 Implementation Guide**: `PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md`

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Supabase logs in the Dashboard
3. Check Phase 2 Sprint 2 documentation
4. Verify all environment variables are set correctly

---

*Last Updated: 2025-12-20*
*Phase 2 Sprint 2: The Configuration Layer*
