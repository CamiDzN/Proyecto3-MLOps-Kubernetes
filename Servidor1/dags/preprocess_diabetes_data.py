from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
import os

RAW_CONN_URI = os.getenv("AIRFLOW_CONN_MYSQL_DEFAULT")
CLEAN_CONN_URI = os.getenv("AIRFLOW_CONN_MYSQL_CLEAN")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

def preprocess_data():
    # Conexión a RawData
    raw_engine = create_engine(RAW_CONN_URI)
    df = pd.read_sql("SELECT * FROM diabetes_raw", con=raw_engine)

    # -----------------------------
    # Preprocesamiento básico
    # -----------------------------
    df = df.drop(columns=["encounter_id", "patient_nbr"], errors='ignore')

    # Convertir tipos numéricos explícitos
    numeric_cols = [
        'time_in_hospital', 'num_lab_procedures', 'num_procedures', 
        'num_medications', 'number_outpatient', 'number_emergency',
        'number_inpatient', 'number_diagnoses'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Llenar valores nulos
    df = df.fillna({
        col: df[col].mode()[0] if df[col].dtype == "object" else df[col].median()
        for col in df.columns
    })

    # Codificar variables categóricas (ejemplo: one-hot)
    df = pd.get_dummies(df, drop_first=True)

    # -----------------------------
    # Guardar en CleanData
    # -----------------------------
    clean_engine = create_engine(CLEAN_CONN_URI)
    df.to_sql("diabetes_processed", con=clean_engine, if_exists="replace", index=False)

    print("Preprocesamiento y guardado en CleanData exitoso.")

with DAG(
    dag_id="preprocess_diabetes_data",
    default_args=default_args,
    schedule_interval="@daily",  # o '@once' para prueba
    catchup=False,
    tags=["mlops", "preprocessing"],
) as dag:

    task_preprocess = PythonOperator(
        task_id="preprocess_raw_to_clean",
        python_callable=preprocess_data
    )

    task_preprocess