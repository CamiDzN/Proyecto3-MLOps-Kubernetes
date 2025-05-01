
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
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

def load_to_staging(**kwargs):
    """Tarea 1: carga diabetes_raw en tabla staging_raw."""
    engine = create_engine(RAW_CONN_URI)
    df = pd.read_sql("SELECT * FROM diabetes_raw", con=engine)
    df.to_sql(
        name="staging_raw",
        con=engine,
        if_exists="replace",
        index=False
    )

def initial_cleaning(**kwargs):
    """Tarea 2: lee staging_raw, limpia y escribe staging_cleaned."""
    engine = create_engine(RAW_CONN_URI)
    df = pd.read_sql("SELECT * FROM staging_raw", con=engine)

    # Eliminar columnas de alta cardinalidad / irrelevantes
    cols_to_drop = [
        "encounter_id", "patient_nbr", "diag_1", "diag_2", "diag_3",
        "payer_code", "medical_specialty", "weight"
    ]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # Convertir numéricos
    numeric_cols = [
        'time_in_hospital','num_lab_procedures','num_procedures',
        'num_medications','number_outpatient','number_emergency',
        'number_inpatient','number_diagnoses'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rellenar NaN: moda/mediana
    fill_map = {
        col: (df[col].mode()[0] if df[col].dtype == "object" else df[col].median())
        for col in df.columns
    }
    df = df.fillna(fill_map)

    # One-hot de las categóricas restantes
    df = pd.get_dummies(df, drop_first=True)

    df.to_sql(
        name="staging_cleaned",
        con=engine,
        if_exists="replace",
        index=False
    )

def feature_selection(**kwargs):
    """Tarea 3: lee staging_cleaned, aplica SelectKBest y escribe staging_selected."""
    engine = create_engine(RAW_CONN_URI)
    df = pd.read_sql("SELECT * FROM staging_cleaned", con=engine)

    if 'readmitted_NO' not in df.columns:
        raise ValueError("Falta la columna 'readmitted_NO' en staging_cleaned")

    X = df.drop(columns=['readmitted_NO'])
    y = df['readmitted_NO']

    selector = SelectKBest(score_func=f_classif, k=50)
    X_sel = selector.fit_transform(X, y)
    sel_cols = X.columns[selector.get_support()]

    df_sel = pd.DataFrame(X_sel, columns=sel_cols)
    df_sel['readmitted_NO'] = y.values

    df_sel.to_sql(
        name="staging_selected",
        con=engine,
        if_exists="replace",
        index=False
    )

def save_to_cleandata(**kwargs):
    """Tarea 4: lee staging_selected y carga CleanData.diabetes_processed."""
    src_engine  = create_engine(RAW_CONN_URI)
    dest_engine = create_engine(CLEAN_CONN_URI)

    df = pd.read_sql("SELECT * FROM staging_selected", con=src_engine)
    df.to_sql(
        name="diabetes_processed",
        con=dest_engine,
        if_exists="replace",
        index=False
    )
    print(f"Se guardaron {len(df)} filas y {len(df.columns)} columnas en CleanData.diabetes_processed")

with DAG(
    dag_id="preprocess_diabetes_data",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["mlops", "preprocessing"],
) as dag:

    t1 = PythonOperator(
        task_id="load_to_staging",
        python_callable=load_to_staging,
        provide_context=True,
    )

    t2 = PythonOperator(
        task_id="initial_cleaning",
        python_callable=initial_cleaning,
        provide_context=True,
    )

    t3 = PythonOperator(
        task_id="feature_selection",
        python_callable=feature_selection,
        provide_context=True,
    )

    t4 = PythonOperator(
        task_id="save_to_cleandata",
        python_callable=save_to_cleandata,
        provide_context=True,
    )

    t1 >> t2 >> t3 >> t4