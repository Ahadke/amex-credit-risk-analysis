import numpy as np
from src.metrics import classification_metrics


def test_classification_metrics_returns_expected_keys():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9])

    metrics = classification_metrics(y_true, y_prob)

    assert "auc" in metrics
    assert "average_precision" in metrics
    assert "brier_score" in metrics
    assert "log_loss" in metrics
    assert 0 <= metrics["auc"] <= 1
    assert metrics["brier_score"] >= 0

