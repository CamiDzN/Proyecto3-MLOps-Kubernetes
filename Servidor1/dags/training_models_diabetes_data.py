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
# Configuración de MLflow y MinIO
# -------------------------------------------------------------------
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://10.43.101.196:30001"
os.environ["AWS_ACCESS_KEY_ID"] = "admin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "supersecret"
mlflow.set_tracking_uri("http://10.43.101.196:30003")
# Actualizamos el nombre del experimento
mlflow.set_experiment("diabetes_readmission_training")

# -------------------------------------------------------------------
# URIs de conexión a la base CleanData
# -------------------------------------------------------------------
db_user = os.getenv("DB_USER", "model_user")
db_pass = os.getenv("DB_PASS", "model_password")
db_host = os.getenv("DB_HOST", "mysql-service")
db_port = os.getenv("DB_PORT", 3306)
clean_db = "CleanData"
CLEAN_URI = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{clean_db}"

# -------------------------------------------------------------------
# Definición de argumentos por defecto del DAG
# -------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

# -------------------------------------------------------------------
# Definición del DAG
# -------------------------------------------------------------------
with DAG(
    dag_id="train_and_register",  # Nombre del DAG
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["mlops", "training"],
) as dag:

    # -------------------------------------------------------------------
    # T1: Entrena varios modelos y registra cada experimento en MLflow
    # -------------------------------------------------------------------
    def train_models(**kwargs):
        # Leer datos procesados desde CleanData
        engine = create_engine(CLEAN_URI)
        df_train = pd.read_sql("SELECT * FROM diabetes_train_processed", engine)
        df_val   = pd.read_sql("SELECT * FROM diabetes_validation_processed", engine)
        df_test  = pd.read_sql("SELECT * FROM diabetes_test_processed", engine)

        # Separar features/target
        X_train = df_train.drop("early_readmit", axis=1)
        y_train = df_train["early_readmit"]
        X_val   = df_val.drop("early_readmit", axis=1)
        y_val   = df_val["early_readmit"]
        X_test  = df_test.drop("early_readmit", axis=1)
        y_test  = df_test["early_readmit"]

        # Escalado de features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled   = scaler.transform(X_val)
        X_test_scaled  = scaler.transform(X_test)

        X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=X_train.columns)
        X_val_scaled_df   = pd.DataFrame(X_val_scaled,   columns=X_val.columns)
        X_test_scaled_df  = pd.DataFrame(X_test_scaled,  columns=X_test.columns)

        # Definición de experimentos (modelos y parámetros)
        experiments = [
            ("LR_C_0.01",    LogisticRegression(C=0.01, max_iter=1000, solver='lbfgs')),
            ("LR_C_0.1",     LogisticRegression(C=0.1,  max_iter=1000, solver='lbfgs')),
            ("LR_C_1",       LogisticRegression(C=1.0,  max_iter=1000, solver='lbfgs')),
            ("RF_100",       RandomForestClassifier(n_estimators=100, random_state=42)),
            ("RF_200",       RandomForestClassifier(n_estimators=200, random_state=42)),
            ("RF_depth10",   RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
        ]

        # Iterar sobre cada experimento
        for name, model in experiments:
            with mlflow.start_run(run_name=name):
                # Entrenar
                model.fit(X_train_scaled_df, y_train)

                # Evaluar en validación
                y_val_pred  = model.predict(X_val_scaled_df)
                y_val_proba = model.predict_proba(X_val_scaled_df)[:, 1]
                val_acc     = accuracy_score(y_val, y_val_pred)
                val_roc     = roc_auc_score(y_val, y_val_proba)

                # Evaluar en test
                y_test_pred  = model.predict(X_test_scaled_df)
                y_test_proba = model.predict_proba(X_test_scaled_df)[:, 1]
                test_acc     = accuracy_score(y_test, y_test_pred)
                test_roc     = roc_auc_score(y_test, y_test_proba)

                # Log de parámetros y métricas
                mlflow.log_params(model.get_params())
                mlflow.log_metric("val_accuracy", val_acc)
                mlflow.log_metric("val_roc_auc", val_roc)
                mlflow.log_metric("test_accuracy", test_acc)
                mlflow.log_metric("test_roc_auc", test_roc)

                # Inferir signature e input example
                input_example = X_train_scaled_df.head(3)
                signature     = infer_signature(X_train_scaled_df, model.predict_proba(X_train_scaled_df))

                # Log del modelo en MLflow
                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path="model",
                    signature=signature,
                    input_example=input_example
                )

    # -------------------------------------------------------------------
    # T2: Seleccionar la mejor ejecución y promover el modelo a Production
    # -------------------------------------------------------------------
    def select_and_promote(**kwargs):
        client = MlflowClient(tracking_uri="http://10.43.101.196:30003")
        # Cambiamos a nuevo experimento
        experiment = client.get_experiment_by_name("diabetes_readmission_training")
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.val_roc_auc DESC"]
        )

        best_run    = runs[0]
        best_run_id = best_run.info.run_id
        model_uri   = f"runs:/{best_run_id}/model"
        model_name  = "best_diabetes_readmission_model"

        # Crear registro si no existe
        try:
            client.get_registered_model(model_name)
        except Exception:
            client.create_registered_model(model_name)

        # Registrar versión y promover a Production
        mv = client.create_model_version(
            name=model_name,
            source=model_uri,
            run_id=best_run_id
        )
        client.transition_model_version_stage(
            name=model_name,
            version=mv.version,
            stage="Production",
            archive_existing_versions=True
        )

    # Definición de tasks
t1 = PythonOperator(
    task_id="train_models",
    python_callable=train_models,
    provide_context=True
)
t2 = PythonOperator(
    task_id="select_and_promote",
    python_callable=select_and_promote,
    provide_context=True
)

# Orquestación del flujo
t1 >> t2
