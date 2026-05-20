import structlog
import litellm
import instructor
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from infrastructure import db

logger = structlog.get_logger(__name__)

class PersonaScore(BaseModel):
    persona_id: str
    semantic_score: float = Field(description="Score from 0.0 to 1.0 indicating semantic match")
    diff_instruction: Optional[str] = Field(default=None, description="If score is between 0.6 and 0.9, provide mutation diff instruction here")

class RegistrySearchResponse(BaseModel):
    scores: List[PersonaScore]

class RegistryQueryResult(BaseModel):
    action: Literal["REUSE", "MUTATE", "SPAWN"]
    persona: Optional[Dict[str, Any]] = None
    diff_instruction: Optional[str] = None

def sort_personas(personas: List[Dict[str, Any]], scores: Dict[str, float]) -> List[Dict[str, Any]]:
    def sort_key(p):
        score = scores.get(p["id"], 0.0)
        success_rate = float(p.get("success_rate", 0.0))
        duration = float(p.get("avg_task_duration_ms", 0.0))
        # Handle duration appropriately (lower is better, so negate or invert)
        duration_score = -duration
        total_runs = int(p.get("total_runs", 0))
        # Simple recency check by string comparison of isoformat is okay, or just rely on total_runs
        last_used = p.get("last_used", "")
        return (score, success_rate, duration_score, total_runs, last_used)
    
    return sorted(personas, key=sort_key, reverse=True)

def query_registry(task_description: str, required_tools: List[str], model_name: str = "gemini/gemini-1.5-flash") -> RegistryQueryResult:
    """
    Executes the Spawning Decision Tree:
    1. Fetches all personas.
    2. Hard filters by required tools.
    3. Uses LLM to semantically score remaining personas.
    4. Applies thresholds to decide REUSE, MUTATE, or SPAWN.
    """
    all_personas = db.get_all_personas()
    
    # 1. Tag/Tool Filter
    filtered_personas = []
    for p in all_personas:
        p_tools = set(p.get("tools") or [])
        if all(req_tool in p_tools for req_tool in required_tools):
            filtered_personas.append(p)
            
    if not filtered_personas:
        logger.info("registry_query_no_tools_match", required_tools=required_tools)
        return RegistryQueryResult(action="SPAWN")
        
    # Prepare lean payload for LLM
    lean_personas = []
    for p in filtered_personas:
        lean_personas.append({
            "id": p["id"],
            "title": p["title"],
            "description": p["description"],
            "tools": p["tools"],
            "tags": p["tags"],
            "success_rate": p["success_rate"]
        })
        
    # 2. Semantic Search via LLM
    try:
        client = instructor.from_litellm(litellm.completion)
        system_prompt = (
            "You are a registry matching engine. Given a task description and a list of available personas, "
            "score each persona's semantic relevance to the task from 0.0 to 1.0. "
            "If a persona is a near-perfect fit but needs a slight adjustment (score 0.6-0.9), "
            "provide a concise `diff_instruction` detailing what needs to be changed (e.g. override prompt to focus on X)."
        )
        
        user_message = f"Task: {task_description}\n\nAvailable Personas:\n{lean_personas}"
        
        response = client.chat.completions.create(
            model=model_name,
            response_model=RegistrySearchResponse,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0
        )
        
        scores_map = {s.persona_id: s.semantic_score for s in response.scores}
        diffs_map = {s.persona_id: s.diff_instruction for s in response.scores}
        
    except Exception as e:
        logger.error("registry_semantic_search_failed", error=str(e))
        # Fallback to SPAWN if LLM fails
        return RegistryQueryResult(action="SPAWN")
        
    # 3. Rank and Threshold
    ranked_personas = sort_personas(filtered_personas, scores_map)
    best_match = ranked_personas[0]
    best_score = scores_map.get(best_match["id"], 0.0)
    
    logger.info("registry_query_result", best_id=best_match["id"], best_score=best_score)
    
    if best_score > 0.9:
        return RegistryQueryResult(action="REUSE", persona=best_match)
    elif 0.6 <= best_score <= 0.9:
        diff_instruction = diffs_map.get(best_match["id"])
        # Fallback diff if missing
        if not diff_instruction:
            diff_instruction = f"Mutate {best_match['title']} to better fit: {task_description}"
        return RegistryQueryResult(action="MUTATE", persona=best_match, diff_instruction=diff_instruction)
    else:
        return RegistryQueryResult(action="SPAWN")
