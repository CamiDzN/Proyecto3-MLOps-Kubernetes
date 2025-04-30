FROM ghcr.io/mlflow/mlflow:latest

# Instala pymysql, boto3 y cryptography
RUN pip install pymysql boto3 cryptography
