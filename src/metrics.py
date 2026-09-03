import numpy as np
import pandas as pd

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
)


# We keep reusable evaluation formulas here
# so notebook 06 stays focused on analysis rather than repeated math.


def classification_metrics(
    y_true,
    probabilities,
):

    return {
        "auc": roc_auc_score(
            y_true,
            probabilities,
        ),
        "average_precision":
            average_precision_score(
                y_true,
                probabilities,
            ),
        "brier_score":
            brier_score_loss(
                y_true,
                probabilities,
            ),
        "log_loss":
            log_loss(
                y_true,
                probabilities,
            ),
    }


def expected_default_hhi(
    segment_df,
    probability_column,
    segment_column,
):

    # We do not have a clean dollar exposure-at-default variable.
    # Therefore the portfolio quantity here is expected-default units:
    # the sum of predicted default probabilities.

    grouped = (
        segment_df
        .groupby(
            segment_column,
            observed=True,
        )[probability_column]
        .sum()
    )

    shares = (
        grouped
        / grouped.sum()
    )

    hhi = (
        shares ** 2
    ).sum()

    return hhi


def concentration_gini(
    values,
):

    # This is a Lorenz-style inequality measure.
    # A value near zero means risk is spread fairly evenly.
    # Larger values mean expected risk is more concentrated.

    values = np.asarray(
        values,
        dtype=float,
    )

    values = values[
        ~np.isnan(values)
    ]

    values = np.sort(
        values
    )

    if len(values) == 0:
        return np.nan

    if values.sum() == 0:
        return 0.0

    cumulative = np.cumsum(
        values
    )

    cumulative = np.insert(
        cumulative,
        0,
        0,
    )

    cumulative = (
        cumulative
        / cumulative[-1]
    )

    population = np.linspace(
        0,
        1,
        len(cumulative),
    )

    area = np.trapezoid(
        cumulative,
        population,
    )

    return (
        1 - 2 * area
    )


def pareto_risk_summary(
    df,
    probability_column,
    fractions=(
        0.01,
        0.05,
        0.10,
        0.20,
    ),
):

    ranked = (
        df
        .sort_values(
            probability_column,
            ascending=False,
        )
        .reset_index(drop=True)
    )

    total_risk = ranked[
        probability_column
    ].sum()

    rows = []

    for fraction in fractions:

        number_customers = max(
            1,
            int(
                np.ceil(
                    len(ranked)
                    * fraction
                )
            ),
        )

        risk_share = (
            ranked.iloc[
                :number_customers
            ][
                probability_column
            ].sum()
            / total_risk
        )

        rows.append(
            {
                "top_customer_pct":
                    fraction * 100,
                "customers":
                    number_customers,
                "expected_default_share_pct":
                    risk_share * 100,
            }
        )

    return pd.DataFrame(
        rows
    )