import asyncio
import os
import sys

# Try to use asyncpg, fallback to nothing for now. Will install if missing.
try:
    import asyncpg
except ImportError:
    print("Please install asyncpg: pip install asyncpg")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL")

# This script initializes the PostgreSQL database with the necessary schema
# for the expanded Tangent Agent Framework (multi-tenant, analytics, human-in-the-loop, etc.)

SCHEMA_SQL = """
-- 1. Tenants (For Multi-Tenant Isolation)
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Users (Under Tenants)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    signup_ip VARCHAR(100),
    budget_limit_usd DECIMAL(10, 4) DEFAULT 100.0,
    current_spend_usd DECIMAL(10, 4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Workflows (For Visual Workflow Builder)
CREATE TABLE IF NOT EXISTS predefined_workflows (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    visual_layout JSONB NOT NULL, -- The React Flow nodes/edges
    synthesis_manifest JSONB NOT NULL, -- The compiled blueprint instructions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Threads (Active execution runs)
CREATE TABLE IF NOT EXISTS execution_threads (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    objective TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'analyzing', -- analyzing, executing, waiting_on_human, completed, failed
    total_cost_usd DECIMAL(10, 4) DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 5. Human-in-the-Loop States
CREATE TABLE IF NOT EXISTS agent_human_input_states (
    thread_id VARCHAR(255) PRIMARY KEY REFERENCES execution_threads(id) ON DELETE CASCADE,
    agent_blueprint JSONB NOT NULL,
    conversation_history JSONB NOT NULL,
    collected_context JSONB,
    human_input_request JSONB NOT NULL,
    human_response JSONB,
    status VARCHAR(50) DEFAULT 'waiting', -- waiting, responded, expired
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE
);

-- 6. Dynamic Tools (Meta-Orchestrator Code Generation)
CREATE TABLE IF NOT EXISTS agent_tools (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    python_code TEXT NOT NULL, -- The dynamically generated code
    is_approved BOOLEAN DEFAULT FALSE, -- Requires Meta-Orchestrator or human approval
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Agent Analytics & Cost Tracking
CREATE TABLE IF NOT EXISTS agent_analytics (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) REFERENCES execution_threads(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    target_task_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50),
    model VARCHAR(100),
    tokens_prompt INTEGER DEFAULT 0,
    tokens_completion INTEGER DEFAULT 0,
    cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    tools_called JSONB DEFAULT '[]',
    was_successful BOOLEAN DEFAULT TRUE,
    lifetime_seconds DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Self-Optimizing Query Feedback
CREATE TABLE IF NOT EXISTS query_optimizations (
    id SERIAL PRIMARY KEY,
    original_query TEXT NOT NULL,
    optimized_query TEXT NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    success_score DECIMAL(5, 2), -- 0.0 to 1.0 based on how useful the result was
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

async def init_db():
    print(f"Connecting to database: {DATABASE_URL}")
    try:
        # We might need to connect to the default 'postgres' DB first to create our target DB
        # But for simplicity, we assume the target DB exists or we are using a cloud instance.
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("Creating tables...")
        await conn.execute(SCHEMA_SQL)
        
        print("Database initialization complete.")
        await conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())