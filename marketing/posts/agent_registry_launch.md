# Stop Spawning Blind: Introducing the Tangent Agent Registry

If you've built multi-agent systems, you know the drill: your orchestrator receives a complex objective, breaks it down, and furiously spawns a dozen fresh LLM agents from scratch to solve it. 

It works, but it’s brutally inefficient. 

Why spin up a brand new "Data Extraction Agent" every single time when you already successfully ran one 10 minutes ago? 

**Today, we’re fixing that with the Tangent Agent Registry and Reuse-First Spawning.**

### The Orchestrator That Remembers
We've rewritten Tangent's MetaAgent orchestration engine. It no longer spawns agents blindly. Instead, it queries a persistent, database-backed registry of battle-tested personas. Spawning an agent from scratch is now the absolute last resort.

Here’s how the new Spawning Decision Tree works under the hood:

1. **Semantic Match:** When a task is generated, Tangent performs a semantic search against the registry to find the closest historical persona.
2. **Hard Tool Filters:** It aggressively filters out any persona that doesn't have the exact tools required for the job.
3. **Performance Ranking:** If multiple personas match, they are ranked by their rolling historical `success_rate` and `avg_task_duration_ms`. Fast, reliable agents rise to the top; slow or failing agents get buried.

### REUSE, MUTATE, SPAWN
Based on the semantic match score, Tangent executes one of three actions:

- **REUSE (Score > 0.9):** The perfect match. Tangent injects the proven persona exactly as-is, saving massive token overhead and ensuring predictable reliability.
- **MUTATE (Score 0.6–0.9):** The sweet spot. Tangent clones an 80% matching persona and applies a targeted diff instruction (e.g., *"Base: Web Scraper. Override: target is a PDF not HTML"*). 
- **SPAWN (Score < 0.6):** Only when completely necessary, Tangent builds a fresh agent from scratch.

### An Organic Lineage of Agents
The best part? **The Post-Run Feedback Loop.**

Every time a *Mutated* or *Spawned* agent successfully completes a task, the JIT Compiler extracts its exact configuration and permanently saves it back into the registry as a new version. 

Over time, your Tangent instance builds an organic lineage tree of hyper-specialized agents—an institutional memory that gets smarter, faster, and cheaper with every single execution.

Stop rebuilding the wheel. Let your agents remember. 🧠⚡
