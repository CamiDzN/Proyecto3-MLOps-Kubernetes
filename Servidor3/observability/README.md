Despliegue de Observabilidad (Prometheus + Grafana) en MicroK8s

1) Despliegue paso a paso:
cd ~/Practica/observability
sudo microk8s enable registry
sudo microk8s kubectl apply -f k8s/observability.yaml
sudo microk8s kubectl -n observability get pods,svc

2) Acceso a UIs:
http://<IP_VM>:30090/  # Prometheus
http://<IP_VM>:30030/  # Grafana

3) Configurar Grafana:
- Login admin/admin
- Connections → Data sources → Add Prometheus
- URL: http://prometheus-nodeport.observability.svc.cluster.local:9090
- Save & Test

4) Limpieza:
sudo microk8s kubectl delete namespace observability
