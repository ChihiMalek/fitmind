FROM python:3.12-slim

# Éviter les warnings pip
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Créer un utilisateur non-root (recommandé)
RUN useradd -m -u 1000 user

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances en premier pour utiliser le cache Docker
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Changer le propriétaire des fichiers
RUN chown -R user:user /app
USER user

# Exposer le port Streamlit
EXPOSE 8501

# Lancer l'application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]