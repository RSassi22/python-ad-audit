# Image de base légère avec Python déjà installé
FROM python:3.11-slim

# Dossier de travail à l'intérieur du conteneur
WORKDIR /app

# On copie d'abord requirements.txt seul (optimisation : si le code change
# mais pas les dépendances, Docker réutilise le cache de cette étape)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie ensuite tout le reste du projet
COPY . .

# Port par défaut utilisé par Streamlit
EXPOSE 8501

# Commande lancée au démarrage du conteneur.
# Note : seul dashboard.py est lancé ici (donc uniquement l'onglet Audit AD
# + l'onglet Wallix, tous deux régénérés/lus à la volée). Les scripts
# scripts/phase9-13 (UEBA + data warehouse PostgreSQL) ne tournent pas
# automatiquement dans ce conteneur : ils s'exécutent à part, en local.
CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0"]