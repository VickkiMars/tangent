import os
import asyncio
from engine.state_manager import StateManager
from engine.blackboard import EventBlackboard
from tools.registry import GlobalToolRegistry

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Global Shared Instances
state_manager = StateManager(redis_url=redis_url)
blackboard = EventBlackboard(redis_url=redis_url)
registry = GlobalToolRegistry()

# Tracking active workflow tasks for graceful shutdown and cancellation: session_id -> asyncio.Task
active_workflow_tasks: dict[str, asyncio.Task] = {}
