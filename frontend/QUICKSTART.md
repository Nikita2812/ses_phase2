# CSA AIaaS Platform Frontend - Quick Start Guide

## 🚀 Complete Frontend in 5 Minutes

This guide will get you up and running with the complete React frontend for all features (Phase 1 + Phase 2).

---

## Step 1: Install Dependencies

```bash
cd frontend
npm install
```

This installs:
- React 18
- React Router
- Tailwind CSS
- Axios
- Zustand (state management)
- React Icons
- React Markdown
- React Hot Toast

---

## Step 2: Verify Backend is Running

The frontend needs the backend API running:

```bash
# In another terminal, from backend/ directory
python main.py
```

Backend should be accessible at: `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/health
```

---

## Step 3: Start Frontend Development Server

```bash
npm run dev
```

The app will start at: **http://localhost:3000**

---

## 🎯 What's Included

### Implemented Features

✅ **Dashboard** - Overview of all features and statistics
✅ **Chat Interface** - Full conversational RAG with citations
✅ **Foundation Designer** - IS 456:2000 calculator with BOQ
✅ **Workflow Manager** - Create/edit workflows without code
✅ **Execution Dashboard** - Monitor workflow runs
✅ **Settings** - Configuration and preferences

### Pages Available

1. `/dashboard` - Main dashboard
2. `/chat` - Chat interface
3. `/foundation-design` - Foundation calculator
4. `/workflows` - Workflow schema manager
5. `/executions` - Execution monitoring
6. `/settings` - App settings

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Layout.jsx   # Main layout with sidebar
│   │   ├── Chat/        # Chat components
│   │   ├── Foundation/  # Foundation design components
│   │   └── Workflow/    # Workflow management components
│   │
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx
│   │   ├── ChatPage.jsx
│   │   ├── FoundationDesignPage.jsx
│   │   ├── WorkflowsPage.jsx
│   │   ├── ExecutionsPage.jsx
│   │   └── SettingsPage.jsx
│   │
│   ├── services/        # API client
│   │   └── api.js      # All API endpoints
│   │
│   ├── store/          # State management (Zustand)
│   │   ├── useAuthStore.js
│   │   ├── useChatStore.js
│   │   └── useWorkflowStore.js
│   │
│   ├── utils/          # Helper functions
│   ├── styles/         # Global CSS
│   ├── App.jsx         # Main app
│   └── main.jsx        # Entry point
│
├── public/             # Static files
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

---

## 🎨 Features Overview

### 1. Chat Interface (Phase 1 Sprint 3)

**Location**: `/chat`

**Features**:
- Create new chat sessions
- Send messages with streaming responses
- View source citations
- Handle ambiguity detection
- Browse chat history

**How to Use**:
1. Click "New Chat"
2. Type your engineering question
3. View AI response with citations
4. Continue conversation

### 2. Foundation Designer (Phase 2 Sprint 1)

**Location**: `/foundation-design`

**Features**:
- Input foundation parameters
- Real-time calculations
- Automatic optimization
- BOQ generation
- Material quantities

**Input Fields**:
- Dead Load (kN)
- Live Load (kN)
- Column Dimensions
- Safe Bearing Capacity
- Material Grades

**Output**:
- Footing dimensions
- Reinforcement details
- Bar bending schedule
- Material quantities (concrete, steel, formwork)

### 3. Workflow Manager (Phase 2 Sprint 2)

**Location**: `/workflows`

**Features**:
- Create workflow schemas
- Edit existing workflows
- Version management
- Execute workflows
- View statistics

**Workflow Schema Includes**:
- Workflow steps
- Variable substitution ($input.*, $step*.*)
- Risk configuration
- Error handling
- Conditional execution

### 4. Execution Dashboard

**Location**: `/executions`

**Features**:
- View all workflow executions
- Filter by status/type
- Execution details
- HITL approval
- Export reports

**Execution Statuses**:
- ✅ Completed
- ⏳ Running
- ❌ Failed
- 🔍 Awaiting Approval
- ✔️ Approved
- ❌ Rejected

---

## 🔧 Configuration

### Environment Variables

Create `.env` in `frontend/` directory:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Proxy Configuration

Already configured in `vite.config.js`:

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

---

## 🎯 Quick Usage Examples

### Example 1: Chat with AI

1. Go to `/chat`
2. Click "New Chat"
3. Ask: "How do I design a foundation for 600 kN dead load?"
4. Get AI response with IS 456:2000 guidance

### Example 2: Design a Foundation

1. Go to `/foundation-design`
2. Enter:
   - Dead Load: 600 kN
   - Live Load: 400 kN
   - Column: 0.4m × 0.4m
   - SBC: 200 kN/m²
3. Click "Calculate Design"
4. View results and BOQ

### Example 3: Create a Workflow

1. Go to `/workflows`
2. Click "Create New Workflow"
3. Fill in details:
   - Type: `my_foundation_design`
   - Name: "My Foundation Design Workflow"
   - Discipline: Civil
4. Add steps:
   - Step 1: Design
   - Step 2: Optimize
5. Save workflow
6. Execute with input data

### Example 4: Monitor Executions

1. Go to `/executions`
2. View all workflow runs
3. Click on execution to see details
4. Approve HITL requests if needed

---

## 🐛 Troubleshooting

### Problem: "Network Error"

**Cause**: Backend not running or wrong URL

**Solution**:
```bash
# Check backend health
curl http://localhost:8000/health

# If failed, start backend
cd backend && python main.py
```

### Problem: Blank page / White screen

**Cause**: Build or dependency issues

**Solution**:
```bash
# Clear cache and rebuild
rm -rf node_modules dist .vite
npm install
npm run dev
```

### Problem: Tailwind styles not working

**Cause**: PostCSS not configured

**Solution**:
```bash
# Restart dev server
npm run dev
```

### Problem: CORS errors

**Cause**: Backend CORS not configured for frontend

**Solution**: Add to `backend/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📱 Responsive Design

The UI is fully responsive:

- **Desktop** (1920px+): Full sidebar, multi-column layout
- **Laptop** (1024px - 1920px): Standard layout
- **Tablet** (768px - 1024px): Collapsible sidebar
- **Mobile** (< 768px): Hamburger menu, single column

---

## 🚢 Production Build

### Build for Production

```bash
npm run build
```

Output: `dist/` directory

### Preview Production Build

```bash
npm run preview
```

### Deploy to Vercel

```bash
npm i -g vercel
vercel
```

### Deploy to Netlify

1. Build: `npm run build`
2. Upload `dist/` to Netlify

---

## 📚 Additional Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Clear cache
rm -rf node_modules .vite dist
```

---

## ✅ Checklist

Before starting:

- [ ] Node.js 18+ installed
- [ ] Backend running on port 8000
- [ ] `npm install` completed
- [ ] `.env` file created (optional)
- [ ] Port 3000 available

To verify setup:

```bash
# Check Node version
node --version  # Should be 18+

# Check backend
curl http://localhost:8000/health

# Start frontend
npm run dev
```

---

## 🎓 Next Steps

1. **Explore the Dashboard** - Get overview of all features
2. **Try the Chat** - Ask engineering questions
3. **Design a Foundation** - Use the calculator
4. **Create a Workflow** - Test configuration over code
5. **Monitor Executions** - View workflow runs

---

## 📞 Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify backend is running
3. Check browser console for errors
4. Review `vite.config.js` proxy settings

---

## 🎉 You're Ready!

Your complete CSA AIaaS Platform frontend is ready to use with all features from Phase 1 and Phase 2.

```bash
npm run dev
```

Visit: **http://localhost:3000**

Enjoy! 🚀

---

*Last Updated: 2025-12-20*
*Version: 1.0.0 - Complete Implementation*
