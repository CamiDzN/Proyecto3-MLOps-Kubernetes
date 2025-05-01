# dags/preprocess_incremental.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
import os
from sklearn.feature_selection import SelectKBest, f_classif

# -------------------------------------------------------------------
# URIs de conexión para RawData y CleanData (Variables de Entorno)
# -------------------------------------------------------------------
RAW_CONN_URI   = os.getenv("AIRFLOW_CONN_MYSQL_DEFAULT")
CLEAN_CONN_URI = os.getenv("AIRFLOW_CONN_MYSQL_CLEAN")

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

# -------------------------------------------------------------------
# T1: load_splits
#   Lee de RawData las tablas train_data, validation_data y test_data
#   Serializa cada DataFrame a JSON para pasar por XCom
# -------------------------------------------------------------------
def load_splits(**kwargs):
    engine = create_engine(RAW_CONN_URI)
    dfs = {
        name: pd.read_sql(f"SELECT * FROM {name}", engine)
        for name in ("train_data", "validation_data", "test_data")
    }
    return {k: v.to_json(orient="split") for k, v in dfs.items()}


# -------------------------------------------------------------------
# T2: clean_splits
#   - Recupera JSON de cada split
#   - Crea columna early_readmit = 1 si readmitted == '<30' else 0
#   - Elimina la columna original readmitted
#   - Elimina columnas irrelevantes/alta cardinalidad
#   - Casteo numérico, fillna y one-hot encoding de FEATURES
# -------------------------------------------------------------------
def clean_splits(**kwargs):
    ti = kwargs["ti"]
    raw = ti.xcom_pull(task_ids="load_splits")
    cleaned = {}

    for name, j in raw.items():
        df = pd.read_json(j, orient="split")

        # 1) Crear target binario
        df["early_readmit"] = (df["readmitted"] == "<30").astype(int)
        df = df.drop(columns=["readmitted"], errors="ignore")

        # 2) Drop columnas no usadas
        to_drop = [
            "encounter_id", "patient_nbr",
            "diag_1", "diag_2", "diag_3",
            "payer_code", "medical_specialty", "weight"
        ]
        df = df.drop(columns=to_drop, errors="ignore")

        # 3) Asegurar tipos numéricos
        num_cols = [
            'time_in_hospital','num_lab_procedures','num_procedures',
            'num_medications','number_outpatient','number_emergency',
            'number_inpatient','number_diagnoses'
        ]
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # 4) Rellenar NaN: moda para object, mediana para numéricos
        fill_map = {
            c: (df[c].mode()[0] if df[c].dtype == "object" else df[c].median())
            for c in df.columns if c != "early_readmit"
        }
        df = df.fillna(fill_map)

        # 5) One-hot encoding SOLO de las columnas explicativas
        features = df.drop("early_readmit", axis=1)
        df_enc = pd.get_dummies(features, drop_first=True)
        df_enc["early_readmit"] = df["early_readmit"]  # reanexar target

        cleaned[name] = df_enc.to_json(orient="split")

    return cleaned


# -------------------------------------------------------------------
# T3: select_features
#   - Recupera DataFrames limpios desde XCom
#   - Ajusta SelectKBest(k=50) sobre train
#   - Transforma train; reindexa val/test para usar mismas columnas
# -------------------------------------------------------------------
def select_features(**kwargs):
    ti = kwargs["ti"]
    clean = ti.xcom_pull(task_ids="clean_splits")

    df_train = pd.read_json(clean["train_data"], orient="split")
    df_val   = pd.read_json(clean["validation_data"], orient="split")
    df_test  = pd.read_json(clean["test_data"], orient="split")

    # Validar target
    if "early_readmit" not in df_train.columns:
        raise ValueError("No se encontró 'early_readmit' en train_data")

    # 1) Separar X_train/y_train
    X_train = df_train.drop("early_readmit", axis=1)
    y_train = df_train["early_readmit"]

    # 2) Ajustar selector en train
    selector = SelectKBest(score_func=f_classif, k=50)
    selector.fit(X_train, y_train)
    sel_cols = X_train.columns[selector.get_support()]

    # 3) Transformar train
    X_train_sel = selector.transform(X_train)
    df_train_sel = pd.DataFrame(X_train_sel, columns=sel_cols)
    df_train_sel["early_readmit"] = y_train.values

    # 4) Aplicar mismo selector a val/test con reindex fill 0
    def apply_sel(df, sel_cols):
        X = df.drop("early_readmit", axis=1)
        y = df["early_readmit"]
        X_sel = X.reindex(columns=sel_cols, fill_value=0)
        X_sel["early_readmit"] = y.values
        return X_sel

    df_val_sel  = apply_sel(df_val, sel_cols)
    df_test_sel = apply_sel(df_test, sel_cols)

    # Devolver JSON de cada split procesado
    return {
        "train_processed": df_train_sel.to_json(orient="split"),
        "validation_processed": df_val_sel.to_json(orient="split"),
        "test_processed": df_test_sel.to_json(orient="split"),
    }


# -------------------------------------------------------------------
# T4: save_processed
#   - Recupera JSON procesados
#   - Guarda en CleanData.diabetes_<split>_processed
# -------------------------------------------------------------------
def save_processed(**kwargs):
    ti = kwargs["ti"]
    proc = ti.xcom_pull(task_ids="select_features")
    engine = create_engine(CLEAN_CONN_URI)

    for name, j in proc.items():
        df = pd.read_json(j, orient="split")
        table = f"diabetes_{name}"
        df.to_sql(table, engine, if_exists="replace", index=False)
        print(f"Guardadas {len(df)} filas en CleanData.{table}")


# -------------------------------------------------------------------
# Definición del DAG y flujo de tareas
# -------------------------------------------------------------------
with DAG(
    dag_id="preprocess_incremental",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["mlops", "preprocessing"],
) as dag:

    t1_load   = PythonOperator(
        task_id="load_splits",
        python_callable=load_splits,
        provide_context=True,
    )
    t2_clean  = PythonOperator(
        task_id="clean_splits",
        python_callable=clean_splits,
        provide_context=True,
    )
    t3_select = PythonOperator(
        task_id="select_features",
        python_callable=select_features,
        provide_context=True,
    )
    t4_save   = PythonOperator(
        task_id="save_processed",
        python_callable=save_processed,
        provide_context=True,
    )

    # Orquestación de tareas
    t1_load >> t2_clean >> t3_select >> t4_save