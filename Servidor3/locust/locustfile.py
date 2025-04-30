from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def predict(self):
        # aquí ajusta la URL a tu API de inferencia
        self.client.post("/predict", json={
            "feature1": 5.1,
            "feature2": 3.5,
            # …
        })
