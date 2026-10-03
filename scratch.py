import sqlglot
from sqlglot import exp

def validate_sql_security(sql: str):
    try:
        parsed = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError as e:
        return False, f"SQL Parse Error: {e}"
        
    # Check if it's a select statement
    if not isinstance(parsed, exp.Select):
        return False, "Security Exception: Non-SELECT statement detected."
        
    # Check for LIMIT, inject if not present
    if not parsed.args.get("limit"):
        parsed = parsed.limit(1000)
        
    return True, parsed.sql(dialect="duckdb") # assuming duckdb dialect based on the sandbox mention

print(validate_sql_security("SELECT * FROM test"))
print(validate_sql_security("SELECT * FROM drop_shipping_data"))
print(validate_sql_security("DROP TABLE test"))
print(validate_sql_security("SELECT * FROM test LIMIT 10"))
