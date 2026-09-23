"""
LangGraph Multi-Agent Workflow Definition.
Constructs the cyclic state graph coordinating the IndicSQL agent swarm:
Supervisor -> SchemaLinker -> Synthesizer -> Critic -> SandboxExecutor -> (ReflectionLoop or Verbalizer) -> END
"""

from typing import Any, Dict, Optional
import uuid

from indicsql.core.state import IndicSQLState
from indicsql.agents.supervisor import supervisor_node
from indicsql.agents.schema_linker import schema_linker_node
from indicsql.agents.sql_synthesizer import sql_synthesizer_node
from indicsql.agents.critic import critic_node
from indicsql.agents.sandbox_executor import sandbox_executor_node
from indicsql.agents.reflection_healer import reflection_healer_node
from indicsql.agents.response_verbalizer import response_verbalizer_node


def route_after_execution(state: IndicSQLState) -> str:
    """
    Decides the next step after sandboxed execution:
    - 'success': Tabular results retrieved successfully -> Response Verbalizer
    - 'retry': Error or empty rows and attempts < 3 -> Reflection Healer
    - 'fatal_error': Max attempts exceeded -> Response Verbalizer (graceful message)
    """
    error = state.get("execution_error")
    attempts = state.get("reflection_attempts", 0)

    if not error and state.get("execution_result") is not None:
        return "success"
    if attempts < 3:
        return "retry"
    return "fatal_error"


def create_indicsql_graph(checkpointer: Optional[Any] = None):
    """
    Compiles the LangGraph StateGraph when langgraph is available.
    """
    try:
        from langgraph.graph import StateGraph, END  # type: ignore
        from langgraph.checkpoint.memory import MemorySaver  # type: ignore

        if checkpointer is None:
            checkpointer = MemorySaver()

        workflow = StateGraph(IndicSQLState)

        # Register Swarm Nodes
        workflow.add_node("supervisor_router", supervisor_node)
        workflow.add_node("schema_linker", schema_linker_node)
        workflow.add_node("sql_synthesizer", sql_synthesizer_node)
        workflow.add_node("critic", critic_node)
        workflow.add_node("sandbox_executor", sandbox_executor_node)
        workflow.add_node("reflection_healer", reflection_healer_node)
        workflow.add_node("response_verbalizer", response_verbalizer_node)

        # Set Entry Point
        workflow.set_entry_point("supervisor_router")

        # Define Linear Edges
        workflow.add_edge("supervisor_router", "schema_linker")
        workflow.add_edge("schema_linker", "sql_synthesizer")
        workflow.add_edge("sql_synthesizer", "critic")
        workflow.add_edge("critic", "sandbox_executor")

        # Conditional Reflection Loop
        workflow.add_conditional_edges(
            "sandbox_executor",
            route_after_execution,
            {
                "success": "response_verbalizer",
                "retry": "reflection_healer",
                "fatal_error": "response_verbalizer",
            },
        )

        workflow.add_edge("reflection_healer", "sql_synthesizer")
        workflow.add_edge("response_verbalizer", END)

        return workflow.compile(checkpointer=checkpointer)
    except ImportError:
        # Fallback executor for environments where LangGraph is not yet installed
        return None


def execute_indicsql_pipeline(query: str, query_id: Optional[str] = None) -> IndicSQLState:
    """
    Executes the multi-agent swarm for a given query, supporting both LangGraph and native execution.
    """
    if not query_id:
        query_id = f"ind-q-{uuid.uuid4().hex[:8]}"

    state: IndicSQLState = {
        "query_id": query_id,
        "raw_query": query,
        "reflection_attempts": 0,
        "audit_trace": [],
    }

    # Step 1: Supervisor
    state.update(supervisor_node(state))

    # Step 2: Schema Linker
    state.update(schema_linker_node(state))

    # Step 3: Loop with Reflection
    while True:
        # Synthesize SQL
        state.update(sql_synthesizer_node(state))

        # Critic security check
        state.update(critic_node(state))
        if not state.get("syntax_valid", True):
            break

        # Sandbox execution
        state.update(sandbox_executor_node(state))

        decision = route_after_execution(state)
        if decision == "success" or decision == "fatal_error":
            break
        elif decision == "retry":
            state.update(reflection_healer_node(state))

    # Step 4: Response Verbalizer
    state.update(response_verbalizer_node(state))

    return state
