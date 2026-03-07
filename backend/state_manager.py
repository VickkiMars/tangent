import json
from typing import Optional
import redis.asyncio as redis
from schemas import WorkflowState

class StateManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.prefix = "workflow:"

    async def save_state(self, state: WorkflowState) -> None:
        """Saves the entire workflow state to Redis."""
        key = f"{self.prefix}{state.session_id}"
        state_json = state.model_dump_json()
        await self.redis_client.set(key, state_json)

    async def load_state(self, session_id: str) -> Optional[WorkflowState]:
        """Loads the workflow state from Redis by session_id."""
        key = f"{self.prefix}{session_id}"
        state_json = await self.redis_client.get(key)
        if state_json:
            data = json.loads(state_json)
            return WorkflowState(**data)
        return None

    async def update_status(self, session_id: str, status: str) -> None:
        """Updates only the status of a specific workflow."""
        state = await self.load_state(session_id)
        if state:
            state.status = status
            await self.save_state(state)
