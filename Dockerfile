FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Désactiver uv pour Streamlit Cloud
ENV STREAMLIT_DISABLE_UV=1

WORKDIR /app

# Installer d'abord setuptools (pour éviter l'erreur pkg_resources)
RUN pip install --no-cache-dir setuptools wheel

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]