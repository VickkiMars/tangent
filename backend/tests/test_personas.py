import pytest
from engine.compiler import JITCompiler
from core.schemas import AgentBlueprint, SubTask
from engine.personas import PERSONAS, get_persona_prompt
from unittest.mock import MagicMock

def test_resolve_persona_prompt():
    compiler = JITCompiler(blackboard=MagicMock(), registry=MagicMock())

    # Case 1: No persona_id, use persona_prompt
    bp1 = AgentBlueprint(
        agent_id="a1",
        target_task_id="t1",
        persona_prompt="Custom prompt",
        injected_tools=[],
        termination_condition="Done"
    )
    assert compiler._resolve_persona_prompt(bp1) == "Custom prompt"

    # Case 2: Valid persona_id, no persona_prompt
    bp2 = AgentBlueprint(
        agent_id="a2",
        target_task_id="t2",
        persona_id="summarizer",
        injected_tools=[],
        termination_condition="Done"
    )
    assert compiler._resolve_persona_prompt(bp2) == PERSONAS["summarizer"]

    # Case 3: Valid persona_id + persona_prompt (concatenation)
    bp3 = AgentBlueprint(
        agent_id="a3",
        target_task_id="t3",
        persona_id="researcher",
        persona_prompt="Focus on 2024 data.",
        injected_tools=[],
        termination_condition="Done"
    )
    expected = f"{PERSONAS['researcher']}\n\nSpecific instructions for this task:\nFocus on 2024 data."
    assert compiler._resolve_persona_prompt(bp3) == expected

    # Case 4: Invalid persona_id, fallback to persona_prompt
    bp4 = AgentBlueprint(
        agent_id="a4",
        target_task_id="t4",
        persona_id="non_existent",
        persona_prompt="Fallback prompt",
        injected_tools=[],
        termination_condition="Done"
    )
    assert compiler._resolve_persona_prompt(bp4) == "Fallback prompt"

    # Case 5: Neither provided
    bp5 = AgentBlueprint(
        agent_id="a5",
        target_task_id="t5",
        persona_prompt=None,
        injected_tools=[],
        termination_condition="Done"
    )
    assert compiler._resolve_persona_prompt(bp5) == "You are a helpful autonomous agent."
