# Script de vérification d'environnement (indépendant du reste du projet) :
# à lancer une fois après `pip install -r requirements.txt` pour confirmer
# que les librairies principales s'importent sans erreur. N'est appelé par
# aucun autre fichier ni par les tests pytest (tests/) ou la CI.
import pandas as pd
import faker
import openpyxl
import matplotlib

print("Tout est installé correctement !")
print(f"Pandas version : {pd.__version__}")