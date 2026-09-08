# Phase 1 — Script d'entraînement autonome, le tout premier du projet.
# Il ne dépend d'aucun module de core/ et n'est appelé par rien d'autre :
# c'est un exercice isolé pour manipuler des listes de dictionnaires Python
# avant d'introduire pandas/Faker dans les phases suivantes (phase2_export_ad.py).
#
# On représente chaque utilisateur AD par un dictionnaire :
# clé = nom du champ (comme une colonne AD), valeur = donnée réelle
utilisateurs = [
    {"nom": "Amira Ben Salah", "departement": "Finance", "groupe": "Accès_Comptabilité"},
    {"nom": "Karim Trabelsi", "departement": "IT", "groupe": "Admins_Serveurs"},
    {"nom": "Sarra Jendoubi", "departement": "Marketing", "groupe": "Accès_Standard"},
    {"nom": "Youssef Gharbi", "departement": "Sécurité", "groupe": "Admins_Domaine"},
    {"nom": "Ines Chaabane", "departement": "RH", "groupe": "Accès_RH"},
]

# On boucle sur chaque dictionnaire de la liste
for utilisateur in utilisateurs:
    nom = utilisateur["nom"]
    dept = utilisateur["departement"]
    groupe = utilisateur["groupe"]
    print(f"{nom} | Département: {dept} | Groupe: {groupe}")