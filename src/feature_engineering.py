import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


# This script converts repeated statement-level records
# into one modeling row per customer.

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT / ".env"
)


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "amex_credit_risk")
DB_USER = os.getenv("DB_USER", "ahadke")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


engine = create_engine(
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
)


OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "customer_features.parquet"
)


# We begin with features representing several AMEX families.
# Later notebooks provide statistical evidence for which variables
# are actually worth carrying into the final models.

KEY_NUMERIC_COLS = [
    "P_2",
    "B_1",
    "B_2",
    "R_1",
    "S_3",
    "D_39",
    "D_41",
    "B_3",
    "D_44",
    "B_4",
    "D_45",
    "B_5",
    "R_2",
    "D_47",
    "B_9",
    "R_3",
]


def pull_customer_statements(
    customer_limit=None,
):

    columns_sql = ", ".join(
        [
            f'f."{column}"'
            for column
            in KEY_NUMERIC_COLS
        ]
    )

    # If we want a smaller development sample,
    # we limit CUSTOMER IDs rather than statement rows.
    # Statement-row LIMIT would create incomplete customer histories.

    customer_cte = ""
    customer_join = ""

    if customer_limit is not None:

        customer_cte = f"""
        WITH selected_customers AS (

            SELECT "customer_ID"

            FROM dim_customer

            ORDER BY "customer_ID"

            LIMIT {int(customer_limit)}
        )
        """

        customer_join = """
        JOIN selected_customers s
          ON f."customer_ID" = s."customer_ID"
        """

    query = f"""
    {customer_cte}

    SELECT
        f."customer_ID",
        f.statement_date,
        {columns_sql},
        d.target

    FROM fact_statements f

    {customer_join}

    JOIN dim_customer d
      ON f."customer_ID" = d."customer_ID"

    ORDER BY
        f."customer_ID",
        f.statement_date
    """

    print(
        "Pulling complete customer histories..."
    )

    df = pd.read_sql(
        query,
        engine,
    )

    print(
        f"Statement rows pulled: {len(df):,}"
    )

    print(
        f"Customers represented: "
        f"{df['customer_ID'].nunique():,}"
    )

    return df


def build_customer_level_features(df):

    df = df.copy()

    df["statement_date"] = pd.to_datetime(
        df["statement_date"]
    )

    # Sorting is essential before using "last".
    # Otherwise pandas could treat an arbitrary database row
    # as the latest customer observation.

    df = df.sort_values(
        [
            "customer_ID",
            "statement_date",
        ]
    )

    # Missingness can itself contain information,
    # so we preserve a simple missing-data measure.

    df["missing_feature_count"] = (
        df[KEY_NUMERIC_COLS]
        .isna()
        .sum(axis=1)
    )

    df["missing_feature_fraction"] = (
        df["missing_feature_count"]
        / len(KEY_NUMERIC_COLS)
    )

    aggregation_functions = [
        "mean",
        "std",
        "min",
        "max",
        "last",
    ]

    feature_frames = []

    for column in KEY_NUMERIC_COLS:

        grouped = (
            df.groupby(
                "customer_ID"
            )[column]
            .agg(
                aggregation_functions
            )
        )

        grouped.columns = [
            f"{column}_{function}"
            for function
            in aggregation_functions
        ]

        feature_frames.append(
            grouped
        )

    customer_features = pd.concat(
        feature_frames,
        axis=1,
    )

    # These fields describe how much longitudinal information
    # we have for each customer.

    metadata = (
        df.groupby(
            "customer_ID"
        )
        .agg(
            n_statements=(
                "statement_date",
                "count",
            ),
            first_statement=(
                "statement_date",
                "min",
            ),
            last_statement=(
                "statement_date",
                "max",
            ),
            avg_missing_fraction=(
                "missing_feature_fraction",
                "mean",
            ),
            target=(
                "target",
                "first",
            ),
        )
    )

    metadata["observed_history_days"] = (
        metadata["last_statement"]
        - metadata["first_statement"]
    ).dt.days

    result = (
        customer_features
        .join(metadata)
        .reset_index()
    )

    if result[
        "customer_ID"
    ].duplicated().any():

        raise ValueError(
            "Customer feature table contains duplicate customers."
        )

    print(
        f"Created {len(result):,} customer-level rows."
    )

    return result


def save_features(
    df,
    path=OUTPUT_PATH,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        path,
        index=False,
    )

    print(
        f"Saved customer features to {path}"
    )


if __name__ == "__main__":

    statements = (
        pull_customer_statements()
    )

    features = (
        build_customer_level_features(
            statements
        )
    )

    print(
        "Feature-table default rate:",
        features["target"].mean(),
    )

    print(
        "Median statements per customer:",
        features[
            "n_statements"
        ].median(),
    )

    save_features(
        features
    )

    print(
        features.head()
    )