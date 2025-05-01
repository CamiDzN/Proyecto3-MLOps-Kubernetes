# Servicios en Servidor1

Este README describe en detalle cómo están organizados y desplegados los servicios en **Servidor1** dentro del proyecto `PROYECTO3-MLOPS-KUBERNETES`.

---

## Distribución de archivos

```text
PROYECTO3-MLOPS-KUBERNETES/
├── Servidor1/
│   ├── airflow/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── dags/
│   │   ├── preprocess_diabetes_data.py
│   │   └── training_models_diabetes_data.py
│   ├── jupyterlab-Image/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── kubernetes/
│   │   ├── deployments/
│   │   │   ├── jupyter-deployment.yaml
│   │   │   ├── jupyter-pvc.yaml
│   │   │   ├── mysql-deployment.yaml
│   │   │   ├── mysql-init-configmap.yaml
│   │   │   └── mysql-pvc.yaml
│   │   ├── services/
│   │   │   ├── jupyter-service.yaml
│   │   │   └── mysql-service.yaml
│   │   └── volumes/    # (opcional para definir PV manuales)
│   ├── logs/           # Carpeta local para logs de Airflow
│   ├── plugins/        # Plugins personalizados de Airflow
│   ├── docker-compose.yaml
│   └── README.md       # Este archivo
└── ... (otros componentes del proyecto)
```

---

## 1. Airflow (Docker Compose)

**Ruta:** `Servidor1/airflow/`

### Contenido

- **Dockerfile**: Define imagen de Airflow con dependencias de Python.
- **requirements.txt**: Paquetes adicionales para el scheduler/worker.
- **docker-compose.yaml** (en nivel superior `Servidor1/`): Definición de servicios:
  - `airflow-webserver`, `airflow-scheduler`, `airflow-worker`, `airflow-triggerer`
  - `airflow-init`, `postgres`, `redis`, `flower`
- Carpetas montadas:
  - `./dags` → `/opt/airflow/dags`
  - `./logs` → `/opt/airflow/logs`
  - `./plugins` → `/opt/airflow/plugins`
  - Volumen `models_volume` para modelos de ML

### Variables de entorno clave (definidas en `docker-compose.yaml`)

A continuación se detallan las variables más relevantes para la conexión de Airflow con los servicios externos:

```bash
# Ejecutor de tareas
AIRFLOW__CORE__EXECUTOR=CeleryExecutor

# Metadatos de Airflow en PostgreSQL local (Docker Compose)
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow

# Broker y backend de Celery (Redis local)
AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0
AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow

# Conexión a MySQL RawData en MicroK8s (máquina local)
#   - Servicio MySQL tipo NodePort expuesto en el puerto 30306 del nodo
AIRFLOW_CONN_MYSQL_DEFAULT=mysql://model_user:model_password@10.43.101.172:30306/RawData

# Conexión a MySQL CleanData en MicroK8s (máquina local)
#   - Servicio MySQL tipo NodePort expuesto en el puerto 30306 del nodo
AIRFLOW_CONN_MYSQL_CLEAN=mysql+pymysql://model_user:model_password@10.43.101.172:30306/CleanData

# URI de tracking de MLflow en Kubernetes externo
#   - Cluster externo accesible en la IP 10.43.101.196, NodePort 30003
AIRFLOW_VAR_MLFLOW_TRACKING_URI=http://10.43.101.196:30003

# Credenciales para MinIO en Kubernetes externo
#   - Cluster externo accesible en la IP 10.43.101.196, NodePort 30001
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=supersecret
MLFLOW_S3_ENDPOINT_URL=http://10.43.101.196:30001
```

### Arranque y gestión

```bash
# Posicionarse en Servidor1
cd Servidor1

# Inicializar metadatos y crear usuario
docker compose up airflow-init

# Levantar todos los servicios en background
docker compose up -d

# Para detener y recrear (no afecta pods de MicroK8s)
docker compose down
# (Opcional)
docker system prune -f && docker volume prune -f
docker compose up -d
```

> **Nota:** Al cambiar variables de entorno (p.ej. puertos MLflow), volver a ejecutar `docker compose down && docker compose up -d` para reaplicar.

---

## 2. PostgreSQL para Airflow (Docker Compose)

- Servicio **postgres** en `docker-compose.yaml`.
- Imagen: `postgres:13`, puerto `5432:5432`.
- Volumen `postgres-db-volume:/var/lib/postgresql/data`.
- Healthcheck con `pg_isready -U airflow`.

---

## 3. MySQL (RawData & CleanData) en MicroK8s

**Ruta:** `Servidor1/kubernetes/deployments` y `Servidor1/kubernetes/services`

### Despliegue

1. **ConfigMap** `mysql-init-configmap.yaml` → crea automáticamente las bases de datos *CleanData* y *RawData*, define permisos de usuario y ejecuta la inicialización. Ejemplo de contenido:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-init-scripts
data:
  create-databases.sql: |
    CREATE DATABASE IF NOT EXISTS CleanData;
    CREATE DATABASE IF NOT EXISTS RawData;
    GRANT ALL PRIVILEGES ON CleanData.* TO 'model_user'@'%';
    GRANT ALL PRIVILEGES ON RawData.* TO 'model_user'@'%';
    FLUSH PRIVILEGES;
```
2. **PersistentVolumeClaim** `mysql-pvc.yaml` → hostPath de 5 Gi.
3. **Deployment** `mysql-deployment.yaml` → contenedor `mysql:8.0`, usuario `model_user`.
4. **Service** `mysql-service.yaml` → `NodePort` 30306 → 3306 interno.

```bash
microk8s kubectl apply -f kubernetes/deployments/mysql-init-configmap.yaml
microk8s kubectl apply -f kubernetes/deployments/mysql-pvc.yaml
microk8s kubectl apply -f kubernetes/deployments/mysql-deployment.yaml
microk8s kubectl apply -f kubernetes/services/mysql-service.yaml
```

### Verificación

```bash
microk8s kubectl get pods,svc,pvc
mysql -h 127.0.0.1 -P 30306 -u model_user -pmodel_password
SHOW DATABASES;
```

---

## 4. JupyterLab en MicroK8s

**Ruta:** `Servidor1/kubernetes/deployments` y `Servidor1/kubernetes/services`

### 4.1. Creación de la imagen personalizada

En `Servidor1/jupyterlab-Image/`, se usa como base la imagen oficial de Jupyter Notebook e instalamos herramientas de sistema y Python necesarias:

```dockerfile
FROM jupyter/base-notebook:latest

USER root

# Librerías del sistema para conectar con MySQL
RUN apt-get update && apt-get install -y \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

# Copiamos y instalamos dependencias Python
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

EXPOSE 8888

# Arranca JupyterLab sin token
CMD ["start-notebook.sh", "--NotebookApp.token='' "]
```

> **Nota:** Los paquetes `mlflow` y `boto3` son necesarios para registrar experimentos y artefactos en el servidor MLflow (almacenamiento en MinIO).

### 4.2. requirements.txt

En `Servidor1/jupyterlab-Image/requirements.txt`:

```text
pandas
numpy
sqlalchemy
pymysql
requests
mlflow       # Necesario para tracking de experimentos en MLflow
scikit-learn
boto3        # Cliente S3 para guardar artefactos en MinIO
``` 

### 4.3. Build y Push al repositorio Docker Hub
```bash
# 1. Construir imagen localmente
docker build -t camidzn/mlops:jupyter-v1 jupyterlab-Image/

# 2. Login a Docker Hub
docker login -u <usuario>

# 3. Tag & Push al repositorio remoto
docker tag camidzn/mlops:jupyter-v1 camidzn/mlops:jupyter-v1
docker push camidzn/mlops:jupyter-v1

# 4. Confirmar en Docker Hub: la imagen "jupyter-v1" debe aparecer en la lista de tags.
```

### 4.4. Uso en el manifiesto de Kubernetes
En `kubernetes/deployments/jupyter-deployment.yaml`, reemplazar la sección de imagen por:
```yaml
spec:
  containers:
  - name: jupyterlab
    image: camidzn/mlops:jupyter-v1      # Imagen con librerías preinstaladas
    imagePullPolicy: Always
    ports:
    - containerPort: 8888
    volumeMounts:
    - name: data
      mountPath: /home/jovyan
```

### 4.5. Despliegue en MicroK8s
```bash
microk8s kubectl apply -f kubernetes/deployments/jupyter-pvc.yaml
microk8s kubectl apply -f kubernetes/deployments/jupyter-deployment.yaml
microk8s kubectl apply -f kubernetes/services/jupyter-service.yaml
```

### 4.6. Validación de despliegue
```bash
microk8s kubectl get pods
microk8s kubectl get svc
# Acceder via navegador:
# http://<IP-nodo>:<NodePort>  (token impreso en logs del pod o configurado en manifest)
```

## 5. Conexiones y Flujo de Datos Conexiones y Flujo de Datos

- **Airflow** orquesta DAGs que:
  - leen de **RawData** (MySQL en K8s)
  - escriben en **CleanData** (MySQL en K8s)
  - registran experimentos en **MLflow** (externo)
  - usan **MinIO** para artefactos
- **JupyterLab** permite exploración y notebooks que:
  - leen/escriben en MySQL
  - reportan a MLflow

> Los componentes de MicroK8s (MySQL, Jupyter) se gestionan con `microk8s kubectl`, no con `docker ps`.

**Fin del README**

