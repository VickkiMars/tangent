# Implementation Roadmap

This document outlines the phased plan to evolve **nagent** from an in-memory prototype to a robust, production-ready system with a web interface.

## Phase 1: Core Infrastructure & Persistence 🏗️
**Goal**: Move from in-memory ephemeral state to durable, distributed state using Redis.

- [x] **Dockerize Environment**
    - [x] Create `docker-compose.yml` with Redis service.
    - [x] Create `Dockerfile` for the python application.
- [x] **Redis Blackboard Implementation**
    - [x] Refactor `EventBlackboard` in `blackboard.py` to accept a Redis connection.
    - [x] Implement `publish` to store messages in Redis streams/lists.
    - [x] Implement `get_thread_history` to fetch persistent history.
    - [x] Create a "Hot/Cold" storage mechanism (Recent messages in memory, full history in Redis).
- [x] **State Restoration**
    - [x] Update `JITCompiler` to hydrate agent context from Redis history instead of just in-memory queues.
    - [x] Implement a `WorkflowState` manager that can save/load the overall progress of a `SynthesisManifest` to Redis.

## Phase 2: Enhanced Agent Runtime ⚡
**Goal**: Support complex, long-running workflows and better error handling.

- [x] **Long-Running Task Support**
    - [x] Implement "hibernate" logic: If an agent needs external input (e.g., human feedback), it should save state to Blackboard and die.
    - [x] Create a polling/listener mechanism in `JITCompiler` to respawn agents when unblocking events occur.
- [x] **Robust Error Handling**
    - [x] Implement retries in `JITCompiler` for failed tool calls or LLM errors.
    - [x] Add "Dead Letter Queue" functionality to the Blackboard for stuck tasks.
- [x] **Agent Memory/History**
    - [x] Update `AgentBlueprint` to include `include_history` and `history_limit` flags.
    - [x] Logic in `_spawn_ephemeral_agent` to fetch and format historical context for the LLM.

## Phase 3: Universal Tool Registry 🧰
**Goal**: Integrate multiple tool providers into a unified interface.

- [x] **Provider Abstraction**
    - [x] Refactor `GlobalToolRegistry` to support "Drivers" or "Adapters" for different providers.
- [x] **Composio Integration**
    - [x] Add `ComposioToolSet` integration for auth-managed tools (GitHub, Gmail, etc.).
- [x] **LangChain Integration**
    - [x] Create adapter to wrap standard LangChain tools.
- [x] **Tool Security**
    - [x] Implement explicit "allow-lists" per agent blueprint (already started, needs hardening).
    - [x] Add logging/auditing for every tool execution.

## Phase 4: API Layer (Backend) 🔌
**Goal**: Expose the system via a standard HTTP API.

- [x] **FastAPI Setup**
    - [x] Initialize a FastAPI project structure.
    - [x] Create endpoints for:
        - `POST /workflows`: Submit a new objective.
        - `GET /workflows/{id}`: Get status and logs.
        - `GET /workflows/{id}/events`: Stream real-time events.
- [x] **WebSockets**
    - [x] Implement WebSocket endpoint to stream Blackboard events to the frontend in real-time.
- [x] **User Management (Basic)**
    - [x] Simple API Key or JWT auth to segregate user workflows (preparation for multi-user support).

## Phase 5: Web Interface (Frontend) 🖥️
**Goal**: A visual interface to monitor and interact with agents.

- [x] **Scaffold Frontend**
    - [x] Initialize Next.js (React) project.
    - [x] Setup Tailwind CSS/Shadcn UI for styling.
- [x] **Dashboard**
    - [x] View list of active and past workflows.
    - [x] "New Workflow" input (Chat interface).
- [x] **Visualizer**
    - [x] **Graph View**: Visualize the `SynthesisManifest` (dependency graph) using React Flow or similar.
    - [x] **Live Logs**: Terminal-like view of agent thoughts and tool outputs (streaming from WebSocket).
- [x] **Human-in-the-Loop UI**
    - [x] Interface for users to provide input if an agent requests it (e.g., "Clarification needed").

## Phase 6: Production Hardening 🛡️
**Goal**: Prepare for deployment.

- [x] **Observability**
    - [x] Integrate OpenTelemetry for tracing requests across agents.
    - [x] Strucutred logging (JSON) for all system events.
- [x] **Testing**
    - [x] Unit tests for `JITCompiler` and `EventBlackboard`.
    - [x] Integration tests using a local LLM (e.g., Ollama) or mocked responses.
- [x] **CI/CD**
    - [x] GitHub Actions for linting and testing.

## Phase 7: Advanced Swarm Architectures & Dynamic Orchestration 🧠
**Goal**: Overcome DAG limitations to support cyclic workflows, continuous monitoring, dynamic scaling, and intelligent routing.

- [x] **Task Complexity Router (Swarm vs. Single LLM)**
    - [x] Implement an initial evaluator system (a fast, cheap LLM call or heuristic classifier) before manifest synthesis.
    - [x] Logic to determine if a user prompt requires a full agent swarm (multi-step, parallelizable, complex) or if it can be efficiently resolved with a standard, single LLM response, avoiding unnecessary compute and orchestration overhead.
- [x] **State Graph Orchestrator (Cyclic Workflows)**
    - [x] Evolve the `JITCompiler` dependency resolution to support state transitions and routing loops (beyond a strict DAG).
    - [x] Allow agents to publish intermediate states (e.g., `propose`, `critique`) without terminating, enabling multi-turn debates and iterative refinement until a consensus condition is met.
- [x] **Long-Running Daemons (Streaming & Real-Time)**
    - [x] Introduce `AgentType.DAEMON` to the `AgentBlueprint` schema.
    - [x] Implement an event loop within the daemon agent lifecycle that continuously listens to specific `EventBlackboard` topics (e.g., continuous log streams) rather than waiting for a single hydration step.
    - [x] Create a Supervisor process to monitor daemon health and restart them if they crash.
- [x] **Dynamic Task Spawning (Agent-Spawned Agents)**
    - [x] Create a privileged system tool: `spawn_subtask(description, tools_needed)`.
    - [x] Update the `JITCompiler` and `SynthesisManifest` to be mutable at runtime, allowing running agents to dynamically append new `SubTask`s and `AgentBlueprint`s to the execution pool.
    - [x] Implement safe-guards and recursion limits to prevent infinite agent spawning loops.
