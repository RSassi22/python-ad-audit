import pandas as pd
from datetime import datetime, timedelta

# On recharge le CSV généré en Phase 2
df = pd.read_csv("data/raw/export_ad_fictif.csv")

# La colonne "derniere_connexion" est lue comme du texte par défaut,
# il faut la convertir en vraie date pour pouvoir calculer des durées
df["derniere_connexion"] = pd.to_datetime(df["derniere_connexion"])

# --- Détection 1 : comptes inactifs depuis plus de 90 jours ---
seuil_inactivite = datetime.now() - timedelta(days=90)
comptes_inactifs = df[df["derniere_connexion"] < seuil_inactivite].copy()
comptes_inactifs["type_alerte"] = "Compte inactif > 90 jours"

print(f"Comptes inactifs détectés : {len(comptes_inactifs)}")

# --- Détection 2 : incohérences département / groupe AD ---
# Exemple de règle métier : certains groupes sensibles ne devraient
# être associés qu'à certains départements
groupes_sensibles = {
    "Admins_Domaine": ["IT", "Sécurité"],
    "Accès_Serveurs_Bancaires": ["IT", "Sécurité", "Opérations"],
    "Admins_Serveurs": ["IT"],
}

def est_incoherent(ligne):
    groupe = ligne["groupe_ad"]
    dept = ligne["departement"]
    if groupe in groupes_sensibles:
        return dept not in groupes_sensibles[groupe]
    return False

df["incoherent"] = df.apply(est_incoherent, axis=1)
incoherences = df[df["incoherent"] == True].copy()
incoherences["type_alerte"] = "Incohérence département/groupe"

print(f"Incohérences détectées : {len(incoherences)}")

# --- Fusion des deux types d'alertes dans un seul rapport ---
colonnes_rapport = ["id", "nom", "departement", "groupe_ad", "derniere_connexion", "type_alerte"]

rapport = pd.concat([
    comptes_inactifs[colonnes_rapport],
    incoherences[colonnes_rapport]
], ignore_index=True)

rapport.to_csv("data/processed/alertes_securite.csv", index=False)
print(f"\nRapport exporté : data/processed/alertes_securite.csv")
print(f"Total d'alertes : {len(rapport)}")