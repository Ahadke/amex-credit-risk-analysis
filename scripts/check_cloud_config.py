"""Report which local/cloud settings are present. Never prints secret values."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (
    DATA_BACKEND,
    aws_ready,
    missing_env,
    postgres_ready,
    snowflake_ready,
)


def _status(ok):
    return "ready" if ok else "not configured"


if __name__ == "__main__":
    print("DATA_BACKEND:", DATA_BACKEND or "(empty)")
    print("PostgreSQL:", _status(postgres_ready()))
    if not postgres_ready():
        print("  missing:", ", ".join(missing_env(["DB_USER", "DB_NAME"])))
    print("AWS S3:", _status(aws_ready()))
    if not aws_ready():
        print(
            "  missing:",
            ", ".join(
                missing_env(
                    [
                        "AWS_REGION",
                        "S3_BUCKET",
                    ]
                )
            ),
        )
    print("Snowflake:", _status(snowflake_ready()))
    if not snowflake_ready():
        print(
            "  missing:",
            ", ".join(
                missing_env(
                    [
                        "SNOWFLAKE_ACCOUNT",
                        "SNOWFLAKE_USER",
                        "SNOWFLAKE_PASSWORD",
                        "SNOWFLAKE_WAREHOUSE",
                        "SNOWFLAKE_DATABASE",
                        "SNOWFLAKE_SCHEMA",
                    ]
                )
            ),
        )
    print()
    print("Do not upload train_data.csv yet.")
    print("Next: create AWS + Snowflake accounts, then fill .env from .env.example.")
