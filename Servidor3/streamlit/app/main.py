# app.py

import streamlit as st
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Usamos el DNS interno de Kubernetes (namespace loadtest)
API_URL = "http://fastapi-service.loadtest.svc.cluster.local:8000"
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Diabetes Readmission Prediction")

# ─────────────────────────────────────────────────────────────────────────────
# Antes de mostrar la UI, pedimos a la API qué modelo está en producción
try:
    info = requests.get(f"{API_URL}/model-info", timeout=2).json()
    modelo = info.get("model_name", "desconocido")
    stage  = info.get("stage", "—")
except:
    modelo = "desconocido"
    stage  = "—"

# Mostramos el modelo y su stage en la cabecera
st.title("Diabetes Readmission Prediction")
st.markdown(f"**Modelo en uso:** `{modelo}` (stage: {stage})")
st.markdown("Rellena los campos y pulsa **Ejecutar inferencia** para obtener la predicción.")
# ─────────────────────────────────────────────────────────────────────────────

# ── Inputs numéricos básicos ─────────────────────────────────────────────────

admission_type_id        = st.number_input("admission_type_id",         value=0.0, format="%.2f")
discharge_disposition_id = st.number_input("discharge_disposition_id", value=0.0, format="%.2f")
admission_source_id      = st.number_input("admission_source_id",      value=0.0, format="%.2f")
time_in_hospital         = st.number_input("time_in_hospital",         value=0.0, format="%.2f")
num_lab_procedures       = st.number_input("num_lab_procedures",       value=0.0, format="%.2f")
num_procedures           = st.number_input("num_procedures",           value=0.0, format="%.2f")
num_medications          = st.number_input("num_medications",          value=0.0, format="%.2f")
number_outpatient        = st.number_input("number_outpatient",        value=0.0, format="%.2f")
number_emergency         = st.number_input("number_emergency",         value=0.0, format="%.2f")
number_inpatient         = st.number_input("number_inpatient",         value=0.0, format="%.2f")
number_diagnoses         = st.number_input("number_diagnoses",         value=0.0, format="%.2f")

# ── One-hot features ─────────────────────────────────────────────────────────

race_Asian      = st.number_input("race_Asian",      value=0.0, format="%.2f")
race_Caucasian  = st.number_input("race_Caucasian",  value=0.0, format="%.2f")
race_Other      = st.number_input("race_Other",      value=0.0, format="%.2f")

# ── Edad (aliases para age_[x-y)) ────────────────────────────────────────────

age_10_20  = st.number_input("age_[10-20)",  value=0.0, format="%.2f")
age_20_30  = st.number_input("age_[20-30)",  value=0.0, format="%.2f")
age_40_50  = st.number_input("age_[40-50)",  value=0.0, format="%.2f")
age_50_60  = st.number_input("age_[50-60)",  value=0.0, format="%.2f")
age_70_80  = st.number_input("age_[70-80)",  value=0.0, format="%.2f")
age_80_90  = st.number_input("age_[80-90)",  value=0.0, format="%.2f")
age_90_100 = st.number_input("age_[90-100)", value=0.0, format="%.2f")

# ── A1Cresult ────────────────────────────────────────────────────────────────

A1Cresult_gt_8 = st.number_input("A1Cresult_>8", value=0.0, format="%.2f")
A1Cresult_Norm = st.number_input("A1Cresult_Norm", value=0.0, format="%.2f")

# ── Medicamentos one-hot ─────────────────────────────────────────────────────

metformin_No        = st.number_input("metformin_No",        value=0.0, format="%.2f")
metformin_Steady    = st.number_input("metformin_Steady",    value=0.0, format="%.2f")
metformin_Up        = st.number_input("metformin_Up",        value=0.0, format="%.2f")
repaglinide_No      = st.number_input("repaglinide_No",      value=0.0, format="%.2f")
repaglinide_Steady  = st.number_input("repaglinide_Steady",  value=0.0, format="%.2f")
chlorpropamide_No   = st.number_input("chlorpropamide_No",   value=0.0, format="%.2f")
chlorpropamide_Steady = st.number_input("chlorpropamide_Steady", value=0.0, format="%.2f")
glimepiride_No      = st.number_input("glimepiride_No",      value=0.0, format="%.2f")
glimepiride_Steady  = st.number_input("glimepiride_Steady",  value=0.0, format="%.2f")
glimepiride_Up      = st.number_input("glimepiride_Up",      value=0.0, format="%.2f")
glipizide_No        = st.number_input("glipizide_No",        value=0.0, format="%.2f")
glipizide_Steady    = st.number_input("glipizide_Steady",    value=0.0, format="%.2f")
glipizide_Up        = st.number_input("glipizide_Up",        value=0.0, format="%.2f")
glyburide_No        = st.number_input("glyburide_No",        value=0.0, format="%.2f")
glyburide_Steady    = st.number_input("glyburide_Steady",    value=0.0, format="%.2f")
tolbutamide_Steady  = st.number_input("tolbutamide_Steady",  value=0.0, format="%.2f")
pioglitazone_Up     = st.number_input("pioglitazone_Up",     value=0.0, format="%.2f")
rosiglitazone_No    = st.number_input("rosiglitazone_No",    value=0.0, format="%.2f")
rosiglitazone_Steady= st.number_input("rosiglitazone_Steady",value=0.0, format="%.2f")
acarbose_Up         = st.number_input("acarbose_Up",         value=0.0, format="%.2f")
tolazamide_Steady   = st.number_input("tolazamide_Steady",   value=0.0, format="%.2f")
insulin_No          = st.number_input("insulin_No",          value=0.0, format="%.2f")
insulin_Up          = st.number_input("insulin_Up",          value=0.0, format="%.2f")
glyburide_metformin_No     = st.number_input("glyburide-metformin_No",     value=0.0, format="%.2f")
glyburide_metformin_Steady = st.number_input("glyburide-metformin_Steady", value=0.0, format="%.2f")
change_No           = st.number_input("change_No",           value=0.0, format="%.2f")
diabetesMed_Yes     = st.number_input("diabetesMed_Yes",     value=0.0, format="%.2f")

# ── Botón y llamada a la API ─────────────────────────────────────────────────
if st.button("Ejecutar inferencia"):
    payload = {
        "admission_type_id": admission_type_id,
        "discharge_disposition_id": discharge_disposition_id,
        "admission_source_id": admission_source_id,
        "time_in_hospital": time_in_hospital,
        "num_lab_procedures": num_lab_procedures,
        "num_procedures": num_procedures,
        "num_medications": num_medications,
        "number_outpatient": number_outpatient,
        "number_emergency": number_emergency,
        "number_inpatient": number_inpatient,
        "number_diagnoses": number_diagnoses,
        "race_Asian": race_Asian,
        "race_Caucasian": race_Caucasian,
        "race_Other": race_Other,
        "age_[10-20)": age_10_20,
        "age_[20-30)": age_20_30,
        "age_[40-50)": age_40_50,
        "age_[50-60)": age_50_60,
        "age_[70-80)": age_70_80,
        "age_[80-90)": age_80_90,
        "age_[90-100)": age_90_100,
        "A1Cresult_>8": A1Cresult_gt_8,
        "A1Cresult_Norm": A1Cresult_Norm,
        "metformin_No": metformin_No,
        "metformin_Steady": metformin_Steady,
        "metformin_Up": metformin_Up,
        "repaglinide_No": repaglinide_No,
        "repaglinide_Steady": repaglinide_Steady,
        "chlorpropamide_No": chlorpropamide_No,
        "chlorpropamide_Steady": chlorpropamide_Steady,
        "glimepiride_No": glimepiride_No,
        "glimepiride_Steady": glimepiride_Steady,
        "glimepiride_Up": glimepiride_Up,
        "glipizide_No": glipizide_No,
        "glipizide_Steady": glipizide_Steady,
        "glipizide_Up": glipizide_Up,
        "glyburide_No": glyburide_No,
        "glyburide_Steady": glyburide_Steady,
        "tolbutamide_Steady": tolbutamide_Steady,
        "pioglitazone_Up": pioglitazone_Up,
        "rosiglitazone_No": rosiglitazone_No,
        "rosiglitazone_Steady": rosiglitazone_Steady,
        "acarbose_Up": acarbose_Up,
        "tolazamide_Steady": tolazamide_Steady,
        "insulin_No": insulin_No,
        "insulin_Up": insulin_Up,
        "glyburide-metformin_No": glyburide_metformin_No,
        "glyburide-metformin_Steady": glyburide_metformin_Steady,
        "change_No": change_No,
        "diabetesMed_Yes": diabetesMed_Yes,
    }
    try:
        response = requests.post(f"{API_URL}/predict", json=payload)
        response.raise_for_status()
        result = response.json().get("prediction")
        st.success(f"Predicción: {result}")
    except Exception as e:
        st.error(f"Error al llamar a la API: {e}")
