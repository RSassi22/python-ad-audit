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