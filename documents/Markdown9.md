**To the Frontend Engineers:** This is **Part 9 of 15** of the Technical Implementation & Domain Specification. This document provides the detailed **Frontend Architecture**, component hierarchy, and state management design for the AIaaS web application.

# Tech Spec 9: Frontend Architecture

**Version:** 1.0 (Implementation-Ready) **Audience:** Frontend Engineers

## 1\. Tech Stack

*   **Framework:** Next.js (App Router)
*   **Language:** TypeScript
*   **Styling:** TailwindCSS
*   **UI Components:** Shadcn/ui
*   **State Management:** Zustand
*   **Data Fetching:** React Query (TanStack Query)

## 2\. Component Hierarchy

The application is structured using a modular, component-based architecture.

/app

/ (dashboard)

\- page.tsx (The main Unified Dashboard)

\- /components

\- TaskList.tsx (AI-powered task prioritization)

\- ProjectHealth.tsx (Real-time project metrics)

\- BottleneckAlerts.tsx

/projects

/ \[projectId\]

\- page.tsx (Project Overview)

\- /deliverables

/ \[deliverableId\]

\- page.tsx (Deliverable-specific workspace)

\- /components

\- InputForm.tsx (Dynamically generated from schema)

\- OutputDisplay.tsx

\- ReviewPanel.tsx

/components

\- Sidebar.tsx (Main navigation)

\- Header.tsx

\- ChatInterface.tsx (Conversational AI panel)

## 3\. State Management (Zustand)

We use Zustand for its simplicity and performance. We will create several stores to manage different parts of the application state.

*   **useAuthStore:** Manages the user's authentication state, JWT, and profile information.
*   **useProjectStore:** Manages the list of projects and the currently selected project.
*   **useTaskStore:** Manages the state of tasks for the current project, including the AI-prioritized list.
*   **useChatStore:** Manages the history and state of the conversational AI interface.

// Example: useTaskStore.ts

import create from 'zustand';

interface TaskState {

tasks: any\[\];

prioritizedTasks: any\[\];

isLoading: boolean;

fetchTasks: (projectId: string) => Promise<void>;

prioritizeTasks: () => void;

}

export const useTaskStore = create<TaskState>((set) => ({

tasks: \[\],

prioritizedTasks: \[\],

isLoading: false,

fetchTasks: async (projectId) => {

set({ isLoading: true });

const response = await fetch(\`/api/v1/projects/${projectId}/tasks\`);

const tasks = await response.json();

set({ tasks, isLoading: false });

},

prioritizeTasks: () => {

// AI-based prioritization logic will be called here

// For now, just sort by due date

set((state) => ({

prioritizedTasks: \[...state.tasks\].sort((a, b) => new Date(a.due\_date).getTime() - new Date(b.due\_date).getTime()),

}));

},

}));

## 4\. Data Fetching (React Query)

React Query is used for all server-side data fetching, caching, and synchronization. This provides a robust data layer with features like automatic refetching, stale-while-revalidate, and optimistic updates.

// Example: Using React Query to fetch a project

import { useQuery } from '@tanstack/react-query';

const fetchProject = async (projectId: string) => {

const res = await fetch(\`/api/v1/projects/${projectId}\`);

return res.json();

};

function ProjectDetails({ projectId }) {

const { data, error, isLoading } = useQuery({

queryKey: \["project", projectId\],

queryFn: () => fetchProject(projectId),

});

if (isLoading) return <div>Loading...</div>;

if (error) return <div>An error occurred: {error.message}</div>;

return <div>{data.name}</div>;

}

## 5\. Dynamic Form Generation

A key feature of the frontend is its ability to dynamically generate input forms based on the input\_schema from the deliverable\_schemas table. A generic DynamicForm component will be created that takes a JSON schema as a prop and renders the appropriate input fields, validation, and labels. This allows new deliverables to be added to the system without any frontend code changes.