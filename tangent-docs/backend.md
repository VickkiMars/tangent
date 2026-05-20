# Backend Architecture

Tangent's backend is a high-performance Python orchestration layer. It is responsible for parsing user intent, compiling dynamic agent pipelines, distributing execution loads asynchronously, and funneling real-time telemetry to the frontend.

## Core Technologies
- **Framework:** FastAPI (for asynchronous HTTP routing and WebSockets)
- **Concurrency:** `asyncio` for parallel agent execution without GIL blocking.
- **Messaging:** Redis (`aioredis`) acting as a publish/subscribe `EventBlackboard`.
- **Database:** PostgreSQL (via `psycopg2`).
- **LLM Integration:** Langchain (for tool wrapping) and direct integration with providers (e.g., Gemini, OpenAI, Anthropic).

---

## Directory & File Breakdown (`backend/`)

### 1. API Routing (`backend/api/`)
Defines the REST endpoints and WebSocket channels.
- **`main.py`**: The entry point for the Uvicorn server. It wires up CORS, registers tool adapters to the global registry upon startup, and manages the application lifecycle (e.g., closing Redis connections gracefully during shutdown).
- **`routes/auth.py`**: Handles user login (`/login`), registration, and JWT issuance using `bcrypt` and `pyjwt`.
- **`routes/workflows.py`**: The primary operational endpoint. It exposes endpoints to kick off new tasks, retrieve existing thread logs, and manage the `WebSocket` endpoint (`/workflows/{id}/events`) that streams `EventBlackboard` updates to the UI.
- **`routes/tools.py`**: CRUD endpoints for managing custom Python agent scripts (stored in `agent_tools`).
- **`routes/apps.py`**: CRUD endpoints for interacting with `predefined_workflows`.
- **`routes/deterministic.py`**: Endpoints related to deterministic workflow triggers.

### 2. The Engine (`backend/engine/`)
This is the "Brain" of Tangent. It contains the logic for creating and running agents.
- **`meta.py`**: Houses the `MetaAgent`. When a user submits an objective, this script uses an LLM to translate the raw text into a highly structured `SynthesisManifest` (a DAG of agent `AgentBlueprint`s).
- **`compiler.py`**: The `JITCompiler` (Just-In-Time Compiler). It receives the manifest from the MetaAgent, figures out the dependency graph (who needs to run first), and executes `asyncio.gather` loops to spawn worker agents. It isolates context, injects required tools, and manages timeouts.
- **`blackboard.py`**: The `EventBlackboard` implementation. Agents do not talk directly to each other; they publish FIPA ACL messages (e.g., `inform`, `request`, `hibernate`) to specific Redis topics. The compiler and the frontend subscribe to this blackboard to observe the swarm.
- **`state_manager.py`**: Handles serialization of agent contexts to the Postgres DB during "Hibernation" and rehydrates them when human input is received.
- **`personas.py` & `prompts.py`**: Define the rigid system prompts and formatting instructions that force the underlying LLMs to behave as predictable software nodes rather than chat bots.
- **`optimization.py`**: Algorithms to streamline execution logic or manage prompt lengths.
- **`deterministic_workflow.py`**: Logic for skipping the MetaAgent and running directly from a saved `predefined_workflow` blueprint.

### 3. Core Definitions (`backend/core/`)
- **`schemas.py`**: Pydantic models. Crucial for ensuring that inputs/outputs across the API, the Event Blackboard, and the UI are strongly typed. Defines `SynthesisManifest`, `SubTask`, `A2AMessage`, etc.
- **`globals.py`**: Instantiates global singletons (like the `blackboard` instance, DB connection pools, and the `GlobalToolRegistry`) so they can be imported across modules without circular dependency issues.

### 4. Infrastructure (`backend/infrastructure/`)
- **`db.py`**: Contains raw SQL for schemas, migrations (`run_schema_migrations`), and all CRUD wrappers (e.g., `get_workflow_analytics`, `check_budget_exceeded`).
- **`init_db.py`**: A bootstrap script to forcibly reset or seed the database.
- **`llm_provider.py`**: An abstraction layer. Instead of tightly coupling agents to OpenAI or Gemini, this module standardizes the interface so Tangent can swap foundation models depending on cost or speed requirements.
- **`telemetry.py`**: OpenTelemetry integrations for distributed tracing across the asynchronous architecture.

### 5. Agent Tools (`backend/tools/`)
Implements the `Agent-Reach` philosophy, giving agents internet sovereignty.
- **`registry.py`**: The `GlobalToolRegistry`. When the API starts, it stores schemas and function pointers here. When the compiler spawns an agent, it pulls only the requested subset of tools from this registry.
- **`filesystem_tools.py`**: Utilities allowing agents to read, write, and manipulate local files.
- **`shell_tools.py`**: Allows agents to execute raw bash commands (highly privileged).
- **`adapters.py`**: Wraps standard Python functions into Langchain `StructuredTool` formats so the LLM understands how to invoke them via native function calling.
- **`tool_creator.py`**: A unique system tool that allows agents to write new Python code, save it to the database, and dynamically inject it into the registry for future agents to use.
- **`deterministic_tool.py` & `tools.py`**: Standard utility functions for complex programmatic interactions.

---

## Design Decisions & Nuances

### Ephemeral Architecture
Agents in `compiler.py` are strictly ephemeral. They are initialized, given a prompt, run inference, publish an output to the blackboard, and immediately terminate. There are no long-running agent loops by default. This forces agents to be deterministic and stateless.

### The FIPA ACL Standard
Instead of arbitrary string messages, all communication on `blackboard.py` requires a "performative" (intent).
- `inform`: "Here is my final answer."
- `hibernate`: "I need human help."
- `failure`: "I crashed."
This makes the distributed system debuggable and predictable.

### Strict Tool Injection
Instead of giving an agent 50 tools (which causes hallucinations and token limit errors), `compiler.py` guarantees an agent only receives the 2 or 3 tools explicitly listed in its `AgentBlueprint` generated by the MetaAgent.
