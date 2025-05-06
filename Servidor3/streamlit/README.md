# construye la imagen:
docker build -t localhost:32000/streamlit-ui:latest .

# Sube la imagen:
docker push localhost:32000/streamlit-ui:latest

# Despliega en k8s:
sudo microk8s kubectl -n loadtest apply -f k8s/streamlit-deployment.yaml

# Revisa que se encuentr correctamente desplegado

Streamlit http://10.43.101.173:30081/