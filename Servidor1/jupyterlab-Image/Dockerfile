FROM jupyter/base-notebook:latest

USER root

RUN apt-get update && apt-get install -y \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

EXPOSE 8888

CMD ["start-notebook.sh", "--NotebookApp.token=''"]