# 🧠 Descripción General del Proyecto

Este proyecto implementa una solución completa de MLOps distribuida en tres servidores, diseñada para gestionar todo el ciclo de vida de un modelo de machine learning que predice la probabilidad de readmisión hospitalaria de pacientes con diabetes en un periodo de 30 días.

La arquitectura del proyecto está basada en contenedores Docker orquestados con Kubernetes (MicroK8s) y está organizada en tres entornos funcionales independientes, desplegados en máquinas virtuales diferentes:

- **Servidor 1**: Encargado del preprocesamiento automático de datos con Apache Airflow.
- **Servidor 2**: Responsable del registro de experimentos y gestión de artefactos con MLflow y MinIO.
- **Servidor 3**: Despliega el modelo en producción mediante una API con FastAPI, integra monitoreo con Prometheus & Grafana, pruebas de carga con Locust y una interfaz de usuario con Streamlit.

Este enfoque modular permite escalar y mantener cada componente de forma independiente, emulando un entorno real de producción distribuido.

> 💡 El objetivo principal es optimizar la gestión hospitalaria mediante un sistema predictivo que permite anticipar la readmisión de pacientes, mejorando así la eficiencia de los recursos médicos disponibles.

---

## 🗂️ Distribución del Proyecto por Servidores

Este proyecto fue desarrollado colaborativamente y distribuido en tres máquinas virtuales, cada una encargada de un componente clave del flujo de trabajo MLOps. Cada servidor tiene su propio `README.md` con detalles técnicos y operativos específicos:

| Servidor | Rol Principal                                   | Enlace al Detalle |
|----------|--------------------------------------------------|-------------------|
| 🟦 Servidor 1 | Preprocesamiento de datos con Airflow           | [Ver README Servidor 1](./Servidor1/README.md) |
| 🟩 Servidor 2 | Seguimiento de experimentos con MLflow y MinIO  | [Ver README Servidor 2](./Servidor2/README.md) |
| 🟥 Servidor 3 | Despliegue, monitoreo y pruebas de inferencia   | [Ver README Servidor 3](./Servidor3/README.md) |

Cada una de estas secciones incluye:
- Los contenedores desplegados.
- Los DAGs y notebooks asociados.
- Instrucciones de uso y pruebas.

> 📌 **Nota:** Todos los servidores están conectados en red local y comparten el acceso a la base de datos y el almacenamiento distribuido configurado para simular un entorno de producción real.

---

---

## 🧱 Arquitectura General del Proyecto

El proyecto está distribuido en **tres servidores (máquinas virtuales)** que trabajan de manera coordinada para implementar un pipeline completo de MLOps. Cada servidor aloja componentes específicos de la arquitectura, asegurando modularidad, escalabilidad y claridad en la implementación.

A continuación se presenta el diagrama de la arquitectura general:

![Arquitectura del Proyecto](![image](https://github.com/user-attachments/assets/ab94263f-fc2e-488d-b24f-562a5c87e984)) 

### 🔹 Servidor 1 – Preprocesamiento y Almacenamiento de Datos
- **Airflow**: Orquestación de pipelines de preprocesamiento y entrenamiento.
- **Base de Datos MySQL**: Almacena datos en dos capas:
  - `RawData`: Datos crudos separados en train, validation y test.
  - `CleanData`: Datos preprocesados listos para entrenamiento.
- **JupyterLab**: Desarrollo exploratorio y carga de datos desde notebooks.
- **DAGs**:
  - `preprocess_incremental`: Preprocesamiento automático.
  - `train_and_register`: Entrenamiento y selección del mejor modelo.

### 🔸 Servidor 2 – Seguimiento de Experimentos
- **MLflow Tracking Server**: Registro de métricas, parámetros y artefactos.
- **MinIO**: Almacenamiento compatible con S3 para guardar artefactos de modelos.
- **MySQL Metadata**: Almacena la metadata generada por MLflow.
- Imagen personalizada de MLflow desplegada con dependencias para conectividad segura.

### 🔺 Servidor 3 – Despliegue, Observabilidad y Experiencia de Usuario
- **FastAPI**: API de inferencia conectada al modelo en producción desde MLflow.
- **Streamlit**: Interfaz gráfica para realizar predicciones desde la web.
- **Prometheus + Grafana**: Monitoreo del comportamiento de la API:
  - Latencia, uso de memoria, conteo de inferencias.
- **Locust**: Pruebas de carga para validar escalabilidad de la API.

> 🧩 Cada componente se desplegó como contenedor independiente y se conectó a través de redes virtuales internas. Las IPs asignadas por el clúster a cada servidor aseguran el enrutamiento correcto entre servicios.

---
##🛠️ Tecnologías y Componentes Utilizados

El proyecto se compone de varios microservicios, cada uno desplegado en contenedores independientes, comunicados entre sí dentro de un entorno orquestado con Kubernetes:

MLflow: Gestión de experimentos y modelos. Conectado a MinIO (artefactos) y MySQL (metadatos).

Airflow: Orquestación de pipelines de preprocesamiento y entrenamiento.

MinIO: Almacenamiento local de artefactos, compatible con S3.

MySQL: Bases de datos para RawData, CleanData y metadata de MLflow y Airflow.

JupyterLab: Ejecución de notebooks para carga, validación y experimentación.

FastAPI: API de inferencia del modelo en producción.

Streamlit: Interfaz gráfica para predicciones del modelo.

Prometheus + Grafana: Observabilidad y monitoreo de métricas de inferencia.

Locust: Pruebas de carga para evaluar el rendimiento de la API.

## 🚀 ¿Cómo ejecutar el proyecto completo?
✅ Asegúrate de que los 3 servidores estén activos, conectados en la misma red y con Kubernetes (MicroK8s) habilitado.

🔌 Paso a paso por servidor
🖥️ Servidor 1 — Preprocesamiento y orquestación

Despliega los servicios con:

```bash
kubectl apply -f Servidor1/kubernetes/
```
Accede a Airflow y ejecuta el DAG preprocess_incremental.

🗃️ Servidor 2 — Almacenamiento y MLflow

Construye y publica la imagen personalizada de MLflow:

```bash
docker build -t custom-mlflow:latest .
docker tag custom-mlflow:latest localhost:32000/custom-mlflow:latest
docker push localhost:32000/custom-mlflow:latest
```
Despliega los servicios:

```bash
kubectl apply -f Servidor2/kubernetes/
```
Ejecuta el job para crear el bucket en MinIO:

```bash
kubectl apply -f Servidor2/kubernetes/create-minio-bucket.yaml
```
📡 Servidor 3 — Inferencia, monitoreo y UI


Despliega los servicios con:

```bash
kubectl apply -f Servidor3/kubernetes/
```
Accede a la API o interfaz de Streamlit para hacer predicciones.

Verifica métricas en Prometheus y visualízalas en Grafana.

Ejecuta pruebas de carga con Locust.

📁 Estructura del Proyecto
El repositorio se organiza en tres carpetas principales, cada una correspondiente a uno de los servidores utilizados en el despliegue distribuido del sistema MLOps. A continuación, se detalla el contenido de cada uno:

🟢 Servidor1/
Responsable del procesamiento de datos y entrenamiento de modelos.

```bash
Servidor1/
├── airflow/
│   ├── Dockerfile
│   └── requirements.txt
├── dags/
│   ├── preprocess_diabetes_data.py
│   └── training_models_diabetes_data.py
├── jupyterlab-Image/
│   ├── Dockerfile
│   └── requirements.txt
├── kubernetes/
│   ├── deployments/
│   ├── services/
│   ├── jupyter-deployment.yaml
│   └── mysql-deployment.yaml
├── Cargar RawData.ipynb
├── Verificacion_Preprocesamiento.ipynb
├── Experimentos.ipynb
└── docker-compose.yaml
```

🔵 Servidor2/
Encargado del almacenamiento de artefactos y seguimiento de experimentos.

```bash
Servidor2/
├── kubernetes/
│   ├── create-minio-bucket.yaml
│   ├── minio-deployment.yaml
│   ├── mlflow-deployment.yaml
│   ├── mysql-deployment.yaml
│   └── servicios.yaml
├── Dockerfile
└── README.md
```
🟣 Servidor3/
Contiene la API de inferencia, observabilidad y la interfaz gráfica.

```bash
Servidor3/
├── api/
│   ├── app/
│   └── k8s/
│       └── Dockerfile
├── locust/
│   ├── locustfile.py
│   └── k8s/
├── observability/
│   ├── k8s/
│   │   ├── grafana-datasources.yaml
│   │   ├── observability.yaml
│   └── prometheus.yml
├── public/
│   ├── Api.png
│   ├── Grafana.png
│   ├── Prometheus.png
│   ├── Locust.png
│   └── Streamlit.png
├── streamlit/
│   ├── app/
│   └── k8s/
└── README.md
```

🔄 Flujo de Trabajo del Proyecto
Este proyecto sigue un flujo de procesamiento y operación distribuido en tres servidores, desde la carga inicial de datos hasta la entrega de predicciones mediante una API y una interfaz gráfica. A continuación, se detalla el pipeline completo:

1. 📥 Carga y partición de datos (Servidor1)
Se ejecuta el notebook Cargar Raw Data.ipynb, que:

Opcionalmente limpia las bases de datos RawData y CleanData.

Descarga el dataset en CSV.

Divide los datos en conjuntos train, validation y test.

Inserta los datos en tablas independientes en la base de datos RawData.

La tabla train carga solo 15.000 registros por lote, simulando una carga incremental.

2. 🧹 Preprocesamiento de datos (Servidor1)
El DAG preprocess_incremental en Airflow contiene 4 tareas:

Carga los datos desde la base RawData.

Elimina características nulas y aplica one-hot encoding a variables categóricas.

Define la variable objetivo (readmisión en 30 días) y selecciona las 50 mejores características.

Guarda los nuevos conjuntos train, val y test en CleanData.

3. ✅ Verificación (Servidor1)
Se ejecuta el notebook Verificacion_Preprocesamiento.ipynb para validar la correcta transformación de los datos.

4. 🧪 Experimentación (Servidor1 + Servidor2)
El notebook Experimentos.ipynb entrena varios modelos y registra:

Métricas.

Artefactos.

Parámetros.

En el experimento diabetes_readmission_experiments de MLflow.

5. 🏁 Entrenamiento y Registro (Servidor1 + Servidor2)
El DAG train_and_register realiza dos tareas:

Entrena modelos usando CleanData y guarda los resultados en MLflow (diabetes_readmission_training).

Promueve el mejor modelo automáticamente a producción (best_diabetes_readmission_model).

6. ⚙️ Inferencia y API (Servidor3)
La API implementada en FastAPI:

Consulta el modelo en producción desde MLflow y MinIO.

Expone endpoints para predicción e inferencia.

7. 📊 Observabilidad (Servidor3)
Se activa el endpoint /metrics en la API.

Prometheus realiza scraping de:

Latencia de inferencias.

Uso de memoria.

Cantidad de inferencias.

Grafana visualiza las métricas para evaluar el rendimiento del sistema.

8. 🧪 Pruebas de carga (Servidor3)
Locust realiza pruebas de estrés sobre la API.

Se determina la capacidad máxima de usuarios concurrentes soportada por el sistema.

9. 🖥️ Interfaz gráfica (Servidor3)
Streamlit permite al usuario ingresar datos y obtener una predicción personalizada sobre el riesgo de readmisión del paciente.
