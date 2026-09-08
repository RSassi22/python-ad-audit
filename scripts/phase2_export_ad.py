# Phase 2 — Première génération de données AD fictives "en dur" dans un
# script, sans encore passer par core/. C'est la version pédagogique de ce
# que fait ensuite core/sources.py::SourceAD.generer() (mêmes idées, mais
# paramètres codés ici plutôt que centralisés dans une Config réutilisable).
from faker import Faker
import pandas as pd
import random


# Faker génère des données réalistes (noms, dates, etc.) automatiquement
fake = Faker()

# Liste fixe de départements et groupes AD réalistes pour un contexte bancaire
departements = ["Finance", "IT", "Marketing", "RH", "Sécurité", "Juridique", "Opérations"]
groupes_ad = ["Accès_Standard", "Admins_Serveurs", "Accès_Comptabilité", 
              "Admins_Domaine", "Accès_RH", "Accès_Serveurs_Bancaires"]

utilisateurs = []  # liste vide qu'on va remplir

for i in range(200):
    utilisateur = {
        "id": i + 1,
        "nom": fake.name(),
        "departement": random.choice(departements),
        "groupe_ad": random.choice(groupes_ad),
        "derniere_connexion": fake.date_between(start_date="-180d", end_date="today")
    }
    utilisateurs.append(utilisateur)

# On transforme la liste de dictionnaires en DataFrame Pandas
df = pd.DataFrame(utilisateurs)

# Aperçu dans le terminal avant export
print(df.head())        # affiche les 5 premières lignes
print(f"\nNombre total d'utilisateurs générés : {len(df)}")

# Export en CSV
df.to_csv("data/raw/export_ad_fictif.csv", index=False)
print("Fichier exporté : data/raw/export_ad_fictif.csv")
