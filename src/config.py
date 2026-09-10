"""Project configuration.

PostgreSQL remains the default local warehouse.
AWS and Snowflake settings are optional until cloud credentials exist.
This module never prints secrets.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


def getenv(name, default=""):
    value = os.getenv(name, default)
    if value is None:
        return default
    return value.strip()


def missing_env(names):
    return [
        name
        for name in names
        if not getenv(name)
    ]


# postgres is the current working warehouse.
# cloud scripts may later read DATA_BACKEND=snowflake.
DATA_BACKEND = getenv("DATA_BACKEND", "postgres")


DB_HOST = getenv("DB_HOST", "localhost")
DB_PORT = getenv("DB_PORT", "5432")
DB_NAME = getenv("DB_NAME", "amex_credit_risk")
DB_USER = getenv("DB_USER", "ahadke")
DB_PASSWORD = getenv("DB_PASSWORD")


AWS_REGION = getenv("AWS_REGION")
S3_BUCKET = getenv("S3_BUCKET")
S3_PREFIX = getenv("S3_PREFIX", "amex/sample")


SNOWFLAKE_ACCOUNT = getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_AUTHENTICATOR = getenv(
    "SNOWFLAKE_AUTHENTICATOR",
    "username_password_mfa"
)
SNOWFLAKE_ROLE = getenv("SNOWFLAKE_ROLE", "SYSADMIN")
SNOWFLAKE_WAREHOUSE = getenv("SNOWFLAKE_WAREHOUSE", "AMEX_WH")
SNOWFLAKE_DATABASE = getenv("SNOWFLAKE_DATABASE", "AMEX_CREDIT_RISK")
SNOWFLAKE_SCHEMA = getenv("SNOWFLAKE_SCHEMA", "ANALYTICS")


def postgres_url():
    return (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


def postgres_ready():
    return not missing_env(["DB_USER", "DB_NAME"])


def aws_ready():
    return not missing_env(
        [
            "AWS_REGION",
            "S3_BUCKET",
        ]
    )


def snowflake_ready():
    return not missing_env(
        [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
        ]
    )


def require_aws():
    missing = missing_env(
        [
            "AWS_REGION",
            "S3_BUCKET",
        ]
    )
    if missing:
        raise RuntimeError(
            "AWS is not configured. Missing: "
            + ", ".join(missing)
        )


def require_snowflake():
    missing = missing_env(
        [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
        ]
    )
    if missing:
        raise RuntimeError(
            "Snowflake is not configured. Missing: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill those names."
        )
