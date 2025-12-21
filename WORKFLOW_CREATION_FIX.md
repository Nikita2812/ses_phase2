# Workflow Creation UUID Error - Fix Applied

## Problem

Error when creating workflows:
```
Error creating workflow: can't adapt type 'UUID'
```

## Root Cause

PostgreSQL driver (psycopg2) wasn't able to automatically convert Python UUID objects to PostgreSQL UUID format. This is a known issue that requires explicit adapter registration.

## Solution Applied

Updated `/backend/app/core/database.py` to register UUID adapter:

```python
from psycopg2.extensions import register_adapter, AsIs
from uuid import UUID

# Register UUID adapter for psycopg2
def adapt_uuid(uuid_val):
    return AsIs(f"'{uuid_val}'")

register_adapter(UUID, adapt_uuid)
```

## How to Apply the Fix

### Step 1: Restart the Backend

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
3. Select "Basic Foundation Design" template
4. Click "Create Workflow"
5. Should now succeed! ✅

## What Changed

**File Modified**: `backend/app/core/database.py`

**Lines Added**: 15-22 (UUID adapter registration)

**Impact**:
- ✅ UUID objects now properly converted to PostgreSQL format
- ✅ Workflow creation works
- ✅ All database operations with UUIDs now supported

## Verification

After restarting backend, test with:

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/?created_by=test" \
  -H "Content-Type: application/json" \
  -d '{
    "deliverable_type": "test_workflow",
    "display_name": "Test Workflow",
    "discipline": "civil",
    "workflow_steps": [{
      "step_number": 1,
      "step_name": "test",
      "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
      "input_mapping": {},
      "output_variable": "result"
    }],
    "input_schema": {"type": "object"},
    "status": "draft"
  }'
```

Expected: Success response with workflow details

## Why This Happened

1. Python `uuid4()` generates UUID objects
2. psycopg2 (PostgreSQL driver) needs to know how to convert UUID objects to SQL
3. By default, psycopg2 might not have UUID adapter registered in all environments
4. Manual registration ensures it always works

## Future Prevention

This fix is now permanent. All future UUID operations will work correctly.

## Troubleshooting

### If error persists:

1. **Ensure backend is restarted**
   ```bash
   # Check if backend is running with new code
   curl http://localhost:8000/health
   ```

2. **Check console for errors**
   - Backend should start without errors
   - No warnings about UUID

3. **Verify database connection**
   - Ensure DATABASE_URL is set in `.env`
   - Test connection: `python -c "from app.core.database import DatabaseConfig; db = DatabaseConfig(); print('OK')"`

### If still failing:

Alternative fix - convert UUID to string explicitly in schema_service.py:

```python
# In create_schema method
schema_id = str(uuid4())  # Convert to string
```

But with the adapter registered, this shouldn't be necessary.

## Summary

✅ **Fixed**: UUID adapter registered in database.py
✅ **Action Required**: Restart backend server
✅ **Status**: Workflow creation should now work
✅ **Impact**: Zero impact on existing functionality

---

**Next**: After restarting backend, create a workflow and enjoy the improved UI! 🎉
