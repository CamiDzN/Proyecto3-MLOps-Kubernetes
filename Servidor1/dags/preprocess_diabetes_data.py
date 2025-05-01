# dags/preprocess_incremental.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
import os
from sklearn.feature_selection import SelectKBest, f_classif

# URIs de conexión (definidas en tus Variables de Entorno de Airflow)
RAW_CONN_URI   = os.getenv("AIRFLOW_CONN_MYSQL_DEFAULT")
CLEAN_CONN_URI = os.getenv("AIRFLOW_CONN_MYSQL_CLEAN")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

def load_splits(**kwargs):
    """T1: leer los splits de RawData en JSON via XCom."""
    engine = create_engine(RAW_CONN_URI)
    dfs = {
        name: pd.read_sql(f"SELECT * FROM {name}", engine)
        for name in ("train_data", "validation_data", "test_data")
    }
    return {k: v.to_json(orient="split") for k, v in dfs.items()}

def clean_splits(**kwargs):
    """T2: limpieza inicial sobre cada split (drop, casteo, fillna, dummies)."""
    ti = kwargs["ti"]
    raw = ti.xcom_pull(task_ids="load_splits")
    cleaned = {}
    for name, j in raw.items():
        df = pd.read_json(j, orient="split")
        # columnas irrelevantes / alta cardinalidad
        to_drop = ["encounter_id", "patient_nbr", "diag_1", "diag_2",
                   "diag_3", "payer_code", "medical_specialty", "weight"]
        df = df.drop(columns=to_drop, errors="ignore")
        # convertir numéricos
        num_cols = ['time_in_hospital','num_lab_procedures','num_procedures',
                    'num_medications','number_outpatient','number_emergency',
                    'number_inpatient','number_diagnoses']
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        # rellenar NaN
        fill_map = {
            c: (df[c].mode()[0] if df[c].dtype == "object" else df[c].median())
            for c in df.columns
        }
        df = df.fillna(fill_map)
        # one-hot encoding
        df = pd.get_dummies(df, drop_first=True)
        cleaned[name] = df.to_json(orient="split")
    return cleaned

def select_features(**kwargs):
    """T3: fit SelectKBest en train y reindex en val/test para igualar columnas."""
    ti = kwargs["ti"]
    clean = ti.xcom_pull(task_ids="clean_splits")

    df_train = pd.read_json(clean["train_data"], orient="split")
    df_val   = pd.read_json(clean["validation_data"], orient="split")
    df_test  = pd.read_json(clean["test_data"], orient="split")

    if "readmitted_NO" not in df_train.columns:
        raise ValueError("No se encontró 'readmitted_NO' en train_data")

    # separar X/y
    X_train = df_train.drop("readmitted_NO", axis=1)
    y_train = df_train["readmitted_NO"]

    # fit selector
    selector = SelectKBest(score_func=f_classif, k=50)
    selector.fit(X_train, y_train)
    sel_cols = X_train.columns[selector.get_support()]

    # transformar train
    X_train_sel = pd.DataFrame(selector.transform(X_train), columns=sel_cols)
    X_train_sel["readmitted_NO"] = y_train.values

    # función helper para val/test
    def apply_sel(df, sel_cols):
        X = df.drop("readmitted_NO", axis=1)
        y = df["readmitted_NO"]
        X_sel = X.reindex(columns=sel_cols, fill_value=0)
        X_sel["readmitted_NO"] = y.values
        return X_sel

    df_val_sel  = apply_sel(df_val, sel_cols)
    df_test_sel = apply_sel(df_test, sel_cols)

    return {
        "train_processed": df_train_sel.to_json(orient="split"),
        "validation_processed": df_val_sel.to_json(orient="split"),
        "test_processed": df_test_sel.to_json(orient="split"),
    }

def save_processed(**kwargs):
    """T4: escribe los splits procesados en CleanData."""
    ti = kwargs["ti"]
    proc = ti.xcom_pull(task_ids="select_features")
    engine = create_engine(CLEAN_CONN_URI)
    for name, j in proc.items():
        df = pd.read_json(j, orient="split")
        table = f"diabetes_{name}"
        df.to_sql(table, engine, if_exists="replace", index=False)
        print(f"Guardadas {len(df)} filas en CleanData.{table}")

with DAG(
    dag_id="preprocess_incremental",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["mlops","preprocessing"],
) as dag:

    t1 = PythonOperator(
        task_id="load_splits",
        python_callable=load_splits,
        provide_context=True,
    )
    t2 = PythonOperator(
        task_id="clean_splits",
        python_callable=clean_splits,
        provide_context=True,
    )
    t3 = PythonOperator(
        task_id="select_features",
        python_callable=select_features,
        provide_context=True,
    )
    t4 = PythonOperator(
        task_id="save_processed",
        python_callable=save_processed,
        provide_context=True,
    )

    t1 >> t2 >> t3 >> t4