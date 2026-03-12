import instructor
import structlog
import litellm
from typing import List
from schemas import SynthesisManifest
from prompts import META_AGENT_SYSTEM_PROMPT
# Assume models (SubTask, AgentBlueprint, SynthesisManifest) are imported
# from your_schema_file import SubTask, AgentBlueprint, SynthesisManifest

logger = structlog.get_logger(__name__)

class MetaAgent:
    def __init__(self, model_name="gemini/gemini-1.5-flash"):
        # We patch the client to enforce Pydantic structure
        self.client = instructor.from_litellm(litellm.completion)
        self.model_name = model_name

    def architect_workflow(self, user_objective: str, available_tool_names: List[str]) -> SynthesisManifest:
        """
        Compiles the user's intent directly into a SynthesisManifest representing the DAG.
        The Meta-Agent is now purely a structural architect, not an evaluator.
        """
        
        # 1. Contextualize the Tool Registry for the Architect
        tools_context = ", ".join(available_tool_names)
        logger.info("meta_architecting_workflow", tool_count=len(available_tool_names))
        
        # 2. Invoke the Architect
        manifest = self.client.chat.completions.create(
            model=self.model_name,
            response_model=SynthesisManifest,
            messages=[
                {
                    "role": "system", 
                    "content": META_AGENT_SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": f"""
                    Objective: "{user_objective}"
                    
                    Available Tools: [{tools_context}]
                    
                    Generate the SynthesisManifest containing the precise Blueprints and Task Routing (dependencies).
                    """
                }
            ],
            temperature=0.1, # High determinism for architecture
        )
        
        logger.info("meta_manifest_generated", blueprints=len(manifest.blueprints))
        
        return manifest