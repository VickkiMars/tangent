import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
from compiler import JITCompiler
from schemas import AgentBlueprint, SubTask, SynthesisManifest, A2AMessage, MessagePayload

@pytest.fixture
def mock_blackboard():
    bb = AsyncMock()
    bb.get_thread_history = AsyncMock(return_value=[])
    bb.subscribe = MagicMock()
    bb.unsubscribe = MagicMock()
    bb.publish = AsyncMock()
    bb.publish_to_dlq = AsyncMock()
    return bb

@pytest.fixture
def mock_registry():
    reg = MagicMock()
    reg.get_ephemeral_toolkit.return_value = {"dummy_tool": lambda x: "dummy_result"}
    reg.get_ephemeral_schemas.return_value = []
    return reg

@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "Task finished"
    mock_response.choices = [MagicMock(message=mock_message)]
    
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client

@pytest.mark.asyncio
async def test_spawn_ephemeral_agent(mock_blackboard, mock_registry, mock_llm_client):
    compiler = JITCompiler(blackboard=mock_blackboard, registry=mock_registry, llm_client=mock_llm_client)

    blueprint = AgentBlueprint(
        agent_id="agent_1",
        target_task_id="t1",
        persona_prompt="You are a helpful agent.",
        injected_tools=[],
        termination_condition="Done",
        temperature=0.0
    )
    task = SubTask(
        task_id="t1",
        description="Do the test",
        required_capabilities=[]
    )

    await compiler._spawn_ephemeral_agent(blueprint, task)
    
    # Assert publish was called to inform completion
    mock_blackboard.publish.assert_called_once()
    published_msg = mock_blackboard.publish.call_args[0][0]
    assert published_msg.performative == "inform"
    assert published_msg.payload.natural_language == "Task finished"

@pytest.mark.asyncio
async def test_agent_hibernate(mock_blackboard, mock_registry, mock_llm_client):
    # Setup LLM to request human input tool
    mock_message = MagicMock()
    
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "request_human_input"
    mock_tool_call.function.arguments = json.dumps({"reason": "Need user approval"})
    
    mock_message.tool_calls = [mock_tool_call]
    mock_message.content = ""
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_message)]
    
    mock_llm_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    compiler = JITCompiler(blackboard=mock_blackboard, registry=mock_registry, llm_client=mock_llm_client)
    
    blueprint = AgentBlueprint(
        agent_id="agent_1",
        target_task_id="t1",
        persona_prompt="You are a helpful agent.",
        injected_tools=[],
        termination_condition="Done",
        temperature=0.0
    )
    task = SubTask(
        task_id="t1",
        description="Do the test",
        required_capabilities=[]
    )

    await compiler._spawn_ephemeral_agent(blueprint, task)

    # Assert agent published hibernate
    mock_blackboard.publish.assert_called_once()
    published_msg = mock_blackboard.publish.call_args[0][0]
    assert published_msg.performative == "hibernate"
    assert "Need user approval" in published_msg.payload.natural_language
