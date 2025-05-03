# ----------------------------------------------------------------
# app/main.py
# ----------------------------------------------------------------
from fastapi import FastAPI,Response
from pydantic import BaseModel, Field
import mlflow.pyfunc
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Métricas para Prometheus
PREDICTIONS = Counter(
    "inference_requests_total", 
    "Total de peticiones de inferencia"
)
LATENCIES = Histogram(
    "inference_request_latency_seconds",
    "Latencia de las peticiones de inferencia (segundos)"
)

# Nombre del modelo en Registry
MODEL_NAME = "best_diabetes_readmission_model"

app = FastAPI()

# Esquema de entrada esperado
class RequestData(BaseModel):
    admission_type_id: float
    discharge_disposition_id: float
    admission_source_id: float
    time_in_hospital: float
    num_lab_procedures: float
    num_procedures: float
    num_medications: float
    number_outpatient: float
    number_emergency: float
    number_inpatient: float
    number_diagnoses: float
    race_Asian: float
    race_Caucasian: float
    race_Other: float

    # Aquí renombramos los campos con corchetes
    age_10_20: float = Field(..., alias="age_[10-20)")
    age_20_30: float = Field(..., alias="age_[20-30)")
    age_40_50: float = Field(..., alias="age_[40-50)")
    age_50_60: float = Field(..., alias="age_[50-60)")
    age_70_80: float = Field(..., alias="age_[70-80)")
    age_80_90: float = Field(..., alias="age_[80-90)")
    age_90_100: float = Field(..., alias="age_[90-100)")

    A1Cresult_gt8: float = Field(..., alias="A1Cresult_>8")
    A1Cresult_Norm: float

    metformin_No: float
    metformin_Steady: float
    metformin_Up: float
    repaglinide_No: float
    repaglinide_Steady: float
    chlorpropamide_No: float
    chlorpropamide_Steady: float
    glimepiride_No: float
    glimepiride_Steady: float
    glimepiride_Up: float
    glipizide_No: float
    glipizide_Steady: float
    glipizide_Up: float
    glyburide_No: float
    glyburide_Steady: float
    tolbutamide_Steady: float
    pioglitazone_Up: float
    rosiglitazone_No: float
    rosiglitazone_Steady: float
    acarbose_Up: float
    tolazamide_Steady: float
    insulin_No: float
    insulin_Up: float
    glyburide_metformin_No: float = Field(..., alias="glyburide-metformin_No")
    glyburide_metformin_Steady: float = Field(..., alias="glyburide-metformin_Steady")
    change_No: float
    diabetesMed_Yes: float

    class Config:
        allow_population_by_field_name = True
# Cargamos el modelo en producción una sola vez
model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/Production")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(payload: RequestData):
    PREDICTIONS.inc()
    #data = payload.dict()
    data = payload.dict(by_alias=True)
    
    with LATENCIES.time():
        # inferencia
        result = model.predict([data])[0]
    
    return {"prediction": int(result)}

@app.get("/metrics")
def metrics():
    # endpoint para que Prometheus le pegue scrape
    #return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

    
