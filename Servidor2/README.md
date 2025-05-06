# Despliegue de MLflow, MYSQL, y MinIO en Kubernetes

Este proyecto implementa una arquitectura completa para el seguimiento de experimentos con MLflow, usando MinIO como almacenamiento de artefactos y MySQL como base de datos para los metadatos, todo desplegado en un clúster local de Kubernetes (MicroK8s).

---

## 🧠 Descripción del Proyecto

Este proyecto implementa una solución de MLOps local utilizando Kubernetes y MicroK8s para desplegar una arquitectura que integra:

![image](https://github.com/user-attachments/assets/fda81945-ce60-4634-bbf3-3c04198d6335)

- 📦 **MLflow** como servidor de seguimiento de experimentos.
- ☁️ **MinIO** como sistema de almacenamiento de artefactos S3-compatible.
- 🗃️ **MySQL** como base de datos para almacenar el backend de MLflow.

La solución está diseñada para correr en entornos locales y facilitar el registro, almacenamiento y visualización de modelos de machine learning. Además, se ha configurado una automatización para la creación del bucket en MinIO y la base de datos en MySQL.

---

## 🏗️ Arquitectura del Sistema

La arquitectura se compone de los siguientes servicios, desplegados como Pods en Kubernetes:

### 🔴 MinIO
- Almacena los artefactos generados por MLflow (modelos, métricas, etc.).
- Expone dos puertos:
  - `9000`: API de S3.
  - `9001`: Consola web para gestión.

![image](https://github.com/user-attachments/assets/42fe5cc6-1233-4e9d-a09f-ee9fbd3a6612)

### 🔵 MySQL
- Actúa como backend para MLflow.
- Almacena metadatos de experimentos, ejecuciones, parámetros y métricas.

### 🐳 Imagen Personalizada de MLflow
Para adaptar MLflow a las necesidades del proyecto, se creó una imagen personalizada basada en ghcr.io/mlflow/mlflow:latest, incorporando las bibliotecas necesarias para la integración con MySQL y MinIO.

Dockerfile:
```bash
FROM ghcr.io/mlflow/mlflow:latest
RUN pip install pymysql boto3 cryptography
```
Construcción de la imagen:
```bash
docker build -t custom-mlflow:latest .
```

### 🟢 MLflow Tracking Server
- Servidor de experimentos accesible desde el navegador.
- Guarda información en MySQL y sube artefactos a MinIO.

![Imagen de WhatsApp 2025-05-01 a las 16 05 44_aa2c6cea](https://github.com/user-attachments/assets/9630cc9d-17a1-49d1-b321-9b37c160f99c)


### 🛠️ Job de Inicialización
- Un Job en Kubernetes crea automáticamente el bucket `mlflows3` en MinIO al iniciar el sistema.

> Todos los servicios están interconectados a través de una red interna de Kubernetes, y los servicios críticos como MLflow y MinIO están expuestos mediante **NodePort** para permitir el acceso desde otras máquinas en la red local.

---

## 🚀 Despliegue en Kubernetes

Sigue estos pasos para desplegar el sistema completo en un clúster con MicroK8s:

### 1. 🧱 Construcción y publicación de imagen de MLflow personalizada

```bash
docker build -t custom-mlflow:latest .
docker tag custom-mlflow:latest localhost:32000/custom-mlflow:latest
docker push localhost:32000/custom-mlflow:latest
```
### 2. 📦 Despliegue de servicios
📂 Base de datos (MySQL)
```bash
microk8s kubectl apply -f kubernetes/mysql-pvc.yaml
microk8s kubectl apply -f kubernetes/mysql-deployment.yaml
microk8s kubectl apply -f kubernetes/mysql-service.yaml
```
🗄️ Almacenamiento (MinIO)
```bash
microk8s kubectl apply -f kubernetes/minio-pvc.yaml
microk8s kubectl apply -f kubernetes/minio-deployment.yaml
microk8s kubectl apply -f kubernetes/minio-service.yaml
```
🔍 Seguimiento de Experimentos (MLflow)

```bash
microk8s kubectl apply -f kubernetes/mlflow-deployment.yaml
microk8s kubectl apply -f kubernetes/mlflow-service.yaml
```
3. 🪣 Crear bucket en MinIO
```bash
microk8s kubectl apply -f kubernetes/create-minio-bucket.yaml
```
