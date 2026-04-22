# My Apps Feature Description & Implementation Guide

## Executive Summary
The "My Apps" feature allows users to productize AI interactions. By taking a successfully executed chat session or orchestrated workflow from the Workspace, users can save the underlying computational graph (the exact sequence of prompts, tool calls, and LLM reasoning steps) as a reusable, one-click "App". 

When an App is deployed, the system bypasses the high-latency "planning and tool-discovery" phase. Instead, it executes the saved deterministic execution graph against the *current* state of the environment (e.g., executing `grep` to find today's TODOs, and passing those results into the LLM for summarization). 

## Core Architecture & Execution Model
To address the critical question: *"How does it know the latest TODO without an LLM call?"*

Apps do **not** eliminate LLM calls entirely. Instead, an App persists the **Workflow Definition** (a Directed Acyclic Graph - DAG) rather than static data. 
- **Dynamic Execution**: When an App is deployed, the platform executes the saved DAG. If step 1 is a shell command (`grep TODO`), it runs in real time against the live codebase. If step 2 requires an LLM to summarize the grep output, an LLM call is made. 
- **Efficiency Gains**: The time and token savings come from bypassing the *Agentic Planning Phase*. The agent doesn't need to deduce *how* to solve the user's problem from a vague prompt; it just executes the predefined, optimized recipe.

## Phasal Implementation Guide

### Phase 1: Foundation (Data Model & Basic UI)
*Goal: Establish the database schema and basic frontend interface to list and manage saved apps.*

1. **Database Schema Update**
   - Create an `App` model/table.
   - Fields: `id`, `user_id`, `name`, `description`, `workflow_payload` (JSON representing the execution graph/DAG), `created_at`, `updated_at`.
2. **Backend Endpoints (CRUD)**
   - `GET /apps`: Fetch user's saved apps.
   - `POST /apps`: Create a new app (save a workflow).
   - `DELETE /apps/{id}`: Remove an app.
3. **Frontend Integration**
   - Implement `Apps.jsx` to fetch and render the saved Apps from the database.
   - Build out the App Card UI (Name, description, created date, run/delete buttons).

### Phase 2: Workflow Extraction & Saving
*Goal: Extract a successful session's execution graph and save it as an App.*

1. **Workspace Action: "Save as App"**
   - Add a "Save as App" button in the Workspace UI for completed tasks/sessions.
2. **DAG Compilation Endpoint**
   - Create a backend utility `compile_session_to_dag(session_id)`.
   - Traverse the session history to identify the exact sequence of tool calls and prompts used to achieve the goal.
   - Abstract the exact responses out, replacing them with runtime variable slots (e.g., `<Step_1_Output>`), transforming the specific run into a dynamic template.
3. **Save Flow Integration**
   - Send the compiled DAG template as `workflow_payload` to `POST /apps`.
   - Prompt the user for an App Name and Description via a Modal.

### Phase 3: The Deployment Engine (Runner)
*Goal: Execute a saved App's static graph dynamically at runtime.*

1. **Execution Endpoint (`POST /apps/{id}/run`)**
   - Retrieve the `workflow_payload` from the database.
   - Create a *new* workspace session (`session_id`).
2. **Deterministic Workflow Engine**
   - Feed the DAG into the `generate_deterministic_workflow` engine (or equivalent workflow executor).
   - The engine iterates through the DAG:
     - *Node 1 (Tool Call)*: Execute tool with saved parameters.
     - *Node 2 (LLM Prompt)*: Make LLM call injecting output from Node 1.
3. **Live UI Hydration**
   - Redirect the user down into the Workspace UI with the new `session_id`.
   - The UI streams the execution steps exactly as if the AI were autonomously running them, but the agent strictly adheres to the DAG.

### Phase 4: App Parameterization (Advanced)
*Goal: Allow users to provide custom inputs to Apps at runtime.*

1. **Parameter Definition**
   - Allow the user to specify required inputs when saving an App (e.g., `Target Directory` or `Search Query`).
2. **Pre-Flight Modal**
   - When a user clicks "Deploy" on an parameterized App, open a modal prompting them for the input variables.
   - Pass variables into the `/apps/{id}/run` payload.
3. **Variable Interpolation**
   - Inject the user-supplied variables into the DAG before execution begins.
