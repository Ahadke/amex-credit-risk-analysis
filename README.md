# American Express Credit Risk

Customer-level default risk analysis on the American Express Default Prediction dataset. The project loads statement-level Kaggle data into PostgreSQL, builds a customer warehouse, and runs a sequence of analyses: EDA, statistical testing, time-to-risk-transition, structural-shift checks, calibrated classification, and portfolio concentration. A Streamlit dashboard reads the saved `data/processed/` artifacts.

This README uses only figures produced by the executed notebooks. It does not treat risk-transition as literal time-to-default, and it does not treat the 2017-06 cohort break as a causal policy effect.

---

## Project Overview

American Express provided anonymized monthly credit-card statements and a customer-level default label. The goal here is not leaderboard scoring. It is to:

1. Understand the statement grain and warehouse it in PostgreSQL.
2. Describe customer histories and default rates.
3. Test which latest-statement features separate defaulters from non-defaulters.
4. Study time until an observable high-risk state appears (not default date).
5. Check whether default rates shift across entry cohorts (not a causal DiD/RDD).
6. Fit default classifiers, recalibrate probabilities on a held-out calibration split, and measure how concentrated expected default is in the test portfolio.

---

## Dataset

Source: [American Express Default Prediction](https://www.kaggle.com/competitions/amex-default-prediction) (Kaggle). This is real production-style credit data, not a toy sample.

| Item | Value |
|---|---|
| Customers (`train_labels.csv`) | 458,913 |
| Statement rows (`train_data.csv`) | 5,531,451 |
| Statement window | 2017-03-01 to 2018-03-31 |
| Default rate | 25.8934% |
| Columns in `train_data.csv` | 190 (188 behavioral features + `customer_ID` + `S_2`) |

Grain: one raw row = one customer × statement date. The target is customer-level. Repeated statements are never treated as independent customer labels.

---

## Architecture

```text
data/raw/train_data.csv          data/raw/train_labels.csv
        |                                  |
        v                                  v
 PostgreSQL COPY                    pandas -> raw_labels
        |
        v
   raw_statements (TEXT landing)
        |
        v
 sql/cleaning.sql
        |
        +--> dim_customer        (one row per customer)
        +--> fact_statements     (typed statements, statement_date)
                    |
                    v
         notebooks 01 → 06
                    |
                    v
         data/processed/*.parquet, *.csv, models/*.joblib
                    |
                    v
         dashboard/app.py  (Streamlit; reads processed files only)
```

Python does not load the 16 GB statement file with all columns after notebook 01. Later phases query PostgreSQL or read `data/processed/`.

---

## Methodology

### Phase 1 — Data understanding (`notebooks/01_data_understanding.ipynb`)

Labels are small enough to load fully: 458,913 unique customers, 0 duplicate IDs, default rate 25.8934%. A 250,000-row statement sample is used only for schema, feature families, and missingness. The full file is scanned with `chunksize` on `customer_ID` and `S_2` only, yielding 5,531,451 rows, 458,913 customers, and dates 2017-03-01 to 2018-03-31. Most customers have 13 statements (mean 12.05).

### Phase 2 — Warehouse (`src/data_cleaning.py`, `sql/cleaning.sql`)

`raw_labels` is loaded with pandas. `raw_statements` is created from the CSV header as TEXT, then filled with PostgreSQL `COPY`. `cleaning.sql` builds `dim_customer` and typed `fact_statements`. Identifiers stay quoted `"customer_ID"`. Source date `S_2` becomes `statement_date`. `D_63` and `D_64` remain TEXT; other features are DOUBLE PRECISION. Confirmed counts: 458,913 labels, 5,531,451 statements, 458,913 customers in both dimension and fact tables. Zero duplicate `(customer_ID, statement_date)` pairs.

### Phase 3 — Customer-level EDA (`notebooks/02_eda.ipynb`)

`dim_customer` is one row per customer. Default rates by statement count range from 23.2% (13 statements, 386,034 customers) to about 32–46% for shorter histories. Latest-statement medians differ by target (example: P_2 0.784 non-default vs 0.352 default). The numeric latest-statement table is `customer_feature_sample.parquet`. An expanded file, `customer_feature_sample_with_categoricals.parquet`, adds the 11 known AMEX categoricals for chi-square testing and does not overwrite the numeric sample.

### Phase 4 — Statistical testing (`notebooks/03_statistical_testing.ipynb`)

Numeric tests use Mann–Whitney U and rank-biserial correlation:

```text
rank-biserial = 2U / (n_default * n_non_default) - 1
```

All 13 numeric candidates were shortlisted. Strongest effect: **P_2**, rank-biserial **0.834**.

Categorical tests (added after the initial numeric-only run) use chi-square and Cramér's V:

```text
V = sqrt( chi2 / (n * min(r-1, c-1)) )
```

FDR (Benjamini–Hochberg) is applied **once** across numeric + categorical p-values. Ten categoricals were testable (`D_66` had a single observed level). Seven categoricals met FDR p < 0.05, V ≥ 0.10, and missingness < 60% (largest: B_38 V = 0.528, B_30 V = 0.407). The combined shortlist has 20 features. Numeric rank-biserial values from the original Mann–Whitney run are unchanged.

### Phase 5 — Time-to-risk-transition (`notebooks/04_survival_analysis.ipynb`)

AMEX does not provide a default date. This phase is **time-to-observed-risk-transition**, not time-to-default.

P_2 is the strongest shortlisted feature; lower values are riskier. A baseline (first-statement) threshold of **0.482** defines the event. Customers who never cross are censored. Event rate **35.75%**. Log-rank p ≈ **0**. Actual default rate is **0.606** among customers who crossed the threshold vs **0.066** among those who never crossed. Cox PH hazard ratios describe faster or slower entry into that proxy state; several covariates fail the PH test at this sample size.

### Phase 6 — Structural shift check (`notebooks/05_causal_policy_impact.ipynb`)

This is a **structural-shift check**, not a causal policy effect. There is no treatment indicator, no confirmed policy date, and no untreated control group.

Every customer's last statement falls in **2018-03**, so a final-statement cohort series has no time variation. The clock used is **first-statement month** (13 months). Candidate break: **2017-06-01**, chosen by residual sum of squares among interrupted time-series fits. The regression is

```text
default_rate ~ time + post + time_after
```

with HAC standard errors. Composition medians of P_2, D_44, B_2, B_1, and B_9 also change across cohorts, so a rate break can reflect who enters the window, not a policy.

### Phase 7 — Classification and calibration (`notebooks/06_classification_calibration_scoring.ipynb`)

Features come from `customer_features.parquet` (458,913 customers, 83 predictors). Split:

| Split | Rows | Role |
|---|---|---|
| Train | 293,704 | Fit classifiers |
| Calibration | 73,426 | Fit probability mapping only |
| Test | 91,783 | Final evaluation |

The test set is not used for imputation, model fitting, or calibration. Logistic regression test AUC **0.9535**, average precision **0.878**, raw Brier **0.087**. Random forest was slightly worse (AUC 0.9493). Platt and isotonic recalibration are fit on the calibration split with the base model frozen. Isotonic Brier **0.075** was the best of the methods tried.

### Phase 8 — Portfolio concentration

Expected default is the sum of predicted default probabilities (no dollar EAD is available).

| Measure | Value |
|---|---|
| Expected-default HHI (10 risk deciles) | 0.2704 |
| Concentration Gini | 0.6692 |
| Share of expected defaults in the top 10% of customers | 36.68% |

```text
HHI = sum_k (share_k)^2
Gini = 1 - 2 * area_under_Lorenz
```

### Phase 9 — Dashboard

`dashboard/app.py` is a Streamlit app. It reads `data/processed/` only. It does not rerun SQL, feature engineering, or model training.

```bash
streamlit run dashboard/app.py
```

---

## Technologies

| Layer | Tools |
|---|---|
| Language | Python 3.12 (`.venv312`) |
| Warehouse | PostgreSQL 16, SQLAlchemy, psycopg2 |
| Analysis | pandas, NumPy, SciPy, statsmodels, scikit-learn, lifelines |
| Notebooks | Jupyter |
| Dashboard | Streamlit |
| Artifacts | Parquet, CSV, joblib |

---

## Known Limitations

1. **Survival analysis is time-to-risk-transition, not time-to-default.** The dataset has no default event date. Last-statement minus first-statement with `target` as the event would not be a valid duration model. Phase 5 uses first crossing of a baseline P_2 threshold as a proxy state.

2. **The “policy impact” notebook is a structural-shift check, not a causal claim.** There is no assigned treatment and no confirmed policy-change date. The last-statement cohort is structurally unusable because every customer ends in 2018-03. First-statement ITS can detect a break in the series; it cannot attribute that break to underwriting policy.

3. **Chi-square / categorical analysis was added after the initial numeric-only submission.** The first EDA sample omitted the 11 known categoricals, so chi-square originally returned an empty table. Categoricals were later pulled into `customer_feature_sample_with_categoricals.parquet`. Joint FDR was recomputed across numeric + categorical tests. Numeric rank-biserial results from Phase 4 were not changed. `D_66` could not be chi-square tested (one observed level).

4. **Large-N tests overstate “significance.”** With 458,913 customers, very small effects still have tiny p-values. Shortlisting therefore requires effect size and missingness filters, not p-values alone.

5. **Calibration and model selection use a single train/calibration/test split.** There is no nested cross-validation of the calibration method.

---

## How to Reproduce

Do **not** re-run the 16 GB `COPY` if PostgreSQL already contains 458,913 labels and 5,531,451 statements.

```bash
cd amex_credit_risk
source .venv312/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DB_USER / DB_PASSWORD / DB_NAME
```

If the warehouse is empty (first machine only):

```bash
createdb amex_credit_risk   # if needed
python src/data_cleaning.py
```

Then, from the project root, run notebooks in order with the `.venv312` kernel:

```text
notebooks/01_data_understanding.ipynb
notebooks/02_eda.ipynb
notebooks/03_statistical_testing.ipynb
notebooks/04_survival_analysis.ipynb
notebooks/05_causal_policy_impact.ipynb
python src/feature_engineering.py
notebooks/06_classification_calibration_scoring.ipynb
```

Feature helpers: `src/feature_engineering.py`, `src/metrics.py`, `src/modeling.py`. The calibrated model file is written by notebook 06 to `data/processed/models/final_calibrated_model.joblib`. That path is gitignored via `*.joblib`; regenerate it locally by re-running notebook 06 (`src/modeling.py` builds the unfitted pipelines and split, not the saved calibrated artifact).

Dashboard:

```bash
streamlit run dashboard/app.py
```

### Git hygiene

`.gitignore` excludes `.env`, `data/raw/` (including `train_data.csv`), virtualenvs, and `*.joblib`. The raw statement CSV is about 15 GB and must never be committed. The saved calibrated model is currently ~11 KB; it is still gitignored with other joblib files so local retrains do not get pushed by accident.
