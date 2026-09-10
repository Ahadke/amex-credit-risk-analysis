import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import PROJECT_ROOT, postgres_url


# This file handles the raw-data-to-PostgreSQL loading step.
# We keep the raw tables close to the downloaded Kaggle data
# and let cleaning.sql create properly typed warehouse tables later.
# Cloud loading is a later step and does not replace this local path.


DATABASE_URL = postgres_url()


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


RAW_DATA = PROJECT_ROOT / "data" / "raw" / "train_data.csv"
RAW_LABELS = PROJECT_ROOT / "data" / "raw" / "train_labels.csv"
CLEANING_SQL = PROJECT_ROOT / "sql" / "cleaning.sql"


def validate_input_files():

    # Failing early is much nicer than discovering a missing file
    # after a long database operation has already started.

    required_files = [
        RAW_DATA,
        RAW_LABELS,
        CLEANING_SQL,
    ]

    for path in required_files:

        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    print("All required raw-data and SQL files were found.")


def load_labels():

    # train_labels.csv is small enough to load with pandas.
    # The target belongs to one customer rather than one statement.

    labels = pd.read_csv(
        RAW_LABELS,
        dtype={
            "customer_ID": "string",
            "target": "int8",
        },
    )

    if labels["customer_ID"].duplicated().any():
        raise ValueError(
            "Duplicate customer_ID values found in train_labels.csv."
        )

    if not set(
        labels["target"].dropna().unique()
    ).issubset({0, 1}):

        raise ValueError(
            "Target should contain only 0 and 1."
        )

    labels.to_sql(
        "raw_labels",
        engine,
        if_exists="replace",
        index=False,
        chunksize=10_000,
        method="multi",
    )

    print(
        f"Loaded {len(labels):,} customer labels."
    )

    print(
        f"Observed default rate: "
        f"{labels['target'].mean():.4%}"
    )


def create_raw_statements_table():

    # Reading zero data rows gives us only the CSV header.
    # This avoids accidentally loading the enormous statement file into RAM.

    header = pd.read_csv(
        RAW_DATA,
        nrows=0,
    )

    columns = header.columns.tolist()

    # We intentionally keep the landing table as TEXT.
    # cleaning.sql will create the typed analytical tables.

    column_definitions = [
        f'"{column}" TEXT'
        for column in columns
    ]

    ddl = f"""
    DROP TABLE IF EXISTS raw_statements CASCADE;

    CREATE TABLE raw_statements (
        {", ".join(column_definitions)}
    );
    """

    with engine.begin() as connection:
        connection.execute(
            text(ddl)
        )

    print(
        f"Created raw_statements with "
        f"{len(columns)} columns."
    )


def load_statements_via_copy():

    # PostgreSQL COPY is dramatically faster than pandas.to_sql
    # for millions of statement rows.

    print(
        "Loading train_data.csv into PostgreSQL with COPY..."
    )

    raw_connection = engine.raw_connection()

    try:

        cursor = raw_connection.cursor()

        with open(
            RAW_DATA,
            "r",
            encoding="utf-8",
        ) as file:

            cursor.copy_expert(
                """
                COPY raw_statements
                FROM STDIN
                WITH CSV HEADER
                """,
                file,
            )

        raw_connection.commit()

    except Exception:

        raw_connection.rollback()
        raise

    finally:

        raw_connection.close()

    print(
        "Finished loading raw statement records."
    )


def run_sql_file(path):

    # The raw table is only a landing zone.
    # cleaning.sql is responsible for building cleaned fact/dimension tables.

    sql_text = path.read_text(
        encoding="utf-8"
    )

    raw_connection = engine.raw_connection()

    try:

        cursor = raw_connection.cursor()

        cursor.execute(
            sql_text
        )

        raw_connection.commit()

    except Exception:

        raw_connection.rollback()
        raise

    finally:

        raw_connection.close()

    print(
        f"Finished running {path.name}."
    )


def validate_database_load():

    # A simple row-count check helps us confirm
    # that the database contains data before notebook work begins.

    checks = {
        "raw_labels":
            "SELECT COUNT(*) FROM raw_labels",

        "raw_statements":
            "SELECT COUNT(*) FROM raw_statements",
    }

    with engine.connect() as connection:

        for table, query in checks.items():

            count = connection.execute(
                text(query)
            ).scalar()

            print(
                f"{table}: {count:,} rows"
            )


def validate_warehouse():

    # These tables exist only after sql/cleaning.sql has run.

    checks = {
        "dim_customer":
            "SELECT COUNT(*) FROM dim_customer",

        "fact_statements":
            "SELECT COUNT(*) FROM fact_statements",
    }

    with engine.connect() as connection:

        for table, query in checks.items():

            count = connection.execute(
                text(query)
            ).scalar()

            print(
                f"{table}: {count:,} rows"
            )


if __name__ == "__main__":

    validate_input_files()

    load_labels()

    create_raw_statements_table()

    load_statements_via_copy()

    validate_database_load()

    run_sql_file(
        CLEANING_SQL
    )

    validate_warehouse()

    print(
        "Phase 2 ETL completed successfully."
    )