# Database Schema

Tangent uses a robust PostgreSQL database architecture to ensure data persistence, tenant isolation, and strict state management for the ephemeral multi-agent workflows. Below is a detailed breakdown of the schema, as defined in `backend/infrastructure/db.py`.

## Overview

The database uses a relational model and serves three primary purposes within the Tangent ecosystem:
1.  **Multi-Tenant Storage**: Handling distinct organizations, user budgets, and scoped execution data.
2.  **State Management**: Saving and recovering in-flight agent contexts (specifically during the "hibernation" protocol for human-in-the-loop interactions).
3.  **Analytics & Telemetry**: Logging granular LLM costs, tokens, and agent lifetimes for budget enforcement.

---

## Table Breakdown

### 1. `tenants`
The foundational table establishing logical isolation for all other data.
- **Columns:**
  - `id` (VARCHAR PRIMARY KEY): Unique identifier for the tenant organization.
  - `name` (VARCHAR NOT NULL): Display name of the tenant.
  - `created_at` (TIMESTAMP): Creation record.
- **Function:** Ensures that users, threads, and tools cannot accidentally leak across boundaries.

### 2. `users`
Represents individual human users utilizing the Tangent framework.
- **Columns:**
  - `id` (VARCHAR PRIMARY KEY): Unique identifier.
  - `tenant_id` (VARCHAR FOREIGN KEY): Links user to their parent tenant.
  - `first_name` / `last_name` (VARCHAR): User identity.
  - `email` (VARCHAR UNIQUE NOT NULL): Login mechanism.
  - `hashed_password` (VARCHAR NOT NULL): Local auth mechanism.
  - `budget_limit_usd` (DECIMAL): Hard limit on LLM API costs this user is allowed to incur (default `$100.00`).
  - `current_spend_usd` (DECIMAL): Running total of actual LLM cost incurred.
- **Function:** Tracks users, handles authentication state natively, and strictly enforces agent token burn rates through dynamic budget checking.

### 3. `predefined_workflows`
Stores user-created or system-provided reusable agent pipelines (referred to as "Apps" in the UI).
- **Columns:**
  - `id` (VARCHAR PRIMARY KEY)
  - `tenant_id` (VARCHAR FOREIGN KEY)
  - `name` (VARCHAR NOT NULL)
  - `visual_layout` (JSONB NOT NULL): Stores the `ReactFlow` graphical node state for the Builder UI.
  - `synthesis_manifest` (JSONB NOT NULL): The actual executable Master Blueprint that the JIT compiler uses to spawn agents.
  - `parameters` (JSONB): Form fields required to kick off the workflow.
- **Function:** Enables users to save complex, multi-agent DAGs to be triggered repeatedly without requiring the MetaAgent to re-architect them from scratch.

### 4. `execution_threads`
The central hub for any running agent workflow.
- **Columns:**
  - `id` (VARCHAR PRIMARY KEY): The unique `thread_id` shared by all agents working on the same user objective.
  - `tenant_id`, `user_id` (VARCHAR FOREIGN KEYS)
  - `objective` (TEXT NOT NULL): The user's natural language goal.
  - `status` (VARCHAR): Tracks states like `analyzing`, `completed`, `failed`.
  - `total_cost_usd` / `total_tokens` (DECIMAL/INTEGER): Real-time aggregated cost of the entire DAG.
- **Function:** Groups isolated agent logs and processes under a single overarching user intent.

### 5. `agent_human_input_states`
The critical table powering Tangent's "Hibernation" feature.
- **Columns:**
  - `thread_id` (VARCHAR PRIMARY KEY FOREIGN KEY)
  - `agent_blueprint` (JSONB NOT NULL): The specific instructions for the agent that paused execution.
  - `conversation_history` (JSONB NOT NULL): All preceding context up to the hibernation point.
  - `collected_context` (JSONB): Any data gathered by the agent thus far.
  - `human_input_request` (JSONB NOT NULL): The explicit question or decision required from the user.
  - `human_response` (JSONB): The human's eventual answer.
  - `status` (VARCHAR): Default `'waiting'`.
- **Function:** When an agent requires human validation, it serializes its entire context into this table and dies. When the human replies, the backend rehydrates a new agent with this data to continue exactly where the previous one left off.

### 6. `agent_tools`
The registry of executable Python functions accessible to agents.
- **Columns:**
  - `id`, `tenant_id`
  - `name`, `description`
  - `python_code` (TEXT NOT NULL): The raw code of the tool.
  - `schema_json` (JSONB): OpenAI/Anthropic compatible function schema.
  - `source` (VARCHAR): e.g., `'agent'` (dynamically generated tool) or system.
  - `is_approved`, `is_active` (BOOLEAN): Security controls.
- **Function:** Allows agents to not only use existing tools but also dynamically author, store, and utilize new python functions (stored in `python_code`) to solve novel problems.

### 7. `agent_analytics`
A highly granular ledger for AI observability.
- **Columns:**
  - `id` (SERIAL PRIMARY KEY)
  - `thread_id` (FOREIGN KEY)
  - `agent_id` / `target_task_id` (VARCHAR)
  - `provider` / `model` (VARCHAR)
  - `tokens_prompt`, `tokens_completion`, `tokens_cache_read`, `tokens_cache_creation` (INTEGER): Exact token counts.
  - `cost_usd` (DECIMAL): Calculated dollar cost of the specific inference.
  - `tools_called` (JSONB): Record of exactly what tools this specific agent utilized.
  - `was_successful` (BOOLEAN): Did the agent crash?
  - `lifetime_seconds` (DECIMAL): How long the agent existed.
- **Function:** Facilitates deep analytics, auditing of what agents did, and strict billing. This enables the UI's telemetry graphs.

### 8. `query_optimizations`
*Future/Experimental*: Stores LLM query refinements.
- **Columns:** `original_query`, `optimized_query`, `tool_name`, `success_score`.

---

## Design Decisions & Nuances

- **JSONB Heavy:** By leaning heavily on Postgres's `JSONB` columns (`agent_blueprint`, `visual_layout`, `tools_called`), Tangent marries the structural integrity of relational databases (for billing and multitenancy) with the flexibility of NoSQL (crucial since agent conversational payloads are highly unstructured and variable).
- **Hard Deletes vs. Cascades:** Tenant deletion implicitly uses `ON DELETE CASCADE` down the entire tree. Erasing a user erases their threads, which erases their hibernation states and analytics, ensuring GDPR-style data hygiene is natively enforced.
- **"Fail Open" Budget Check:** In `db.py::check_budget_exceeded`, if the DB connection drops, it returns `False`. The framework prioritizes keeping execution running over strictly enforcing billing during network hiccups, avoiding catastrophic pipeline death due to momentary Postgres unavailability.
