# Servidor3/locust/locustfile.py

from locust import HttpUser, task, between

class ApiUser(HttpUser):
    # No definas aquí `host`, lo pondrás desde la UI
    wait_time = between(1, 3)

    @task(5)
    def predict(self):
        payload = {
            "admission_type_id": 2.0,
            "discharge_disposition_id": 1.0,
            "admission_source_id": 7.0,
            "time_in_hospital": 3.0,
            "num_lab_procedures": 40.0,
            "num_procedures": 1.0,
            "num_medications": 13.0,
            "number_outpatient": 0.0,
            "number_emergency": 0.0,
            "number_inpatient": 0.0,
            "number_diagnoses": 9.0,
            "race_Asian": 0.0,
            "race_Caucasian": 1.0,
            "race_Other": 0.0,
            "age_[10-20)": 0.0,
            "age_[20-30)": 0.0,
            "age_[40-50)": 0.0,
            "age_[50-60)": 1.0,
            "age_[70-80)": 0.0,
            "age_[80-90)": 0.0,
            "age_[90-100)": 0.0,
            "A1Cresult_>8": 0.0,
            "A1Cresult_Norm": 1.0,
            "metformin_No": 0.0,
            "metformin_Steady": 1.0,
            "metformin_Up": 0.0,
            "repaglinide_No": 1.0,
            "repaglinide_Steady": 0.0,
            "chlorpropamide_No": 1.0,
            "chlorpropamide_Steady": 0.0,
            "glimepiride_No": 1.0,
            "glimepiride_Steady": 0.0,
            "glimepiride_Up": 0.0,
            "glipizide_No": 1.0,
            "glipizide_Steady": 0.0,
            "glipizide_Up": 0.0,
            "glyburide_No": 1.0,
            "glyburide_Steady": 0.0,
            "tolbutamide_Steady": 0.0,
            "pioglitazone_Up": 0.0,
            "rosiglitazone_No": 1.0,
            "rosiglitazone_Steady": 0.0,
            "acarbose_Up": 0.0,
            "tolazamide_Steady": 0.0,
            "insulin_No": 0.0,
            "insulin_Up": 1.0,
            "glyburide-metformin_No": 1.0,
            "glyburide-metformin_Steady": 0.0,
            "change_No": 1.0,
            "diabetesMed_Yes": 1.0
        }
        # Como `host` lo pasarás en la UI,
        # aquí las rutas son relativas:
        self.client.post("/predict", json=payload)
