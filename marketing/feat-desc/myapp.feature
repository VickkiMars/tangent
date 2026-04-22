### The Scenario: A "Weekly Code Auditor"
Imagine you frequently want your AI agent to check your project for specific code smells, summarize them, and write the findings to a markdown report. 

#### Step 1: Creation (In the Workspace)
Instead of manually doing this every Friday, you enter the Tangent **Workspace** and give the agent a prompt:
> *"Search the codebase for any '# TODO' and '# FIXME' comments. Read the context around those lines, summarize the 5 most critical ones based on severity, and write the summary to `audit_report.md`."*

The AI platform "thinks," orchestrates the necessary tools (like `grep_search`, `view_file`, and `write_to_file`), and successfully runs this multi-step workflow.

#### Step 2: Saving as an App
Once the workflow finishes and you are satisfied with the result, you realize you'll need this exact process again next week. You click a button to **Save as App** and name it **"Weekly Code Auditor"**.
*Behind the scenes:* Tangent takes the complex, compiled workflow logic you just orchestrated and saves its exact instructions to the database.

#### Step 3: Reusing the App (In "My Apps")
Next Friday rolls around. Instead of typing out that long prompt again and waiting for the AI to figure out which tools to use and how to chain them together, you simply:
1. Navigate to the **My Apps** page.
2. Find the **"Weekly Code Auditor"** app card.
3. Click **Deploy**.

#### What Happens Next:
The application instantly redirects you to a fresh Workspace session. However, it completely skips the AI's "planning" phase. It immediately begins executing the exact sequence of tool calls you saved—fetching the latest TODOs from the *current* state of the codebase and generating the new report. 

### Why is this powerful?
It allows you to transition an AI interaction from a **dynamic, conversational task** (which costs time and tokens for prompt engineering) into a **static, click-and-run utility** (which runs predictably and instantly whenever you need it).
