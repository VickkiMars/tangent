**PRD**
### 1. Background of the Study

The rapid evolution of large language models (LLMs) has catalyzed the development of multi‑agent systems capable of decomposing complex tasks and executing them collaboratively. Traditional multi‑agent architectures often rely on static teams of agents, each equipped with a global set of tools and long‑term memory. While functional in controlled environments, these designs exhibit critical shortcomings when deployed at scale: they bloat the LLM context window with irrelevant tool descriptions, increase hallucination rates, and create systemic security vulnerabilities where an agent might be tricked into invoking a tool for which it lacks authorization. Moreover, persistent agents accumulate state, making debugging, auditing, and cost attribution difficult.

This proposal introduces **N‑Agent**, a novel orchestration framework that treats agents as ephemeral, just‑in‑time (JIT) computational units. Inspired by serverless computing and capability‑based security, N‑Agent dynamically assembles a team of agents for each incoming task, equips each agent with only the tools it absolutely requires, and terminates them immediately after task completion. Communication occurs through an immutable, persistent blackboard that serves both as a coordination medium and an auditable ledger. The system is designed for maximum parallelism while respecting data dependencies, ensuring that agents execute concurrently whenever possible and only block when awaiting required inputs. By inverting control—moving tool selection from the agent to a central registry—N‑Agent achieves a level of security, observability, and efficiency that is essential for production‑grade deployments in enterprise and regulated environments.

---

### 2. Problem Statement and Facts about the Problem

Contemporary multi‑agent systems suffer from several interrelated problems:

- **Context Window Pollution**: Agents are typically provisioned with a global list of all available tools. Each tool’s description consumes valuable tokens in the LLM’s context window, increasing latency and cost. More importantly, the presence of irrelevant tools confuses the model and elevates the probability of hallucinating non‑existent functions or misusing legitimate ones.

- **Security Vulnerabilities**: When every agent has access to every tool, a single compromised agent can execute arbitrary actions—deleting user data, accessing sensitive information, or issuing destructive commands. Conventional permission checks are implemented at the application level and can be bypassed through prompt injection or model errors.

- **Inefficient Resource Utilisation**: Persistent agents consume memory and compute even when idle. Long‑running agents accumulate conversation history, further straining context windows and making it difficult to trace the origin of errors.

- **Auditability and Observability**: In traditional designs, agent interactions are scattered across logs, making it nearly impossible to reconstruct the full sequence of events that led to a particular outcome. Compliance with regulations such as GDPR or financial auditing standards becomes impractical.

- **Difficulty in Parallel Execution**: Many frameworks execute agents sequentially or require complex hand‑crafted workflows. Automatic parallelisation based on task dependencies is rarely supported, leading to underutilised infrastructure and increased latency.

These problems are not merely academic; they manifest in production systems where cost overruns, security breaches, and operational complexity hinder the adoption of agentic AI.

---

### 3. Motivation of Study

The motivation for N‑Agent arises from the observation that agents should be treated as **functions** rather than **services**. In cloud computing, serverless functions have revolutionised scalability by spinning up compute only when needed and discarding it afterward. Applying this paradigm to AI agents promises analogous benefits:

- **Cost Efficiency**: Agents exist only for the duration of their task, eliminating idle‑time costs.
- **Security by Isolation**: By injecting only a precisely defined set of tools into each agent’s namespace, the attack surface is dramatically reduced. An agent literally cannot call a tool it was never given.
- **Deterministic Auditability**: Every message published to the blackboard is stored immutably, creating an end‑to‑end trail suitable for forensic analysis and regulatory compliance.
- **Automatic Parallelism**: A dependency graph derived from task specifications enables the orchestrator to launch all independent agents concurrently, reducing overall execution time.

The confluence of these benefits motivates the design and implementation of N‑Agent as a research prototype and, eventually, as a production‑ready framework. The study aims to validate whether such an architecture can achieve the promised gains without introducing prohibitive overhead.

---

### 4. Aims and Objectives

**Aim**  
To design, implement, and evaluate N‑Agent, an orchestration framework that dynamically composes ephemeral agents with capability‑based security and dependency‑aware parallel execution, and to demonstrate its superiority over conventional multi‑agent systems in terms of security, cost, and auditability.

**Objectives**  
1. **Develop the GlobalToolRegistry**: A centralised vault that stores executable function pointers and their corresponding JSON schemas, capable of injecting only authorised tools into agent instances.  
2. **Implement the JITCompiler**: An orchestrator that, given a task manifest, spawns agents on‑demand, resolves dependencies via an event blackboard, and manages agent lifecycles.  
3. **Construct the EventBlackboard**: A persistent, immutable message bus that records all inter‑agent communications and provides both synchronous subscription for dependency waiting and historical querying for audit.  
4. **Enable Dependency‑Aware Parallel Execution**: Design a scheduler that analyses task dependencies and launches agents as soon as their prerequisites are satisfied, maximising concurrency.  
5. **Evaluate the System**: Measure context‑window savings, tool‑call security enforcement, execution latency, and audit completeness against baseline frameworks (e.g., LangChain, AutoGPT) using representative benchmarks.  
6. **Document the Architecture**: Produce comprehensive design documents and user guides to facilitate adoption and further research.

---

### 5. Methodology

The project will be executed in iterative phases, combining theoretical design with practical implementation and evaluation.

**Phase 1: Core Component Design**  
- Define data structures: `AgentBlueprint`, `SubTask`, `SynthesisManifest`, `A2AMessage`.  
- Specify the interfaces for `GlobalToolRegistry`, `EventBlackboard`, and `JITCompiler`.  
- Choose technology stack: Python 3.11+, asyncio for concurrency, Redis for persistent blackboard storage, and OpenAI‑compatible LLM clients.

**Phase 2: Implementation of Foundational Components**  
- Build `GlobalToolRegistry` with methods `register_tool`, `get_ephemeral_toolkit`, `get_ephemeral_schemas`, and `list_available_tools`.  
- Implement `EventBlackboard` with in‑memory queues for live routing and Redis backend for persistent history. Include `publish`, `subscribe`, `unsubscribe`, and `get_thread_history`.  
- Develop the `JITCompiler`’s core loop: parsing manifests, building dependency graphs, and spawning agents using asyncio tasks.

**Phase 3: Dependency Resolution and Parallel Execution**  
- Enhance the compiler to use a directed acyclic graph (DAG) of tasks.  
- Implement a ready queue and monitor task completion via `asyncio.wait` to trigger dependent agents.  
- Integrate blackboard subscription for dependency blocking within each agent’s execution.

**Phase 4: Security Enforcement**  
- Ensure that `get_ephemeral_toolkit` returns **only** the requested function pointers; any attempt by an agent to call an unlisted tool results in a `PermissionError`.  
- Validate that tool schemas supplied to the LLM are strictly limited to the allowed set, preventing the model from even knowing about other capabilities.

**Phase 5: Persistence and Auditability**  
- Extend `EventBlackboard` to persist all messages to Redis with appropriate time‑to‑live (TTL) policies.  
- Provide query interfaces for retrieving thread history, cost summaries, and agent lifecycles.

**Phase 6: Evaluation and Benchmarking**  
- Select a suite of multi‑agent tasks (e.g., customer support ticket processing, code review, data analysis).  
- Implement equivalent solutions using baseline frameworks.  
- Measure metrics: tokens consumed per agent, execution time, number of security violations (simulated), audit completeness, and infrastructure overhead.  
- Analyse results and refine the architecture accordingly.

**Phase 7: Documentation and Dissemination**  
- Write API documentation, architectural overview, and usage examples.  
- Prepare a research paper for submission to a relevant conference (e.g., NeurIPS, ICML workshop).  
- Release the code as open source with a permissive licence.

---

### 6. Significance of the Study

The N‑Agent project addresses foundational gaps in the design of production‑ready multi‑agent systems:

- **Security by Construction**: By moving from permission checks to capability injection, the system eliminates entire classes of vulnerabilities. This is particularly critical for applications handling sensitive data or interacting with external services.

- **Economic Efficiency**: Reducing context‑window usage directly lowers LLM API costs. The ephemeral nature of agents also minimises idle compute, making large‑scale deployments financially viable.

- **Regulatory Compliance**: The immutable blackboard provides a tamper‑evident log of every decision and action, satisfying audit requirements in finance, healthcare, and other regulated industries.

- **Scalability**: Automatic parallelisation based on data dependencies allows the system to fully utilise modern hardware and cloud infrastructure, reducing task completion times.

- **Academic Contribution**: The project offers a concrete instantiation of theoretical concepts (capability security, event sourcing, dataflow programming) in the domain of LLM agents, providing a basis for further research.

The outcomes of this study will benefit both industry practitioners seeking robust agent orchestration and researchers exploring the intersection of programming languages, security, and AI.

---

### 7. Scope of the Study

The project will focus on the following aspects:

- **Agent Lifecycle**: Only ephemeral agents are considered; persistent agents are out of scope, although the blackboard’s persistent storage allows long‑running workflows via sequences of ephemeral agents.
- **Tool Integration**: The registry will initially support custom Python functions and integrations via Composio. Wrapping tools from other ecosystems (LangChain, CrewAI) is planned but not part of the core evaluation.
- **Communication Model**: Agents communicate exclusively through the blackboard; direct agent‑to‑agent messaging is not supported.
- **Scalability Limits**: The study will evaluate performance with up to 100 concurrent agents; extreme scale (thousands) is left for future work.
- **LLM Backend**: The implementation assumes an OpenAI‑compatible API; support for other providers (Anthropic, open‑source models) can be added later.
- **Security Analysis**: The evaluation will include penetration testing simulations but not formal verification.

Excluded are topics such as agent learning, dynamic tool creation, and multi‑modal inputs.

---

### 8. Definition of Terms

- **Ephemeral Agent**: An AI agent instantiated for a single task, provided with a limited set of tools, and terminated immediately after task completion. It leaves no residual state except its published messages.

- **GlobalToolRegistry**: A central component that stores all available tools (as executable code and JSON schemas) and, upon request, returns a restricted toolkit containing only the functions an agent is permitted to use.

- **JITCompiler**: The orchestrator that interprets a `SynthesisManifest`, resolves task dependencies, spawns agents at the appropriate time, and monitors their execution.

- **EventBlackboard**: A persistent message bus that records every communication between agents and system components. Agents subscribe to topics (task IDs) to await inputs and publish their results to the same topics.

- **SynthesisManifest**: A high‑level plan comprising multiple `AgentBlueprint`s, each specifying the target task, persona, permitted tools, and termination condition.

- **AgentBlueprint**: A template for creating an agent, including its persona prompt, the list of tools it may access, temperature, and termination condition.

- **SubTask**: A unit of work with a unique identifier, description, and a list of dependencies (other task IDs whose outputs are required).

- **A2AMessage**: The standard message format exchanged via the blackboard, containing sender, receiver, payload, timestamp, and metadata.

- **Dependency Graph**: A directed acyclic graph representing the relationships between tasks, used by the JITCompiler to determine which agents can run in parallel.

- **Capability‑Based Security**: A security model where access to resources is granted by possession of an unforgeable reference (capability) rather than by identity‑based permissions. In N‑Agent, the toolkit itself is the capability.
