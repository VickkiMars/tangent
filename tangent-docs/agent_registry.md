# Agent Registry & Reuse-First Spawning

## Core Concept
The MetaAgent within the Tangent framework never spawns agents "blind." Before generating a completely new Agent Blueprint from scratch, the orchestration engine queries a persistent registry of battle-tested personas. It attempts to find the closest fit—making spawning the absolute last resort, not the first.

---

## The Registry Record (Schema)

Each registry entry (referred to in the database as `personas`) stores a complete profile of a specialized agent.

```json
{
  "id": "uuid",
  "title": "Data Extraction Specialist",
  "description": "Extracts structured data from unstructured sources",
  "prompt": "You are a...",
  "tools": ["web_scraper", "html_parser", "csv_writer"],
  "tags": ["extraction", "parsing", "ETL"],
  "success_rate": 0.94,
  "avg_task_duration_ms": 1200,
  "total_runs": 87,
  "last_used": "2026-05-19T14:22:00Z",
  "created_by": "meta_agent",
  "version": 3
}
```

To maintain a lean context window, the MetaAgent evaluates the `title`, `description`, `tools`, `tags`, and `success_rate`—it does *not* read the full base prompt during the initial query phase.

---

## The Spawning Decision Tree

When the MetaAgent decomposes a user objective into a DAG of sub-tasks, it evaluates each sub-task against the registry using the following flow:

```
MetaAgent creates a SubTask
        ↓
Query Registry (Semantic Search via LLM + Hard filter on required tools)
        ↓
Match found (score > threshold)?
    ├── YES, score > 0.9   → REUSE: Use the persona exactly as-is.
    ├── YES, score 0.6–0.9 → MUTATE: Clone the persona and patch the prompt/toolcase.
    └── NO, score < 0.6    → SPAWN: Create a new agent from scratch.
```

### Mutation vs. Spawn
Mutation is the highly efficient middle path. You retain 80% of a proven agent's capability and apply a targeted override rather than starting from zero.

When mutating, the MetaAgent applies a diff instruction (e.g., *"Base: Data Extraction Specialist. Override: target is a PDF not HTML. Add `pdf_parser`"*). If the mutated agent succeeds, it is saved as a **new version** (child persona), maintaining an organic lineage tree of specialization.

---

## Performance-Weighted Selection

When multiple personas score similarly on semantic match, the system ranks them using historical telemetry:
1. **`success_rate`** (Quality/Reliability)
2. **`avg_task_duration_ms`** (Speed)
3. **`total_runs`** (Battle-tested preference)
4. **`last_used`** (Freshness signal)

This creates a self-improving registry: degraded or slow agents get outcompeted and gradually fall out of the selection pool.

---

## Post-Run Feedback Loop

After every ephemeral execution, the JIT Compiler feeds the results back into the registry:
- **Success/Failure:** Updates the rolling `success_rate` and `total_runs`.
- **Duration:** Updates the `avg_task_duration_ms`.
- **Lineage Tracking:** If the agent was a Mutation or a brand new Spawn, it gets permanently registered into the database upon success, making the system's institutional memory robust over time.
