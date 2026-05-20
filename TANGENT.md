# Tangent: The Just-In-Time Multi-Agent Orchestration Framework

## Executive Summary

Tangent is a revolutionary, Just-In-Time (JIT) multi-agent orchestration framework designed to address the inherent limitations of static artificial intelligence pipelines and monolithic Large Language Model (LLM) agents. At its core, Tangent represents a paradigm shift from pre-configured, rigid agent teams to an entirely dynamic, objective-driven compiled team architecture. 

When a user submits a high-level objective using natural language, Tangent does not attempt to brute-force a solution through a single context window. Instead, its orchestrator—the MetaAgent—evaluates the request, synthesizes a dependency graph of specialized sub-tasks, and provisions a fleet of ephemeral, purpose-built sub-agents. These spawned agents execute their tasks in parallel, collaborate where necessary via an Event Blackboard, aggregate the final results, and dissolve seamlessly, leaving no persistent computational overhead.

This approach ensures absolute observability, strict tool injection limits, and massive parallelization. 

---

## Extensive Project Documentation

To provide absolute clarity into the architecture, the project documentation has been decoupled into highly specific, deep-dive documents. Please refer to the `tangent-docs/` directory for exhaustive information regarding the frontend rendering logic, the backend orchestration engine, and the Postgres database schema.

### 📚 Deep Dives

1. **[Backend Architecture & Orchestration](file:///home/kami/Desktop/codebase/tangent/tangent-docs/backend.md)**
   Details the FastAPI implementation, the Just-In-Time (JIT) `compiler.py`, the `MetaAgent`, and the Redis `EventBlackboard`. Explains how agents are spawned ephemerally and how the FIPA ACL messaging protocol dictates their communication.

2. **[Frontend Visualization & Real-Time Sync](file:///home/kami/Desktop/codebase/tangent/tangent-docs/frontend.md)**
   Explores the React 19 / Vite application that powers the Tangent UI. Details the WebSocket implementation in `TaskBoard.jsx`, the `ReactFlow` integration in `GraphView.jsx`, and the UI virtualization strategies used to prevent browser freezes during massive agent swarms.

3. **[Database Schema & Persistence](file:///home/kami/Desktop/codebase/tangent/tangent-docs/database.md)**
   Breaks down the PostgreSQL schema defined in `db.py`. Covers multi-tenant isolation, real-time cost telemetry mapping via `agent_analytics`, and the critical `agent_human_input_states` table that powers Tangent's unique agent "Hibernation" protocol.

4. **[System Optimizations & Infrastructure Gaps](file:///home/kami/Desktop/codebase/tangent/tangent-docs/optimization.md)**
   Identifies the current architectural limits of the Tangent framework (e.g., the inability to run cyclic workflows or long-running daemon agents) and proposes comprehensive engineering solutions to overcome them.

---

## Core Value Proposition

1. **Execution Fan-Out:** Fracturing tasks into a Directed Acyclic Graph (DAG) mitigates LLM hallucination and context amnesia by ensuring each sub-agent focuses on a single, isolated problem.
2. **Dynamic Pipelines:** The pipeline is compiled at runtime. Whether a task requires 5 parallel researchers or a sequential debugging tree, Tangent builds the exact architecture required for the problem.
3. **Absolute Observability:** Users are not bystanders. Every thought, tool usage, and network performative is streamed via WebSockets to the frontend timeline.
4. **Hibernation Protocol (Human-in-the-loop):** When agents face ambiguity, they safely serialize their state to Postgres and yield execution. Once a human provides input, the agent is rehydrated and continues seamlessly.
