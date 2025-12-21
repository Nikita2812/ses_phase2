# Phase 2 Sprint 4: Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- PostgreSQL database (Supabase)
- Python 3.11+ with venv activated
- Node.js 18+ for frontend
- Backend and frontend dependencies installed

---

## Step 1: Database Setup (2 minutes)

```bash
# Navigate to project root
cd /home/nikita/Documents/The\ LinkAI/new_proj

# Run Sprint 4 schema
psql -U postgres -d your_database_name < backend/init_phase2_sprint4.sql

# Verify tables created
psql -U postgres -d your_database_name -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'csa'
  AND table_name LIKE '%approval%';"
```

**Expected Output:**
```
 table_name
------------------
 approval_requests
 approval_history
 approvers
(3 rows)
```

---

## Step 2: Start Backend (1 minute)

```bash
cd backend
source venv/bin/activate
python main.py
```

**Expected Output:**
```
Starting CSA AIaaS Platform v1.0.0
✓ Configuration validated successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test API:**
```bash
curl http://localhost:8000/api/v1/approvals/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "approval_workflow",
  "version": "1.0.0"
}
```

---

## Step 3: Start Frontend (1 minute)

```bash
# In a new terminal
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## Step 4: Access Approval Dashboard (1 minute)

**Open browser:**
```
http://localhost:5173/approvals
```

**You should see:**
- Statistics cards (pending approvals, reviewed today, etc.)
- Empty state if no approvals yet
- "Refresh" button to reload

---

## Step 5: Test the System

### Option A: Via API

```bash
# 1. Create a high-risk workflow execution (this would trigger approval)
curl -X POST http://localhost:8000/api/v1/workflows/foundation_design/execute \
  -H "Content-Type: application/json" \
  -d '{
    "axial_load_dead": 600,
    "axial_load_live": 400,
    "column_width": 0.4,
    "column_depth": 0.4,
    "safe_bearing_capacity": 150,
    "concrete_grade": "M20",
    "steel_grade": "Fe415"
  }'

# 2. Check pending approvals
curl http://localhost:8000/api/v1/approvals/pending

# 3. Get approver stats
curl http://localhost:8000/api/v1/approvals/approvers/me/stats
```

### Option B: Via Frontend

1. **Navigate to Workflows page:**
   ```
   http://localhost:5173/workflows
   ```

2. **Execute a foundation design workflow:**
   - Click "Execute" on foundation_design
   - Enter parameters
   - Submit

3. **Check Approvals page:**
   ```
   http://localhost:5173/approvals
   ```
   - Should show new pending approval if risk > 0.9

4. **Review and approve:**
   - Click "View Details"
   - Click "✓ Approve"
   - Add notes
   - Submit

---

## Key URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | React app |
| **Approvals Dashboard** | http://localhost:5173/approvals | HITL approval UI |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Approval Health** | http://localhost:8000/api/v1/approvals/health | Health check |

---

## Sample Approvers (Pre-configured)

The database includes 5 sample approvers:

| User ID | Name | Discipline | Seniority | Max Risk |
|---------|------|------------|-----------|----------|
| `approver_civil_junior` | Rajesh Kumar | Civil | 1 | 0.6 |
| `approver_civil_senior` | Priya Sharma | Civil | 2 | 0.85 |
| `approver_structural_senior` | Amit Patel | Structural | 2 | 0.85 |
| `approver_principal` | Dr. Anjali Verma | All | 3 | 0.95 |
| `approver_director` | S. Venkatesh | All | 4 | 1.0 |

---

## Risk Score Ranges

| Risk Score | Level | Action | Approver Required |
|------------|-------|--------|-------------------|
| 0.0 - 0.3 | Low | Auto Approve | None |
| 0.3 - 0.6 | Medium | Optional Review | Junior+ |
| 0.6 - 0.9 | High | Recommended Review | Senior+ |
| 0.9 - 1.0 | Critical | **Mandatory HITL** | Principal+ |

---

## Common Commands

### Check Approval Status

```bash
# Get all pending approvals
curl http://localhost:8000/api/v1/approvals/pending

# Get specific approval
curl http://localhost:8000/api/v1/approvals/{approval_id}

# Get approver statistics
curl http://localhost:8000/api/v1/approvals/approvers/me/stats
```

### Approve a Design

```bash
curl -X POST http://localhost:8000/api/v1/approvals/{approval_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve", "notes": "Reviewed and approved"}'
```

### Reject a Design

```bash
curl -X POST http://localhost:8000/api/v1/approvals/{approval_id}/reject \
  -H "Content-Type: application/json" \
  -d '{"decision": "reject", "notes": "Shear capacity insufficient"}'
```

### Request Revision

```bash
curl -X POST http://localhost:8000/api/v1/approvals/{approval_id}/request-revision \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "revision",
    "revision_notes": "Please increase footing depth to 0.8m and recalculate"
  }'
```

---

## Database Queries

### View Pending Approvals

```sql
SELECT
    id,
    deliverable_type,
    risk_score,
    status,
    assigned_to,
    created_at
FROM csa.approval_requests
WHERE status IN ('assigned', 'in_review')
ORDER BY priority, created_at;
```

### View Approval History

```sql
SELECT
    ar.deliverable_type,
    ar.risk_score,
    ah.action,
    ah.performed_by,
    ah.created_at
FROM csa.approval_history ah
JOIN csa.approval_requests ar ON ar.id = ah.approval_request_id
ORDER BY ah.created_at DESC
LIMIT 20;
```

### View Approver Workload

```sql
SELECT
    a.full_name,
    a.seniority_level,
    COUNT(*) FILTER (WHERE ar.status IN ('assigned', 'in_review')) as pending,
    a.total_approvals,
    a.avg_review_time_hours
FROM csa.approvers a
LEFT JOIN csa.approval_requests ar ON ar.assigned_to = a.user_id
WHERE a.is_active = true
GROUP BY a.id
ORDER BY pending DESC;
```

---

## Troubleshooting

### Issue: "No approvals showing"

**Solution:**
1. Create a high-risk execution first
2. Check database: `SELECT * FROM csa.approval_requests;`
3. Verify risk score > 0.9 in execution

### Issue: "Approver not found"

**Solution:**
1. Check approvers table: `SELECT * FROM csa.approvers;`
2. Run init_phase2_sprint4.sql to insert sample approvers
3. Ensure approver has correct discipline and max_risk_score

### Issue: "API returns 500 error"

**Solution:**
1. Check backend logs
2. Verify database connection in .env
3. Ensure all tables created: `\dt csa.*`
4. Check Python dependencies installed

### Issue: "Frontend not loading"

**Solution:**
1. Check Node.js version: `node --version` (need 18+)
2. Reinstall dependencies: `npm install`
3. Clear cache: `rm -rf node_modules/.vite`
4. Restart dev server

---

## Next Steps

1. **Execute workflows** and watch approvals flow
2. **Test approval actions** (approve/reject/revision)
3. **Monitor statistics** on dashboard
4. **Review audit trail** in approval_history table
5. **Customize risk thresholds** in database

---

## Support

- **Design Doc**: PHASE2_SPRINT4_DESIGN.md
- **Implementation Summary**: PHASE2_SPRINT4_IMPLEMENTATION_SUMMARY.md
- **Main README**: CLAUDE.md
- **API Docs**: http://localhost:8000/docs (when running)

---

**Happy Approving! 🎉**
