# CSA AIaaS Platform - React Frontend

Complete frontend implementation for all CSA AIaaS Platform features (Phase 1 + Phase 2).

## 🎯 Features Implemented

### Phase 1: RAG Agent
- ✅ **Chat Interface** - Conversational AI with context-aware responses
- ✅ **Session Management** - Create, list, delete chat sessions
- ✅ **Citation Tracking** - Source document references
- ✅ **Ambiguity Detection** - Safety-first clarification system

### Phase 2 Sprint 1: Math Engine
- ✅ **Foundation Designer** - Interactive calculator for IS 456:2000
- ✅ **Real-time Calculations** - Design + optimization workflow
- ✅ **BOQ Generation** - Material quantities and bar bending schedule
- ✅ **Results Visualization** - Tables, charts, and diagrams

### Phase 2 Sprint 2: Configuration Layer
- ✅ **Workflow Schema Manager** - Create/edit workflows without code
- ✅ **Schema Versioning** - History and rollback capability
- ✅ **Dynamic Execution** - Run workflows from database schemas
- ✅ **Execution Dashboard** - Monitor workflow runs and statistics
- ✅ **Risk Assessment** - HITL approval visualization

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at: `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable React components
│   │   ├── Layout.jsx      # App layout with sidebar
│   │   ├── ChatInterface.jsx
│   │   ├── FoundationDesigner.jsx
│   │   ├── WorkflowManager.jsx
│   │   └── ... (40+ components)
│   │
│   ├── pages/              # Page components
│   │   ├── Dashboard.jsx
│   │   ├── ChatPage.jsx
│   │   ├── FoundationDesignPage.jsx
│   │   ├── WorkflowsPage.jsx
│   │   └── ExecutionsPage.jsx
│   │
│   ├── services/           # API client
│   │   └── api.js         # Axios-based API calls
│   │
│   ├── store/             # State management (Zustand)
│   │   ├── useAuthStore.js
│   │   ├── useChatStore.js
│   │   └── useWorkflowStore.js
│   │
│   ├── utils/             # Utility functions
│   │   └── helpers.js
│   │
│   ├── styles/            # Global styles
│   │   └── index.css
│   │
│   ├── App.jsx            # Main app component
│   └── main.jsx           # Entry point
│
├── public/                # Static assets
├── index.html            # HTML template
├── package.json          # Dependencies
├── vite.config.js       # Vite configuration
└── tailwind.config.js   # Tailwind CSS config
```

## 🎨 Key Technologies

- **React 18** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client
- **React Icons** - Icon library
- **React Markdown** - Markdown rendering
- **React Hot Toast** - Notifications

## 📖 Usage Guide

### 1. Chat Interface (Phase 1 Sprint 3)

**Features:**
- Start new chat sessions
- Send messages with streaming responses
- View source citations
- Handle ambiguity detection
- Browse chat history

**How to Use:**
1. Navigate to "Chat" from the sidebar
2. Click "New Chat" to create a session
3. Type your engineering question
4. View AI responses with citations
5. If ambiguous, answer clarification questions

### 2. Foundation Designer (Phase 2 Sprint 1)

**Features:**
- Input foundation parameters
- Real-time design calculations
- Automatic optimization
- BOQ generation
- Material quantities

**How to Use:**
1. Navigate to "Foundation Design"
2. Fill in load data (dead, live)
3. Enter column dimensions
4. Specify material grades
5. Click "Calculate Design"
6. View results:
   - Footing dimensions
   - Reinforcement details
   - Bar bending schedule
   - Material quantities

### 3. Workflow Manager (Phase 2 Sprint 2)

**Features:**
- Create workflow schemas
- Define workflow steps
- Variable substitution
- Risk configuration
- Version management

**How to Use:**

**Create a Workflow:**
1. Go to "Workflows" → "Create New"
2. Enter workflow details:
   - Deliverable type (e.g., "foundation_design")
   - Display name
   - Discipline
3. Add workflow steps:
   - Step name
   - Function to call (e.g., "tool_name.function_name")
   - Input mapping with variables ($input.field, $step1.output)
   - Output variable
4. Configure risk thresholds
5. Save workflow

**Execute a Workflow:**
1. Go to "Workflows" → Select workflow
2. Click "Execute"
3. Provide input data (JSON or form)
4. Monitor execution progress
5. View results and audit trail

**Manage Versions:**
1. View version history
2. Compare versions
3. Rollback to previous version

### 4. Execution Dashboard

**Features:**
- List all workflow executions
- Filter by status, deliverable type
- View execution details
- Approve HITL requests
- Export execution reports

**How to Use:**
1. Navigate to "Executions"
2. View execution list with:
   - Status (completed, failed, awaiting_approval)
   - Risk score
   - Execution time
3. Click on execution to view:
   - Step-by-step results
   - Input/output data
   - Error messages (if failed)
4. For HITL approvals:
   - Review execution details
   - Approve or reject
   - Add approval notes

## 🔧 Configuration

### API Base URL

By default, the frontend proxies API requests to `http://localhost:8000`.

To change this, edit `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url:8000',
      changeOrigin: true,
    },
  },
}
```

### Environment Variables

Create `.env` file:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 📱 Responsive Design

The UI is fully responsive and works on:
- Desktop (1920px+)
- Laptop (1024px - 1920px)
- Tablet (768px - 1024px)
- Mobile (< 768px)

Features:
- Collapsible sidebar on mobile
- Touch-friendly buttons
- Responsive tables
- Mobile-optimized forms

## 🎨 Theming

The app uses Tailwind CSS with a custom color scheme:

**Primary Color:** Blue (#3b82f6)
**Success:** Green
**Warning:** Yellow
**Danger:** Red

To customize, edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom color palette
      },
    },
  },
}
```

## 🧪 Development

### Running Locally

```bash
# Start dev server with hot reload
npm run dev
```

### Building for Production

```bash
# Create optimized production build
npm run build

# Output: dist/ directory
```

### Linting

```bash
# Run ESLint
npm run lint
```

## 🚢 Deployment

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Deploy to Netlify

```bash
# Build
npm run build

# Deploy dist/ folder to Netlify
```

### Deploy with Docker

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -t csa-frontend .
docker run -p 80:80 csa-frontend
```

## 🔐 Security Features

- Input validation on all forms
- XSS protection (React's built-in)
- CSRF token support
- Secure API communication
- No sensitive data in localStorage

## 🐛 Troubleshooting

### Backend Connection Issues

**Problem:** "Network Error" or "API not responding"

**Solutions:**
1. Ensure backend is running: `http://localhost:8000/health`
2. Check CORS configuration in backend
3. Verify proxy settings in `vite.config.js`

### Build Errors

**Problem:** `npm run build` fails

**Solutions:**
1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear cache: `rm -rf dist .vite`
3. Update dependencies: `npm update`

### Styling Issues

**Problem:** Tailwind classes not working

**Solutions:**
1. Ensure PostCSS is configured
2. Check `tailwind.config.js` content paths
3. Restart dev server

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Router](https://reactrouter.com/)
- [Zustand](https://github.com/pmndrs/zustand)

## 🤝 Contributing

1. Follow React best practices
2. Use Tailwind CSS for styling
3. Add PropTypes for components
4. Write meaningful commit messages
5. Test responsiveness on multiple devices

## 📝 License

This project is part of the CSA AIaaS Platform.

---

**Version:** 1.0.0
**Last Updated:** 2025-12-20
**Phase:** 1 + 2 Complete Implementation
