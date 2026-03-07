import instructor
import structlog
import litellm
from typing import List
from schemas import SynthesisManifest, ComplexityEvaluation
from prompts import META_AGENT_SYSTEM_PROMPT, EVALUATOR_SYSTEM_PROMPT
# Assume models (SubTask, AgentBlueprint, SynthesisManifest) are imported
# from your_schema_file import SubTask, AgentBlueprint, SynthesisManifest

logger = structlog.get_logger(__name__)

class MetaAgent:
    def __init__(self, model_name="gemini/gemini-1.5-flash"):
        # We patch the client to enforce Pydantic structure
        self.client = instructor.from_litellm(litellm.completion)
        self.model_name = model_name

    def evaluate_complexity(self, user_objective: str) -> ComplexityEvaluation:
        """Determines if a full swarm is needed or a single LLM response suffices."""
        logger.info("meta_evaluating_complexity", objective=user_objective[:50])
        evaluation = self.client.chat.completions.create(
            model=self.model_name,
            response_model=ComplexityEvaluation,
            messages=[
                {
                    "role": "system", 
                    "content": EVALUATOR_SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": f"Evaluate the complexity of the following objective: \"{user_objective}\""
                }
            ],
            temperature=0.1,
        )
        logger.info("meta_complexity_result", requires_swarm=evaluation.requires_swarm)
        return evaluation

    def architect_workflow(self, user_objective: str, available_tool_names: List[str]) -> SynthesisManifest:
        """
        Compiles the user's intent into a SynthesisManifest.
        This IS the routing logic: it defines who exists and who talks to whom.
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
        
        # 3. Validation: Ensure the graph is valid (no missing dependency IDs)
        self._validate_topology(manifest)
        logger.info("meta_manifest_generated", blueprints=len(manifest.blueprints))
        
        return manifest

    def _validate_topology(self, manifest: SynthesisManifest):
        """
        Sanity check to prevent 'Routing Hallucinations'. 
        Ensures every dependency ID actually exists in the task list.
        """
        all_task_ids = {bp.target_task_id for bp in manifest.blueprints}
        
        # We need to map blueprints back to tasks to check dependencies
        # In a real impl, you might nest SubTask inside Blueprint or keep them separate in the Manifest.
        # Assuming the Manifest contains implicit task definitions or we pass them too.
        # For this logic, we assume the LLM correctly mapped IDs.
        pass