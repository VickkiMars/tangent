# N-Agent Task Validation & Infrastructure Gaps

Based on the capabilities of an agent swarm, here are 10 complex tasks `nagent` could be assigned, categorized by their swarm type, and a validation of whether the current `JITCompiler` and `EventBlackboard` infrastructure can effectively execute them.

## 10 Proposed Swarm Tasks

### Large-Scale Research & Synthesis
1.  **Market Research Synthesis:** 50 agents independently scan 50 different competitor websites to extract pricing and feature data, while a final Synthesizer agent aggregates the data into a competitive matrix.
    *   **Validation:** ✅ **Supported.** The current architecture handles this perfectly. It forms a Directed Acyclic Graph (DAG) where the Synthesizer agent depends on the 50 parallel scraping tasks.
2.  **Policy Evaluation:** Analyze a massive 500-page policy document against 10 different regulatory frameworks (e.g., GDPR, HIPAA, SOC2) simultaneously using specialized compliance agents.
    *   **Validation:** ✅ **Supported.** Parallel agents can read the document using injected tools and output their compliance checks for a final reviewer agent.

### Complex Software Development
3.  **Full-Stack Feature Implementation:** Given a Product Requirements Document (PRD), a Frontend Agent builds the React component, a Backend Agent builds the FastAPI endpoint, and a Test Agent writes end-to-end tests relying on the outputs of the first two.
    *   **Validation:** ✅ **Supported.** Standard DAG execution. The Test agent waits for the `inform` messages from the Frontend and Backend agents.
4.  **Codebase Security Audit:** Review 100 distinct files or modules in a repository for OWASP top 10 vulnerabilities simultaneously.
    *   **Validation:** ✅ **Supported.** Highly parallelizable; fits the JIT Compiler's ephemeral agent spawning model.

### Simulation & Strategy Testing
5.  **Business Strategy Wargaming:** Simulate a product launch where 3 agents act as competitors reacting to the launch strategy, and 1 agent acts as the market. They debate and counter each other's moves over 5 simulated quarters.
    *   **Validation:** ❌ **Unsupported (Iterative/Cyclic).** The current infrastructure expects agents to wait for dependencies, execute *once* until they reach a termination condition, publish an `inform` message, and then terminate (ephemeral lifecycle). Multi-turn debates require cyclic message passing or stateful loops, which the current DAG dependency model does not support.

### Monitoring & Real-Time Response
6.  **Network Anomaly Detection:** Monitor 5 different continuous server log streams in real-time. If multiple agents detect suspicious patterns aligning across streams, escalate to a human operator.
    *   **Validation:** ❌ **Unsupported (Continuous/Streaming).** `JITCompiler.execute_manifest()` is designed for finite batch processing (it uses `asyncio.gather` to wait for all tasks to complete). Agents are not currently designed as long-running daemon processes that continuously ingest streams of events without terminating.
7.  **Supply Chain Fraud Detection:** Continuously analyze vendor invoices as they arrive in a live system and flag anomalies.
    *   **Validation:** ❌ **Unsupported (Continuous/Streaming).** Same as above; the system expects a predefined list of tasks upfront rather than an infinite stream of incoming tasks.

### Creative Ideation at Scale
8.  **Story Idea Generation & Refinement:** Agent A generates 5 story premises. Agent B critiques them. Agent A refines them based on the critique. Agent C scores the final results.
    *   **Validation:** ❌ **Unsupported (Cyclic/Feedback Loops).** This requires a feedback loop (A -> B -> A). The current JIT Compiler's dependency resolution cannot handle cyclic dependencies without deadlocking.

### Large Optimization Problems
9.  **Logistics Routing Optimization:** Find the optimal delivery route for a massive fleet by having 10 parallel agents explore different routing heuristics (e.g., shortest path, least traffic, lowest fuel cost) and a Coordinator agent picking the best one.
    *   **Validation:** ✅ **Supported.** This is a scatter-gather pattern, which is perfectly supported by the existing DAG implementation.
10. **Multi-Constraint Dynamic Scheduling:** Schedule shifts for 500 employees. If an agent encounters an impossible constraint (e.g., no manager available for a shift), it needs to spawn a *new* agent to negotiate shift trades with specific employees.
    *   **Validation:** ❌ **Unsupported (Dynamic Task Spawning).** The current `execute_manifest` requires all tasks and `AgentBlueprint`s to be defined entirely upfront in the `SynthesisManifest`. Agents cannot dynamically spawn new sub-tasks or new agents at runtime.

---

## Infrastructure Gaps to Overcome

To fully realize the potential of agent swarms (specifically for Simulation, Real-Time Monitoring, Ideation, and Dynamic Optimization), the following architectural changes must be implemented in the `backend`:

### 1. Support for Cyclic Workflows & Stateful Debates
*   **The Issue:** The `JITCompiler` currently models execution as a Directed Acyclic Graph (DAG). Agents are ephemeral: they wake up, do one job, and die.
*   **The Solution:** Implement a **State Graph Orchestrator** (similar to LangGraph). Instead of just `SubTask` dependencies, we need the ability to define state transitions or routing loops. Agents should be able to publish intermediate performatives (e.g., `propose`, `critique`) without terminating, allowing multiple agents to subscribe to the same thread and converse iteratively until a consensus condition is met.

### 2. Long-Running Daemons & Streaming Event Ingestion
*   **The Issue:** `asyncio.gather(*ephemeral_threads)` assumes tasks eventually finish. There is no concept of a "Daemon Agent."
*   **The Solution:** 
    *   Introduce a `AgentType.DAEMON` in the `AgentBlueprint`. 
    *   Instead of waiting for a single set of upstream context to hydrate before running, Daemon agents should have an event loop that continuously listens to a specific topic on the `EventBlackboard` (e.g., `topic:network_logs`). 
    *   They run indefinitely, analyzing batches of events and publishing alerts, requiring a Supervisor process to manage their health and restarts.

### 3. Dynamic Task Spawning (Agent-spawned Agents)
*   **The Issue:** The `SynthesisManifest` is static. If an agent realizes a problem is too complex, it cannot break it down and delegate it further on the fly.
*   **The Solution:** 
    *   Expose a system tool to the agents: `spawn_subtask(description, tools_needed)`.
    *   When invoked, this tool interacts directly with the `EventBlackboard` or `JITCompiler` to append a new `SubTask` to the running pool and dynamically generate a new `AgentBlueprint` for it. 
    *   The JIT Compiler's ready queue must become dynamic, able to accept new tasks while execution is already underway.