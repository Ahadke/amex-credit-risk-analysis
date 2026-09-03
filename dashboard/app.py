"""Streamlit dashboard for the AMEX credit-risk project.

Reads verified artifacts in data/processed/ only. Does not query PostgreSQL
or retrain models.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from lifelines import KaplanMeierFitter


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


st.set_page_config(
    page_title="AMEX Credit Risk",
    layout="wide",
)


@st.cache_data
def load_parquet(name: str) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / name)


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED / name)


def fig_style():
    fig, ax = plt.subplots(figsize=(8, 4.2))
    return fig, ax


dim = load_parquet("dim_customer.parquet")
latest = load_parquet("customer_feature_sample.parquet")
latest_cat = load_parquet("customer_feature_sample_with_categoricals.parquet")
shortlist = load_csv("statistical_shortlist.csv")
survival = load_parquet("survival_proxy_dataset.parquet")
monthly = load_csv("monthly_policy_analysis.csv")
calibration = load_csv("calibration_comparison.csv")
predictions = load_parquet("predictions.parquet")
segments = load_csv("risk_segment_summary.csv")
pareto = load_csv("risk_pareto_summary.csv")

monthly["cohort_month"] = pd.to_datetime(monthly["cohort_month"])

# Confirmed notebook outputs used as labels only (not recomputed).
LOG_RANK_P = 0.0
P2_THRESHOLD = 0.482
EVENT_RATE = 0.3575
DEFAULT_IF_CROSSED = 0.606
DEFAULT_IF_NEVER = 0.066
HHI = 0.2704
GINI = 0.6692
BREAK_DATE = pd.Timestamp("2017-06-01")

default_rate = float(dim["target"].mean())
n_customers = int(len(dim))

st.title("American Express Credit Risk")
st.caption(
    "All charts and KPIs are read from data/processed/. "
    "Risk-transition is not time-to-default. The 2017-06 break is not a causal policy effect."
)

tab_land, tab_surv, tab_shift, tab_model, tab_port = st.tabs(
    [
        "Risk landscape",
        "Risk-transition",
        "Structural shift",
        "Model performance",
        "Portfolio concentration",
    ]
)


with tab_land:
    c1, c2, c3 = st.columns(3)
    c1.metric("Customers", f"{n_customers:,}")
    c2.metric("Default rate", f"{default_rate:.2%}")
    c3.metric("Shortlisted features", f"{len(shortlist):,}")

    st.subheader("Default rate by statement-count bucket")
    by_hist = (
        dim.groupby("n_statements", as_index=False)
        .agg(customers=("customer_ID", "count"), default_rate=("target", "mean"))
        .sort_values("n_statements")
    )
    fig, ax = fig_style()
    ax.plot(by_hist["n_statements"], by_hist["default_rate"], marker="o")
    ax.set_xlabel("Statements per customer")
    ax.set_ylabel("Default rate")
    ax.set_title("Default rate by n_statements")
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Source: data/processed/dim_customer.parquet")

    st.subheader("Latest-statement features: default vs non-default")
    numeric_top = [
        feature
        for feature in shortlist.loc[
            shortlist["test_type"] == "mannwhitney", "feature"
        ].tolist()
        if feature in latest.columns
    ][:5]

    cols = st.columns(2)
    for i, feature in enumerate(numeric_top):
        fig, ax = fig_style()
        for label, value in [("Non-default", 0), ("Default", 1)]:
            series = latest.loc[latest["target"] == value, feature].dropna()
            if series.nunique() > 1:
                series.plot.kde(ax=ax, label=label)
        ax.set_xlabel(feature)
        ax.set_ylabel("Density")
        ax.set_title(f"{feature}: default vs non-default")
        ax.legend()
        cols[i % 2].pyplot(fig)
        plt.close(fig)
    st.caption("Source: data/processed/customer_feature_sample.parquet")

    st.subheader("Categorical shortlist (chi-square / Cramér's V)")
    cat_short = shortlist.loc[shortlist["test_type"] == "chi_square"].copy()
    st.dataframe(
        cat_short[
            ["feature", "abs_effect_size", "p_value_fdr", "missing_pct"]
        ].rename(columns={"abs_effect_size": "cramers_v"}),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Source: data/processed/statistical_shortlist.csv "
        "(categorical tests added after the numeric-only run)."
    )

    if "B_38" in latest_cat.columns:
        mix = (
            latest_cat.groupby(["B_38", "target"], dropna=False)
            .size()
            .rename("customers")
            .reset_index()
        )
        fig, ax = fig_style()
        for value, label in [(0, "Non-default"), (1, "Default")]:
            part = mix.loc[mix["target"] == value]
            ax.bar(
                part["B_38"].astype(str),
                part["customers"],
                alpha=0.6,
                label=label,
            )
        ax.set_xlabel("B_38")
        ax.set_ylabel("Customers")
        ax.set_title("B_38 (strongest categorical) by target")
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Source: data/processed/customer_feature_sample_with_categoricals.parquet")


with tab_surv:
    st.subheader("Time-to-risk-transition (not time-to-default)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("P_2 threshold", f"{P2_THRESHOLD:.3f}")
    k2.metric("Event rate", f"{EVENT_RATE:.2%}")
    k3.metric("Log-rank p-value", f"{LOG_RANK_P:.0f}")
    k4.metric("Default | crossed vs never", f"{DEFAULT_IF_CROSSED:.3f} vs {DEFAULT_IF_NEVER:.3f}")

    st.info(
        "AMEX does not provide a default date. The event is first crossing of a "
        "baseline-derived P_2 risk threshold. Censored customers never cross."
    )

    fig, ax = fig_style()
    kmf = KaplanMeierFitter()
    quartiles = (
        survival["baseline_quartile"].dropna().astype(str).sort_values().unique()
    )
    for quartile in quartiles:
        mask = survival["baseline_quartile"].astype(str) == quartile
        kmf.fit(
            survival.loc[mask, "duration"],
            event_observed=survival.loc[mask, "event"],
            label=quartile,
        )
        kmf.plot_survival_function(ax=ax)
    ax.set_xlabel("Months since first statement")
    ax.set_ylabel("Probability of remaining below risk threshold")
    ax.set_title("Risk transition by baseline P_2 quartile")
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Source: data/processed/survival_proxy_dataset.parquet. Log-rank p from notebook 04.")

    event_table = (
        survival.groupby("event", as_index=False)
        .agg(customers=("customer_ID", "count"), default_rate=("target", "mean"))
    )
    event_table["event"] = event_table["event"].map(
        {0: "Never crossed threshold", 1: "Crossed threshold"}
    )
    st.dataframe(event_table, width="stretch", hide_index=True)


with tab_shift:
    st.subheader("Structural shift check (not a causal policy effect)")
    st.warning(
        "Every customer's last statement is 2018-03, so a final-statement cohort "
        "has no time variation. The series below uses first-statement month. "
        "The 2017-06-01 marker is a candidate breakpoint, not a confirmed policy date."
    )

    fig, ax = fig_style()
    ax.plot(monthly["cohort_month"], monthly["default_rate"], marker="o")
    ax.axvline(BREAK_DATE, color="black", linestyle="--", label="Candidate break 2017-06-01")
    ax.set_xlabel("First-statement cohort")
    ax.set_ylabel("Future default rate")
    ax.set_title("Default rate by first-statement month")
    ax.legend()
    fig.autofmt_xdate()
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Source: data/processed/monthly_policy_analysis.csv")

    fig, ax = fig_style()
    for feature in ["P_2", "D_44", "B_2", "B_1", "B_9"]:
        if feature in monthly.columns:
            ax.plot(monthly["cohort_month"], monthly[feature], marker="o", label=feature)
    ax.axvline(BREAK_DATE, color="black", linestyle="--")
    ax.set_xlabel("First-statement cohort")
    ax.set_ylabel("Median latest-statement value")
    ax.set_title("Composition control: shortlisted feature medians")
    ax.legend()
    fig.autofmt_xdate()
    st.pyplot(fig)
    plt.close(fig)


with tab_model:
    st.subheader("Held-out test performance")
    st.caption("Train 293,704 / calibration 73,426 / test 91,783. Test set was not used to fit calibration.")

    show = calibration.rename(
        columns={
            "auc": "AUC",
            "average_precision": "Average precision",
            "brier_score": "Brier",
            "log_loss": "Log loss",
        }
    )
    st.dataframe(show, width="stretch", hide_index=True)
    st.caption("Source: data/processed/calibration_comparison.csv")

    raw_row = calibration.loc[calibration["method"] == "raw"].iloc[0]
    iso_row = calibration.loc[calibration["method"] == "isotonic"].iloc[0]
    m1, m2, m3 = st.columns(3)
    m1.metric("Logistic raw AUC", f"{raw_row['auc']:.4f}")
    m2.metric("Raw Brier", f"{raw_row['brier_score']:.3f}")
    m3.metric("Isotonic Brier (selected)", f"{iso_row['brier_score']:.3f}")

    st.subheader("Calibration on saved test probabilities")
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    y = predictions["target"].astype(int)
    p = predictions["predicted_default_probability"]
    bins = pd.qcut(p.rank(method="first"), q=10, labels=False)
    cal = (
        pd.DataFrame({"p": p, "y": y, "bin": bins})
        .groupby("bin", as_index=False)
        .mean()
    )
    ax.plot(cal["p"], cal["y"], marker="o", label="Isotonic-calibrated test scores")
    ax.plot([0, 1], [0, 1], linestyle="--", label="Perfect calibration")
    ax.set_xlabel("Predicted default probability")
    ax.set_ylabel("Observed default rate")
    ax.set_title("Reliability (test set, saved scores)")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Source: data/processed/predictions.parquet (already-calibrated test scores).")

    st.subheader("Predicted vs observed default by risk decile")
    fig, ax = fig_style()
    ax.plot(segments["risk_decile"], segments["average_predicted_pd"], marker="o", label="Predicted")
    ax.plot(segments["risk_decile"], segments["observed_default_rate"], marker="o", label="Observed")
    ax.set_xlabel("Risk decile (1 = lowest risk)")
    ax.set_ylabel("Default probability / rate")
    ax.set_title("Test-set risk segments")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Source: data/processed/risk_segment_summary.csv")


with tab_port:
    p1, p2, p3 = st.columns(3)
    p1.metric("Expected-default HHI", f"{HHI:.4f}")
    p2.metric("Concentration Gini", f"{GINI:.4f}")
    top10 = float(pareto.loc[pareto["top_customer_pct"] == 10.0, "expected_default_share_pct"].iloc[0])
    p3.metric("Top 10% expected-default share", f"{top10:.2f}%")

    st.subheader("Pareto: share of expected defaults")
    st.caption(
        "Saved output of src.metrics.pareto_risk_summary on the test predictions "
        "(data/processed/risk_pareto_summary.csv)."
    )
    fig, ax = fig_style()
    ax.plot(pareto["top_customer_pct"], pareto["expected_default_share_pct"], marker="o")
    ax.set_xlabel("Top customer share (%)")
    ax.set_ylabel("Share of expected defaults (%)")
    ax.set_title("Pareto concentration of expected default")
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(pareto, width="stretch", hide_index=True)

    ranked = predictions.sort_values(
        "predicted_default_probability", ascending=False
    ).reset_index(drop=True)
    ranked["customer_share"] = (ranked.index + 1) / len(ranked)
    ranked["cumulative_risk_share"] = (
        ranked["predicted_default_probability"].cumsum()
        / ranked["predicted_default_probability"].sum()
    )
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.plot(ranked["customer_share"], ranked["cumulative_risk_share"], label="Lorenz (saved scores)")
    ax.plot([0, 1], [0, 1], linestyle="--", label="Equal share")
    ax.set_xlabel("Cumulative share of test customers")
    ax.set_ylabel("Cumulative share of expected defaults")
    ax.set_title("Portfolio expected-default concentration")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)
    st.caption("Source: data/processed/predictions.parquet")
