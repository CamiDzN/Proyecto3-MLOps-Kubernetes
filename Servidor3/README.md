# 🚀 Proyecto MLOps con Kubernetes

## 📋 Descripción General

Este proyecto implementa una arquitectura completa de MLOps utilizando Kubernetes para el despliegue de un modelo de predicción de readmisión de pacientes con diabetes. La arquitectura está compuesta por varios componentes interconectados que permiten la inferencia del modelo, pruebas de carga, monitorización y visualización de métricas en tiempo real.

El sistema está diseñado siguiendo las mejores prácticas de MLOps, permitiendo un despliegue escalable, monitorizable y mantenible de modelos de machine learning en un entorno de producción.

![Arquitectura del Proyecto](public\Locust.png)

## 🏗️ Arquitectura

El proyecto está desplegado a través de Kubernetes con los siguientes componentes:

### 🔹 API de Inferencia (FastAPI)

Servicio que expone el modelo de machine learning para realizar predicciones en tiempo real.

- **Tecnología**: FastAPI
- **Funcionalidad**: Realiza inferencia utilizando el mejor modelo clasificado en producción
- **Métricas**: Integración con Prometheus para monitorización
- **Endpoints**:
  - `/predict`: Realiza predicciones basadas en los datos de entrada
  - `/health`: Verifica el estado del servicio
  - `/metrics`: Expone métricas para Prometheus

**Características técnicas:**
- Carga automática del modelo desde MLflow Registry
- Validación de datos de entrada mediante Pydantic
- Instrumentación con métricas de Prometheus para monitorizar latencia y número de peticiones
- Optimización para alto rendimiento y baja latencia
- Manejo de errores robusto con respuestas HTTP apropiadas

**Ejemplo de uso:**
```json
// POST /predict
{
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
  "A1Cresult_Norm": 1.0
  // ... otros campos
}
```

### 🔹 Interfaz de Usuario (Streamlit)

Aplicación web que permite a los usuarios interactuar con el modelo de forma intuitiva.

- **Tecnología**: Streamlit
- **Funcionalidad**: Proporciona una interfaz gráfica para introducir datos y visualizar predicciones
- **Integración**: Se comunica con la API de FastAPI para realizar predicciones

**Características técnicas:**
- Interfaz de usuario intuitiva y responsive
- Formularios interactivos para introducir datos del paciente
- Visualización clara de resultados de predicción
- Validación de datos en el cliente
- Comunicación asíncrona con la API de inferencia
- Manejo de errores con mensajes informativos para el usuario

**Flujo de usuario:**
1. El usuario introduce los datos del paciente a través de formularios interactivos
2. La aplicación valida los datos introducidos
3. Se envía una petición a la API de inferencia
4. Se muestra el resultado de la predicción con una explicación clara
5. El usuario puede realizar nuevas predicciones o modificar los datos existentes

### 🔹 Pruebas de Carga (Locust)

Herramienta para realizar pruebas de rendimiento sobre la API de inferencia.

- **Tecnología**: Locust
- **Funcionalidad**: Simula múltiples usuarios concurrentes para evaluar el rendimiento y la escalabilidad
- **Arquitectura**: Implementación master-worker para distribuir la carga

**Características técnicas:**
- Arquitectura distribuida con un nodo master y múltiples workers
- Definición de comportamientos de usuario realistas mediante Python
- Simulación de patrones de tráfico variables
- Métricas detalladas de rendimiento (RPS, tiempos de respuesta, errores)
- Interfaz web para configurar y monitorizar pruebas
- Exportación de resultados para análisis posterior

**Escenarios de prueba implementados:**
- Prueba de carga constante: Mantiene un número fijo de usuarios concurrentes
- Prueba de escalado: Incrementa gradualmente el número de usuarios
- Prueba de estrés: Determina el punto de ruptura del sistema
- Prueba de resistencia: Mantiene carga durante períodos prolongados

**Métricas clave:**
- Tiempo de respuesta (mínimo, máximo, percentiles)
- Tasa de solicitudes por segundo (RPS)
- Tasa de errores
- Distribución de tiempos de respuesta

### 🔹 Observabilidad (Prometheus + Grafana)

Stack de monitorización para recolectar y visualizar métricas de rendimiento.

- **Prometheus**: Recolecta métricas de la API de inferencia
- **Grafana**: Visualiza las métricas recolectadas en dashboards personalizables

**Características de Prometheus:**
- Recolección de métricas mediante scraping HTTP
- Almacenamiento eficiente de series temporales
- Lenguaje de consulta potente (PromQL)
- Alertas configurables
- Integración con múltiples exporters

**Características de Grafana:**
- Dashboards personalizables y reutilizables
- Soporte para múltiples fuentes de datos
- Visualizaciones avanzadas (gráficos, tablas, heatmaps)
- Anotaciones y alertas
- Compartición y exportación de dashboards

**Métricas monitorizadas:**
- Latencia de las peticiones de inferencia
- Número total de predicciones
- Uso de recursos (CPU, memoria, red)
- Estado de los servicios
- Tasas de error

**Dashboard principal:**
- Panel de estado general del sistema
- Gráficos de latencia (p50, p95, p99)
- Contador de predicciones por resultado
- Uso de recursos por servicio
- Historial de errores

## 🛠️ Despliegue

### Requisitos Previos

- Kubernetes (MicroK8s)
- Docker
- Registro de imágenes local (puerto 32000)
- MLflow (para gestión del modelo)

### Pasos de Despliegue

#### 1. Crear Namespace

```bash
sudo microk8s kubectl create namespace loadtest
```

#### 2. API de Inferencia (FastAPI)

```bash
# Situarse en el directorio de la API
cd api

# Construir y subir la imagen
docker build -t localhost:32000/fastapi-service:latest .
docker push localhost:32000/fastapi-service:latest

# Desplegar en Kubernetes
sudo microk8s kubectl -n loadtest apply -f k8s/fastapi-deployment.yaml
```

#### 3. Interfaz de Usuario (Streamlit)

```bash
# Situarse en el directorio de Streamlit
cd streamlit

# Construir y subir la imagen
docker build -t localhost:32000/streamlit-ui:latest .
docker push localhost:32000/streamlit-ui:latest

# Desplegar en Kubernetes
sudo microk8s kubectl -n loadtest apply -f k8s/streamlit-deployment.yaml
```

#### 4. Pruebas de Carga (Locust)

```bash
# Situarse en el directorio de Locust
cd locust

# Construir y subir la imagen
docker build -t localhost:32000/locust:latest .
docker push localhost:32000/locust:latest

# Desplegar en Kubernetes
sudo microk8s kubectl -n loadtest apply -f k8s/locust-k8s.yaml
```

#### 5. Observabilidad (Prometheus + Grafana)

```bash
# Situarse en el directorio de observabilidad
cd observability/k8s

# Crear el namespace y desplegar
sudo microk8s kubectl apply -f observability.yaml
```

## 🔍 Verificación del Despliegue

Verificar que todos los servicios estén correctamente desplegados:

```bash
# Verificar pods
sudo microk8s kubectl -n loadtest get pods
sudo microk8s kubectl -n observability get pods

# Verificar servicios
sudo microk8s kubectl -n loadtest get svc
sudo microk8s kubectl -n observability get svc
```

## 🌐 Acceso a los Servicios

- **API de FastAPI**: http://[IP-DEL-NODO]:30080
  - Documentación interactiva: http://[IP-DEL-NODO]:30080/docs
  - Métricas: http://[IP-DEL-NODO]:30080/metrics

- **Interfaz Streamlit**: http://[IP-DEL-NODO]:30081
  - Interfaz principal para usuarios finales
  - No requiere conocimientos técnicos para su uso

- **Locust**: http://[IP-DEL-NODO]:30009
  - Interfaz de configuración de pruebas
  - Visualización de resultados en tiempo real
  - Exportación de informes

- **Prometheus**: http://[IP-DEL-NODO]:30090
  - Explorador de métricas
  - Configuración de alertas
  - Consultas PromQL

- **Grafana**: http://[IP-DEL-NODO]:30030
  - Credenciales por defecto: admin/admin
  - Dashboards preconfigurados
  - Personalización de visualizaciones

![Dashboard de Grafana](ruta-a-tu-imagen-de-dashboard.png)

## 📊 Modelo de Machine Learning

El modelo desplegado predice la readmisión de pacientes con diabetes basándose en diversos factores clínicos y demográficos.

### Características del Modelo

- **Tipo**: Clasificación binaria (readmisión: sí/no)
- **Algoritmo**: Gradient Boosting (XGBoost)
- **Métricas de evaluación**:
  - Precisión (Accuracy): 0.85
  - F1-Score: 0.83
  - AUC-ROC: 0.87
  - Recall: 0.81

### Variables de entrada

- **Datos demográficos**: Edad, raza
- **Datos de admisión**: Tipo de admisión, fuente, tiempo de hospitalización
- **Procedimientos médicos**: Número de procedimientos, pruebas de laboratorio
- **Medicamentos**: Metformina, repaglinida, glimepirida, etc.
- **Resultados de pruebas**: Niveles de A1C, etc.

### Gestión del Modelo

- **Registro**: MLflow para el versionado y seguimiento de experimentos
- **Despliegue**: Carga automática desde MLflow Registry
- **Monitorización**: Métricas de rendimiento en producción
- **Actualización**: Proceso automatizado para nuevas versiones

## 📝 Estructura del Proyecto

```
.
├── api/                    # Servicio de API con FastAPI
│   ├── app/                # Código de la aplicación
│   │   ├── main.py         # Punto de entrada de la API
│   │   └── requirements.txt # Dependencias
│   ├── Dockerfile          # Configuración para la imagen Docker
│   └── k8s/                # Manifiestos de Kubernetes
│       └── fastapi-deployment.yaml
├── streamlit/              # Interfaz de usuario con Streamlit
│   ├── app/                # Código de la aplicación
│   │   ├── main.py         # Punto de entrada de la UI
│   │   └── requirements.txt # Dependencias
│   ├── Dockerfile          # Configuración para la imagen Docker
│   └── k8s/                # Manifiestos de Kubernetes
│       └── streamlit-deployment.yaml
├── locust/                 # Pruebas de carga con Locust
│   ├── locustfile.py       # Configuración de pruebas
│   ├── Dockerfile          # Configuración para la imagen Docker
│   └── k8s/                # Manifiestos de Kubernetes
│       └── locust-k8s.yaml
└── observability/          # Monitorización con Prometheus y Grafana
    ├── prometheus.yml      # Configuración de Prometheus
    └── k8s/                # Manifiestos de Kubernetes
        ├── grafana-datasources.yaml
        └── observability.yaml
```

## 🔄 Flujo de Trabajo

1. **Preparación de datos**: Los datos del paciente se introducen a través de la interfaz de Streamlit o se envían directamente a la API.

2. **Procesamiento de la solicitud**: 
   - La interfaz de Streamlit valida los datos y los envía a la API de FastAPI.
   - La API valida nuevamente los datos utilizando Pydantic.

3. **Inferencia del modelo**:
   - La API carga el modelo desde MLflow Registry.
   - Se realiza la predicción utilizando los datos procesados.
   - Se registran métricas de rendimiento en Prometheus.

4. **Respuesta al usuario**:
   - El resultado de la predicción se devuelve a la interfaz de Streamlit.
   - Se presenta al usuario de forma clara y comprensible.

5. **Monitorización continua**:
   - Prometheus recolecta métricas de rendimiento de la API.
   - Grafana visualiza estas métricas en dashboards personalizados.
   - Se generan alertas en caso de anomalías.

6. **Pruebas de carga**:
   - Locust permite realizar pruebas de rendimiento programadas o bajo demanda.
   - Los resultados ayudan a optimizar la configuración y el escalado.

![Flujo de Trabajo](ruta-a-tu-imagen-de-flujo.png)

## 🔧 Mantenimiento y Escalabilidad

### Actualización del Modelo

1. Entrenar y registrar un nuevo modelo en MLflow
2. Actualizar la referencia en la configuración de la API
3. Reconstruir y desplegar la imagen de la API

### Escalado Horizontal

Kubernetes permite escalar los componentes según la demanda:

```bash
# Escalar la API a 3 réplicas
sudo microk8s kubectl -n loadtest scale deployment fastapi-service --replicas=3

# Escalar workers de Locust a 5
sudo microk8s kubectl -n loadtest scale deployment locust-worker --replicas=5
```

### Backup y Restauración

```bash
# Backup de configuraciones
sudo microk8s kubectl -n loadtest get all -o yaml > loadtest-backup.yaml
sudo microk8s kubectl -n observability get all -o yaml > observability-backup.yaml

# Restauración
sudo microk8s kubectl apply -f loadtest-backup.yaml
sudo microk8s kubectl apply -f observability-backup.yaml
```

## 👥 Contribuciones

Para contribuir al proyecto:

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit (`git commit -am 'Añadir nueva funcionalidad'`)
4. Sube los cambios a tu fork (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo [incluir tipo de licencia].

## 📞 Contacto

Para más información, contacta con [tu información de contacto].
