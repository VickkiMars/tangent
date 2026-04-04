import asyncio
import json
from typing import Dict, List, Optional, Set
from collections import defaultdict
import redis.asyncio as redis
import structlog
from core.schemas import A2AMessage

logger = structlog.get_logger(__name__)

class EventBlackboard:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # Maps routing keys (e.g., 'tenant_1:agent_id' or 'tenant_1:broadcast') to specific subscriber queues
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self.redis_client = redis.from_url(redis_url)

    def get_history_key(self, tenant_id: str) -> str:
        return f"{tenant_id}:blackboard:history"

    def get_dlq_key(self, tenant_id: str) -> str:
        return f"{tenant_id}:blackboard:dlq"

    def get_state_key(self, tenant_id: str, thread_id: str) -> str:
        return f"{tenant_id}:human_input:{thread_id}"

    async def save_agent_state(self, thread_id: str, state_data: dict, tenant_id: str = "tenant_1"):
        """Saves a hibernated agent's full context to Redis in a tenant isolated bucket."""
        key = self.get_state_key(tenant_id, thread_id)
        await self.redis_client.set(key, json.dumps(state_data))
        logger.info("agent_state_saved", thread_id=thread_id, tenant_id=tenant_id)

    async def get_agent_state(self, thread_id: str, tenant_id: str = "tenant_1") -> Optional[dict]:
        """Retrieves a hibernated agent's full context from Redis securely."""
        key = self.get_state_key(tenant_id, thread_id)
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    def subscribe(self, topic: str, tenant_id: str = "tenant_1") -> asyncio.Queue:
        """Creates an isolated queue for an ephemeral agent to listen to a specific topic within a tenant."""
        queue = asyncio.Queue()
        queue_topic = f"{tenant_id}:{topic}"
        self._subscribers[queue_topic].append(queue)
        logger.debug("subscribed", topic=topic, tenant_id=tenant_id)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue, tenant_id: str = "tenant_1"):
        """Garbage collection for when an ephemeral agent self-destructs."""
        queue_topic = f"{tenant_id}:{topic}"
        if queue_topic in self._subscribers and queue in self._subscribers[queue_topic]:
            self._subscribers[queue_topic].remove(queue)
            logger.debug("unsubscribed", topic=topic, tenant_id=tenant_id)

    async def publish(self, message: A2AMessage):
        """Pushes state changes to the target receiver without blocking the sender, fully isolated by tenant."""
        tenant_id = getattr(message, "tenant_id", "tenant_1")
        
        # Save to Redis history (Cold Storage)
        history_key = self.get_history_key(tenant_id)
        await self.redis_client.rpush(history_key, message.model_dump_json())
        
        target_topic = f"{tenant_id}:{message.receiver_id}"
        logger.info("publish_message", sender=message.sender_id, receiver=message.receiver_id, performative=message.performative, tenant_id=tenant_id)
        
        # Route directly to specific listeners (Hot Storage / Memory)
        if target_topic in self._subscribers:
            for queue in self._subscribers[target_topic]:
                await queue.put(message)
                
        # Always route to global broadcast listeners (like the Meta-Agent)
        global_topic = f"{tenant_id}:blackboard"
        if target_topic != global_topic and global_topic in self._subscribers:
            for queue in self._subscribers[global_topic]:
                await queue.put(message)

    async def get_thread_history(self, thread_ids: Optional[Set[str]] = None, tenant_id: str = "tenant_1") -> List[A2AMessage]:
        """Fetches persistent history from Redis, optionally filtered by a set of thread_ids, strictly locked to the tenant."""
        history_key = self.get_history_key(tenant_id)
        raw_history = await self.redis_client.lrange(history_key, 0, -1)
        history = []
        for raw_msg in raw_history:
            msg_data = json.loads(raw_msg)
            msg = A2AMessage(**msg_data)
            if thread_ids is None or msg.thread_id in thread_ids:
                history.append(msg)
        return history

    async def publish_to_dlq(self, message: A2AMessage, error_reason: str):
        """Pushes a failed or stuck message to the Dead Letter Queue for a specific tenant."""
        tenant_id = getattr(message, "tenant_id", "tenant_1")
        dlq_key = self.get_dlq_key(tenant_id)
        dlq_entry = {
            "error_reason": error_reason,
            "message": message.model_dump()
        }
        await self.redis_client.rpush(dlq_key, json.dumps(dlq_entry))
        logger.error("dlq_entry_added", message_id=message.message_id, error_reason=error_reason, tenant_id=tenant_id)

    async def close(self):
        """Closes the Redis connection cleanly."""
        await self.redis_client.aclose()
