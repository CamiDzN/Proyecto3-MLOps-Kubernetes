# Usa la imagen oficial de Locust
FROM locustio/locust:2.16.0

# Copia tu script al contenedor
COPY locustfile.py /mnt/locust/locustfile.py

WORKDIR /mnt/locust

# Exponer puertos:
# - 8089: UI/master web
# - 5557: master <-> worker
# - 5558: worker también
EXPOSE 8089 5557 5558

# Comando por defecto; override en k8s con args
ENTRYPOINT ["locust"]
