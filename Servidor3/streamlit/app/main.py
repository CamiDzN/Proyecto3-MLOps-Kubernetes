import streamlit as st
import requests

st.title("Interfaz de Inferencia")

# Input del usuario
age     = st.number_input("Edad", min_value=0, max_value=120, value=30)
gender  = st.selectbox("Género", ["Male", "Female"])
bmi     = st.number_input("BMI", min_value=0.0, value=25.0)
glucose = st.number_input("Glucosa", min_value=0.0, value=100.0)
insulin = st.number_input("Insulina", min_value=0.0, value=80.0)

if st.button("Predecir"):
    payload = {
        "age": age,
        "gender": gender,
        "bmi": bmi,
        "glucose": glucose,
        "insulin": insulin
    }
    # Ajusta la URL si tu FastAPI corre en otro namespace/servicio
    resp = requests.post("http://fastapi-service.default.svc.cluster.local:8000/predict", json=payload)
    if resp.status_code == 200:
        r = resp.json()
        st.success(f"Predicción: {r['prediction']}")
        st.info(f"Modelo usado: {r.get('model_version', 'desconocido')}")
    else:
        st.error("Error al llamar a la API")
