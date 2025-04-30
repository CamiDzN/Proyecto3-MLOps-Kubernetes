FROM python:3.9-slim
WORKDIR /app

# Instala dependencias
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY app/main.py .

EXPOSE 8501

# Lanza Streamlit en modo headless
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.headless=true"]
