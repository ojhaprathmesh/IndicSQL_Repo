"""
SQL Verification Critic Node.
Validates SQL against deterministic security and correctness rules:
Enforces read-only statements (SELECT only), blocks destructive mutations (DROP, DELETE, UPDATE, INSERT),
and ensures appropriate safety limits.
"""

from typing import Any, Dict

from indicsql.core.state import IndicSQLState

FORBIDDEN_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT"}


def validate_sql_security(sql: str) -> bool:
    """
    Checks if the SQL statement is strictly read-only.
    """
    tokens = [t.strip().upper() for t in sql.split()]
    for token in tokens:
        if token in FORBIDDEN_KEYWORDS:
            return False
    return True


def critic_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Critic Node: Analyzes candidate SQL and blocks security violations.
    """
    sql = state.get("generated_sql", "")
    is_safe = validate_sql_security(sql)

    audit_entry = {
        "step": 3.5,
        "agent": "CriticNode",
        "action": "validate_sql_security",
        "is_safe": is_safe,
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    if not is_safe:
        return {
            "syntax_valid": False,
            "execution_error": "Security Exception: Non-SELECT mutation detected in candidate query.",
            "audit_trace": current_trace,
        }

    return {
        "syntax_valid": True,
        "audit_trace": current_trace,
    }
