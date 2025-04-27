En el Servidor 3 se alojara la siguiente arquitectura:

Desplegado a través de Kubernetes:

-Contenedor de FastAPI para realizar la inferencia tomando el mejor modelo clasificado en producción.

-Contenedor de Locust para realizar las pruebas de carga sobre la API de inferencia.

-Contenedor de Prometheus para recolectar los eventos del contenedor de la API de inferencia.

-Contenedor de Grafana para graficar los eventos recolectados a través de Prometheus.
