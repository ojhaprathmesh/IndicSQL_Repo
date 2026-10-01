"""
SQL Verification Critic Node.
Validates SQL against deterministic security and correctness rules:
Enforces read-only statements (SELECT only), blocks destructive mutations (DROP, DELETE, UPDATE, INSERT),
and ensures appropriate safety limits.
"""

from typing import Any, Dict, Tuple
import sqlglot
from sqlglot import exp

from indicsql.core.state import IndicSQLState


def validate_sql_security(sql: str) -> Tuple[bool, str]:
    """
    Parses SQL and checks if the statement is strictly read-only.
    Injects LIMIT 1000 if no LIMIT is present.
    Returns a tuple of (is_safe, regenerated_sql_or_error_message).
    """
    if not sql or not sql.strip():
        return False, "Security Exception: Empty SQL statement."

    try:
        # Parse the SQL using sqlglot
        parsed = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError as e:
        return False, f"SQL Parse Error: {e}"

    if not parsed:
        return False, "Security Exception: Empty SQL statement."

    # Allow only SELECT statements
    if not isinstance(parsed, exp.Select):
        return False, "Security Exception: Non-SELECT mutation detected in candidate query."

    # If it's a select query but has no limit, inject LIMIT 1000
    if not parsed.args.get("limit"):
        parsed = parsed.limit(1000)

    # Regenerate the SQL with duckdb dialect (as per sandbox defaults)
    return True, parsed.sql(dialect="duckdb")


def critic_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Critic Node: Analyzes candidate SQL and blocks security violations.
    """
    sql = state.get("generated_sql", "")
    is_safe, result = validate_sql_security(sql)

    audit_entry = {
        "step": 3.5,
        "agent": "CriticNode",
        "action": "validate_sql_security",
        "is_safe": is_safe,
    }
    
    if not is_safe:
        audit_entry["error"] = result

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    if not is_safe:
        return {
            "syntax_valid": False,
            "execution_error": result,
            "audit_trace": current_trace,
        }

    return {
        "syntax_valid": True,
        "generated_sql": result,
        "audit_trace": current_trace,
    }
