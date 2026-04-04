import instructor
import structlog
import litellm
from datetime import date
from typing import Dict, List, Optional
from core.schemas import SynthesisManifest
from engine.prompts import META_AGENT_SYSTEM_PROMPT

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
        user_message = (
            f'Current date: {today}\n\n'
            f'Objective: "{user_objective}"\n\n'
            f"Available Tools:\n{tools_context}\n\n"
            "Generate the SynthesisManifest containing the precise Blueprints and Task Routing (dependencies)."
        )

        logger.info(
            "meta_input",
            tool_count=len(available_tool_names),
            objective=user_objective,
            tools=available_tool_names,
        )

        manifest = self.client.chat.completions.create(
            model=self.model_name,
            response_model=SynthesisManifest,
            messages=[
                {"role": "system", "content": META_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=1.0,
        )

        logger.info(
            "meta_output",
            blueprints=len(manifest.blueprints),
            manifest=[b.model_dump() for b in manifest.blueprints],
        )
        return manifest