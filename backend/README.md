# tangent: Just-In-Time (JIT) Multi-Agent System

**tangent** is a next-generation framework for orchestrating ephemeral AI agents to solve complex, multi-step tasks. Unlike traditional agent frameworks that maintain long-running stateful agents, **tangent** adopts a **Just-In-Time (JIT) compilation** approach. Agents are spun up on-demand to perform specific sub-tasks and then strictly disposed of, with all state persisted to a central, immutable blackboard.

## 🧠 Core Philosophy

1.  **Ephemeral Compute, Persistent State**: Agents are stateless functions that transform events. They live only as long as their specific sub-task requires.
2.  **JIT Compilation**: The "Meta-Agent" architects a solution by compiling a high-level objective into a dependency graph of `SubTask`s and `AgentBlueprint`s.
3.  **Event Sourcing**: The `EventBlackboard` is the single source of truth. Every interaction is an immutable event, enabling replayability, auditability, and long-running workflows that span days or weeks.
4.  **Universal Tooling**: A unified registry interface that aggregates tools from multiple providers (Composio, LangChain, CrewAI, Custom) into a strictly scoped toolkit for each ephemeral agent.

## 🏗 Architecture

### 1. Meta-Agent Architect (`meta.py`)
The system's "brain." It analyzes a user's objective and "compiles" it into a `SynthesisManifest`. This manifest describes the topology of agents required, their distinct personas, and the precise tools they need.

### 2. JIT Compiler (`compiler.py`)
The execution engine. It takes the `SynthesisManifest` and:
*   Resolves dependencies (waiting for upstream agents to finish).
*   **Spawns** ephemeral agents with strictly injected contexts.
*   Executes the agent loop (LLM + Tools).
*   Publishes results to the Blackboard.
*   **Garbage Collects** the agent instance immediately after task completion.

### 3. Event Blackboard (`blackboard.py`)
The central nervous system. It acts as a pub/sub message bus and a persistent event store.
*   **Current Status**: In-memory (Ephemeral).
*   **Roadmap**: Redis-backed persistence to support system restarts and long-running "human-in-the-loop" workflows.

### 4. Universal Tool Registry (`registry.py`)
A facade over various tool ecosystems. It allows the Meta-Agent to select the best tool for the job, regardless of whether it comes from a proprietary API, a community library, or a local function.

## 🚀 Key Features (Planned)

*   **Resilience**: System restarts don't kill workflows. The next compiler instance picks up where the last one left off by reading the Blackboard history.
*   **Security**: Agents only see the tools they are explicitly granted in their blueprint.
*   **Observability**: Complete audit trail of every thought and action via the event log.
*   **Flexibility**: Mix and match tools from different providers in a single workflow.

## 📂 Project Structure

```
tangent/
├── blackboard.py       # Event bus & state management
├── compiler.py         # Agent lifecycle & execution engine
├── meta.py             # Architect agent (planner)
├── registry.py         # Tool management facade
├── schemas.py          # Pydantic models & data structures
├── prompts.py          # System prompts for agents
├── PROBLEMS.md         # Architecture decision log & roadmap
└── ...
```

## 🛠 Usage (Conceptual)

```python
from meta import MetaAgent
from compiler import JITCompiler
from blackboard import EventBlackboard

# 1. Initialize Core Systems
blackboard = EventBlackboard()
meta = MetaAgent()
compiler = JITCompiler(blackboard=blackboard, ...)

# 2. Architect the Solution
manifest = meta.architect_workflow(
    user_objective="Research the current state of Quantum Computing and write a blog post about it.",
    available_tool_names=["web_search", "write_file"]
)

# 3. Execute
await compiler.execute_manifest(manifest)
```
