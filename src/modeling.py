from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import (
    RandomForestClassifier,
)
from sklearn.impute import (
    SimpleImputer,
)
from sklearn.linear_model import (
    LogisticRegression,
)
from sklearn.model_selection import (
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    StandardScaler,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


FEATURE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "customer_features.parquet"
)


MODEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "models"
)


def load_features(
    path=FEATURE_PATH,
):

    df = pd.read_parquet(
        path
    )

    print(
        f"Loaded {len(df):,} customer feature rows."
    )

    return df


def prepare_xy(df):

    # Customer identifiers, dates and the target
    # should never become predictive inputs.

    drop_columns = [
        "customer_ID",
        "target",
        "first_statement",
        "last_statement",
    ]

    feature_columns = [
        column
        for column in df.columns
        if column not in drop_columns
    ]

    X = df[
        feature_columns
    ].copy()

    y = df[
        "target"
    ].astype(int)

    print(
        f"Predictor count: "
        f"{len(feature_columns)}"
    )

    return (
        X,
        y,
        feature_columns,
    )


def split_data(
    X,
    y,
    random_state=42,
):

    # We reserve the final test set first.
    # Nothing involved in model selection or calibration
    # should learn from the final test labels.

    X_development, X_test, \
    y_development, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            stratify=y,
            random_state=random_state,
        )
    )

    # A separate calibration set lets us improve probability accuracy
    # without using the final test set.

    X_train, X_calibration, \
    y_train, y_calibration = (
        train_test_split(
            X_development,
            y_development,
            test_size=0.20,
            stratify=y_development,
            random_state=random_state,
        )
    )

    print(
        f"Train: {len(X_train):,}"
    )

    print(
        f"Calibration: "
        f"{len(X_calibration):,}"
    )

    print(
        f"Test: {len(X_test):,}"
    )

    return {
        "X_train":
            X_train,
        "X_calibration":
            X_calibration,
        "X_test":
            X_test,
        "y_train":
            y_train,
        "y_calibration":
            y_calibration,
        "y_test":
            y_test,
    }


def create_models():

    # Imputation lives inside the pipeline,
    # preventing information from the test data
    # from leaking into training medians.

    logistic_regression = Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    random_forest = Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=8,
                    min_samples_leaf=10,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    return {
        "logistic_regression":
            logistic_regression,

        "random_forest":
            random_forest,
    }


def train_models(
    models,
    X_train,
    y_train,
):

    trained_models = {}

    for name, model in models.items():

        print(
            f"Training {name}..."
        )

        model.fit(
            X_train,
            y_train,
        )

        trained_models[name] = (
            model
        )

    return trained_models


def save_model(
    model,
    name,
):

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        MODEL_DIR
        / f"{name}.joblib"
    )

    joblib.dump(
        model,
        path,
    )

    print(
        f"Saved {name} to {path}"
    )