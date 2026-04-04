import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from engine.blackboard import EventBlackboard
from core.schemas import A2AMessage, MessagePayload
import time

@pytest.fixture
def mock_redis():
    with patch("redis.asyncio.from_url") as mock:
        mock_client = AsyncMock()
        mock_client.rpush = AsyncMock()
        mock_client.lrange = AsyncMock(return_value=[])
        mock_client.aclose = AsyncMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def blackboard(mock_redis):
    bb = EventBlackboard("redis://mock")
    yield bb

@pytest.mark.asyncio
async def test_subscribe_unsubscribe(blackboard):
    queue = blackboard.subscribe("agent_1")
    assert "agent_1" in blackboard._subscribers
    assert queue in blackboard._subscribers["agent_1"]

    blackboard.unsubscribe("agent_1", queue)
    assert queue not in blackboard._subscribers["agent_1"]

@pytest.mark.asyncio
async def test_publish(blackboard, mock_redis):
    queue = blackboard.subscribe("agent_2")
    msg = A2AMessage(
        message_id="123",
        thread_id="t1",
        sender_id="agent_1",
        receiver_id="agent_2",
        performative="inform",
        payload=MessagePayload(natural_language="hello"),
        timestamp=time.time()
    )

    await blackboard.publish(msg)
    
    # Assert pushed to redis
    mock_redis.rpush.assert_called_once()
    
    # Assert put in queue
    received_msg = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received_msg.message_id == "123"

@pytest.mark.asyncio
async def test_publish_to_dlq(blackboard, mock_redis):
    msg = A2AMessage(
        message_id="456",
        thread_id="t1",
        sender_id="agent_1",
        receiver_id="agent_2",
        performative="failure",
        payload=MessagePayload(natural_language="error"),
        timestamp=time.time()
    )

    await blackboard.publish_to_dlq(msg, "Something went wrong")
    mock_redis.rpush.assert_called_once()

@pytest.mark.asyncio
async def test_get_thread_history(blackboard, mock_redis):
    msg = A2AMessage(
        message_id="789",
        thread_id="t1",
        sender_id="agent_1",
        receiver_id="agent_2",
        performative="inform",
        payload=MessagePayload(natural_language="test"),
        timestamp=time.time()
    )
    mock_redis.lrange.return_value = [msg.model_dump_json()]

    history = await blackboard.get_thread_history(thread_ids={"t1"})
    assert len(history) == 1
    assert history[0].message_id == "789"
