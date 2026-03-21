import json
from typing import Optional
import redis.asyncio as redis
from schemas import WorkflowState

class StateManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)

    def get_key(self, session_id: str, tenant_id: str = "tenant_1") -> str:
        return f"{tenant_id}:workflow:{session_id}"

    async def save_state(self, state: WorkflowState) -> None:
        """Saves the entire workflow state to Redis under a tenant-specific key."""
        key = self.get_key(state.session_id, state.tenant_id)
        state_json = state.model_dump_json()
        await self.redis_client.set(key, state_json)

    async def load_state(self, session_id: str, tenant_id: str = "tenant_1") -> Optional[WorkflowState]:
        """Loads the workflow state from Redis securely scoped to the tenant."""
        key = self.get_key(session_id, tenant_id)
        state_json = await self.redis_client.get(key)
        if state_json:
            data = json.loads(state_json)
            return WorkflowState(**data)
        return None

    async def update_status(self, session_id: str, status: str, tenant_id: str = "tenant_1") -> None:
        """Updates only the status of a specific workflow, validating tenant boundary first."""
        state = await self.load_state(session_id, tenant_id)
        if state:
            state.status = status
            await self.save_state(state)

    async def list_workflows(self, tenant_id: str = "tenant_1", user_id: Optional[str] = None) -> list:
        """Lists workflow states for a given tenant, optionally filtered by user_id."""
        pattern = f"{tenant_id}:workflow:*"
        keys = await self.redis_client.keys(pattern)
        if not keys:
            return []
        states_json = await self.redis_client.mget(keys)
        workflows = []
        for state_json in states_json:
            if state_json:
                data = json.loads(state_json)
                if user_id is None or data.get('user_id') == user_id:
                    workflows.append(data)
        workflows.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return workflows

