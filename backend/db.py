import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import structlog
from contextlib import contextmanager

logger = structlog.get_logger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except Exception as e:
        logger.error("db_connection_error", error=str(e))
        raise
    finally:
        if conn:
            conn.close()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
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
CREATE TABLE IF NOT EXISTS predefined_workflows (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    visual_layout JSONB NOT NULL,
    synthesis_manifest JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS execution_threads (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
    objective TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'analyzing',
    total_cost_usd DECIMAL(10, 4) DEFAULT 0.0,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
CREATE TABLE IF NOT EXISTS agent_human_input_states (
    thread_id VARCHAR(255) PRIMARY KEY REFERENCES execution_threads(id) ON DELETE CASCADE,
    agent_blueprint JSONB NOT NULL,
    conversation_history JSONB NOT NULL,
    collected_context JSONB,
    human_input_request JSONB NOT NULL,
    human_response JSONB,
    status VARCHAR(50) DEFAULT 'waiting',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    responded_at TIMESTAMP WITH TIME ZONE
);
CREATE TABLE IF NOT EXISTS agent_tools (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    python_code TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
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
CREATE TABLE IF NOT EXISTS query_optimizations (
    id SERIAL PRIMARY KEY,
    original_query TEXT NOT NULL,
    optimized_query TEXT NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    success_score DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

def run_schema_migrations():
    """Creates all required tables if they don't already exist."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
        logger.info("db_schema_ready")
    except Exception as e:
        logger.error("db_migration_error", error=str(e))

def ensure_tenant_user(user_id: str, tenant_id: str = "tenant_1"):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO tenants (id, name) VALUES (%s, 'Default Org') ON CONFLICT DO NOTHING", (tenant_id,))
                cur.execute(
                    "INSERT INTO users (id, tenant_id, name, email) VALUES (%s, %s, 'User', 'user_' || %s || '@tangent.ai') ON CONFLICT DO NOTHING",
                    (user_id, tenant_id, user_id)
                )
            conn.commit()
    except Exception:
        pass # Ignore in dev if DB missing

def check_budget_exceeded(user_id: str, anticipated_cost: float = 0.0) -> bool:
    """Returns True if budget is exceeded. Updates spend if false."""
    try:
        ensure_tenant_user(user_id)
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "UPDATE users SET current_spend_usd = current_spend_usd + %s WHERE id = %s RETURNING current_spend_usd, budget_limit_usd",
                    (anticipated_cost, user_id)
                )
                res = cur.fetchone()
                if res:
                    conn.commit()
                    return float(res['current_spend_usd']) >= float(res['budget_limit_usd'])
                return False
    except Exception as e:
        logger.error("budget_check_error", error=str(e))
        return False # Fail open in case DB fails

def create_user(user_id: str, email: str, hashed_password: str, name: str, signup_ip: str, tenant_id: str = "tenant_1"):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Ensure tenant exists
                cur.execute("INSERT INTO tenants (id, name) VALUES (%s, 'Default Org') ON CONFLICT DO NOTHING", (tenant_id,))
                cur.execute(
                    "INSERT INTO users (id, tenant_id, email, hashed_password, name, signup_ip) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, tenant_id, email, hashed_password, name, signup_ip)
                )
            conn.commit()
            return True
    except Exception as e:
        logger.error("create_user_error", error=str(e))
        return False

def get_user_by_email(email: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                return cur.fetchone()
    except Exception as e:
        logger.error("get_user_by_email_error", error=str(e))
        return None

def is_ip_restricted(ip_address: str) -> bool:
    """Check if an account already exists with this IP."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE signup_ip = %s", (ip_address,))
                return cur.fetchone() is not None
    except Exception as e:
        logger.error("ip_check_error", error=str(e))
        return False # Fail open to prevent locking everyone out if DB is down, but ideally should be strict

def record_agent_analytics(thread_id, agent_id, target_task_id, provider, model, tokens_prompt, tokens_completion, cost, tools_called, was_successful, lifetime):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # ensure thread exists
                cur.execute("INSERT INTO execution_threads (id, tenant_id, user_id, objective) VALUES (%s, 'tenant_1', 'dev_user', 'Auto-created') ON CONFLICT DO NOTHING", (thread_id,))
                
                cur.execute("""
                    INSERT INTO agent_analytics (
                        thread_id, agent_id, target_task_id, provider, model, 
                        tokens_prompt, tokens_completion, cost_usd, tools_called, 
                        was_successful, lifetime_seconds
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    thread_id, agent_id, target_task_id, provider, model,
                    tokens_prompt, tokens_completion, cost, json.dumps(tools_called),
                    was_successful, float(lifetime)
                ))
                conn.commit()
    except Exception as e:
        logger.error("analytics_record_error", error=str(e))

def get_workflow_analytics(thread_ids: list) -> list:
    """Fetch analytics for a set of thread IDs."""
    if not thread_ids:
        return []
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT agent_id, target_task_id, provider, model, tokens_prompt, 
                           tokens_completion, cost_usd, tools_called, was_successful, lifetime_seconds
                    FROM agent_analytics
                    WHERE thread_id = ANY(%s)
                """, (thread_ids,))
                rows = cur.fetchall()
                # Converting Decimal to float for JSON serialization
                return [
                    {
                        **dict(row),
                        "cost_usd": float(row["cost_usd"]) if row["cost_usd"] else 0.0,
                        "lifetime_seconds": float(row["lifetime_seconds"]) if row["lifetime_seconds"] else 0.0
                    }
                    for row in rows
                ]
    except Exception as e:
        logger.error("get_analytics_error", error=str(e))
        return []

def get_global_cost_summary(tenant_id: str = "tenant_1") -> dict:
    """Fetch global aggregated analytics across all threads for a tenant."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COALESCE(SUM(cost_usd), 0.0) as total_cost,
                        COALESCE(SUM(tokens_prompt + tokens_completion), 0) as total_tokens,
                        COUNT(DISTINCT agent_analytics.thread_id) as total_threads
                    FROM agent_analytics
                    INNER JOIN execution_threads ON agent_analytics.thread_id = execution_threads.id
                    WHERE execution_threads.tenant_id = %s
                """, (tenant_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "total_cost_usd": float(row["total_cost"]),
                        "total_tokens": int(row["total_tokens"]),
                        "total_threads": int(row["total_threads"])
                    }
                return {"total_cost_usd": 0.0, "total_tokens": 0, "total_threads": 0}
    except Exception as e:
        logger.error("get_global_cost_summary_error", error=str(e))
        return {"total_cost_usd": 0.0, "total_tokens": 0, "total_threads": 0}

