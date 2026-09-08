# Phase 4 — Trois graphiques matplotlib à partir du rapport d'alertes
# (sortie de phase3_audit.py). Script autonome, non relié à core/ : les
# graphiques équivalents dans le dashboard (dashboard.py) sont recalculés en
# direct avec st.bar_chart plutôt que sauvegardés en PNG.
import pandas as pd
import matplotlib.pyplot as plt

# On recharge le rapport d'alertes généré en Phase 3
df = pd.read_csv("data/processed/alertes_securite.csv")

# --- Graphique 1 : nombre d'alertes par type ---
compte_par_type = df["type_alerte"].value_counts()

plt.figure(figsize=(8, 5))
compte_par_type.plot(kind="bar", color=["#c0392b", "#e67e22"])
plt.title("Répartition des alertes par type")
plt.xlabel("Type d'alerte")
plt.ylabel("Nombre d'alertes")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("outputs/repartition_alertes.png")
plt.show()

# --- Graphique 2 : comptes inactifs par département ---
inactifs = df[df["type_alerte"] == "Compte inactif > 90 jours"]
inactifs_par_dept = inactifs["departement"].value_counts()

plt.figure(figsize=(8, 5))
inactifs_par_dept.plot(kind="bar", color="#2980b9")
plt.title("Comptes inactifs (>90j) par département")
plt.xlabel("Département")
plt.ylabel("Nombre de comptes inactifs")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("outputs/inactifs_par_departement.png")
plt.show()

# --- Graphique 3 : incohérences par groupe AD ---
incoherences = df[df["type_alerte"] == "Incohérence département/groupe"]
incoherences_par_groupe = incoherences["groupe_ad"].value_counts()

plt.figure(figsize=(8, 5))
incoherences_par_groupe.plot(kind="bar", color="#8e44ad")
plt.title("Incohérences département/groupe par groupe AD")
plt.xlabel("Groupe AD")
plt.ylabel("Nombre d'incohérences")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("outputs/incoherences_par_groupe.png")
plt.show()

print("3 graphiques générés dans le dossier outputs/")