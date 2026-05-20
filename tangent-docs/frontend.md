# Frontend Architecture

Tangent features a highly dynamic, real-time frontend built to visualize massive concurrent agent operations seamlessly. It leverages **React 19**, **Vite**, and **Tailwind CSS**, emphasizing absolute observability into the backend orchestration engine.

## Core Technologies
- **Framework:** React (via Vite for instantaneous HMR and optimized builds)
- **Styling:** Tailwind CSS (utility-first approach enabling rapid dark-mode aesthetics)
- **State Management:** React Hooks (`useState`, `useEffect`) combined with contextual boundaries (`AuthContext.jsx`).
- **Real-Time Data:** Native WebSockets directly bound to FastAPI event streams.
- **Visuals:** `ReactFlow` for rendering complex Directed Acyclic Graphs (DAGs), and `Framer Motion` for fluid micro-animations.

---

## Directory & File Breakdown (`frontend/src/`)

### 1. The Root Level
- **`App.jsx`**: The core routing hub. It implements React Router to manage navigation between the Landing page, Authentication, and protected application views.
- **`main.jsx`**: The React DOM entry point that wraps the application in the `AuthContext.Provider`.
- **`api.js`**: A centralized Axios/Fetch wrapper handling backend HTTP communication, token injection, and global error catching.
- **`index.css` & `App.css`**: Global stylesheet definitions containing Tailwind directives and specific animation keyframes required for the dark-mode "hacker" aesthetic.
- **`mockData.js`**: Static JSON fixtures used during frontend development before the FastAPI backend was fully integrated.

### 2. Context (`src/context/`)
- **`AuthContext.jsx`**: Manages the user session. It interacts with `localStorage` to securely store JWTs, providing `login`, `logout`, and `user` state globally to prevent prop-drilling authentication props.

### 3. Pages (`src/pages/`)
These are the top-level route components.

- **`Landing.jsx`, `Pricing.jsx`, `Features.jsx`, `Docs.jsx`**: Unauthenticated marketing pages. They are heavily animated to pitch the "Just-In-Time orchestration" concept to new users.
- **`MarketingComplexGraph.jsx`, `MarketingMyApps.jsx`, `MarketingScreenshot.jsx`**: Specialized components likely utilized to generate screenshots or iframe embeds for the project's marketing site (referenced in the `marketing` folder).
- **`Auth.jsx`**: The login and registration portal.
- **`Workspace.jsx`**: The primary authenticated dashboard wrapper holding the sidebar and active view.
- **`Builder.jsx`**: The visual drag-and-drop workflow constructor. It allows users to manually define Agent Blueprints and wire dependencies before saving them to `predefined_workflows` in the DB.
- **`Apps.jsx`**: A library view showing workflows the user has saved.
- **`Chat.jsx`**: An alternative conversational interface where users can type natural language objectives and let the `MetaAgent` dynamically compile a workflow, bypassing the manual `Builder`.
- **`ToolRepository.jsx`**: The interface for developers to view, edit, and approve custom Python scripts that agents can use.
- **`History.jsx` & `TaskView.jsx`**: Views for auditing past workflow executions, analyzing token spend, and viewing final agent outputs.

### 4. Components (`src/components/`)
Reusable UI elements that construct the pages.

- **`TaskBoard.jsx`**: The absolute centerpiece of the frontend.
  - **Function:** It establishes a WebSocket connection to the backend (`/workflows/{id}/events`) and renders a live, chronological feed of every agent action (`spawn`, `inform`, `hibernate`, tool usage).
  - **Nuance:** It implements a complex UI mapping logic (`mapBackendEvent`) to translate dense FIPA ACL messages from the `EventBlackboard` into human-readable timeline blocks, complete with Framer Motion entry animations. It also houses the UI for replying to "Hibernated" agents.
- **`GraphView.jsx`**: 
  - **Function:** Uses `ReactFlow` to parse the `SynthesisManifest` into a visual graph. 
  - **Nuance:** As agents execute, it dynamically updates node colors (e.g., green for success, flashing for active, orange for hibernation) giving a physical map of the JIT compilation process.
- **`Sidebar.jsx` & `Navbar.jsx`**: Navigation scaffolding.
- **`Notification.jsx`**: A global toast system for alerting users to backend errors or successful task completions without interrupting their workflow.
- **`ProtectedRoute.jsx`**: A higher-order component that wraps authenticated routes and redirects unauthenticated users back to `/auth`.
- **`Layout.jsx`**: Structural wrapper ensuring consistent padding, backgrounds, and responsiveness across distinct views.

---

## Key Design Decisions

### Event Virtualization & Performance
Because a swarm of 50 agents might generate 500+ messages in seconds (thoughts, tool usages, status updates), the `TaskBoard` uses careful React state management. While not explicitly using a library like `react-window`, it heavily filters and scopes re-renders to prevent the browser UI thread from freezing during massive compilation spikes.

### The "Inspector" Pattern
Instead of overwhelming the user with raw JSON logs, the timeline provides summarized "pills". Users must explicitly click an event to open the right-hand `Inspector` panel in `TaskBoard.jsx`, which then lazily renders the heavy JSON payload. This keeps the primary view clean.

### Unified Color Token System
The UI strictly adheres to a minimalist dark theme defined by constants in components (e.g., `_C` in `TaskBoard`): 
- `#FFFFFF` (Cyan/White - Standard execution)
- `#FF8A00` (Orange - Human intervention required / Tool usage)
- `#10B981` (Green - Success)
- `#EF4444` (Red - Failure)
This ensures users can understand the health of a complex distributed system via peripheral vision.
