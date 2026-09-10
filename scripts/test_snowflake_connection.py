import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()

conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    authenticator=os.getenv("SNOWFLAKE_AUTHENTICATOR"),
    role=os.getenv("SNOWFLAKE_ROLE"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)

cur = conn.cursor()

try:
    cur.execute("""
        SELECT
            CURRENT_USER(),
            CURRENT_ROLE(),
            CURRENT_WAREHOUSE(),
            CURRENT_DATABASE(),
            CURRENT_SCHEMA()
    """)

    print(cur.fetchone())

finally:
    cur.close()
    conn.close()
