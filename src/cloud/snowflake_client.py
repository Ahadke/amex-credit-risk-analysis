"""Snowflake connection helper.

Does not create or drop warehouses. That stays a manual/account step.
"""

from src.config import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_AUTHENTICATOR,
    SNOWFLAKE_DATABASE,
    SNOWFLAKE_PASSWORD,
    SNOWFLAKE_ROLE,
    SNOWFLAKE_SCHEMA,
    SNOWFLAKE_USER,
    SNOWFLAKE_WAREHOUSE,
    require_snowflake,
)


def get_snowflake_connection():
    require_snowflake()

    try:
        import snowflake.connector
    except ImportError as exc:
        raise RuntimeError(
            "snowflake-connector-python is not installed. "
            "Run: pip install snowflake-connector-python"
        ) from exc

    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        authenticator=SNOWFLAKE_AUTHENTICATOR,
        role=SNOWFLAKE_ROLE or None,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
    )
