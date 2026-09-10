import mlflow

mlflow.set_experiment("amex-credit-risk")

with mlflow.start_run():
    mlflow.log_param("model", "test-model")
    mlflow.log_metric("auc", 0.95)
    mlflow.log_metric("brier_improvement", 0.14)

print("MLflow logging works")
