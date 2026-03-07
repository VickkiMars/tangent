import asyncio
import json
from typing import Dict, List, Optional, Set
from collections import defaultdict
import redis.asyncio as redis
import structlog
from schemas import A2AMessage

logger = structlog.get_logger(__name__)

class EventBlackboard:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # Maps routing keys (e.g., agent_id or 'broadcast') to specific subscriber queues
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        
        # Redis connection for durable state
        self.redis_client = redis.from_url(redis_url)
        self.history_key = "blackboard:history"
        self.dlq_key = "blackboard:dlq"

    def subscribe(self, topic: str) -> asyncio.Queue:
        """Creates an isolated queue for an ephemeral agent to listen to a specific topic."""
        queue = asyncio.Queue()
        self._subscribers[topic].append(queue)
        logger.debug("subscribed", topic=topic)
        return queue

    def unsubscribe(self, topic: str, queue: asyncio.Queue):
        """Garbage collection for when an ephemeral agent self-destructs."""
        if topic in self._subscribers and queue in self._subscribers[topic]:
            self._subscribers[topic].remove(queue)
            logger.debug("unsubscribed", topic=topic)

    async def publish(self, message: A2AMessage):
        """Pushes state changes to the target receiver without blocking the sender."""
        # Save to Redis history (Cold Storage)
        await self.redis_client.rpush(self.history_key, message.model_dump_json())
        
        target_topic = message.receiver_id
        logger.info("publish_message", sender=message.sender_id, receiver=message.receiver_id, performative=message.performative)
        
        # Route directly to specific listeners (Hot Storage / Memory)
        if target_topic in self._subscribers:
            for queue in self._subscribers[target_topic]:
                await queue.put(message)
                
        # Always route to global broadcast listeners (like the Meta-Agent)
        if target_topic != "blackboard" and "blackboard" in self._subscribers:
            for queue in self._subscribers["blackboard"]:
                await queue.put(message)

    async def get_thread_history(self, thread_ids: Optional[Set[str]] = None) -> List[A2AMessage]:
        """Fetches persistent history from Redis, optionally filtered by a set of thread_ids."""
        raw_history = await self.redis_client.lrange(self.history_key, 0, -1)
        history = []
        for raw_msg in raw_history:
            msg_data = json.loads(raw_msg)
            msg = A2AMessage(**msg_data)
            if thread_ids is None or msg.thread_id in thread_ids:
                history.append(msg)
        return history

    async def publish_to_dlq(self, message: A2AMessage, error_reason: str):
        """Pushes a failed or stuck message to the Dead Letter Queue."""
        dlq_entry = {
            "error_reason": error_reason,
            "message": message.model_dump()
        }
        await self.redis_client.rpush(self.dlq_key, json.dumps(dlq_entry))
        logger.error("dlq_entry_added", message_id=message.message_id, error_reason=error_reason)

    async def close(self):
        """Closes the Redis connection cleanly."""
        await self.redis_client.aclose()
