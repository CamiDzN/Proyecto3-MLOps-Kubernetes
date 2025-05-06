# Sitúate en la carpeta de tu proyecto Locust
locust/

# Asegura el registry interno activo
sudo microk8s enable registry
sudo microk8s status --wait-ready

# Construye y sube la imagen de Locust
docker build -t localhost:32000/locust:latest .
docker push localhost:32000/locust:latest

# Crea el namespace y despliega
sudo microk8s kubectl create namespace loadtest
sudo microk8s kubectl -n loadtest apply -f k8s/locust-k8s.yaml

# Verifica que master y workers estén Running
sudo microk8s kubectl -n loadtest get pods

# Confirma el Service NodePort en el puerto 30009
sudo microk8s kubectl -n loadtest get svc locust-master-ui

# Revisar en navegador que se encuentre desplegado correctamente
Locust - http://10.43.101.173:30009/
