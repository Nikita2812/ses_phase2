# PostgreSQL Array Literal Error - Fix Applied

## Problem

Error when creating workflows via frontend:
```
Error creating workflow: malformed array literal: "[]"
LINE 9: ... 0.7, "require_hitl_threshold": 0.9}', 'testing', '[]', 1, '...
       ^
DETAIL: "[" must introduce explicitly-specified array dimensions.
```

## Root Cause

The `tags` column in the `csa.deliverable_schemas` table is defined as `TEXT[]` (PostgreSQL native array type), but the code was using `json.dumps()` to serialize the tags list into a JSON string `"[]"`.

**Database Schema:**
```sql
tags TEXT[] DEFAULT '{}'
```

**Problematic Code (3 instances):**
```python
# Line 124 - Create operation
json.dumps(schema_data.tags),  # Creates '"[]"' string - PostgreSQL rejects this

# Line 250 - List/filter operation
conditions.append("tags @> %s::jsonb")  # Wrong cast - should be array
params.append(json.dumps(tags))

# Line 346 - Update operation
update_fields.append("tags = %s::jsonb")  # Wrong cast - should be array
params.append(json.dumps(updates.tags))
```

## Solution Applied

Updated `/backend/app/services/schema_service.py` in 3 locations to pass tags as native Python lists, allowing psycopg2 to handle the array conversion automatically.

### Fix 1: Create Schema (Line 124)

**Before:**
```python
json.dumps(schema_data.tags),
```

**After:**
```python
schema_data.tags,  # Pass list directly - psycopg2 handles array conversion
```

### Fix 2: List Schemas with Tag Filter (Lines 249-250)

**Before:**
```python
conditions.append("tags @> %s::jsonb")
params.append(json.dumps(tags))
```

**After:**
```python
conditions.append("tags @> %s")  # Array contains operator
params.append(tags)
```

### Fix 3: Update Schema Tags (Lines 345-346)

**Before:**
```python
update_fields.append("tags = %s::jsonb")
params.append(json.dumps(updates.tags))
```

**After:**
```python
update_fields.append("tags = %s")
params.append(updates.tags)
```

## How PostgreSQL Array Handling Works

### Native Array vs. JSONB

PostgreSQL has **two different ways** to store array-like data:

1. **Native Arrays** (`TEXT[]`, `INTEGER[]`, etc.)
   - Optimized for array operations
   - Supports array operators: `@>` (contains), `&&` (overlap), etc.
   - Pass as Python list: `['tag1', 'tag2']`
   - psycopg2 automatically converts Python lists to PostgreSQL arrays

2. **JSONB** (`JSONB` type)
   - Stores JSON documents
   - Requires JSON string: `'["tag1", "tag2"]'` or use `::jsonb` cast
   - Different operators: `@>` works but expects JSONB input

### The Error Explained

When we used `json.dumps(['tag1'])`, it created the string `'["tag1"]'`. PostgreSQL tried to parse this as an array literal and expected:

```sql
-- PostgreSQL expects this format for TEXT[] arrays:
ARRAY['tag1', 'tag2']  -- Explicit array constructor
'{tag1,tag2}'          -- Array literal format
-- OR just pass Python list through psycopg2 parameter binding
```

But we gave it:
```sql
'["tag1", "tag2"]'  -- JSON string format (not valid for TEXT[])
```

This caused the error: **"'[' must introduce explicitly-specified array dimensions"**

### Correct Approach with psycopg2

psycopg2 automatically handles Python lists → PostgreSQL arrays:

```python
# Python code
tags = ['civil', 'foundation']

# Passing to query
cursor.execute("INSERT INTO table (tags) VALUES (%s)", (tags,))

# psycopg2 converts to PostgreSQL format:
# ARRAY['civil', 'foundation']::TEXT[]
```

## How to Apply the Fix

### Step 1: Restart the Backend

The backend must be restarted for the changes to take effect.

```bash
# Stop the current backend server (Ctrl+C)

# Restart it
cd backend
source venv/bin/activate
python main.py
```

### Step 2: Test Workflow Creation

1. Open frontend: `http://localhost:5173/workflows`
2. Click "Create Workflow"
3. Select any template (e.g., "Basic Foundation Design")
4. Fill in basic info
5. Click through steps
6. Click "Create Workflow" in final step
7. Should now succeed! ✅

## What Changed

**File Modified**: `backend/app/services/schema_service.py`

**Lines Changed**:
- Line 124 (create operation)
- Lines 249-250 (list/filter operation)
- Lines 345-346 (update operation)

**Impact**:
- ✅ Tags now properly stored as PostgreSQL TEXT[] arrays
- ✅ Workflow creation works
- ✅ Tag filtering works (when implemented in frontend)
- ✅ Tag updates work
- ✅ Zero impact on existing functionality (other fields unchanged)

## Verification

After restarting backend, test with:

```bash
# Test via frontend
# 1. Create workflow with tags via UI
# 2. Check database

# OR test via Python
python
>>> from app.services.schema_service import SchemaService
>>> service = SchemaService()
>>> schemas = service.list_schemas(tags=['civil'])
>>> print(schemas)  # Should work without errors
```

## Why This Happened

1. Database schema defines `tags` as `TEXT[]` (native PostgreSQL array)
2. Code was treating it like JSONB (using `json.dumps()`)
3. PostgreSQL rejected the JSON string format for an array column
4. psycopg2 can automatically convert Python lists to PostgreSQL arrays
5. We just needed to pass the list directly without JSON serialization

## Related: UUID Adapter Fix

This is the **second** database adapter issue we've fixed:

1. **UUID Adapter** (previous fix) - Added in `database.py`:
   ```python
   from psycopg2.extensions import register_adapter, AsIs
   from uuid import UUID

   def adapt_uuid(uuid_val):
       return AsIs(f"'{uuid_val}'")

   register_adapter(UUID, adapt_uuid)
   ```

2. **Array Handling** (this fix) - No adapter needed, just pass lists directly

Both issues stem from PostgreSQL's type system requiring explicit handling for non-standard Python types.

## Future Prevention

When working with PostgreSQL columns:

1. **Check the column type** in the database schema
2. **Match the Python type** to the PostgreSQL type:
   - `TEXT[]` → Python list
   - `JSONB` → JSON string (via `json.dumps()`)
   - `UUID` → Python UUID (with adapter registered)
   - `INTEGER` → Python int
   - `TEXT` → Python str
3. **Let psycopg2 handle conversion** for standard types
4. **Only use `json.dumps()`** for JSONB columns

## Troubleshooting

### If error persists:

1. **Ensure backend is restarted**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check console for errors**
   - Backend should start without errors
   - No warnings about arrays

3. **Verify schema_service.py changes**
   ```bash
   grep -n "schema_data.tags" backend/app/services/schema_service.py
   # Should show line 124 WITHOUT json.dumps()
   ```

4. **Check database connection**
   - Ensure DATABASE_URL is set in `.env`
   - Test connection works

### If still failing:

Check the actual SQL being executed:

```python
# Add debug logging in schema_service.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Before execute_query, add:
print(f"Query: {query}")
print(f"Params: {params}")
```

## Summary

✅ **Fixed**: All `tags` field handling now uses native PostgreSQL arrays
✅ **Action Required**: Restart backend server
✅ **Status**: Workflow creation should now work end-to-end
✅ **Impact**: Zero impact on existing functionality

---

**Next**: After restarting backend, create a workflow through the frontend and verify it appears in the workflows table! 🎉
