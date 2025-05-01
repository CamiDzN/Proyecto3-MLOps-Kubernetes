from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pandas as pd
from sqlalchemy import create_engine
import mlflow
import mlflow.sklearn
from sklearn.preprocessing import StandardScaler
from mlflow.models.signature import infer_signature
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from mlflow.tracking import MlflowClient

# -------------------------------------------------------------------
# Configuración de MLflow y MinIO usando variables de entorno definidas en Docker Compose
# -------------------------------------------------------------------
mlflow.set_tracking_uri(os.getenv("AIRFLOW_VAR_MLFLOW_TRACKING_URI"))
mlflow.set_experiment("diabetes_readmission_training")

# Si MLFLOW_S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY están definidas en el entorno,
# el cliente de MLflow las detectará automáticamente.
# -------------------------------------------------------------------
# URI de conexión a la base de datos CleanData usando la conexión de Airflow
# -------------------------------------------------------------------
CLEAN_URI = os.getenv("AIRFLOW_CONN_MYSQL_CLEAN")

# -------------------------------------------------------------------
# Argumentos por defecto del DAG
# -------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

# -------------------------------------------------------------------
# Definición del DAG completo
# -------------------------------------------------------------------
with DAG(
    dag_id="train_and_register",     # Identificador único del DAG
    default_args=default_args,
    schedule_interval="@daily",     # Se ejecuta una vez al día
    catchup=False,                    # No ejecuta instancias pasadas
    tags=["mlops", "training"],
) as dag:

    # -------------------------------------------------------------------
    # T1: Entrenar modelos y registrar cada experimento en MLflow
    # -------------------------------------------------------------------
    def train_models(**kwargs):
        # Cargar data preprocesada de CleanData
        engine = create_engine(CLEAN_URI)
        df_train = pd.read_sql("SELECT * FROM diabetes_train_processed", engine)
        df_val   = pd.read_sql("SELECT * FROM diabetes_validation_processed", engine)
        df_test  = pd.read_sql("SELECT * FROM diabetes_test_processed", engine)

        # Separar features y target
        X_train = df_train.drop("early_readmit", axis=1)
        y_train = df_train["early_readmit"]
        X_val   = df_val.drop("early_readmit", axis=1)
        y_val   = df_val["early_readmit"]
        X_test  = df_test.drop("early_readmit", axis=1)
        y_test  = df_test["early_readmit"]

        # Escalado de características
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled   = scaler.transform(X_val)
        X_test_scaled  = scaler.transform(X_test)

        # Reconstruir DataFrames escalados
        X_train_df = pd.DataFrame(X_train_scaled, columns=X_train.columns)
        X_val_df   = pd.DataFrame(X_val_scaled,   columns=X_val.columns)
        X_test_df  = pd.DataFrame(X_test_scaled,  columns=X_test.columns)

        # Definir experimentos: (nombre, modelo)
        experiments = [
            ("LR_C_0.01",  LogisticRegression(C=0.01, max_iter=1000)),
            ("LR_C_0.1",   LogisticRegression(C=0.1,  max_iter=1000)),
            ("LR_C_1",     LogisticRegression(C=1.0,  max_iter=1000)),
            ("RF_100",     RandomForestClassifier(n_estimators=100, random_state=42)),
            ("RF_200",     RandomForestClassifier(n_estimators=200, random_state=42)),
            ("RF_depth10", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
        ]

        for name, model in experiments:
            with mlflow.start_run(run_name=name):
                # Entrenar modelo
                model.fit(X_train_df, y_train)

                # Evaluar en validación
                y_val_pred  = model.predict(X_val_df)
                y_val_proba = model.predict_proba(X_val_df)[:, 1]
                val_acc     = accuracy_score(y_val, y_val_pred)
                val_roc     = roc_auc_score(y_val, y_val_proba)

                # Evaluar en test
                y_test_pred  = model.predict(X_test_df)
                y_test_proba = model.predict_proba(X_test_df)[:, 1]
                test_acc     = accuracy_score(y_test, y_test_pred)
                test_roc     = roc_auc_score(y_test, y_test_proba)

                # Registra parámetros y métricas
                mlflow.log_params(model.get_params())
                mlflow.log_metric("val_accuracy", val_acc)
                mlflow.log_metric("val_roc_auc",    val_roc)
                mlflow.log_metric("test_accuracy",  test_acc)
                mlflow.log_metric("test_roc_auc",   test_roc)

                # Inferir y registrar signature e input_example
                input_example = X_train_df.head(3)
                signature     = infer_signature(X_train_df, model.predict_proba(X_train_df))
                mlflow.sklearn.log_model(
                    sk_model       = model,
                    artifact_path  = "model",
                    signature      = signature,
                    input_example  = input_example
                )

    train_task = PythonOperator(
        task_id="train_models",
        python_callable=train_models
    )

    # -------------------------------------------------------------------
    # T2: Seleccionar mejor ejecución y promover modelo a Production
    # -------------------------------------------------------------------
    def select_and_promote(**kwargs):
        client = MlflowClient(tracking_uri=os.getenv("AIRFLOW_VAR_MLFLOW_TRACKING_URI"))
        exp    = client.get_experiment_by_name("diabetes_readmission_training")
        runs   = client.search_runs(
            experiment_ids = [exp.experiment_id],
            order_by       = ["metrics.val_roc_auc DESC"]
        )
        best = runs[0]
        run_id    = best.info.run_id
        model_uri = f"runs:/{run_id}/model"
        name      = "best_diabetes_readmission_model"

        # Asegurar que el registro exista
        try:
            client.get_registered_model(name)
        except Exception:
            client.create_registered_model(name)
        mv = client.create_model_version(
            name    = name,
            source  = model_uri,
            run_id  = run_id
        )
        client.transition_model_version_stage(
            name    = name,
            version = mv.version,
            stage   = "Production",
            archive_existing_versions=True
        )

    promote_task = PythonOperator(
        task_id="select_and_promote",
        python_callable=select_and_promote
    )

    # Definir flujo de ejecución: primero entrena, luego promueve
    train_task >> promote_task
