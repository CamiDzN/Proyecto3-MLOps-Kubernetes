# Sitúate en la carpeta de observabilidad
/observability/k8s/

# Crea el namespace y despliega todo
sudo microk8s kubectl apply -f observability.yaml

# Verifica pods
sudo microk8s kubectl -n observability get pods

# Verifica servicios NodePort
sudo microk8s kubectl -n observability get svc

# Revisa que se encuentren correctamente desplegados
Prometheus - http://10.43.101.173:30090/
Grafana - http://10.43.101.173:30030/
