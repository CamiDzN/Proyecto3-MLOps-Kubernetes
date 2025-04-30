# Despliegue de Locust en MicroK8s

Este documento explica cómo reconstruir y redeplegar **Locust** desde cero en tu clúster de MicroK8s, usando un Service de tipo **NodePort** para que cualquiera en la red pueda acceder vía IP:puerto.

---

## Paso 1: Situarse en el proyecto

```bash
cd ~/Practica/locust

```

# Paso 2: Habilitar el registry interno
sudo microk8s enable registry
sudo microk8s status --wait-ready

# Paso 3: Reconstruir y subir la imagen
1. Construir la imagen

docker build -t localhost:32000/locust:latest .

2. Subir al registry de MicroK8s

docker push localhost:32000/locust:latest

# Paso 4: Desplegar de nuevo en Kubernetes
1. Crear el namespace

sudo microk8s kubectl create namespace loadtest

2. Aplicar el Deployment y Service (ClusterIP + Workers)

sudo microk8s kubectl -n loadtest apply -f k8s/locust-k8s.yaml

3. Aplicar el Service NodePort

sudo microk8s kubectl -n loadtest apply -f k8s/locust-master-nodeport.yaml

# Paso 5: Verificar el despliegue

sudo microk8s kubectl -n loadtest get pods,svc

Deberías ver:

* Pods
    * locust-master (1/1 Running)
    * locust-worker (3/3 Running)

* Service NodePort

NAME                     TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)
locust-master-nodeport   NodePort   10.xxx.xxx.xxx <none>        8089:30009/TCP

# Paso 6: Acceder a la UI de Locust

Abre en tu navegador:

http://10.43.101.173:30009/

Allí verás la interfaz de Locust, lista para iniciar tu test de carga.