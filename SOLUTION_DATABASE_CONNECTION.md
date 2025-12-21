# Solution: Database Connection Issue

## Current Situation

✅ **Database is configured** - Your screenshot shows tables exist in Supabase
✅ **SQL scripts were executed** - Tables like `audit_log`, `knowledge_chunks`, etc. are visible
✅ **Backend server is running** - Port 8000 is active
✅ **Frontend is running** - Port 3001 is active
❌ **Python backend can't connect** - Network unreachable (IPv6 issue)

## The Problem

Your system is trying to connect to Supabase using IPv6, but your network doesn't support it:

```
connection to server at "db.fqfifwrpgzaldmxatozs.supabase.co"
(2406:da18:243:741d:f0c8:4e4:332b:8e14), port 5432 failed:
Network is unreachable
```

## Quick Fix: Use Supabase Connection Pooler

The Connection Pooler has better network compatibility and often resolves IPv6 issues.

### Step 1: Get Your Pooler Connection String

1. Go to your Supabase Dashboard: https://app.supabase.com/
2. Select your project: `fqfifwrpgzaldmxatozs`
3. Navigate to: **Settings** → **Database**
4. Scroll to: **Connection String** section
5. Select: **"Connection Pooling"** (NOT "Session mode")
6. Click: **"URI"** tab
7. Copy the connection string (it will look like):

```
postgresql://postgres.fqfifwrpgzaldmxatozs:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 2: Update Your .env File

```bash
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
nano .env  # or use your preferred editor
```

**Replace this line:**
```
DATABASE_URL=postgresql://postgres:nikita_linkai11@db.fqfifwrpgzaldmxatozs.supabase.co:5432/postgres?sslmode=require
```

**With the pooler URL** (example - use YOUR actual password):
```
DATABASE_URL=postgresql://postgres.fqfifwrpgzaldmxatozs:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Important notes:**
- Port changes from `5432` → `6543`
- Hostname changes from `db.xxx` → `aws-0-xx.pooler.xxx`
- Username format changes from `postgres:password` → `postgres.project:password`
- Remove `?sslmode=require` from the end (pooler handles SSL automatically)

### Step 3: Restart the Backend

```bash
# Kill the current backend process
pkill -f "python main.py"

# Restart
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
python main.py
```

### Step 4: Verify the Connection

```bash
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
python check_database.py
```

You should see:
```
✅ Connection successful!
✅ CSA schema exists
📊 Tables in csa schema (3):
   ✓ csa.deliverable_schemas
   ✓ csa.workflow_executions
   ✓ csa.schema_version_history
```

### Step 5: Test the Frontend

1. Open browser: http://localhost:3001
2. Navigate to: **Workflows** page
3. The warning should disappear
4. You should see real workflows from the database (not `[DEMO]`)

---

## Alternative Solution: If Pooler Doesn't Work

If the connection pooler still doesn't work, you have two options:

### Option A: Add IPv4 Route (Advanced)

This requires system-level changes and may not be possible on all networks.

```bash
# Get the actual IPv4 address
dig +short db.fqfifwrpgzaldmxatozs.supabase.co A

# If it returns an IP like 3.xxx.xxx.xxx, add to /etc/hosts
sudo nano /etc/hosts

# Add line:
# 3.xxx.xxx.xxx db.fqfifwrpgzaldmxatozs.supabase.co
```

### Option B: Use Supabase REST API Only (Recommended if Pooler fails)

Modify the schema service to use the Supabase Python client (which uses HTTPS/REST) instead of direct PostgreSQL connection.

**Benefits:**
- Works over HTTPS (no network issues)
- Already working for Sprint 1-3 features
- No configuration changes needed

**Trade-offs:**
- Can't use complex SQL queries with JSONB operations
- Need to rewrite some queries to use Supabase client syntax

I can implement this if the pooler doesn't work.

---

## Checking Your Current Setup

### Verify CSA Schema Exists

Since you ran `init_phase2_sprint2.sql` in Supabase SQL Editor, the `csa` schema should exist.

**In Supabase Dashboard:**
1. Go to: **Table Editor**
2. Look for schema dropdown (currently showing "public")
3. Click it and select: **"csa"**
4. You should see tables:
   - `deliverable_schemas`
   - `workflow_executions`
   - `schema_version_history`

If you **don't see the csa schema**:
- The SQL script didn't run completely
- Re-run `init_phase2_sprint2.sql` in Supabase SQL Editor
- Check for errors in the SQL output

### Expected Database Structure

**public schema** (Sprint 1-3):
- `audit_log` ✓ (visible in your screenshot)
- `deliverables` ✓
- `documents` ✓
- `knowledge_chunks` ✓
- `projects` ✓
- `users` ✓

**csa schema** (Phase 2 Sprint 2):
- `deliverable_schemas` (workflow definitions)
- `workflow_executions` (execution history)
- `schema_version_history` (version control)

---

## Testing After Fix

Once connected, test the workflow system:

### Test 1: List Workflows

```bash
curl http://localhost:8000/api/v1/workflows/ | python3 -m json.tool
```

**Expected output:**
```json
[
  {
    "deliverable_type": "foundation_design",
    "display_name": "Isolated Footing Design",
    "discipline": "civil",
    "status": "active",
    "version": 1,
    "steps_count": 2,
    "created_at": "2025-12-20T...",
    "updated_at": "2025-12-20T..."
  }
]
```

### Test 2: Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/foundation_design/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "axial_load_dead": 600.0,
      "axial_load_live": 400.0,
      "column_width": 0.4,
      "column_depth": 0.4,
      "safe_bearing_capacity": 200.0,
      "concrete_grade": "M25",
      "steel_grade": "Fe415"
    },
    "user_id": "test_user"
  }'
```

### Test 3: Frontend

Visit http://localhost:3001/workflows

**You should see:**
- ✅ No warning banner
- ✅ Real workflow data from database
- ✅ "Foundation Design (IS 456)" workflow listed
- ✅ All CRUD operations working

---

## Summary

**Root Cause:** Network doesn't support IPv6 connection to Supabase

**Solution:** Use Supabase Connection Pooler (IPv4-compatible)

**Steps:**
1. Get pooler connection string from Supabase Dashboard
2. Update `backend/.env` with pooler URL
3. Restart backend server
4. Verify with `check_database.py`
5. Test frontend

**Time Required:** ~5 minutes

---

## Need Help?

If the pooler still doesn't work, let me know and I can:
1. Implement REST API fallback (uses HTTPS instead of PostgreSQL protocol)
2. Help debug network/firewall settings
3. Provide alternative connection methods

The good news is: **Your database is properly configured!** We just need to fix the network connectivity from Python to Supabase.
