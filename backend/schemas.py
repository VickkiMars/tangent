from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

# 1. Task Definition
class SubTask(BaseModel):
    task_id: str = Field(description="Unique identifier for the sub-task")
    description: str = Field(description="Clear, actionable description of the work required")
    required_capabilities: List[str] = Field(description="Specific skills or tools needed")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must complete before this begins")
    provider: Literal["openai", "anthropic", "google"] = Field(default="google", description="The LLM provider to use for this task")
    model: str = Field(default="gemini-3.1-flash-lite-preview", description="The specific LLM model to use")

# 2. JIT Compilation
class AgentBlueprint(BaseModel):
    agent_id: str = Field(description="Unique ID for the ephemeral instance, linked to the task_id")
    target_task_id: str = Field(description="The exact SubTask this agent is born to solve")
    agent_type: Literal["ephemeral", "daemon"] = Field(default="ephemeral", description="Type of the agent: ephemeral or daemon")
    persona_prompt: str = Field(description="Highly specific instructions generated JIT for this task")
    injected_tools: List[str] = Field(description="Strictly bound functions for this ephemeral instance")
    temperature: float = Field(default=1.0, description="Task-specific creativity level")
    termination_condition: str = Field(description="Deterministic criteria for the agent to post results and self-destruct")
    include_history: bool = Field(default=False, description="Whether to include thread history in the context")
    history_limit: Optional[int] = Field(default=None, description="Maximum number of historical messages to include")
    provider: Literal["openai", "anthropic", "google"] = Field(default="google", description="The LLM provider to use")
    model: str = Field(default="gemini-3.1-flash-lite-preview", description="The specific LLM model to use")
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids this agent depends on")
    max_iterations: int = Field(default=20, description="Max steps for the LLM loop to prevent runaway costs")

class SynthesisManifest(BaseModel):
    session_id: str = Field(default="", description="Populated by the server after architect_workflow returns")
    blueprints: List[AgentBlueprint] = Field(description="The exact list of agents being JIT compiled")



# 3. Blackboard Communication
class MessagePayload(BaseModel):
    natural_language: str = Field(description="The discrete token output")
    state_deltas: Optional[List[List[float]]] = Field(
        default=None,
        description="Hidden state transition trajectories (SDE) for latent reasoning transfer"
    )
    structured_data: Dict[str, Any] = Field(default_factory=dict, description="JSON payloads from tool executions")

class A2AMessage(BaseModel):
    message_id: str
    tenant_id: str = "tenant_1"
    thread_id: str = Field(description="Ties messages to a specific SubTask lifecycle")
    sender_id: str = Field(description="The agent_id of the ephemeral agent, or 'meta_agent'")
    receiver_id: str = Field(description="Target agent_id, or 'blackboard' for broadcast")
    performative: Literal["request", "propose", "accept", "inform", "failure", "hibernate"] = Field(
        description="FIPA ACL standard interaction types"
    )
    payload: MessagePayload
    timestamp: float

# 4. Global State
class WorkflowState(BaseModel):
    session_id: str
    tenant_id: str = "tenant_1"
    user_id: str = "default"
    original_objective: str
    tasks: List[SubTask]
    manifest: Optional[SynthesisManifest] = None
    shared_memory: Dict[str, Any] = Field(default_factory=dict, description="Context shared via the blackboard")
    status: Literal["analyzing", "architecting", "executing", "completed", "failed"] = "analyzing"
    timestamp: float = 0.0

# 5. Auth
class UserSignup(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    tenant_id: str