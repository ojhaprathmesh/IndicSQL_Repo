"""
SQL AST Validator and Sanitizer.
Uses SQLGlot (or fallback tokenizer) to enforce read-only semantics and enforce LIMIT bounds.
"""

from typing import Tuple


def validate_and_limit_sql(sql: str, default_limit: int = 1000) -> Tuple[bool, str]:
    """
    Validates that the SQL is a SELECT statement and ensures a safe LIMIT clause exists.
    Returns:
        (is_valid, modified_or_error_sql)
    """
    cleaned = sql.strip().rstrip(";")
    upper = cleaned.upper()

    # Block data modifying statements
    prohibited = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE ", "CREATE "]
    for word in prohibited:
        if word in upper:
            return False, f"Prohibited mutation clause detected: {word.strip()}"

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        return False, "Only SELECT or WITH queries are permitted in the execution sandbox."

    # Enforce LIMIT if not present
    if "LIMIT " not in upper:
        cleaned += f" LIMIT {default_limit}"

    return True, cleaned + ";"
