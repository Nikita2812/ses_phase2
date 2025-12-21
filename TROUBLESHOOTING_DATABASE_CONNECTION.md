# Database Connection Troubleshooting Guide

## Current Status

✅ **SQL Schema Initialized**: The `init_phase2_sprint2.sql` script ran successfully
✅ **Data Inserted**: The `foundation_design` workflow is in the database
✅ **Backend Running**: FastAPI server is running on port 8000
✅ **Frontend Running**: Vite dev server is running on port 3001
❌ **Backend → Database Connection**: Python backend cannot connect to Supabase

## The Issue

The JSON output you saw was **NOT an error** - it was the successful result of running this query:

```sql
SELECT
    deliverable_type,
    jsonb_pretty(workflow_steps) as workflow_definition
FROM csa.deliverable_schemas
WHERE deliverable_type = 'foundation_design';
```

The actual problem is that the Python backend process cannot connect to your Supabase database due to network connectivity issues (IPv6/IPv4 resolution).

## Solution Options

### Option 1: Use Supabase Connection Pooler (Recommended)

Supabase provides a connection pooler that often has better network compatibility.

1. **Get your pooler connection string** from Supabase Dashboard:
   - Go to: Project Settings → Database → Connection String
   - Select: **"Connection Pooling"** (not "Session mode")
   - Copy the connection string (it will include `/pooler` in the hostname)

2. **Update your `.env` file**:
   ```bash
   cd backend
   nano .env  # or use your preferred editor
   ```

3. **Replace the `DATABASE_URL`** with the pooler URL:
   ```
   # Old (direct connection):
   DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

   # New (connection pooler):
   DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

4. **Restart the backend**:
   ```bash
   pkill -f "python main.py"
   cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
   python main.py
   ```

### Option 2: Test Connection from Python

Verify the connection string works from Python:

```bash
cd backend
python3 << 'EOF'
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('DATABASE_URL')

print(f"Testing connection to: {db_url[:50]}...")

try:
    conn = psycopg2.connect(db_url, connect_timeout=10)
    print("✅ Connection successful!")

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM csa.deliverable_schemas")
    count = cursor.fetchone()[0]
    print(f"✅ Found {count} workflow schemas in database")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

### Option 3: Use IPv4-Only Connection

If your system doesn't support IPv6, force IPv4 DNS resolution:

```bash
# Get the IPv4 address of your Supabase host
host -4 -t A db.xxxxx.supabase.co

# Add to /etc/hosts (requires sudo)
sudo nano /etc/hosts

# Add line:
# xxx.xxx.xxx.xxx db.xxxxx.supabase.co
```

### Option 4: Use Supabase REST API Instead

If PostgreSQL direct connection continues to fail, you can modify the schema service to use the Supabase REST API:

```python
# This uses the Supabase client (already working in your setup)
# instead of raw SQL queries via psycopg2
```

This requires modifying [backend/app/services/schema_service.py](backend/app/services/schema_service.py) to use the Supabase client instead of direct SQL.

## Verify the Fix

After trying any of the above solutions, test with:

```bash
# Test the API
curl http://localhost:8000/api/v1/workflows/

# Should return:
# [
#   {
#     "deliverable_type": "foundation_design",
#     "display_name": "Isolated Footing Design",
#     "discipline": "civil",
#     "status": "active",
#     "version": 1,
#     "steps_count": 2,
#     ...
#   }
# ]
```

## What's Working vs. What's Not

| Component | Status | Notes |
|-----------|--------|-------|
| Database Schema | ✅ Working | Tables created, data inserted |
| Supabase REST API | ✅ Working | Used by Sprint 1-3 features |
| PostgreSQL Direct Connection | ❌ Failing | Used by Phase 2 Sprint 2 features |
| Backend Server | ✅ Running | Port 8000 |
| Frontend Server | ✅ Running | Port 3001 |
| Error Handling | ✅ Improved | Shows helpful setup instructions |

## Background: Why Two Connection Methods?

Your application uses two different connection methods:

1. **Supabase Client (REST API)**: Used in Sprint 1-3
   - Works via HTTPS
   - Already functional
   - Used for: `projects`, `deliverables`, `audit_log`, `knowledge_chunks`

2. **PostgreSQL Direct Connection**: Added in Phase 2 Sprint 2
   - Works via PostgreSQL protocol (port 5432 or 6543)
   - Currently failing due to network issues
   - Used for: `csa.deliverable_schemas`, `csa.workflow_executions`

The workflow management features (Phase 2 Sprint 2) require direct PostgreSQL connection because they use advanced SQL queries with JSONB operations that aren't easily available via the Supabase REST API.

## Next Steps

1. **Try Option 1** (Connection Pooler) - this usually works
2. **Test with Option 2** to verify the connection string
3. **If still failing**, check your network firewall/proxy settings
4. **Last resort**: Consider implementing Option 4 to use Supabase REST API instead

## Need Help?

The frontend now shows clear setup instructions. Once the database connection is working, you'll see:
- Real workflows from the database (not `[DEMO]` samples)
- No warning banner
- Full CRUD operations working
