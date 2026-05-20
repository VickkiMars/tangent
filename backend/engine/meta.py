import instructor
import structlog
import litellm
from datetime import date
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from core.schemas import SynthesisManifest, SubTask
from engine.prompts import META_AGENT_SYSTEM_PROMPT
from engine.registry_search import query_registry

class TaskDecomposition(BaseModel):
    tasks: List[SubTask] = Field(description="The DAG of tasks to accomplish the objective")

logger = structlog.get_logger(__name__)

class MetaAgent:
    def __init__(self, model_name="gemini/gemini-1.5-flash"):
        # We patch the client to enforce Pydantic structure
        self.client = instructor.from_litellm(litellm.completion)
        self.model_name = model_name

    def architect_workflow(
        self,
        user_objective: str,
        available_tool_names: List[str],
        tool_descriptions: Optional[Dict[str, str]] = None
    ) -> SynthesisManifest:
        """
        Compiles the user's intent directly into a SynthesisManifest representing the DAG.
        The Meta-Agent is now purely a structural architect, not an evaluator.
        """

        # Build a rich tool list that includes descriptions when available so the
        # meta agent can make informed assignment decisions.
        if tool_descriptions:
            tools_lines = [
                f"- {name}: {tool_descriptions.get(name, '').strip() or 'No description'}"
                for name in available_tool_names
            ]
            tools_context = "\n".join(tools_lines)
        else:
            tools_context = "\n".join(f"- {name}" for name in available_tool_names)

        today = date.today().isoformat()
        user_message_1 = (
            f'Current date: {today}\n\n'
            f'Objective: "{user_objective}"\n\n'
            f"Available Tools:\n{tools_context}\n\n"
            "Step 1: Decompose the objective into a DAG of SubTasks."
        )

        logger.info("meta_input_decomposition", objective=user_objective)

        decomposition = self.client.chat.completions.create(
            model=self.model_name,
            response_model=TaskDecomposition,
            messages=[
                {"role": "system", "content": META_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message_1},
            ],
            temperature=0.0,
        )

        registry_context = []
        for task in decomposition.tasks:
            reg_res = query_registry(task.description, task.required_capabilities, self.model_name)
            ctx = f"Task '{task.task_id}':\n- Action: {reg_res.action}\n"
            if reg_res.persona:
                ctx += f"- Persona ID: {reg_res.persona['id']}\n"
                ctx += f"- Persona Title: {reg_res.persona['title']}\n"
                ctx += f"- Persona Base Prompt: {reg_res.persona['prompt']}\n"
                ctx += f"- Persona Tools: {reg_res.persona['tools']}\n"
            if reg_res.diff_instruction:
                ctx += f"- Mutation Diff: {reg_res.diff_instruction}\n"
            registry_context.append(ctx)

        registry_text = "\n".join(registry_context)

        user_message_2 = (
            f'Current date: {today}\n\n'
            f'Objective: "{user_objective}"\n\n'
            f"Available Tools:\n{tools_context}\n\n"
            f"Task Decomposition:\n{[t.model_dump() for t in decomposition.tasks]}\n\n"
            f"Registry Recommendations:\n{registry_text}\n\n"
            "Step 2: Generate the final SynthesisManifest. "
            "For REUSE, copy the base prompt and tools exactly and set persona_id. "
            "For MUTATE, apply the Mutation Diff to the base prompt and set persona_id to the base persona_id (it will be forked later). "
            "For SPAWN, create from scratch."
        )

        manifest = self.client.chat.completions.create(
            model=self.model_name,
            response_model=SynthesisManifest,
            messages=[
                {"role": "system", "content": META_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message_2},
            ],
            temperature=1.0,
        )

        # Force the generated manifest's blueprints to align with the registry recommendations
        for bp in manifest.blueprints:
            for task in decomposition.tasks:
                if bp.target_task_id == task.task_id:
                    # Find matching recommendation
                    for ctx in registry_context:
                        if f"Task '{task.task_id}'" in ctx and "- Action: REUSE" in ctx:
                            pid_line = [l for l in ctx.split('\n') if "- Persona ID: " in l]
                            if pid_line:
                                bp.persona_id = pid_line[0].split(": ")[1].strip()
                        elif f"Task '{task.task_id}'" in ctx and "- Action: MUTATE" in ctx:
                            pid_line = [l for l in ctx.split('\n') if "- Persona ID: " in l]
                            if pid_line:
                                parent_id = pid_line[0].split(": ")[1].strip()
                                bp.parent_persona_id = parent_id
                                bp.is_mutation = True
                                bp.persona_id = None # It will be created upon success

        logger.info(
            "meta_output",
            blueprints=len(manifest.blueprints),
            manifest=[b.model_dump() for b in manifest.blueprints],
        )
        return manifest