from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
import os
from sklearn.feature_selection import SelectKBest, f_classif

RAW_CONN_URI   = os.getenv("AIRFLOW_CONN_MYSQL_DEFAULT")
CLEAN_CONN_URI = os.getenv("AIRFLOW_CONN_MYSQL_CLEAN")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024,1,1),
    "retries": 1,
}

def load_splits(**kwargs):
    """T1: leer las tablas de RawData en XCom como JSON."""
    engine = create_engine(RAW_CONN_URI)
    dfs = {
        name: pd.read_sql(f"SELECT * FROM {name}", engine)
        for name in ("train_data","validation_data","test_data")
    }
    # serializar cada uno
    return {k: v.to_json(orient="split") for k,v in dfs.items()}

def clean_splits(**kwargs):
    """T2: limpieza inicial sobre cada split."""
    ti = kwargs["ti"]
    raw = ti.xcom_pull(task_ids="load_splits")
    cleaned = {}
    for name, j in raw.items():
        df = pd.read_json(j, orient="split")
        # drop irrelevantes
        to_drop = ["encounter_id","patient_nbr","diag_1","diag_2","diag_3",
                   "payer_code","medical_specialty","weight"]
        df = df.drop(columns=to_drop, errors="ignore")
        # convertir numéricos
        num_cols = ['time_in_hospital','num_lab_procedures','num_procedures',
                    'num_medications','number_outpatient','number_emergency',
                    'number_inpatient','number_diagnoses']
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        # rellenar NaN
        fill_map = {
            c: (df[c].mode()[0] if df[c].dtype=="object" else df[c].median())
            for c in df.columns
        }
        df = df.fillna(fill_map)
        # dummies
        df = pd.get_dummies(df, drop_first=True)
        cleaned[name] = df.to_json(orient="split")
    return cleaned

def select_features(**kwargs):
    """T3: aplicar SelectKBest(50) fit en train y transformar los 3 splits."""
    ti = kwargs["ti"]
    clean = ti.xcom_pull(task_ids="clean_splits")
    # reconstruir
    df_train = pd.read_json(clean["train_data"], orient="split")
    df_val   = pd.read_json(clean["validation_data"], orient="split")
    df_test  = pd.read_json(clean["test_data"], orient="split")
    # verificar target
    if "readmitted_NO" not in df_train.columns:
        raise ValueError("Falta readmitted_NO en train_data")
    # separar
    X_train = df_train.drop("readmitted_NO", axis=1)
    y_train = df_train["readmitted_NO"]
    # selector
    selector = SelectKBest(f_classif, k=50)
    X_train_sel = selector.fit_transform(X_train, y_train)
    selected = X_train.columns[selector.get_support()]
    # transformar los otros
    def apply_sel(df, sel):
        arr = df[sel].values
        out = pd.DataFrame(arr, columns=sel)
        if "readmitted_NO" in df.columns:
            out["readmitted_NO"] = df["readmitted_NO"].values
        return out
    dfs = {
        "train_processed": pd.concat([pd.DataFrame(X_train_sel, columns=selected),
                                      pd.Series(y_train.values, name="readmitted_NO")], axis=1),
        "validation_processed": apply_sel(df_val, selected),
        "test_processed": apply_sel(df_test, selected),
    }
    return {k: v.to_json(orient="split") for k,v in dfs.items()}

def save_processed(**kwargs):
    """T4: escribe las 3 tablas procesadas en CleanData."""
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
        provide_context=True
    )
    t2 = PythonOperator(
        task_id="clean_splits",
        python_callable=clean_splits,
        provide_context=True
    )
    t3 = PythonOperator(
        task_id="select_features",
        python_callable=select_features,
        provide_context=True
    )
    t4 = PythonOperator(
        task_id="save_processed",
        python_callable=save_processed,
        provide_context=True
    )

    t1 >> t2 >> t3 >> t4