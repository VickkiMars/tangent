import asyncio
import json
import structlog
from db import get_workflow_analytics
import datetime

logger = structlog.get_logger(__name__)

async def optimize_blueprints_task(session_id: str, state_manager, blackboard):
    """
    Background daemon that analyzes completed threads and generates optimizer feedback
    to store in query_optimizations or for future blueprint generation.
    """
    try:
        # 1. Load the state and tools
        state = await state_manager.load_state(session_id)
        if not state or not state.manifest:
            return
            
        # 2. Extract run metrics
        task_ids = [t.task_id for t in state.tasks]
        analytics = await asyncio.to_thread(get_workflow_analytics, task_ids)
        
        # Determine if optimization is necessary (e.g. poor success rates or high cost/tokens)
        poor_performance_agents = [a for a in analytics if not a.get("was_successful", True) or a.get("tokens_prompt", 0) > 4000]
        
        if not poor_performance_agents:
            logger.info("optimization_skipped", reason="Run metrics within acceptable bounds", session_id=session_id)
            return
            
        # 3. Formulate optimization prompt
        history = await blackboard.get_thread_history(thread_ids=set(task_ids))
        
        history_summary = "\n".join([f"[{m.sender_id} -> {m.receiver_id}]: {m.payload.natural_language[:200]}..." for m in history[-20:]])
        
        optimization_prompt = f"""
        Analyze the following agent execution thread which showed poor performance or high cost.
        Original Objective: {state.original_objective}
        
        Problematic Agents (Analytics metrics):
        {json.dumps(poor_performance_agents, indent=2)}
        
        Recent Thread History:
        {history_summary}
        
        Provide 2 concrete recommendations:
        1. Query Optimization: How should the original prompt or agent persona be rewritten to be more efficient?
        2. Tooling Improvement: What specific tools were missing or misused?
        
        Output as a JSON object with keys 'optimized_persona' and 'tooling_recommendation'.
        """
        
        # 4. Request Meta Agent to Synthesize Improvements
        provider_name = "google"
        model_name = "gemini-3.1-flash-lite-preview"
        from llm_provider import LLMFactory
        llm_provider = LLMFactory.get_provider(provider_name, model=model_name)
        
        messages = [
            {"role": "system", "content": "You are the Automated Blueprint Optimizer. Identify inefficiencies in agent runs."},
            {"role": "user", "content": optimization_prompt}
        ]
        
        response = await llm_provider.generate(messages=messages, temperature=0.1)
        recommendation = response.choices[0].message.content
        
        logger.info("blueprint_optimized", session_id=session_id, recommendation=recommendation)
        
        # Note: At a larger scale, we would intercept and write this to query_optimizations DB
    except Exception as e:
        logger.error("optimization_failed", session_id=session_id, error=str(e))
