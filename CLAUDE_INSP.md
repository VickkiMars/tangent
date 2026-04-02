# Claude Code Inspiration — Tangent Improvement Suggestions

_Derived from analysis of `claude-code-doc/` internals, with special focus on Coordinator Mode._

---

## Overview

Tangent is a static DAG orchestrator: the MetaAgent plans upfront, the JITCompiler executes, agents live and die. Claude Code's Coordinator Mode is a live LLM session that reasons dynamically — it decides what to spawn, when to continue a worker, and how to adapt based on results as they arrive. These two models are complementary, and Tangent has clear gaps that Coordinator Mode fills.

---

## 1. Coordinator Mode Deep Dive

**File:** `claude-code-doc/coordinator/coordinatorMode.ts`

The Coordinator is not a dispatcher or planner — it is a persistent LLM session with its own tool set:
- `Agent` — spawn a background worker
- `SendMessage` — continue/message an existing worker by name or ID
- `TaskStop` — kill a worker
- MCP subscription tools (PR webhooks, etc.)

Worker results are delivered back to the coordinator as **`<task-notification>` XML injected as user-role messages**. The coordinator's context grows with each result, so it can reason across all prior findings before deciding next steps.

The key design insight from the system prompt:
> "Every message you send is to the user. Worker results and system notifications are internal signals — never thank or acknowledge them."

The coordinator reasons through distinct phases (defined in its prompt as an explicit table):

| Phase | Executor | Purpose |
|---|---|---|
| Research | Workers (parallel) | Investigate, find files, understand scope |
| Synthesis | Coordinator | Read findings, craft implementation spec |
| Implementation | Workers | Make changes, commit |
| Verification | Workers (fresh, not continued) | Prove it works independently |

**Parallelism is explicit:** "To launch workers in parallel, make multiple tool calls in a single message."

**Continue vs. Spawn Fresh decision matrix** is baked into the prompt: `SendMessage` when context overlap is high; spawn fresh when the worker has wrong context or for independent verification.

---

## 2. Gap Analysis & Suggestions

### 2.1 — Dynamic Re-Planning (Coordinator Persistence)

**Current problem:** Tangent's MetaAgent is one-shot. It generates the full manifest, gets discarded, and the JITCompiler executes it blindly. If an agent fails or the results suggest a different approach, there is no adaptive reasoning layer.

**What to build:**

Implement a **Coordinator Agent** — a persistent LLM session that lives for the lifetime of the workflow. Instead of the MetaAgent generating the entire DAG upfront, the Coordinator:

1. Receives the user objective
2. Spawns an initial wave of research agents
3. Receives their results (via blackboard notifications redelivered to the Coordinator's message history)
4. Synthesizes findings and decides the next set of agents to spawn
5. Repeats until the workflow is complete

The Coordinator session is a standard LLM conversation loop — no new infrastructure needed, just a persistent `messages[]` list and a set of orchestration tools.

**Model for the coordinator call:**
```python
# coordinator_session.py
messages = [{"role": "system", "content": COORDINATOR_SYSTEM_PROMPT}]

async def on_agent_result(task_id: str, result: str, status: str):
    messages.append({
        "role": "user",
        "content": f"""<task-notification>
<task-id>{task_id}</task-id>
<status>{status}</status>
<result>{result}</result>
</task-notification>"""
    })
    await coordinator_turn()  # let coordinator decide next step

async def coordinator_turn():
    response = await llm_call(messages, tools=COORDINATOR_TOOLS)
    # handle Agent/SendMessage/TaskStop tool calls
```

**System prompt key rules to adopt from claude-code-doc:**
- Never re-delegate understanding ("based on your findings, fix it" is an anti-pattern — summarize the finding in the next worker's prompt)
- Workers cannot see the coordinator's conversation — always inject context explicitly into each worker prompt
- Verification workers must be spawned fresh (not continued) to get independent perspective

---

### 2.2 — Worker Continuation via SendMessage

**Current problem:** Tangent's hibernation pathway (`request_human_input`) serializes agent state to Redis and resumes it, but agents can only be resumed with a user-provided objective, not a follow-up message from the coordinator. Mid-flight continuation (e.g., "you found the files, now also check X") is impossible.

**What to build:**

A `send_message_to_agent(task_id: str, message: str)` tool for the coordinator that:
1. If the agent is **running** — queues the message; agent receives it at the next tool boundary
2. If the agent is **hibernated** — appends the message to its Redis history and resumes it
3. If the agent is **done** — auto-resumes from its saved transcript with the new message

Implementation sketch:
```python
# In blackboard.py or compiler.py
async def send_message_to_agent(task_id: str, message: str):
    agent_state = await blackboard.get_agent_state(task_id)
    if agent_state.status == "running":
        await blackboard.publish(f"agent:{task_id}:inbox", message)
    elif agent_state.status == "hibernated":
        history = await blackboard.load_agent_history(task_id)
        history.append({"role": "user", "content": message})
        await blackboard.save_agent_history(task_id, history)
        await resume_agent(task_id)
```

Worker agents need a small inbox loop — check the inbox topic between tool calls and inject pending messages into their conversation.

---

### 2.3 — Shared Scratchpad Directory

**Current problem:** Tangent workers communicate only through blackboard `natural_language` string payloads. There is no shared structured knowledge store. Worker A's intermediate findings (e.g., a parsed JSON, a list of URLs, code snippets) cannot be consumed as structured data by Worker B.

**What to build:**

A per-workflow **scratchpad** — either a temp directory or a Redis hash — that all workers can read/write without going through the blackboard message format:

```python
# In schemas.py — add to AgentBlueprint
scratchpad_path: Optional[str] = None  # injected by coordinator at spawn time

# In compiler.py — create per-workflow scratchpad
async def execute_manifest(manifest: SynthesisManifest, ...):
    scratchpad = f"/tmp/tangent/{workflow_id}/scratch"
    os.makedirs(scratchpad, exist_ok=True)
    for blueprint in manifest.agents:
        blueprint.scratchpad_path = scratchpad
```

Inject the path into each worker's system prompt:
> "You have access to a shared scratchpad at `{scratchpad_path}`. Write intermediate findings as JSON files. Read files written by prior agents to avoid duplicating work."

Workers can then use a `read_scratchpad(filename)` / `write_scratchpad(filename, content)` tool pair instead of relying on downstream agents re-reading everything from their prompt context.

---

### 2.4 — Verification Phase (Built Into Orchestration)

**Current problem:** No verification step. Agents produce output and it's assumed correct. There is no second agent that independently validates results.

**What to build:**

Update `prompts.py` (`META_AGENT_SYSTEM_PROMPT`) to make verification mandatory for implementation agents:

```
ORCHESTRATION PHASES:
1. Research — parallel agents investigate, discover, and report
2. Synthesis — coordinator digests findings (no agents spawned here)
3. Implementation — agents make changes based on synthesized spec
4. Verification — ALWAYS spawn a fresh verification agent after any implementation agent completes.
   The verification agent must NOT be a continuation of the implementation agent.
   It receives only: the original objective + the implementation agent's output summary.
   It must independently confirm the result meets the termination condition.
```

In the `AgentBlueprint` schema, add:
```python
requires_verification: bool = False  # MetaAgent sets this for implementation agents
verification_criteria: Optional[str] = None  # what to check
```

In `compiler.py`, after an implementation agent completes, auto-spawn a verifier:
```python
if blueprint.requires_verification:
    verifier = AgentBlueprint(
        agent_id=f"verifier_{blueprint.agent_id}",
        persona_prompt=f"Verify: {blueprint.verification_criteria}",
        injected_tools=[...read-only tools only...],
        dependencies=[blueprint.target_task_id],
    )
    await _spawn_ephemeral_agent(verifier, ...)
```

---

### 2.5 — Deferred Tool Discovery (ToolSearch Pattern)

**Current problem:** Every agent receives the full schemas for all its allowed tools upfront in the system prompt. For large tool registries, this wastes significant tokens on tools the agent never uses.

**What to build:**

Adopt claude-code-doc's `ToolSearch` pattern:

1. Mark most tools as "deferred" — include only their name and a one-line description in the initial prompt
2. Provide a `discover_tools(query: str) -> list[ToolSchema]` tool
3. The agent calls `discover_tools("web search")` and receives the full schema for matching tools

```python
# In registry.py
class GlobalToolRegistry:
    def get_tool_stubs(self, tool_names: list[str]) -> list[ToolStub]:
        """Returns name + description only, no full schema."""
        ...

    def get_tool_schema(self, tool_name: str) -> ToolSchema:
        """Returns full schema for a single named tool."""
        ...

# New tool: discover_system_tools (replace the existing one)
async def discover_tools(query: str) -> list[dict]:
    """Semantic search over registered tools, returns full schemas for matches."""
    results = registry.semantic_search(query, top_k=5)
    return [registry.get_tool_schema(name) for name in results]
```

Estimated token savings: 40–70% on tool-heavy workloads where agents only use 2–3 of their 10+ allowed tools.

---

### 2.6 — Agent Summarization on Completion

**Current problem:** When downstream agents depend on upstream results, they receive the raw `natural_language` output string from the blackboard. For long-running agents that produce verbose output, this floods the dependent agent's context.

**What to build:**

Auto-summarize agent output before publishing to the blackboard:

```python
# In compiler.py — _spawn_ephemeral_agent()
async def _summarize_agent_output(task_id: str, full_output: str) -> str:
    summary_prompt = f"""Summarize this agent's findings in under 300 words.
    Focus on: key facts, decisions made, outputs produced, and what's left for downstream agents.
    
    Agent output:
    {full_output[:8000]}"""
    
    summary = await litellm.acompletion(
        model="gemini-flash",  # cheap summarizer
        messages=[{"role": "user", "content": summary_prompt}]
    )
    return summary.choices[0].message.content

# After agent completes:
summary = await _summarize_agent_output(task_id, agent_result)
await blackboard.publish(
    blueprint.target_task_id,
    A2AMessage(performative="inform", content=summary, full_content=agent_result)
)
```

Dependents receive the summary. Coordinator (if implemented) receives the summary in `<task-notification>`. Full content stays in Redis for inspection.

---

### 2.7 — Per-Task Budget Limits

**Current problem:** Tangent enforces per-user budgets (`max_budget_usd`) but not per-task or per-agent budgets. A single runaway agent can consume the entire workflow budget.

**What to build:**

Add `max_cost_usd: Optional[float]` to `AgentBlueprint` and enforce it in `_spawn_ephemeral_agent()`:

```python
# In compiler.py
agent_cost = 0.0

async def _llm_call_with_budget(blueprint, messages, tools):
    nonlocal agent_cost
    response = await litellm.acompletion(...)
    call_cost = litellm.completion_cost(response)
    agent_cost += call_cost
    
    if blueprint.max_cost_usd and agent_cost > blueprint.max_cost_usd:
        raise BudgetExceededError(
            f"Agent {blueprint.agent_id} exceeded budget: "
            f"${agent_cost:.4f} > ${blueprint.max_cost_usd}"
        )
    return response
```

Publish a `budget_exceeded` performative to the dead letter queue so the coordinator can decide whether to retry with a cheaper model.

---

### 2.8 — Dynamic Task Spawning at Runtime

**Current problem:** All agent blueprints must be declared upfront in the manifest. Agents cannot spawn sub-agents at runtime. The `INFRASTRUCTURE_GAPS.md` explicitly lists this.

**What to build:**

Add a `spawn_subtask(task_description, tools, model, depends_on_current=True)` tool to the agent toolkit:

```python
async def spawn_subtask(
    task_description: str,
    injected_tools: list[str],
    model: str = "default",
    depends_on_current: bool = True,
) -> str:
    """Spawn a child agent. Returns the child task_id."""
    child_blueprint = AgentBlueprint(
        agent_id=f"{current_agent_id}_child_{uuid4().hex[:6]}",
        persona_prompt=task_description,
        injected_tools=injected_tools,
        dependencies=[current_task_id] if depends_on_current else [],
        parent_task_id=current_agent_id,
    )
    await compiler.spawn_single_agent(child_blueprint)
    return child_blueprint.agent_id
```

This closes the most significant architectural gap between Tangent and Coordinator Mode — it allows recursive decomposition at runtime, not just at planning time.

---

## 3. Lower-Priority / Longer-Term Ideas

### Git Worktree Isolation
Claude Code's `AgentTool` supports `isolation: "worktree"` — spawning agents in isolated git worktrees so parallel implementation agents don't conflict. For Tangent's code-related workloads, wrapping each implementation agent's execution in a temp worktree (using `git worktree add`) would prevent file conflicts and make merging explicit.

### Skill / Workflow Templates
Claude Code has reusable SKILL.md files that pre-define common workflows (commit, review-pr, etc.). Tangent's `.agent/skills/` has business-domain skills but they're not integrated into the runtime. Formalizing a `SkillLibrary` that the MetaAgent can reference when constructing blueprints (e.g., "use the `web_research` skill template for information-gathering agents") would reduce prompt engineering in the MetaAgent and improve consistency.

### Session Resume with Mode Awareness
Claude Code's `matchSessionMode()` detects when a resumed session was in coordinator mode and automatically re-enables it. Tangent's workflow resume (`POST /resume`) already injects prior context — add a `workflow_mode` field to the persisted state so resumed workflows can restart in the right orchestration configuration.

### Cross-Workflow Memory
Claude Code's agent memory system persists successful patterns across sessions. Tangent's optimizer daemon (`optimization.py`) already generates recommendations — close the loop by feeding those recommendations into a `WorkflowMemory` store that the MetaAgent queries at the start of each new workflow: "have I seen a similar objective before? what worked?"

---

## 4. Summary — Priority Order

| Priority | Suggestion | Effort | Impact |
|---|---|---|---|
| 1 | Persistent Coordinator Agent (§2.1) | High | Transforms orchestration model |
| 2 | Worker Continuation / SendMessage (§2.2) | Medium | Eliminates cold-restart waste |
| 3 | Dynamic Subtask Spawning (§2.8) | Medium | Closes biggest architecture gap |
| 4 | Shared Scratchpad (§2.3) | Low | Structured inter-agent data sharing |
| 5 | Verification Phase (§2.4) | Low | Output quality assurance |
| 6 | Deferred Tool Discovery (§2.5) | Medium | Token efficiency |
| 7 | Agent Output Summarization (§2.6) | Low | Context window management |
| 8 | Per-Task Budget Limits (§2.7) | Low | Cost control granularity |
