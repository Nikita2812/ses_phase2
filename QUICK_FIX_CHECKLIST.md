# Quick Fix Checklist - Database Connection

## Issue Summary
Frontend shows: "Database connection failed"
**Cause**: Python backend can't connect to Supabase (IPv6 network issue)
**Solution**: Use Supabase Connection Pooler

---

## ✅ Step-by-Step Fix (5 minutes)

### 1. Get Pooler Connection String

```
📍 Supabase Dashboard → Your Project → Settings → Database
   → Connection String → "Connection Pooling" → URI
```

**Copy the string that looks like:**
```
postgresql://postgres.fqfifwrpgzaldmxatozs:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### 2. Update backend/.env

```bash
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
nano .env
```

**Find this line:**
```
DATABASE_URL=postgresql://postgres:nikita_linkai11@db.fqfifwrpgzaldmxatozs.supabase.co:5432/postgres?sslmode=require
```

**Replace with pooler URL:**
```
DATABASE_URL=postgresql://postgres.fqfifwrpgzaldmxatozs:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Save and exit** (Ctrl+X, Y, Enter)

### 3. Restart Backend

```bash
pkill -f "python main.py"
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
python main.py &
```

### 4. Verify Connection

```bash
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
python check_database.py
```

**Expected output:**
```
✅ Connection successful!
✅ CSA schema exists
📋 Workflow schemas defined: 1
```

### 5. Test Frontend

Open browser: http://localhost:3001/workflows

**You should see:**
- ✅ No warning
- ✅ "Foundation Design (IS 456)" workflow
- ✅ Status: active, Version: 1

---

## If It Still Doesn't Work

Run this diagnostic:

```bash
cd /home/nikita/Documents/The\ LinkAI/new_proj/backend
python check_database.py 2>&1 | tee /tmp/db_check.log
cat /tmp/db_check.log
```

Then share the output so I can help further.

---

## Alternative: Check if CSA Schema Exists

If you want to verify the database is properly set up through Supabase UI:

1. **Supabase Dashboard** → **Table Editor**
2. Click schema dropdown (currently shows "public")
3. Select **"csa"**
4. You should see 3 tables:
   - `deliverable_schemas`
   - `workflow_executions`
   - `schema_version_history`

If you **don't see "csa"** in the dropdown:
```bash
# Re-run the initialization script in Supabase SQL Editor
# File: backend/init_phase2_sprint2.sql
```

---

## Quick Test Commands

After fixing connection, test these:

```bash
# Test 1: List workflows
curl http://localhost:8000/api/v1/workflows/

# Test 2: Health check
curl http://localhost:8000/health

# Test 3: Workflow health
curl http://localhost:8000/api/v1/workflows/health/check
```

All should return JSON (not errors).

---

## Files Created to Help You

1. **[SOLUTION_DATABASE_CONNECTION.md](SOLUTION_DATABASE_CONNECTION.md)** - Detailed solution guide
2. **[TROUBLESHOOTING_DATABASE_CONNECTION.md](TROUBLESHOOTING_DATABASE_CONNECTION.md)** - Troubleshooting guide
3. **[backend/check_database.py](backend/check_database.py)** - Diagnostic script
4. **This file** - Quick checklist

---

## What's Actually Wrong?

**Technical explanation:**
- Your system is trying IPv6: `2406:da18:243:741d:f0c8:4e4:332b:8e14`
- But your network doesn't route IPv6
- Connection Pooler uses IPv4, so it works

**Why Supabase SQL Editor works but Python doesn't:**
- Supabase UI uses HTTPS/REST API (works fine)
- Python backend uses PostgreSQL wire protocol (IPv6 issue)

**The fix changes:**
- Port: 5432 → 6543 (pooler port)
- Host: `db.xxx` → `pooler.xxx`
- Removes IPv6 from the equation

---

That's it! 5 minutes and your database connection should work perfectly. 🚀
